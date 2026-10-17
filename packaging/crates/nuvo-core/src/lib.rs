//! Explicit Nuvo configuration and typed refusals. No provider defaults or network IO.
use std::{env, fs, path::Path};
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RefusalCode {
    Unconfigured,
    InvalidConfiguration,
    ConfigurationRead,
    Usage,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Refusal {
    pub code: RefusalCode,
    pub message: &'static str,
}
impl Refusal {
    pub fn json(&self) -> String {
        let code = match self.code {
            RefusalCode::Unconfigured => "NUVO_UNCONFIGURED",
            RefusalCode::InvalidConfiguration => "NUVO_INVALID_CONFIGURATION",
            RefusalCode::ConfigurationRead => "NUVO_CONFIGURATION_READ",
            RefusalCode::Usage => "NUVO_USAGE",
        };
        format!(
            "{{\"status\":\"refused\",\"code\":{},\"message\":{}}}",
            json_string(code),
            json_string(self.message)
        )
    }
}
fn invalid() -> Refusal {
    Refusal {
        code: RefusalCode::InvalidConfiguration,
        message:
            "Invalid Nuvo configuration; see README for the supported keys and endpoint format.",
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Config {
    pub provider: Option<String>,
    pub cortex_endpoint: Option<String>,
}
impl Config {
    /// Two keys, one explicit file format. Empty values clear the field.
    pub fn parse(text: &str) -> Result<Self, Refusal> {
        let mut config = Self::default();
        let (mut provider_seen, mut endpoint_seen) = (false, false);
        for line in text
            .lines()
            .map(str::trim)
            .filter(|s| !s.is_empty() && !s.starts_with('#'))
        {
            let (key, value) = line.split_once('=').ok_or_else(invalid)?;
            let seen = match key.trim() {
                "provider" => &mut provider_seen,
                "cortex_endpoint" => &mut endpoint_seen,
                _ => return Err(invalid()),
            };
            if *seen {
                return Err(invalid());
            }
            *seen = true;
            match key.trim() {
                "provider" => config.provider = nonempty(value),
                _ => config.cortex_endpoint = nonempty(value),
            }
        }
        Ok(config)
    }
    /// Environment values replace file fields, including an explicitly empty value.
    pub fn selected(
        mut self,
        provider: Option<String>,
        endpoint: Option<String>,
    ) -> Result<Self, Refusal> {
        if let Some(v) = provider {
            self.provider = nonempty(&v);
        }
        if let Some(v) = endpoint {
            self.cortex_endpoint = nonempty(&v);
        }
        if let Some(v) = &self.provider {
            if v.len() > 128
                || !v
                    .chars()
                    .all(|c| c.is_ascii_alphanumeric() || "._-/".contains(c))
            {
                return Err(invalid());
            }
        }
        if let Some(v) = &self.cortex_endpoint {
            // Configuration report only. Reject userinfo, query strings and fragments to
            // avoid echoing credentials; no connection is attempted.
            let rest = v
                .strip_prefix("https://")
                .or_else(|| v.strip_prefix("http://"))
                .ok_or_else(invalid)?;
            let authority = rest.split('/').next().unwrap_or("");
            if v.len() > 2048
                || authority.is_empty()
                || authority.starts_with(':')
                || v.chars()
                    .any(|c| c.is_whitespace() || c.is_control() || "@?#\\\"".contains(c))
            {
                return Err(invalid());
            }
        }
        if self.provider.is_none() && self.cortex_endpoint.is_none() {
            return Err(Refusal { code: RefusalCode::Unconfigured, message: "Set NUVO_PROVIDER or NUVO_CORTEX_ENDPOINT, or explicitly select a NUVO_CONFIG file." });
        }
        Ok(self)
    }
    pub fn json(&self) -> String {
        fn field(v: &Option<String>) -> String {
            v.as_deref()
                .map(json_string)
                .unwrap_or_else(|| "null".into())
        }
        format!("{{\"status\":\"configured\",\"check\":\"configuration_only\",\"provider\":{},\"cortex_endpoint\":{}}}", field(&self.provider), field(&self.cortex_endpoint))
    }
}
fn nonempty(s: &str) -> Option<String> {
    let s = s.trim();
    if s.is_empty() {
        None
    } else {
        Some(s.into())
    }
}
fn read_env(name: &str) -> Result<Option<String>, Refusal> {
    match env::var(name) {
        Ok(v) => Ok(Some(v)),
        Err(env::VarError::NotPresent) => Ok(None),
        Err(_) => Err(invalid()),
    }
}
pub fn load() -> Result<Config, Refusal> {
    let config = match read_env("NUVO_CONFIG")? {
        Some(path) if !path.trim().is_empty() => read_file(Path::new(&path))?,
        Some(_) => return Err(invalid()),
        None => Config::default(),
    };
    config.selected(
        read_env("NUVO_PROVIDER")?,
        read_env("NUVO_CORTEX_ENDPOINT")?,
    )
}
pub fn read_file(path: &Path) -> Result<Config, Refusal> {
    let text = fs::read_to_string(path).map_err(|_| Refusal {
        code: RefusalCode::ConfigurationRead,
        message: "Cannot read NUVO_CONFIG as UTF-8; check the explicit path and permissions.",
    })?;
    Config::parse(&text)
}
pub fn json_string(s: &str) -> String {
    let mut out = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            c if c.is_control() => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn empty_refuses() {
        assert_eq!(
            Config::default().selected(None, None).unwrap_err().code,
            RefusalCode::Unconfigured
        );
    }
    #[test]
    fn provider_only() {
        assert_eq!(
            Config::default()
                .selected(Some("selected-provider".into()), None)
                .unwrap()
                .provider
                .as_deref(),
            Some("selected-provider")
        );
    }
    #[test]
    fn endpoint_only() {
        assert!(Config::default()
            .selected(None, Some("http://localhost:123/cortex".into()))
            .is_ok());
    }
    #[test]
    fn config_file() {
        assert_eq!(
            Config::parse(
                "# comment\nprovider = chosen\ncortex_endpoint=https://example.invalid/api\n"
            )
            .unwrap()
            .selected(None, None)
            .unwrap()
            .provider
            .as_deref(),
            Some("chosen")
        );
    }
    #[test]
    fn precedence() {
        let c = Config::parse("provider=file")
            .unwrap()
            .selected(Some("env".into()), None)
            .unwrap();
        assert_eq!(c.provider.as_deref(), Some("env"));
    }
    #[test]
    fn explicit_empty_clears() {
        assert_eq!(
            Config::parse("provider=file")
                .unwrap()
                .selected(Some(" ".into()), None)
                .unwrap_err()
                .code,
            RefusalCode::Unconfigured
        );
    }
    #[test]
    fn unknown_key() {
        assert!(Config::parse("token=secret").is_err());
    }
    #[test]
    fn duplicate_key() {
        assert!(Config::parse("provider=a\nprovider=b").is_err());
    }
    #[test]
    fn malformed_line() {
        assert!(Config::parse("provider").is_err());
    }
    #[test]
    fn endpoint_secrets_refused() {
        for endpoint in [
            "https://user:secret@example.invalid",
            "https://example.invalid?token=secret",
            "https://example.invalid/#secret",
        ] {
            let error = Config::default()
                .selected(None, Some(endpoint.into()))
                .unwrap_err()
                .json();
            assert!(!error.contains("secret"));
        }
    }
    #[test]
    fn invalid_endpoint() {
        for endpoint in [
            "ftp://localhost",
            "https://",
            "http://:23",
            "https://host/white space",
        ] {
            assert!(Config::default()
                .selected(None, Some(endpoint.into()))
                .is_err());
        }
    }
    #[test]
    fn provider_control_refused() {
        assert!(Config::default()
            .selected(Some("bad\nvalue".into()), None)
            .is_err());
    }
    #[test]
    fn json_escapes() {
        assert_eq!(json_string("a\"\n\\"), "\"a\\\"\\u000a\\\\\"");
    }
    #[test]
    fn missing_file() {
        assert_eq!(
            read_file(Path::new("/nuvo/missing/config"))
                .unwrap_err()
                .code,
            RefusalCode::ConfigurationRead
        );
    }
}
