use anyhow::{Result, Context};
use google_youtube3::{YouTube, api::Subscription};
use hyper_rustls::{HttpsConnectorBuilder};
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use log::{info, warn, debug};
use serde::{Deserialize, Serialize};
use google_youtube3::yup_oauth2::{self as oauth2, InstalledFlowAuthenticator, InstalledFlowReturnMethod};
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artist {
    pub name: String,
    pub channel_id: String,
    pub subscriber_count: Option<u64>,
    pub description: Option<String>,
}

pub struct YouTubeClient {
    youtube: YouTube<hyper_rustls::HttpsConnector<hyper_util::client::legacy::connect::HttpConnector>>,
    api_key: Option<String>,
}

impl YouTubeClient {
    pub async fn new() -> Result<Self> {
        info!("Initializing YouTube API client");
        info!("Note: Listing subscriptions requires OAuth authentication (API key not sufficient)");
        let secret = oauth2::read_application_secret("client_secret.json")
            .await
            .context("Failed to read client_secret.json. Please:\n1. Download credentials from Google Cloud Console\n2. Save as 'client_secret.json' in project root\n3. See client_secret.json.example for format")?;

        // Check for existing tokens first
        let scopes = &[
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube"
        ];
        
        let auth = InstalledFlowAuthenticator::builder(
            secret,
            InstalledFlowReturnMethod::HTTPRedirect,
        )
        .persist_tokens_to_disk("tokencache.json")
        .build()
        .await?;

        // Check if we have valid cached tokens
        match std::fs::metadata("tokencache.json") {
            Ok(_) => {
                info!("Found existing token cache, attempting to use cached tokens");
                match auth.token(scopes).await {
                    Ok(_) => info!("Successfully using cached authentication tokens"),
                    Err(e) => {
                        warn!("Cached tokens invalid, will need fresh authentication: {}", e);
                        println!("\n⚠️  Authentication required!");
                        println!("Please visit the URL shown below in your browser to authenticate:");
                        println!("After authentication, the app will continue automatically.\n");
                    }
                }
            }
            Err(_) => {
                info!("No existing token cache found, will need fresh authentication");
                println!("\n🔐 First-time authentication required!");
                println!("Please visit the URL shown below in your browser to authenticate:");
                println!("After authentication, the app will continue automatically.\n");
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

        // Read API key if available for public operations
        let api_key = std::fs::read_to_string("api.key")
            .map(|key| key.trim().to_string())
            .ok();
        
        if api_key.is_some() {
            info!("API key available for public operations");
        }

        Ok(Self { 
            youtube, 
            api_key 
        })
    }


    pub async fn get_my_subscriptions(&self) -> Result<Vec<Artist>> {
        info!("Fetching user subscriptions");
        
        let mut artists = Vec::new();
        let mut page_token: Option<String> = None;

        loop {
            let mut req = self.youtube.subscriptions().list(&vec!["snippet".to_string()]);
            req = req.mine(true);
            req = req.max_results(50);
            
            if let Some(token) = &page_token {
                req = req.page_token(token);
            }

            // Add timeout to API requests (5 minutes for authentication if needed)
            let response = tokio::time::timeout(
                Duration::from_secs(300),
                req.doit()
            ).await
                .context("API request timed out after 5 minutes. Please ensure you've completed browser authentication.")?
                .context("Failed to fetch subscriptions from YouTube API")?;

            let (_, subscription_list) = response;

            if let Some(items) = subscription_list.items {
                for item in items {
                    if let Some(snippet) = &item.snippet {
                        if let Some(resource_id) = &snippet.resource_id {
                            if let Some(channel_id) = &resource_id.channel_id {
                                let artist = Artist {
                                    name: snippet.title.clone().unwrap_or_else(|| "Unknown Artist".to_string()),
                                    channel_id: channel_id.clone(),
                                    subscriber_count: None,
                                    description: snippet.description.clone(),
                                };
                                debug!("Found subscription: {}", artist.name);
                                artists.push(artist);
                            }
                        }
                    }
                }
            }

            page_token = subscription_list.next_page_token;
            if page_token.is_none() {
                break;
            }
        }

        info!("Found {} subscriptions", artists.len());
        Ok(artists)
    }

    pub async fn search_artist(&self, artist_name: &str) -> Result<Option<Artist>> {
        info!("Searching for artist: {}", artist_name);
        
        let req = self.youtube.search().list(&vec!["snippet".to_string()])
            .q(artist_name)
            .param("type", "channel")
            .max_results(10);

        let response = req.doit().await
            .context(format!("Failed to search for artist '{}'. This might indicate: 1) YouTube Data API v3 is not enabled, 2) Missing search permissions, or 3) API quota exceeded", artist_name))?;

        let (_, search_response) = response;

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

        warn!("No matching artist found for: {}", artist_name);
        Ok(None)
    }

    pub async fn subscribe_to_channel(&self, channel_id: &str) -> Result<()> {
        info!("Subscribing to channel: {}", channel_id);

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

        let req = self.youtube.subscriptions().insert(subscription)
            .add_part("snippet");

        req.doit().await
            .context("Failed to subscribe to channel")?;

        info!("Successfully subscribed to channel: {}", channel_id);
        Ok(())
    }

    pub async fn unsubscribe_from_channel(&self, subscription_id: &str) -> Result<()> {
        info!("Unsubscribing from subscription: {}", subscription_id);

        let req = self.youtube.subscriptions().delete(subscription_id);
        
        req.doit().await
            .context("Failed to unsubscribe from channel")?;

        info!("Successfully unsubscribed from: {}", subscription_id);
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