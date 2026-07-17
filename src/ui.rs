use ratatui::{
    Frame,
    layout::{Alignment, Constraint, Layout, Margin, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
    widgets::{Block, Borders, Clear, Gauge, List, ListItem, Padding, Paragraph, Row, Table, Wrap},
};

use crate::{
    app::{App, Overlay, Panel},
    config::{Decision, PermissionMode},
    model::Status,
};

const BG: Color = Color::Rgb(12, 17, 23);
const PANEL_BG: Color = Color::Rgb(18, 25, 33);
const BORDER: Color = Color::Rgb(44, 55, 67);
const MUTED: Color = Color::Rgb(117, 132, 148);
const TEXT: Color = Color::Rgb(222, 230, 238);
const CYAN: Color = Color::Rgb(74, 222, 203);
const BLUE: Color = Color::Rgb(96, 165, 250);
const GOLD: Color = Color::Rgb(250, 204, 21);
const RED: Color = Color::Rgb(248, 113, 113);

pub fn render(frame: &mut Frame, app: &App) {
    let area = frame.area();
    frame.render_widget(Block::new().style(Style::new().bg(BG)), area);
    if area.width < 60 || area.height < 18 {
        frame.render_widget(
            Paragraph::new("DONNA\n\nTerminal too small. Resize to at least 60 × 18.")
                .alignment(Alignment::Center)
                .style(Style::new().fg(TEXT).bg(BG))
                .block(Block::bordered().border_style(Style::new().fg(CYAN))),
            area,
        );
        return;
    }
    let root = Layout::vertical([
        Constraint::Length(3),
        Constraint::Min(12),
        Constraint::Length(2),
    ])
    .split(area);
    render_header(frame, app, root[0]);
    if let Some(panel) = app.focused {
        render_panel(
            frame,
            app,
            panel,
            root[1].inner(Margin {
                horizontal: 2,
                vertical: 1,
            }),
        );
    } else if area.width < app.config.ui.compact_width {
        render_compact(frame, app, root[1]);
    } else {
        render_dashboard(frame, app, root[1]);
    }
    render_footer(frame, app, root[2]);
    match app.overlay {
        Some(Overlay::Help) => render_help(frame, area),
        Some(Overlay::Command) => render_command(frame, app, area),
        Some(Overlay::Permissions) => render_permissions(frame, app, area),
        None => {}
    }
}

fn render_header(frame: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::horizontal([
        Constraint::Length(25),
        Constraint::Min(20),
        Constraint::Length(27),
    ])
    .split(area);
    let underline = || {
        Block::new()
            .borders(Borders::BOTTOM)
            .border_style(Style::new().fg(BORDER))
    };
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled(
                " DONNA ",
                Style::new().fg(BG).bg(CYAN).add_modifier(Modifier::BOLD),
            ),
            Span::styled("  personal command", Style::new().fg(MUTED)),
        ]))
        .block(underline()),
        chunks[0],
    );
    frame.render_widget(
        Paragraph::new(app.briefing.greeting.as_str())
            .alignment(Alignment::Center)
            .style(Style::new().fg(TEXT).add_modifier(Modifier::BOLD))
            .block(underline()),
        chunks[1],
    );
    let ago = (chrono::Local::now() - app.briefing.updated_at)
        .num_seconds()
        .max(0);
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled("● ", Style::new().fg(GOLD)),
            Span::styled("DEMO", Style::new().fg(GOLD).add_modifier(Modifier::BOLD)),
            Span::styled(format!("  updated {ago}s ago "), Style::new().fg(MUTED)),
        ]))
        .alignment(Alignment::Right)
        .block(underline()),
        chunks[2],
    );
}

fn render_dashboard(frame: &mut Frame, app: &App, area: Rect) {
    let rows = Layout::vertical([Constraint::Percentage(52), Constraint::Percentage(48)])
        .margin(1)
        .split(area);
    let top = Layout::horizontal([
        Constraint::Percentage(34),
        Constraint::Percentage(33),
        Constraint::Percentage(33),
    ])
    .split(rows[0]);
    let bottom =
        Layout::horizontal([Constraint::Percentage(50), Constraint::Percentage(50)]).split(rows[1]);
    render_calendar(frame, app, top[0]);
    render_tasks(frame, app, top[1]);
    render_mail(frame, app, top[2]);
    render_research(frame, app, bottom[0]);
    render_markets(frame, app, bottom[1]);
}

fn render_compact(frame: &mut Frame, app: &App, area: Rect) {
    let inner = Layout::vertical([Constraint::Length(5), Constraint::Min(8)])
        .margin(1)
        .split(area);
    frame.render_widget(
        Paragraph::new(app.briefing.summary.as_str())
            .wrap(Wrap { trim: true })
            .style(Style::new().fg(TEXT))
            .block(panel_block("Daily brief", false)),
        inner[0],
    );
    render_panel(frame, app, app.panel(), inner[1]);
}

fn render_panel(frame: &mut Frame, app: &App, panel: Panel, area: Rect) {
    match panel {
        Panel::Calendar => render_calendar(frame, app, area),
        Panel::Tasks => render_tasks(frame, app, area),
        Panel::Mail => render_mail(frame, app, area),
        Panel::Research => render_research(frame, app, area),
        Panel::Markets => render_markets(frame, app, area),
    }
}

fn is_selected(app: &App, panel: Panel) -> bool {
    app.focused == Some(panel) || (app.focused.is_none() && app.panel() == panel)
}

fn panel_block(title: &str, active: bool) -> Block<'_> {
    Block::new()
        .title(Line::from(vec![
            Span::styled(
                if active { " ◆ " } else { " ◇ " },
                Style::new().fg(if active { CYAN } else { MUTED }),
            ),
            Span::styled(
                title,
                Style::new()
                    .fg(if active { TEXT } else { MUTED })
                    .add_modifier(Modifier::BOLD),
            ),
        ]))
        .borders(Borders::ALL)
        .border_style(Style::new().fg(if active { CYAN } else { BORDER }))
        .style(Style::new().bg(PANEL_BG))
        .padding(Padding::horizontal(1))
}

fn render_calendar(frame: &mut Frame, app: &App, area: Rect) {
    let items = app.briefing.events.iter().map(|e| {
        ListItem::new(Line::from(vec![
            Span::styled(
                format!("{:<9}", e.time),
                Style::new().fg(BLUE).add_modifier(Modifier::BOLD),
            ),
            Span::styled(&e.title, Style::new().fg(TEXT)),
            Span::styled(format!("  {}", e.calendar), Style::new().fg(MUTED)),
        ]))
    });
    frame.render_widget(
        List::new(items).block(panel_block(
            "Calendar · today",
            is_selected(app, Panel::Calendar),
        )),
        area,
    );
}

fn render_tasks(frame: &mut Frame, app: &App, area: Rect) {
    let items = app.briefing.tasks.iter().map(|task| {
        let mark = if task.done { "✓" } else { "○" };
        let color = if task.priority >= 3 {
            RED
        } else if task.priority == 2 {
            GOLD
        } else {
            MUTED
        };
        ListItem::new(Line::from(vec![
            Span::styled(
                format!("{mark} "),
                Style::new().fg(color).add_modifier(Modifier::BOLD),
            ),
            Span::styled(&task.title, Style::new().fg(TEXT)),
            Span::styled(
                format!("  {} · {}", task.project, task.due),
                Style::new().fg(MUTED),
            ),
        ]))
    });
    frame.render_widget(
        List::new(items).block(panel_block("Tasks · 2 due", is_selected(app, Panel::Tasks))),
        area,
    );
}

fn render_mail(frame: &mut Frame, app: &App, area: Rect) {
    let mut lines = Vec::new();
    for mail in &app.briefing.mail {
        lines.push(Line::from(vec![
            Span::styled(if mail.unread { "● " } else { "  " }, Style::new().fg(CYAN)),
            Span::styled(
                format!("{}  ", mail.sender),
                Style::new().fg(TEXT).add_modifier(Modifier::BOLD),
            ),
            Span::styled(&mail.received, Style::new().fg(MUTED)),
        ]));
        lines.push(Line::from(vec![
            Span::raw("  "),
            Span::styled(&mail.subject, Style::new().fg(TEXT)),
        ]));
    }
    frame.render_widget(
        Paragraph::new(lines)
            .block(panel_block(
                "Needs attention",
                is_selected(app, Panel::Mail),
            ))
            .wrap(Wrap { trim: true }),
        area,
    );
}

fn render_research(frame: &mut Frame, app: &App, area: Rect) {
    let block = panel_block("Research · running", is_selected(app, Panel::Research));
    let inner = block.inner(area);
    frame.render_widget(block, area);
    let chunks =
        Layout::vertical(app.briefing.jobs.iter().map(|_| Constraint::Length(3))).split(inner);
    for (job, slot) in app.briefing.jobs.iter().zip(chunks.iter()) {
        let label = format!("{} · {}%  {}", job.title, job.progress, job.detail);
        frame.render_widget(
            Gauge::default()
                .label(label)
                .ratio(f64::from(job.progress) / 100.0)
                .gauge_style(
                    Style::new()
                        .fg(status_color(job.state))
                        .bg(BORDER)
                        .add_modifier(Modifier::BOLD),
                )
                .use_unicode(true),
            *slot,
        );
    }
}

fn render_markets(frame: &mut Frame, app: &App, area: Rect) {
    let rows = app.briefing.markets.iter().map(|m| {
        Row::new(vec![
            m.symbol.clone(),
            m.price.clone(),
            format!("{:+.2}%", m.change),
            m.note.clone(),
        ])
        .style(Style::new().fg(TEXT))
    });
    let table = Table::new(
        rows,
        [
            Constraint::Length(8),
            Constraint::Length(12),
            Constraint::Length(10),
            Constraint::Min(10),
        ],
    )
    .header(
        Row::new(["Asset", "Value", "Move", "Context"])
            .style(Style::new().fg(MUTED).add_modifier(Modifier::BOLD)),
    )
    .column_spacing(1)
    .block(panel_block(
        "Markets · delayed demo",
        is_selected(app, Panel::Markets),
    ));
    frame.render_widget(table, area);
}

fn render_footer(frame: &mut Frame, app: &App, area: Rect) {
    let line = if let Some(toast) = &app.toast {
        Line::from(vec![
            Span::styled(format!(" {toast}"), Style::new().fg(GOLD)),
            Span::styled(
                "    Tab navigate  Enter focus  : ask  ? help  q quit ",
                Style::new().fg(MUTED),
            ),
        ])
    } else {
        Line::styled(
            " Tab navigate  Enter focus  Esc back  : ask Donna  p permissions  ? help  q quit",
            Style::new().fg(MUTED),
        )
    };
    frame.render_widget(
        Paragraph::new(line).style(Style::new().bg(Color::Rgb(9, 13, 18))),
        area,
    );
}

fn render_help(frame: &mut Frame, area: Rect) {
    let popup = centered(area, 68, 20);
    frame.render_widget(Clear, popup);
    let text = Text::from(vec![
        Line::styled("Move", Style::new().fg(CYAN).add_modifier(Modifier::BOLD)),
        Line::raw("  Tab / Shift-Tab     cycle widgets"),
        Line::raw("  h j k l / arrows    move selection"),
        Line::raw("  1…5                 jump to widget"),
        Line::raw("  Enter / Esc          focus / return"),
        Line::raw(""),
        Line::styled("Act", Style::new().fg(CYAN).add_modifier(Modifier::BOLD)),
        Line::raw("  : or /               command + ask bar"),
        Line::raw("  r                    refresh"),
        Line::raw("  p                    permission policy"),
        Line::raw("  ?                    this help"),
        Line::raw("  q / Ctrl-C           quit"),
        Line::raw(""),
        Line::styled(
            "Commands: calendar, tasks, mail, research, markets, permissions",
            Style::new().fg(MUTED),
        ),
    ]);
    frame.render_widget(
        Paragraph::new(text).block(panel_block("Keyboard", true)),
        popup,
    );
}

fn render_command(frame: &mut Frame, app: &App, area: Rect) {
    let popup = centered(area, area.width.saturating_sub(8).min(88), 5);
    frame.render_widget(Clear, popup);
    let prompt = Line::from(vec![
        Span::styled(
            " donna › ",
            Style::new().fg(BG).bg(CYAN).add_modifier(Modifier::BOLD),
        ),
        Span::styled(format!(" {}", app.command), Style::new().fg(TEXT)),
        Span::styled("█", Style::new().fg(CYAN)),
    ]);
    frame.render_widget(
        Paragraph::new(prompt).block(panel_block("Ask or jump to a view", true)),
        popup,
    );
}

fn render_permissions(frame: &mut Frame, app: &App, area: Rect) {
    let popup = centered(area, 72, 22);
    frame.render_widget(Clear, popup);
    let p = &app.config.permissions;
    let rows = [
        ("Read files", p.read_files),
        ("Write files", p.write_files),
        ("Delete files", p.delete_files),
        ("Run commands", p.run_commands),
        ("Send email", p.send_email),
        ("Modify calendar", p.modify_calendar),
        ("Modify tasks", p.modify_tasks),
    ]
    .into_iter()
    .map(|(name, decision)| {
        Row::new([name.to_string(), decision_label(decision).to_string()])
            .style(Style::new().fg(TEXT))
    });
    let mode = match p.mode {
        PermissionMode::Guarded => "GUARDED",
        PermissionMode::Yolo => "YOLO",
    };
    let table = Table::new(
        rows,
        [Constraint::Percentage(68), Constraint::Percentage(32)],
    )
    .header(
        Row::new([format!("Policy · {mode}"), "Decision".into()])
            .style(Style::new().fg(CYAN).add_modifier(Modifier::BOLD)),
    )
    .footer(
        Row::new([
            "Destructive actions always require confirmation",
            "Esc close",
        ])
        .style(Style::new().fg(MUTED)),
    )
    .block(panel_block("Permissions · config file", true));
    frame.render_widget(table, popup);
}

fn centered(area: Rect, width: u16, height: u16) -> Rect {
    let width = width.min(area.width.saturating_sub(2));
    let height = height.min(area.height.saturating_sub(2));
    Rect::new(
        area.x + (area.width - width) / 2,
        area.y + (area.height - height) / 2,
        width,
        height,
    )
}
fn status_color(status: Status) -> Color {
    match status {
        Status::Healthy => CYAN,
        Status::Working => BLUE,
        Status::Attention => GOLD,
        Status::Offline => RED,
    }
}
fn decision_label(decision: Decision) -> &'static str {
    match decision {
        Decision::Allow => "ALLOW",
        Decision::Ask => "ASK",
        Decision::Deny => "DENY",
    }
}

#[cfg(test)]
mod tests {
    use crate::{app::App, config::Config};
    use ratatui::{Terminal, backend::TestBackend};

    #[test]
    fn renders_target_vertical_monitor_region() {
        let backend = TestBackend::new(100, 31);
        let mut terminal = Terminal::new(backend).unwrap();
        terminal
            .draw(|frame| super::render(frame, &App::new(Config::default())))
            .unwrap();
        let rendered: String = terminal
            .backend()
            .buffer()
            .content
            .iter()
            .map(|cell| cell.symbol())
            .collect();
        assert!(rendered.contains("DONNA"));
        assert!(rendered.contains("Calendar"));
        assert!(rendered.contains("Research"));
    }

    #[test]
    fn renders_compact_and_small_sizes() {
        for (width, height) in [(120, 55), (100, 45), (90, 40), (70, 25), (50, 15)] {
            let backend = TestBackend::new(width, height);
            let mut terminal = Terminal::new(backend).unwrap();
            terminal
                .draw(|frame| super::render(frame, &App::new(Config::default())))
                .unwrap();
        }
    }
}
