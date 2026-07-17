use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};

use crate::{config::Config, model::Briefing};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Panel {
    Calendar,
    Tasks,
    Mail,
    Research,
    Markets,
}

impl Panel {
    pub const ALL: [Self; 5] = [
        Self::Calendar,
        Self::Tasks,
        Self::Mail,
        Self::Research,
        Self::Markets,
    ];
    pub fn title(self) -> &'static str {
        match self {
            Self::Calendar => "Calendar",
            Self::Tasks => "Tasks",
            Self::Mail => "Attention",
            Self::Research => "Research",
            Self::Markets => "Markets",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Overlay {
    Help,
    Command,
    Permissions,
}

#[derive(Debug)]
pub struct App {
    pub briefing: Briefing,
    pub config: Config,
    pub selected: usize,
    pub focused: Option<Panel>,
    pub overlay: Option<Overlay>,
    pub command: String,
    pub toast: Option<String>,
    pub should_quit: bool,
}

impl App {
    pub fn new(config: Config) -> Self {
        Self {
            briefing: Briefing::demo(),
            config,
            selected: 0,
            focused: None,
            overlay: None,
            command: String::new(),
            toast: Some("Demo mode · server disconnected".into()),
            should_quit: false,
        }
    }
    pub fn panel(&self) -> Panel {
        Panel::ALL[self.selected]
    }
    pub fn handle_key(&mut self, key: KeyEvent) {
        if self.overlay == Some(Overlay::Command) {
            self.handle_command_key(key);
            return;
        }
        if self.overlay.is_some() {
            if matches!(
                key.code,
                KeyCode::Esc | KeyCode::Char('?') | KeyCode::Char('q')
            ) {
                self.overlay = None;
            }
            return;
        }
        match key.code {
            KeyCode::Char('q') if self.focused.is_none() => self.should_quit = true,
            KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.should_quit = true
            }
            KeyCode::Char('?') => self.overlay = Some(Overlay::Help),
            KeyCode::Char(':') | KeyCode::Char('/') => {
                self.command.clear();
                self.overlay = Some(Overlay::Command);
            }
            KeyCode::Char('p') => self.overlay = Some(Overlay::Permissions),
            KeyCode::Esc => self.focused = None,
            KeyCode::Enter => self.focused = Some(self.panel()),
            KeyCode::Tab | KeyCode::Right | KeyCode::Char('l') => {
                self.selected = (self.selected + 1) % Panel::ALL.len()
            }
            KeyCode::BackTab | KeyCode::Left | KeyCode::Char('h') => {
                self.selected = (self.selected + Panel::ALL.len() - 1) % Panel::ALL.len()
            }
            KeyCode::Down | KeyCode::Char('j') => {
                self.selected = (self.selected + 1) % Panel::ALL.len()
            }
            KeyCode::Up | KeyCode::Char('k') => {
                self.selected = (self.selected + Panel::ALL.len() - 1) % Panel::ALL.len()
            }
            KeyCode::Char('1'..='5') => {
                if let KeyCode::Char(c) = key.code {
                    self.selected = c.to_digit(10).unwrap() as usize - 1;
                }
            }
            KeyCode::Char('r') => self.toast = Some("Refresh queued · demo data unchanged".into()),
            _ => {}
        }
    }
    fn handle_command_key(&mut self, key: KeyEvent) {
        match key.code {
            KeyCode::Esc => {
                self.overlay = None;
                self.command.clear();
            }
            KeyCode::Enter => {
                let command = std::mem::take(&mut self.command);
                self.overlay = None;
                self.run_command(command.trim());
            }
            KeyCode::Backspace => {
                self.command.pop();
            }
            KeyCode::Char(c) if !key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.command.push(c)
            }
            _ => {}
        }
    }
    fn run_command(&mut self, command: &str) {
        match command.to_ascii_lowercase().as_str() {
            "calendar" | "cal" => self.focus(Panel::Calendar),
            "tasks" | "todo" => self.focus(Panel::Tasks),
            "mail" | "inbox" => self.focus(Panel::Mail),
            "research" | "jobs" => self.focus(Panel::Research),
            "markets" | "finance" => self.focus(Panel::Markets),
            "permissions" | "perms" => self.overlay = Some(Overlay::Permissions),
            "help" | "?" => self.overlay = Some(Overlay::Help),
            "quit" | "exit" => self.should_quit = true,
            "" => {}
            other => self.toast = Some(format!("Ask Donna: “{other}” · backend not connected")),
        }
    }
    fn focus(&mut self, panel: Panel) {
        self.selected = Panel::ALL.iter().position(|p| *p == panel).unwrap();
        self.focused = Some(panel);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn navigation_wraps() {
        let mut app = App::new(Config::default());
        app.handle_key(KeyEvent::new(KeyCode::Left, KeyModifiers::NONE));
        assert_eq!(app.panel(), Panel::Markets);
    }
    #[test]
    fn command_focuses_panel() {
        let mut app = App::new(Config::default());
        app.run_command("tasks");
        assert_eq!(app.focused, Some(Panel::Tasks));
    }
}
