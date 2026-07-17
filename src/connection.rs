use std::{
    error::Error,
    fmt,
    sync::mpsc::{self, Receiver, Sender},
    thread,
    time::Duration,
};

use anyhow::{Context, Result, anyhow, bail};
use base64::{Engine, engine::general_purpose::URL_SAFE_NO_PAD};
use chrono::{SecondsFormat, Utc};
use hmac::{Hmac, Mac};
use keyring::Entry;
use rand::RngCore;
use reqwest::{
    Method,
    blocking::Client,
    header::{HeaderMap, HeaderName, HeaderValue},
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tungstenite::{Message, client::IntoClientRequest};

use crate::{cache, config::ServerConfig, model::DashboardSnapshot};

type HmacSha256 = Hmac<Sha256>;

#[derive(Debug)]
struct AuthenticationRequiredError;

impl fmt::Display for AuthenticationRequiredError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("device authentication expired; run `donna pair` again")
    }
}

impl Error for AuthenticationRequiredError {}

const DEVICE_ID: &str = "X-Donna-Device-Id";
const TIMESTAMP: &str = "X-Donna-Timestamp";
const NONCE: &str = "X-Donna-Nonce";
const SIGNATURE: &str = "X-Donna-Signature";

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct DeviceCredential {
    pub device_id: String,
    pub secret: String,
}

#[derive(Debug)]
pub enum ConnectionEvent {
    Snapshot(DashboardSnapshot),
    State(ConnectionState),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ConnectionState {
    Demo,
    Connecting,
    Online,
    Stale(String),
    AuthenticationRequired,
}

#[derive(Debug, Deserialize)]
struct PairingResponse {
    device_id: String,
    secret: String,
}

#[derive(Serialize)]
struct PairingRequest<'a> {
    code: &'a str,
    friendly_name: &'a str,
    capabilities: [&'a str; 2],
}

#[derive(Debug, Deserialize)]
struct EventEnvelope {
    sequence: u64,
    #[serde(rename = "type")]
    event_type: String,
}

fn credential_entry(server_url: &str) -> Result<Entry> {
    let digest = Sha256::digest(server_url.as_bytes());
    let digest_text = format!("{digest:x}");
    let account = format!("device-{}", &digest_text[..16]);
    Entry::new("donna", &account).context("open platform credential store")
}

pub fn store_credential(server_url: &str, credential: &DeviceCredential) -> Result<()> {
    credential_entry(server_url)?
        .set_password(&serde_json::to_string(credential)?)
        .context("store Donna device credential in the platform credential store")
}

pub fn load_credential(server_url: &str) -> Result<Option<DeviceCredential>> {
    match credential_entry(server_url)?.get_password() {
        Ok(raw) => Ok(Some(
            serde_json::from_str(&raw).context("parse stored Donna device credential")?,
        )),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(error) => Err(error).context("read Donna device credential from platform store"),
    }
}

pub fn pair_device(server: &ServerConfig, code: &str) -> Result<String> {
    if code.len() != 6 || !code.bytes().all(|byte| byte.is_ascii_digit()) {
        bail!("pairing code must contain exactly six digits");
    }
    let client = Client::builder().timeout(Duration::from_secs(10)).build()?;
    let response = client
        .post(format!(
            "{}/v1/pairing/complete",
            server.url.trim_end_matches('/')
        ))
        .json(&PairingRequest {
            code,
            friendly_name: &server.device_name,
            capabilities: ["dashboard.read", "events.read"],
        })
        .send()
        .context("connect to Donna pairing endpoint")?;
    if !response.status().is_success() {
        bail!("pairing failed with server status {}", response.status());
    }
    let paired: PairingResponse = response.json().context("parse pairing response")?;
    let credential = DeviceCredential {
        device_id: paired.device_id,
        secret: paired.secret,
    };
    store_credential(&server.url, &credential)?;
    Ok(credential.device_id)
}

pub fn start(server: ServerConfig, initial_sequence: u64) -> Receiver<ConnectionEvent> {
    let (sender, receiver) = mpsc::channel();
    thread::Builder::new()
        .name("donna-connection".into())
        .spawn(move || connection_loop(server, initial_sequence, sender))
        .expect("spawn Donna connection thread");
    receiver
}

fn connection_loop(server: ServerConfig, mut sequence: u64, sender: Sender<ConnectionEvent>) {
    let credential = match load_credential(&server.url) {
        Ok(Some(credential)) => credential,
        Ok(None) => {
            let _ = sender.send(ConnectionEvent::State(
                ConnectionState::AuthenticationRequired,
            ));
            return;
        }
        Err(error) => {
            let _ = sender.send(ConnectionEvent::State(ConnectionState::Stale(
                error.to_string(),
            )));
            return;
        }
    };
    let client = match Client::builder().timeout(Duration::from_secs(10)).build() {
        Ok(client) => client,
        Err(error) => {
            let _ = sender.send(ConnectionEvent::State(ConnectionState::Stale(
                error.to_string(),
            )));
            return;
        }
    };
    let mut backoff = Duration::from_secs(1);
    loop {
        let _ = sender.send(ConnectionEvent::State(ConnectionState::Connecting));
        match connected_session(&client, &server, &credential, &mut sequence, &sender) {
            Ok(()) => backoff = Duration::from_secs(1),
            Err(error) => {
                if error
                    .downcast_ref::<AuthenticationRequiredError>()
                    .is_some()
                {
                    let _ = sender.send(ConnectionEvent::State(
                        ConnectionState::AuthenticationRequired,
                    ));
                    return;
                }
                let _ = sender.send(ConnectionEvent::State(ConnectionState::Stale(
                    error.to_string(),
                )));
                thread::sleep(backoff);
                backoff = (backoff * 2).min(Duration::from_secs(30));
            }
        }
    }
}

fn connected_session(
    client: &Client,
    server: &ServerConfig,
    credential: &DeviceCredential,
    sequence: &mut u64,
    sender: &Sender<ConnectionEvent>,
) -> Result<()> {
    refresh_snapshot(client, server, credential, *sequence, sender)?;
    sender.send(ConnectionEvent::State(ConnectionState::Online))?;

    let http_url = server.url.trim_end_matches('/');
    let websocket_base = http_url
        .strip_prefix("http://")
        .map(|value| format!("ws://{value}"))
        .or_else(|| {
            http_url
                .strip_prefix("https://")
                .map(|value| format!("wss://{value}"))
        })
        .context("server URL must use http or https")?;
    let websocket_url = format!("{websocket_base}/v1/events?after={sequence}");
    let mut request = websocket_url.into_client_request()?;
    let signed = signed_values(credential, "GET", "/v1/events", b"")?;
    for (name, value) in signed {
        request.headers_mut().insert(
            HeaderName::from_bytes(name.as_bytes())?,
            HeaderValue::from_str(&value)?,
        );
    }
    let (mut socket, _) = tungstenite::connect(request).context("connect to Donna event stream")?;
    loop {
        let message = socket.read().context("read Donna event stream")?;
        if let Message::Text(text) = message {
            let event: EventEnvelope = serde_json::from_str(&text)?;
            if event.sequence <= *sequence {
                continue;
            }
            *sequence = (*sequence).max(event.sequence);
            if matches!(
                event.event_type.as_str(),
                "dashboard.invalidated" | "events.replay_expired"
            ) {
                refresh_snapshot(client, server, credential, *sequence, sender)?;
            }
        }
    }
}

fn refresh_snapshot(
    client: &Client,
    server: &ServerConfig,
    credential: &DeviceCredential,
    sequence: u64,
    sender: &Sender<ConnectionEvent>,
) -> Result<()> {
    let path = "/v1/dashboard";
    let headers = signed_headers(credential, "GET", path, b"")?;
    let response = client
        .request(
            Method::GET,
            format!("{}{path}?window=today", server.url.trim_end_matches('/')),
        )
        .headers(headers)
        .send()
        .context("request dashboard snapshot")?;
    if response.status() == reqwest::StatusCode::UNAUTHORIZED {
        return Err(AuthenticationRequiredError.into());
    }
    if !response.status().is_success() {
        bail!("dashboard request failed with status {}", response.status());
    }
    let snapshot: DashboardSnapshot = response.json().context("parse dashboard snapshot")?;
    if snapshot.schema_version != "1.0" {
        bail!("unsupported dashboard schema {}", snapshot.schema_version);
    }
    cache::save(&snapshot, sequence)?;
    sender.send(ConnectionEvent::Snapshot(snapshot))?;
    Ok(())
}

fn signed_headers(
    credential: &DeviceCredential,
    method: &str,
    path: &str,
    body: &[u8],
) -> Result<HeaderMap> {
    let mut headers = HeaderMap::new();
    for (name, value) in signed_values(credential, method, path, body)? {
        headers.insert(
            HeaderName::from_bytes(name.as_bytes())?,
            HeaderValue::from_str(&value)?,
        );
    }
    Ok(headers)
}

fn signed_values(
    credential: &DeviceCredential,
    method: &str,
    path: &str,
    body: &[u8],
) -> Result<[(String, String); 4]> {
    let timestamp = Utc::now().to_rfc3339_opts(SecondsFormat::Millis, true);
    let mut nonce_bytes = [0_u8; 16];
    rand::rng().fill_bytes(&mut nonce_bytes);
    let nonce = URL_SAFE_NO_PAD.encode(nonce_bytes);
    let secret = URL_SAFE_NO_PAD
        .decode(&credential.secret)
        .context("decode stored device credential")?;
    let signature = signature_for(&secret, method, path, &timestamp, &nonce, body)?;
    Ok([
        (DEVICE_ID.into(), credential.device_id.clone()),
        (TIMESTAMP.into(), timestamp),
        (NONCE.into(), nonce),
        (SIGNATURE.into(), signature),
    ])
}

fn signature_for(
    secret: &[u8],
    method: &str,
    path: &str,
    timestamp: &str,
    nonce: &str,
    body: &[u8],
) -> Result<String> {
    let body_digest = format!("{:x}", Sha256::digest(body));
    let message = format!(
        "{}\n{path}\n{timestamp}\n{nonce}\n{body_digest}",
        method.to_ascii_uppercase()
    );
    let mut mac = HmacSha256::new_from_slice(secret).map_err(|_| anyhow!("invalid HMAC key"))?;
    mac.update(message.as_bytes());
    Ok(format!("{:x}", mac.finalize().into_bytes()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Deserialize)]
    struct SignatureFixture {
        secret_base64url: String,
        method: String,
        path: String,
        timestamp: String,
        nonce: String,
        signature: String,
    }

    #[test]
    fn signing_headers_do_not_contain_the_secret() {
        let credential = DeviceCredential {
            device_id: "device_test".into(),
            secret: URL_SAFE_NO_PAD.encode([7_u8; 32]),
        };
        let values = signed_values(&credential, "GET", "/v1/dashboard", b"").unwrap();
        assert!(values.iter().all(|(_, value)| value != &credential.secret));
        assert_eq!(values[0].1, "device_test");
    }

    #[test]
    fn signature_matches_shared_cross_language_fixture() {
        let fixture: SignatureFixture =
            serde_json::from_str(include_str!("../contracts/examples/auth-signature.v1.json"))
                .unwrap();
        let secret = URL_SAFE_NO_PAD.decode(fixture.secret_base64url).unwrap();
        let actual = signature_for(
            &secret,
            &fixture.method,
            &fixture.path,
            &fixture.timestamp,
            &fixture.nonce,
            b"",
        )
        .unwrap();
        assert_eq!(actual, fixture.signature);
    }
}
