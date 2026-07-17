use std::time::Duration;

use anyhow::Result;
use crossterm::event::{self, Event, KeyEventKind};
use donna::{app::App, config::Config, ui};

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.iter().any(|arg| arg == "--help" || arg == "-h") {
        println!(
            "donna — your local-first personal command center\n\nUSAGE:\n    donna                 Open the dashboard\n    donna config path     Print the config path\n    donna config example  Print an example config\n\nKEYS:\n    Tab/arrows navigate · Enter focus · : ask · ? help · q quit"
        );
        return Ok(());
    }
    if args.as_slice() == ["config", "path"] {
        println!(
            "{}",
            Config::path().map_or_else(|| "unavailable".into(), |path| path.display().to_string())
        );
        return Ok(());
    }
    if args.as_slice() == ["config", "example"] {
        print!("{}", Config::example()?);
        return Ok(());
    }
    if !args.is_empty() {
        anyhow::bail!("unknown arguments; run donna --help");
    }

    let config = Config::load()?;
    let tick_rate = Duration::from_millis(config.ui.tick_rate_ms.max(50));
    let mut app = App::new(config);
    let mut terminal = ratatui::init();
    let result = run(&mut terminal, &mut app, tick_rate);
    ratatui::restore();
    result
}

fn run(terminal: &mut ratatui::DefaultTerminal, app: &mut App, tick_rate: Duration) -> Result<()> {
    loop {
        terminal.draw(|frame| ui::render(frame, app))?;
        if app.should_quit {
            return Ok(());
        }
        if event::poll(tick_rate)? {
            match event::read()? {
                Event::Key(key) if key.kind == KeyEventKind::Press => app.handle_key(key),
                Event::Resize(_, _) => {}
                _ => {}
            }
        }
    }
}
