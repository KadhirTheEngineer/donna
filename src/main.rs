use std::{io, sync::mpsc::Receiver, time::Duration};

use anyhow::Result;
use crossterm::event::{self, Event, KeyEventKind};
use donna::{
    app::App,
    cache,
    config::Config,
    connection::{self, ConnectionEvent, ConnectionState},
    ui,
};

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.iter().any(|arg| arg == "--help" || arg == "-h") {
        println!(
            "donna — your local-first personal command center\n\nUSAGE:\n    donna                 Open the dashboard\n    donna pair            Pair without putting the code in process arguments\n    donna config path     Print the config path\n    donna config example  Print an example config\n\nKEYS:\n    Tab/arrows navigate · Enter focus · : ask · ? help · q quit"
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
    if args.as_slice() == ["pair"] {
        let config = Config::load()?;
        eprint!("Pairing code: ");
        let mut code = String::new();
        io::stdin().read_line(&mut code)?;
        let device_id = connection::pair_device(&config.server, code.trim())?;
        println!(
            "Paired device {}. The credential is stored by the operating system.",
            device_id
        );
        return Ok(());
    }
    if !args.is_empty() {
        anyhow::bail!("unknown arguments; run donna --help");
    }

    let config = Config::load()?;
    let tick_rate = Duration::from_millis(config.ui.tick_rate_ms.max(50));
    let mut app = App::new(config.clone());
    let receiver = if config.ui.show_demo_data {
        None
    } else {
        let cached = match cache::load() {
            Ok(cached) => cached,
            Err(error) => {
                app.apply_connection_event(ConnectionEvent::State(ConnectionState::Stale(
                    format!("local cache unavailable: {error}"),
                )));
                None
            }
        };
        let initial_sequence = cached.as_ref().map_or(0, |value| value.last_sequence);
        if let Some(cached) = cached {
            app.apply_connection_event(ConnectionEvent::Snapshot(cached.snapshot));
            app.apply_connection_event(ConnectionEvent::State(ConnectionState::Stale(
                "showing cached data while reconnecting".into(),
            )));
        }
        Some(connection::start(config.server.clone(), initial_sequence))
    };
    let mut terminal = ratatui::init();
    let result = run(&mut terminal, &mut app, tick_rate, receiver.as_ref());
    ratatui::restore();
    result
}

fn run(
    terminal: &mut ratatui::DefaultTerminal,
    app: &mut App,
    tick_rate: Duration,
    receiver: Option<&Receiver<ConnectionEvent>>,
) -> Result<()> {
    loop {
        if let Some(receiver) = receiver {
            while let Ok(event) = receiver.try_recv() {
                app.apply_connection_event(event);
            }
        }
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
