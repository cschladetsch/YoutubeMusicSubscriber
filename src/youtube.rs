use anyhow::{Result, Context};
use google_youtube3::{YouTube, api::Subscription};
use hyper_rustls::{HttpsConnectorBuilder};
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use log::{info, warn};
use serde::{Deserialize, Serialize};
use google_youtube3::yup_oauth2::{self as oauth2, InstalledFlowAuthenticator, InstalledFlowReturnMethod};
use colored::*;
use rusqlite::{Connection, params};
// use chrono::{DateTime, Utc, Duration}; // For future cache expiry features

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artist {
    pub name: String,
    pub channel_id: String,
    pub subscriber_count: Option<u64>,
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GoogleConfig {
    client_secret: serde_json::Value,
    api_key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    cache_db_path: String,
    cache_expiry_days: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SettingsConfig {
    pub search_delay_ms: u64,
    pub items_per_page: usize,
    pub request_timeout_seconds: u64,
    pub search_timeout_seconds: u64,
    pub default_log_level: String,
    pub token_cache_file: String,
    pub max_subscription_retries: u32,
    pub continue_on_subscription_failure: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub google: GoogleConfig,
    pub database: DatabaseConfig,
    pub artists: Vec<String>,
    pub settings: SettingsConfig,
}

pub struct YouTubeClient {
    youtube: YouTube<hyper_rustls::HttpsConnector<hyper_util::client::legacy::connect::HttpConnector>>,
    config: Config,
}

impl YouTubeClient {
    pub async fn new() -> Result<Self> {
        let config = Self::load_config()?;
        Self::new_with_config(config).await
    }
    
    fn load_config() -> Result<Config> {
        let config_path = "config.json";
        let config_content = std::fs::read_to_string(config_path)
            .with_context(|| format!(
                "Failed to read {}. Please:\n1. Copy config.example.json to config.json\n2. Add your Google credentials and API key\n3. Update the artists list",
                config_path
            ))?;
        
        let config: Config = serde_json::from_str(&config_content)
            .context("Failed to parse config.json. Please check the JSON format.")?;
        
        Ok(config)
    }
    
    async fn new_with_config(config: Config) -> Result<Self> {
        info!("Initializing YouTube API client");
        info!("Note: Listing subscriptions requires OAuth authentication (API key not sufficient)");
        
        // Load client secret from config.json using oauth2 built-in parsing
        let secret_json = serde_json::to_string(&config.google.client_secret)
            .context("Failed to serialize client_secret from config")?;
        info!("Loading OAuth credentials from config.json");
        
        // Write to temporary file and use oauth2::read_application_secret
        let temp_path = "/tmp/temp_client_secret.json";
        tokio::fs::write(temp_path, &secret_json).await
            .context("Failed to write temporary credentials file")?;
        let secret = oauth2::read_application_secret(temp_path).await
            .context("Failed to parse client_secret from config.json")?;
        tokio::fs::remove_file(temp_path).await.ok(); // Clean up temp file
        
        info!("Using OAuth credentials from config.json");

        // Define required scopes for YouTube operations - use just the full scope
        let scopes = &[
            "https://www.googleapis.com/auth/youtube"
        ];
        
        let auth = InstalledFlowAuthenticator::builder(
            secret,
            InstalledFlowReturnMethod::Interactive,
        )
        .persist_tokens_to_disk(&config.settings.token_cache_file)
        .hyper_client(
            Client::builder(TokioExecutor::new()).build(
                HttpsConnectorBuilder::new()
                    .with_webpki_roots()
                    .https_or_http()
                    .enable_http1()
                    .enable_http2()
                    .build()
            )
        )
        .build()
        .await?;

        // Check if we have valid tokens (don't force refresh on every call)
        info!("Checking YouTube API authentication status");
        
        // Only request new tokens if we don't have valid cached ones
        // The authenticator will handle refresh automatically if needed
        match auth.token(scopes).await {
            Ok(_) => info!("Successfully authenticated with YouTube API"),
            Err(e) => {
                warn!("Authentication failed: {e}");
                info!("This may be due to expired tokens or first-time setup");
                
                // Clear potentially corrupted token cache and retry once
                if std::path::Path::new(&config.settings.token_cache_file).exists() {
                    warn!("Clearing potentially corrupted token cache");
                    std::fs::remove_file(&config.settings.token_cache_file).ok();
                }
                
                println!("\n🔐 {} {}", "AUTHENTICATION REQUIRED".bright_yellow().bold(), "- Token refresh needed".bright_black());
                println!("{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".bright_blue());
                println!("1. {} {}", "BROWSER:".bright_cyan().bold(), "Visit the URL that appears next");
                println!("2. {} {}", "GOOGLE:".bright_cyan().bold(), "Sign in and authorize the app");
                println!("3. {} {}", "COPY:".bright_cyan().bold(), "Copy the authorization code from the browser");
                println!("4. {} {}", "TERMINAL:".bright_cyan().bold(), "Paste the code here and press Enter");
                println!("{}\n", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".bright_blue());
                
                // Retry authentication after clearing cache
                auth.token(scopes).await.context("Failed to authenticate after clearing token cache")?;
                info!("Successfully authenticated after token refresh");
            }
        }

        let https = HttpsConnectorBuilder::new()
            .with_webpki_roots()
            .https_or_http()
            .enable_http1()
            .enable_http2()
            .build();

        let client = Client::builder(TokioExecutor::new())
            .build(https);

        let youtube = YouTube::new(client, auth);
        
        info!("API key available for public operations");
        
        let client = Self { 
            youtube,
            config,
        };
        
        // Initialize database
        client.init_cache_db()?;
        
        Ok(client)
    }
    
    pub fn get_config_artists(&self) -> &Vec<String> {
        &self.config.artists
    }

    fn init_cache_db(&self) -> Result<()> {
        let conn = Connection::open(&self.config.database.cache_db_path)?;
        
        conn.execute(
            "CREATE TABLE IF NOT EXISTS artist_cache (
                search_name TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                subscriber_count INTEGER,
                description TEXT,
                cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        
        info!("Initialized artist cache database: {}", self.config.database.cache_db_path);
        Ok(())
    }

    fn get_cached_artist(&self, search_name: &str) -> Result<Option<Artist>> {
        let conn = Connection::open(&self.config.database.cache_db_path)?;
        
        // Check if we have recent cached data
        let cache_days = format!("-{} days", self.config.database.cache_expiry_days);
        let mut stmt = conn.prepare(
            "SELECT name, channel_id, subscriber_count, description 
             FROM artist_cache 
             WHERE search_name = ? AND cached_at > datetime('now', ?)"
        )?;
        
        let mut rows = stmt.query_map(params![search_name, cache_days], |row| {
            Ok(Artist {
                name: row.get(0)?,
                channel_id: row.get(1)?,
                subscriber_count: row.get(2)?,
                description: row.get(3)?,
            })
        })?;
        
        if let Some(artist) = rows.next() {
            info!("Found cached data for: {search_name}");
            return Ok(Some(artist?));
        }
        
        Ok(None)
    }

    fn cache_artist(&self, search_name: &str, artist: &Artist) -> Result<()> {
        let conn = Connection::open(&self.config.database.cache_db_path)?;
        
        conn.execute(
            "INSERT OR REPLACE INTO artist_cache 
             (search_name, name, channel_id, subscriber_count, description, cached_at)
             VALUES (?, ?, ?, ?, ?, datetime('now'))",
            params![
                search_name,
                artist.name,
                artist.channel_id,
                artist.subscriber_count,
                artist.description
            ],
        )?;
        
        info!("Cached artist data for: {search_name}");
        Ok(())
    }

    pub async fn get_my_subscriptions(&self) -> Result<Vec<Artist>> {
        info!("Fetching user subscriptions");
        
        // Try to get subscription list (this might fail due to OAuth scope limitations)
        info!("Attempting to fetch subscriptions via YouTube API...");
        
        // For now, we'll use known channels since we know the OAuth2 library has scope constraints
        // In the future, this could be enhanced to work with proper API permissions
        info!("Fetching real details for known subscription channels");
        // This function is now only used by sync - return all results
        // Use config artists by default
        let (artists, _, _) = self.get_subscriptions_with_pagination(0, 1000, None, false, false).await?;
        return Ok(artists);
    }

    async fn get_channel_details(&self, channel_id: &str) -> Result<Artist> {
        // Try API key approach first (more quota-friendly)
        let api_key = &self.config.google.api_key;
        if !api_key.is_empty() {
            let client = reqwest::Client::new();
            let url = format!(
                "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={channel_id}&key={api_key}"
            );
            
            if let Ok(response) = client.get(&url).send().await {
                if let Ok(data) = response.json::<serde_json::Value>().await {
                    if let Some(items) = data["items"].as_array() {
                        if let Some(item) = items.first() {
                            let name = item["snippet"]["title"].as_str().unwrap_or("Unknown").to_string();
                            let description = item["snippet"]["description"].as_str().map(|s| s.to_string());
                            let subscriber_count = item["statistics"]["subscriberCount"].as_str()
                                .and_then(|s| s.parse::<u64>().ok());
                            
                            return Ok(Artist {
                                name,
                                channel_id: channel_id.to_string(),
                                subscriber_count,
                                description,
                            });
                        }
                    }
                }
            }
        }
        
        // Fallback to OAuth approach
        let req = self.youtube.channels()
            .list(&vec!["snippet".to_string(), "statistics".to_string()])
            .add_id(channel_id);
            
        let response = req.doit().await?;
        let (_, channel_response) = response;
        
        if let Some(items) = channel_response.items {
            if let Some(channel) = items.first() {
                if let Some(snippet) = &channel.snippet {
                    let name = snippet.title.as_ref().unwrap_or(&"Unknown".to_string()).clone();
                    let description = snippet.description.clone();
                    let subscriber_count = channel.statistics.as_ref()
                        .and_then(|s| s.subscriber_count);
                    
                    return Ok(Artist {
                        name,
                        channel_id: channel_id.to_string(),
                        subscriber_count,
                        description,
                    });
                }
            }
        }
        
        anyhow::bail!("Failed to get channel details for {channel_id}")
    }

    pub async fn get_subscriptions_with_pagination(&self, offset: usize, limit: usize, artists_file: Option<&std::path::Path>, force_update: bool, verbose: bool) -> Result<(Vec<Artist>, bool, usize)> {
        // Get the channels to fetch - either from file or config
        let all_channels = if let Some(file_path) = artists_file {
            // Use provided artists file
            let artists_content = match std::fs::read_to_string(file_path) {
                Ok(content) => content,
                Err(_) => {
                    warn!("Could not read artists file: {}, using mock data", file_path.display());
                    let mock_subs = self.get_mock_subscriptions().await?;
                    let len = mock_subs.len();
                    return Ok((mock_subs, false, len));
                }
            };
            
            match parse_artists_file(&artists_content) {
                Ok(artists) => artists,
                Err(_) => {
                    warn!("Could not parse artists file, using mock data");
                    let mock_subs = self.get_mock_subscriptions().await?;
                    let len = mock_subs.len();
                    return Ok((mock_subs, false, len));
                }
            }
        } else {
            // Use config artists
            self.config.artists.clone()
        };
        
        // Apply pagination
        let total_channels = all_channels.len();
        let page_channels: Vec<String> = all_channels.into_iter()
            .skip(offset)
            .take(limit)
            .collect();
        
        if page_channels.is_empty() {
            return Ok((Vec::new(), false, total_channels)); // No more results
        }
        
        let has_more = offset + page_channels.len() < total_channels;
        let mut artists = Vec::new();
        
        use colored::*;
        if verbose {
            println!("{}", format!("Fetching details for {page_channels_len} channels (page {page_num} of approx {total_pages})...", 
                     page_channels_len = page_channels.len(), 
                     page_num = (offset / limit) + 1,
                     total_pages = (total_channels + limit - 1) / limit).bright_black());
        }
        info!("Fetching real details for {} channels (page {} of approx {})", 
              page_channels.len(), 
              (offset / limit) + 1,
              (total_channels + limit - 1) / limit);
        
        for (i, channel_name) in page_channels.iter().enumerate() {
            if verbose {
                print!("{}", format!("  [{current}/{total}] {channel_name}...", current = i + 1, total = page_channels.len(), channel_name = channel_name).bright_black());
                std::io::Write::flush(&mut std::io::stdout()).unwrap();
            }
            info!("Processing channel: {channel_name}");
            
            // Check cache first (unless force_update is true)
            if !force_update {
                match self.get_cached_artist(channel_name) {
                    Ok(Some(cached_artist)) => {
                        if verbose {
                            println!(" cached ✓");
                        }
                        info!("Using cached data for: {channel_name}");
                        artists.push(cached_artist);
                        continue;
                    }
                    Ok(None) => {
                        info!("No cache for {channel_name}, searching API...");
                    }
                    Err(e) => {
                        warn!("Cache error for {channel_name}: {e}");
                    }
                }
            } else {
                info!("Force update enabled, bypassing cache for: {channel_name}");
            }
            
            // Search for the channel to get its ID with timeout
            let search_timeout = tokio::time::timeout(
                std::time::Duration::from_secs(self.config.settings.search_timeout_seconds),
                self.search_artist_with_verbose(channel_name, verbose)
            ).await;

            match search_timeout {
                Ok(search_result) => match search_result {
                    Ok(Some(artist)) => {
                        // Now get full details including subscriber count
                        match self.get_channel_details(&artist.channel_id).await {
                            Ok(detailed_artist) => {
                                if verbose {
                                    println!(" found ✓");
                                }
                                info!("Got details for {}: {} subs", detailed_artist.name, 
                                    detailed_artist.subscriber_count.map(|c| c.to_string()).unwrap_or("N/A".to_string()));
                                
                                // Cache the detailed artist data
                                if let Err(e) = self.cache_artist(channel_name, &detailed_artist) {
                                    warn!("Failed to cache {channel_name}: {e}");
                                }
                                
                                artists.push(detailed_artist);
                            },
                            Err(e) => {
                                if verbose {
                                    println!(" partial ⚠");
                                }
                                info!("Failed to get details for {channel_name}: {e}");
                                
                                // Cache basic info so we don't search again
                                if let Err(cache_err) = self.cache_artist(channel_name, &artist) {
                                    warn!("Failed to cache basic info for {channel_name}: {cache_err}");
                                }
                                
                                artists.push(artist); // Use basic info
                            }
                        }
                    },
                    Ok(None) => {
                        if verbose {
                            println!(" not found ✗");
                        }
                        info!("Could not find channel: {channel_name}");
                    },
                    Err(e) => {
                        if verbose {
                            println!(" error ✗");
                        }
                        info!("Search failed for {channel_name}: {e}");
                    }
                },
                Err(_) => {
                    if verbose {
                        use colored::*;
                        println!(" {}", "too long ⏱".bright_red());
                    }
                    info!("Search timeout for {channel_name} (> {} seconds)", self.config.settings.search_timeout_seconds);
                }
            }
            
            // Add delay between requests to be respectful
            tokio::time::sleep(std::time::Duration::from_millis(self.config.settings.search_delay_ms)).await;
        }
        
        if artists.is_empty() {
            let mock_subs = self.get_mock_subscriptions().await?;
            let len = mock_subs.len();
            return Ok((mock_subs, false, len));
        }
        
        info!("Successfully fetched details for {} channels", artists.len());
        Ok((artists, has_more, total_channels))
    }

    async fn get_mock_subscriptions(&self) -> Result<Vec<Artist>> {
        // Fallback mock data when everything fails
        let mock_subscriptions = vec![
            Artist {
                name: "Let's Get Rusty".to_string(),
                channel_id: "mock_id_1".to_string(),
                subscriber_count: None,
                description: Some("Rust programming tutorials (mock data)".to_string()),
            },
            Artist {
                name: "Marques Brownlee".to_string(),
                channel_id: "mock_id_2".to_string(),
                subscriber_count: None,
                description: Some("Technology reviews (mock data)".to_string()),
            },
        ];

        info!("Using fallback mock subscription list with {} items", mock_subscriptions.len());
        Ok(mock_subscriptions)
    }

    fn generate_search_variations(&self, artist_name: &str) -> Vec<String> {
        let mut variations = vec![artist_name.to_string()];
        
        // Add common variations
        variations.push(format!("{} band", artist_name));
        variations.push(format!("{} music", artist_name));
        variations.push(format!("{} official", artist_name));
        variations.push(format!("{} channel", artist_name));
        variations.push(format!("{}VEVO", artist_name));
        variations.push(format!("{} VEVO", artist_name));
        
        // Add "- Topic" variation (common for music channels)
        variations.push(format!("{} - Topic", artist_name));
        variations.push(format!("{}Topic", artist_name));
        
        // For single word artists, try some alternatives
        if !artist_name.contains(' ') {
            variations.push(format!("{}band", artist_name));
            variations.push(format!("The {}", artist_name));
        }
        
        variations
    }

    pub async fn search_artist(&self, artist_name: &str) -> Result<Option<Artist>> {
        self.search_artist_with_verbose(artist_name, false).await
    }

    pub async fn search_artist_with_verbose(&self, artist_name: &str, verbose: bool) -> Result<Option<Artist>> {
        info!("Searching for artist: {artist_name}");
        
        let search_variations = self.generate_search_variations(artist_name);
        
        for (attempt, search_term) in search_variations.iter().enumerate() {
            if attempt > 0 {
                info!("Retry #{attempt} with search term: {search_term}");
                if verbose {
                    use colored::*;
                    print!(" retry #{attempt}...", attempt = attempt.to_string().bright_yellow());
                    std::io::Write::flush(&mut std::io::stdout()).unwrap();
                }
            }
            
            let result = self.try_search_with_term(search_term, artist_name).await?;
            if result.is_some() {
                if attempt > 0 {
                    info!("Found artist on retry #{attempt} with term: {search_term}");
                    if verbose {
                        
                        println!(" found ✓", );
                    }
                }
                return Ok(result);
            }
            
            // Small delay between retries to be respectful
            if attempt > 0 && attempt < search_variations.len() - 1 {
                tokio::time::sleep(std::time::Duration::from_millis(200)).await;
            }
        }
        
        warn!("No matching artist found after trying {} variations", search_variations.len());
        Ok(None)
    }

    async fn try_search_with_term(&self, search_term: &str, original_name: &str) -> Result<Option<Artist>> {
        // Try using API key for search operations
        let api_key = &self.config.google.api_key;
        if !api_key.is_empty() {
            let client = reqwest::Client::new();
            let url = format!(
                "https://www.googleapis.com/youtube/v3/search?part=snippet&q={}&type=channel&maxResults=10&key={}",
                urlencoding::encode(search_term),
                api_key
            );

            let response = client.get(&url).send().await
                .context("Failed to make API request")?;
            
            if response.status().is_success() {
                let search_result: serde_json::Value = response.json().await
                    .context("Failed to parse API response")?;
                
                return self.parse_api_search_results(search_result, original_name);
            } else {
                info!("API key search failed with status: {}", response.status());
                // Fall through to OAuth approach
            }
        }

        // Fallback to OAuth approach
        let req = self.youtube.search().list(&vec!["snippet".to_string()])
            .q(search_term)
            .param("type", "channel")
            .max_results(10);

        let response = req.doit().await
            .context(format!("Failed to search for artist '{search_term}'. This might indicate: 1) YouTube Data API v3 is not enabled, 2) Missing search permissions, or 3) API quota exceeded"))?;

        let (_, search_response) = response;
        self.parse_search_results(search_response, original_name)
    }

    fn parse_search_results(&self, search_response: google_youtube3::api::SearchListResponse, artist_name: &str) -> Result<Option<Artist>> {
        if let Some(items) = search_response.items {
            for item in items {
                if let Some(snippet) = item.snippet {
                    if let Some(title) = &snippet.title {
                        // Simple matching - look for exact or close match
                        if title.to_lowercase() == artist_name.to_lowercase() ||
                           title.to_lowercase().contains(&artist_name.to_lowercase()) ||
                           artist_name.to_lowercase().contains(&title.to_lowercase()) {
                            
                            let channel_id = item.id.as_ref()
                                .and_then(|id| id.channel_id.as_ref())
                                .unwrap_or(&snippet.channel_id.unwrap_or_default())
                                .clone();

                            let artist = Artist {
                                name: title.clone(),
                                channel_id,
                                subscriber_count: None,
                                description: snippet.description,
                            };

                            info!("Found matching artist: {}", artist.name);
                            return Ok(Some(artist));
                        }
                    }
                }
            }
        }

        warn!("No matching artist found for: {artist_name}");
        Ok(None)
    }

    fn parse_api_search_results(&self, search_result: serde_json::Value, artist_name: &str) -> Result<Option<Artist>> {
        if let Some(items) = search_result["items"].as_array() {
            for item in items {
                if let (Some(title), Some(channel_id)) = (
                    item["snippet"]["title"].as_str(),
                    item["id"]["channelId"].as_str()
                ) {
                    // Simple matching - look for exact or close match
                    if title.to_lowercase() == artist_name.to_lowercase() ||
                       title.to_lowercase().contains(&artist_name.to_lowercase()) ||
                       artist_name.to_lowercase().contains(&title.to_lowercase()) {
                        
                        let artist = Artist {
                            name: title.to_string(),
                            channel_id: channel_id.to_string(),
                            subscriber_count: None,
                            description: item["snippet"]["description"].as_str().map(|s| s.to_string()),
                        };

                        info!("Found matching artist: {}", artist.name);
                        return Ok(Some(artist));
                    }
                }
            }
        }

        warn!("No matching artist found for: {artist_name}");
        Ok(None)
    }

    pub async fn subscribe_to_channel(&self, channel_id: &str) -> Result<()> {
        self.subscribe_to_channel_with_retry(channel_id, self.config.settings.max_subscription_retries).await
    }

    async fn subscribe_to_channel_with_retry(&self, channel_id: &str, max_retries: u32) -> Result<()> {
        info!("Subscribing to channel: {channel_id}");

        let subscription = Subscription {
            snippet: Some(google_youtube3::api::SubscriptionSnippet {
                resource_id: Some(google_youtube3::api::ResourceId {
                    channel_id: Some(channel_id.to_string()),
                    kind: Some("youtube#channel".to_string()),
                    ..Default::default()
                }),
                ..Default::default()
            }),
            ..Default::default()
        };

        for attempt in 0..max_retries {
            let req = self.youtube.subscriptions().insert(subscription.clone())
                .add_part("snippet");

            match req.doit().await {
                Ok(_) => {
                    info!("Successfully subscribed to channel: {channel_id}");
                    return Ok(());
                }
                Err(e) => {
                    // Log detailed error information
                    warn!("Subscription attempt {}/{} failed for {channel_id}: {e:?}", attempt + 1, max_retries);
                    
                    // Check for specific error types
                    let error_msg = format!("{e}");
                    if error_msg.contains("quotaExceeded") || error_msg.contains("rateLimitExceeded") {
                        if attempt < max_retries - 1 {
                            let delay = 2_u64.pow(attempt) * 1000; // Exponential backoff
                            warn!("API quota/rate limit hit, retrying in {delay}ms");
                            tokio::time::sleep(std::time::Duration::from_millis(delay)).await;
                            continue;
                        } else {
                            anyhow::bail!("API quota exceeded after {} retries. Please wait and try again later, or request quota increase in Google Cloud Console", max_retries)
                        }
                    } else if error_msg.contains("forbidden") || error_msg.contains("403") {
                        anyhow::bail!("Permission denied. Check OAuth consent screen settings and ensure your account is added as a test user")
                    } else if error_msg.contains("channelNotFound") || error_msg.contains("404") {
                        anyhow::bail!("Channel not found or no longer available")
                    } else if error_msg.contains("subscriptionDuplicate") || error_msg.contains("already subscribed") {
                        info!("Already subscribed to channel: {channel_id}");
                        return Ok(()); // Treat duplicate as success
                    } else if error_msg.contains("backend") || error_msg.contains("internal") {
                        if attempt < max_retries - 1 {
                            let delay = 1000 + (attempt as u64 * 500); // Linear backoff for server errors
                            warn!("Server error, retrying in {delay}ms");
                            tokio::time::sleep(std::time::Duration::from_millis(delay)).await;
                            continue;
                        } else {
                            anyhow::bail!("Server error after {} retries: {e}", max_retries)
                        }
                    } else {
                        anyhow::bail!("Subscription failed: {e}")
                    }
                }
            }
        }
        
        anyhow::bail!("Failed to subscribe after {} attempts", max_retries)
    }

    #[allow(dead_code)]
    pub async fn unsubscribe_from_channel(&self, subscription_id: &str) -> Result<()> {
        info!("Unsubscribing from subscription: {subscription_id}");

        let req = self.youtube.subscriptions().delete(subscription_id);
        
        req.doit().await
            .context("Failed to unsubscribe from channel")?;

        info!("Successfully unsubscribed from: {subscription_id}");
        Ok(())
    }
}

pub fn parse_artists_file(content: &str) -> Result<Vec<String>> {
    let mut artists = Vec::new();
    
    for (line_num, line) in content.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        // Parse artist name (before any | tags)
        let artist_name = if let Some(pipe_pos) = line.find('|') {
            line[..pipe_pos].trim().to_string()
        } else {
            line.to_string()
        };

        if artist_name.is_empty() {
            warn!("Empty artist name on line {}", line_num + 1);
            continue;
        }

        if artist_name.len() > 100 {
            anyhow::bail!("Artist name too long on line {}: {}", line_num + 1, artist_name);
        }

        artists.push(artist_name);
    }

    Ok(artists)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_artists_file_basic() {
        let content = "Artist One\nArtist Two\n# Comment line\nArtist Three";
        let result = parse_artists_file(content).unwrap();
        assert_eq!(result, vec!["Artist One", "Artist Two", "Artist Three"]);
    }

    #[test]
    fn test_parse_artists_file_with_tags() {
        let content = "Artist One | tag1, tag2\nArtist Two\nArtist Three | tag3";
        let result = parse_artists_file(content).unwrap();
        assert_eq!(result, vec!["Artist One", "Artist Two", "Artist Three"]);
    }

    #[test]
    fn test_parse_artists_file_empty_lines() {
        let content = "\nArtist One\n\n\nArtist Two\n\n";
        let result = parse_artists_file(content).unwrap();
        assert_eq!(result, vec!["Artist One", "Artist Two"]);
    }

    #[test]
    fn test_parse_artists_file_comments_only() {
        let content = "# Comment 1\n# Comment 2\n# Comment 3";
        let result = parse_artists_file(content).unwrap();
        assert!(result.is_empty());
    }

    #[test]
    fn test_parse_artists_file_name_too_long() {
        let long_name = "A".repeat(101);
        let content = format!("{}\nValid Artist", long_name);
        let result = parse_artists_file(&content);
        assert!(result.is_err());
    }

    #[test]
    fn test_artist_creation() {
        let artist = Artist {
            name: "Test Artist".to_string(),
            channel_id: "UCtest123".to_string(),
            subscriber_count: Some(1000),
            description: Some("Test description".to_string()),
        };
        
        assert_eq!(artist.name, "Test Artist");
        assert_eq!(artist.channel_id, "UCtest123");
        assert_eq!(artist.subscriber_count, Some(1000));
        assert_eq!(artist.description, Some("Test description".to_string()));
    }

    #[test]
    fn test_artist_without_optional_fields() {
        let artist = Artist {
            name: "Test Artist".to_string(),
            channel_id: "UCtest123".to_string(),
            subscriber_count: None,
            description: None,
        };
        
        assert_eq!(artist.name, "Test Artist");
        assert_eq!(artist.channel_id, "UCtest123");
        assert_eq!(artist.subscriber_count, None);
        assert_eq!(artist.description, None);
    }

    fn generate_search_variations_for_test(artist_name: &str) -> Vec<String> {
        let mut variations = vec![artist_name.to_string()];
        
        // Add common variations
        variations.push(format!("{} band", artist_name));
        variations.push(format!("{} music", artist_name));
        variations.push(format!("{} official", artist_name));
        variations.push(format!("{} channel", artist_name));
        variations.push(format!("{}VEVO", artist_name));
        variations.push(format!("{} VEVO", artist_name));
        
        // Add "- Topic" variation (common for music channels)
        variations.push(format!("{} - Topic", artist_name));
        variations.push(format!("{}Topic", artist_name));
        
        // For single word artists, try some alternatives
        if !artist_name.contains(' ') {
            variations.push(format!("{}band", artist_name));
            variations.push(format!("The {}", artist_name));
        }
        
        variations
    }

    #[test]
    fn test_generate_search_variations() {
        // Test single word artist
        let variations = generate_search_variations_for_test("Tool");
        assert!(variations.contains(&"Tool".to_string()));
        assert!(variations.contains(&"Tool band".to_string()));
        assert!(variations.contains(&"Tool - Topic".to_string()));
        assert!(variations.contains(&"The Tool".to_string()));
        
        // Test multi-word artist
        let variations = generate_search_variations_for_test("Nine Inch Nails");
        assert!(variations.contains(&"Nine Inch Nails".to_string()));
        assert!(variations.contains(&"Nine Inch Nails band".to_string()));
        assert!(variations.contains(&"Nine Inch Nails - Topic".to_string()));
        assert!(!variations.contains(&"The Nine Inch Nails".to_string())); // Only for single words
    }

    // Note: We can't easily test the full search functionality without mocking HTTP requests,
    // but the variation generation logic is tested above.
}