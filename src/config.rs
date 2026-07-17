use std::{fs, path::PathBuf};

use anyhow::{Context, Result};
use directories::ProjectDirs;
use serde::{Deserialize, Serialize};
use url::Url;

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(default)]
pub struct Config {
    pub server: ServerConfig,
    pub ui: UiConfig,
    pub permissions: Permissions,
    pub workspaces: Vec<PathBuf>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default)]
pub struct ServerConfig {
    pub url: String,
    pub device_name: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default)]
pub struct UiConfig {
    pub tick_rate_ms: u64,
    pub compact_width: u16,
    pub show_demo_data: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default)]
pub struct Permissions {
    pub mode: PermissionMode,
    pub read_files: Decision,
    pub write_files: Decision,
    pub delete_files: Decision,
    pub run_commands: Decision,
    pub send_email: Decision,
    pub modify_calendar: Decision,
    pub modify_tasks: Decision,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Decision {
    Allow,
    Ask,
    Deny,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PermissionMode {
    Guarded,
    Yolo,
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            url: "http://127.0.0.1:8742".into(),
            device_name: hostname(),
        }
    }
}
impl Default for UiConfig {
    fn default() -> Self {
        Self {
            tick_rate_ms: 250,
            compact_width: 82,
            show_demo_data: true,
        }
    }
}
impl Default for Permissions {
    fn default() -> Self {
        Self {
            mode: PermissionMode::Guarded,
            read_files: Decision::Allow,
            write_files: Decision::Ask,
            delete_files: Decision::Ask,
            run_commands: Decision::Ask,
            send_email: Decision::Ask,
            modify_calendar: Decision::Ask,
            modify_tasks: Decision::Ask,
        }
    }
}

impl Config {
    pub fn load() -> Result<Self> {
        let Some(path) = Self::path() else {
            return Ok(Self::default());
        };
        if !path.exists() {
            return Ok(Self::default());
        }
        let raw = fs::read_to_string(&path)
            .with_context(|| format!("read config at {}", path.display()))?;
        let config: Self =
            toml::from_str(&raw).with_context(|| format!("parse config at {}", path.display()))?;
        config.validate()?;
        Ok(config)
    }

    pub fn path() -> Option<PathBuf> {
        ProjectDirs::from("dev", "kadhirtheengineer", "donna")
            .map(|d| d.config_dir().join("config.toml"))
    }

    pub fn example() -> Result<String> {
        toml::to_string_pretty(&Self::default()).context("serialize example config")
    }

    pub fn validate(&self) -> Result<()> {
        let url = Url::parse(&self.server.url).context("server.url must be an absolute URL")?;
        let host = url.host_str().context("server.url must include a host")?;
        let loopback = matches!(host, "127.0.0.1" | "::1" | "localhost");
        if url.scheme() == "http" && !loopback {
            anyhow::bail!("server.url may use cleartext HTTP only for a loopback host");
        }
        if !matches!(url.scheme(), "http" | "https") {
            anyhow::bail!("server.url must use http or https");
        }
        if !url.username().is_empty() || url.password().is_some() {
            anyhow::bail!("server.url must not contain credentials");
        }
        if url.path() != "/" || url.query().is_some() || url.fragment().is_some() {
            anyhow::bail!("server.url must not contain a path, query, or fragment");
        }
        Ok(())
    }
}

fn hostname() -> String {
    std::env::var("HOSTNAME")
        .or_else(|_| std::env::var("COMPUTERNAME"))
        .unwrap_or_else(|_| "donna-client".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn defaults_round_trip() {
        let encoded = Config::example().unwrap();
        let decoded: Config = toml::from_str(&encoded).unwrap();
        assert_eq!(decoded.permissions.write_files, Decision::Ask);
        assert_eq!(decoded.permissions.mode, PermissionMode::Guarded);
        decoded.validate().unwrap();
    }

    #[test]
    fn cleartext_lan_server_is_rejected() {
        let config = Config {
            server: ServerConfig {
                url: "http://192.0.2.1:8742".into(),
                ..ServerConfig::default()
            },
            ..Config::default()
        };
        assert!(config.validate().is_err());
    }
}
