use chrono::{DateTime, Duration, Local};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Status {
    Healthy,
    Working,
    Attention,
    Offline,
}

#[derive(Clone, Debug)]
pub struct Event {
    pub time: String,
    pub title: String,
    pub calendar: String,
    pub location: Option<String>,
}

#[derive(Clone, Debug)]
pub struct Task {
    pub title: String,
    pub project: String,
    pub due: String,
    pub priority: u8,
    pub done: bool,
}

#[derive(Clone, Debug)]
pub struct MailItem {
    pub sender: String,
    pub subject: String,
    pub received: String,
    pub reason: String,
    pub unread: bool,
}

#[derive(Clone, Debug)]
pub struct Job {
    pub title: String,
    pub state: Status,
    pub progress: u16,
    pub detail: String,
}

#[derive(Clone, Debug)]
pub struct MarketItem {
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

impl Briefing {
    pub fn demo() -> Self {
        let now = Local::now();
        Self {
            greeting: "Good afternoon, Kadhir.".into(),
            summary: "A focused day: two meetings remain, one email needs a reply, and Donna is researching three companies on your watchlist.".into(),
            events: vec![
                Event { time: "2:00 PM".into(), title: "Product sync".into(), calendar: "Work".into(), location: Some("Google Meet".into()) },
                Event { time: "4:30 PM".into(), title: "Dentist appointment".into(), calendar: "Personal".into(), location: Some("Oak Park".into()) },
                Event { time: "7:00 PM".into(), title: "Dinner with Arun".into(), calendar: "Personal".into(), location: None },
                Event { time: "Tomorrow".into(), title: "Deep work: Donna API".into(), calendar: "Focus".into(), location: None },
            ],
            tasks: vec![
                Task { title: "Review quarterly budget".into(), project: "Finance".into(), due: "Today".into(), priority: 3, done: false },
                Task { title: "Reply to Maya".into(), project: "Inbox".into(), due: "Today".into(), priority: 2, done: false },
                Task { title: "Order replacement filters".into(), project: "Home".into(), due: "Fri".into(), priority: 1, done: false },
                Task { title: "Outline orchestrator contract".into(), project: "Donna".into(), due: "Sat".into(), priority: 2, done: false },
            ],
            mail: vec![
                MailItem { sender: "Maya Chen".into(), subject: "Re: Friday launch checklist".into(), received: "18m".into(), reason: "Direct question; reply requested today".into(), unread: true },
                MailItem { sender: "Google Calendar".into(), subject: "Updated: Product sync".into(), received: "1h".into(), reason: "Meeting moved by 30 minutes".into(), unread: true },
                MailItem { sender: "Fidelity".into(), subject: "Your monthly statement is ready".into(), received: "3h".into(), reason: "Financial document".into(), unread: false },
            ],
            jobs: vec![
                Job { title: "Semiconductor watchlist brief".into(), state: Status::Working, progress: 68, detail: "Reading earnings transcripts · 14 sources".into() },
                Job { title: "Morning inbox triage".into(), state: Status::Healthy, progress: 100, detail: "42 messages classified · 3 surfaced".into() },
                Job { title: "CPI + rates weekly context".into(), state: Status::Working, progress: 31, detail: "Collecting primary sources".into() },
            ],
            markets: vec![
                MarketItem { symbol: "SPY".into(), price: "$624.18".into(), change: 0.42, note: "Broad market".into() },
                MarketItem { symbol: "NVDA".into(), price: "$177.91".into(), change: 1.28, note: "Watchlist".into() },
                MarketItem { symbol: "10Y".into(), price: "4.22%".into(), change: -0.03, note: "Treasury yield".into() },
                MarketItem { symbol: "VIX".into(), price: "16.40".into(), change: -2.10, note: "Volatility".into() },
            ],
            updated_at: now - Duration::seconds(12),
        }
    }
}
