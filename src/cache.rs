use std::{fs, io::Write, path::PathBuf};

use anyhow::{Context, Result};
use directories::ProjectDirs;
use serde::{Deserialize, Serialize};

use crate::model::{CachePolicy, DashboardSnapshot};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct CachedDashboard {
    pub snapshot: DashboardSnapshot,
    pub last_sequence: u64,
}

pub fn path() -> Option<PathBuf> {
    ProjectDirs::from("dev", "kadhirtheengineer", "donna")
        .map(|directories| directories.cache_dir().join("dashboard-v1.json"))
}

pub fn load() -> Result<Option<CachedDashboard>> {
    let Some(cache_path) = path() else {
        return Ok(None);
    };
    if !cache_path.exists() {
        return Ok(None);
    }
    let bytes = fs::read(&cache_path)
        .with_context(|| format!("read dashboard cache at {}", cache_path.display()))?;
    let cache: CachedDashboard = serde_json::from_slice(&bytes)
        .with_context(|| format!("parse dashboard cache at {}", cache_path.display()))?;
    if cache.snapshot.schema_version != "1.0" {
        return Ok(None);
    }
    Ok(Some(cache))
}

pub fn save(snapshot: &DashboardSnapshot, last_sequence: u64) -> Result<()> {
    if snapshot.cache_policy != CachePolicy::AllowLocal {
        return Ok(());
    }
    let Some(cache_path) = path() else {
        return Ok(());
    };
    let parent = cache_path
        .parent()
        .context("dashboard cache path has no parent")?;
    fs::create_dir_all(parent)
        .with_context(|| format!("create dashboard cache directory at {}", parent.display()))?;
    let mut temporary = tempfile::NamedTempFile::new_in(parent)
        .with_context(|| format!("create temporary cache file in {}", parent.display()))?;
    serde_json::to_writer(
        &mut temporary,
        &CachedDashboard {
            snapshot: snapshot.clone(),
            last_sequence,
        },
    )
    .context("serialize dashboard cache")?;
    temporary.flush().context("flush dashboard cache")?;
    temporary
        .as_file()
        .sync_all()
        .context("sync dashboard cache")?;
    temporary
        .persist(&cache_path)
        .map_err(|error| error.error)
        .with_context(|| format!("replace dashboard cache at {}", cache_path.display()))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use crate::model::{Briefing, DashboardSnapshot};

    #[test]
    fn shared_fixture_is_cacheable() {
        let raw = include_str!("../contracts/examples/dashboard-snapshot.v1.json");
        let snapshot: DashboardSnapshot = serde_json::from_str(raw).unwrap();
        assert_eq!(Briefing::from(snapshot).events.len(), 1);
    }
}
