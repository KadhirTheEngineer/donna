use chrono::{DateTime, Local, Utc};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Healthy,
    Working,
    Attention,
    Offline,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Event {
    pub id: String,
    pub source: String,
    pub source_id: String,
    pub time: String,
    pub title: String,
    pub calendar: String,
    pub location: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Task {
    pub id: String,
    pub source: String,
    pub source_id: String,
    pub title: String,
    pub project: String,
    pub due: String,
    pub priority: u8,
    pub done: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct MailItem {
    pub id: String,
    pub source: String,
    pub source_id: String,
    pub sender: String,
    pub subject: String,
    pub received: String,
    pub reason: String,
    pub unread: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Job {
    pub id: String,
    pub source: String,
    pub source_id: String,
    pub title: String,
    pub state: Status,
    pub progress: u16,
    pub detail: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct MarketItem {
    pub id: String,
    pub source: String,
    pub source_id: String,
    pub symbol: String,
    pub price: String,
    pub change: f64,
    pub note: String,
}

#[derive(Clone, Debug)]
pub struct Briefing {
    pub greeting: String,
    pub summary: String,
    pub events: Vec<Event>,
    pub tasks: Vec<Task>,
    pub mail: Vec<MailItem>,
    pub jobs: Vec<Job>,
    pub markets: Vec<MarketItem>,
    pub updated_at: DateTime<Local>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FreshnessState {
    Current,
    Stale,
    Partial,
    Failed,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Freshness {
    pub state: FreshnessState,
    pub source_updated_at: DateTime<Utc>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CachePolicy {
    AllowLocal,
    MemoryOnly,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct DashboardSnapshot {
    pub schema_version: String,
    pub generated_at: DateTime<Utc>,
    pub freshness: Freshness,
    pub cache_policy: CachePolicy,
    pub greeting: String,
    pub summary: String,
    pub events: Vec<Event>,
    pub tasks: Vec<Task>,
    pub mail: Vec<MailItem>,
    pub jobs: Vec<Job>,
    pub markets: Vec<MarketItem>,
}

impl From<DashboardSnapshot> for Briefing {
    fn from(snapshot: DashboardSnapshot) -> Self {
        Self {
            greeting: snapshot.greeting,
            summary: snapshot.summary,
            events: snapshot.events,
            tasks: snapshot.tasks,
            mail: snapshot.mail,
            jobs: snapshot.jobs,
            markets: snapshot.markets,
            updated_at: snapshot.freshness.source_updated_at.with_timezone(&Local),
        }
    }
}

impl Briefing {
    pub fn demo() -> Self {
        let snapshot: DashboardSnapshot = serde_json::from_str(include_str!(
            "../contracts/examples/dashboard-snapshot.v1.json"
        ))
        .expect("checked-in dashboard fixture must match the Rust contract");
        snapshot.into()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shared_dashboard_fixture_deserializes() {
        let briefing = Briefing::demo();
        assert_eq!(briefing.events[0].id, "event-demo-1");
        assert_eq!(briefing.jobs[0].state, Status::Healthy);
    }
}
