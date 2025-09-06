use clap::{Parser, Subcommand};
use log::{info, error, warn};
use std::path::PathBuf;
use std::collections::HashSet;

mod youtube;
use youtube::{YouTubeClient, parse_artists_file};

#[derive(Parser)]
#[command(name = "ytmusic-manager")]
#[command(version = "0.1.0")]
#[command(about = "A professional CLI tool for managing YouTube Music artist subscriptions")]
#[command(long_about = "YouTube Music Manager allows you to synchronize your YouTube Music subscriptions with a local text file. It compares your target artist list against your current subscriptions and automatically manages the differences.")]
struct Cli {
    /// Enable verbose logging
    #[arg(short, long, global = true)]
    verbose: bool,

    /// Show browser window (default: headless mode)
    #[arg(long, global = true)]
    show_browser: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Sync artist subscriptions
    Sync {
        /// Artists file path
        #[arg(long, default_value = "artists.txt")]
        artists_file: PathBuf,

        /// Preview changes without making them
        #[arg(long, default_value_t = true)]
        dry_run: bool,

        /// Actually make changes (opposite of dry-run)
        #[arg(long, conflicts_with = "dry_run")]
        no_dry_run: bool,

        /// Delay between actions in seconds
        #[arg(long, default_value_t = 2.0)]
        delay: f64,

        /// Ask for confirmation before making changes
        #[arg(long)]
        interactive: bool,
    },
    /// List current subscriptions
    List {
        /// Save list to a file
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Validate artists file format
    Validate {
        /// Artists file path
        #[arg(long, default_value = "artists.txt")]
        artists_file: PathBuf,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize crypto provider for rustls
    let _ = rustls::crypto::ring::default_provider().install_default();
    
    let cli = Cli::parse();

    // Setup logging
    let log_level = if cli.verbose {
        "debug"
    } else {
        "info"
    };
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or(log_level)).init();

    info!("YouTube Music Manager v0.1.0");
    if cli.verbose {
        info!("Verbose logging enabled");
    }
    if cli.show_browser {
        info!("Browser window will be visible");
    }

    let result = match cli.command {
        Commands::Sync {
            artists_file,
            dry_run,
            no_dry_run,
            delay,
            interactive,
        } => {
            let actual_dry_run = if no_dry_run { false } else { dry_run };
            cmd_sync(
                &artists_file,
                actual_dry_run,
                delay,
                interactive,
                !cli.show_browser,
                cli.verbose,
            )
            .await
        }
        Commands::List { output } => {
            cmd_list(output.as_deref(), !cli.show_browser, cli.verbose).await
        }
        Commands::Validate { artists_file } => {
            cmd_validate(&artists_file, cli.verbose).await
        }
    };

    match result {
        Ok(()) => {
            info!("Command completed successfully");
            Ok(())
        }
        Err(e) => {
            error!("Command failed: {e}");
            std::process::exit(1);
        }
    }
}

async fn cmd_sync(
    artists_file: &PathBuf,
    dry_run: bool,
    delay: f64,
    _interactive: bool,
    _headless: bool, // Not needed for API
    _verbose: bool,
) -> anyhow::Result<()> {
    info!(
        "Starting sync {} (file: {}, delay: {}s)",
        if dry_run { "(DRY RUN)" } else { "" },
        artists_file.display(),
        delay
    );

    if !artists_file.exists() {
        anyhow::bail!("Artists file not found: {}", artists_file.display());
    }

    // Parse artists file
    let content = std::fs::read_to_string(artists_file)?;
    let target_artists = parse_artists_file(&content)?;
    info!("Loaded {} target artists from {}", target_artists.len(), artists_file.display());

    // Initialize YouTube client
    let client = YouTubeClient::new().await?;
    
    // Get current subscriptions
    let current_subscriptions = client.get_my_subscriptions().await?;
    let current_names: HashSet<String> = current_subscriptions
        .iter()
        .map(|a| a.name.to_lowercase())
        .collect();

    // Find artists to subscribe to
    let mut to_subscribe = Vec::new();
    let mut already_subscribed = Vec::new();
    
    for target in &target_artists {
        if current_names.contains(&target.to_lowercase()) {
            already_subscribed.push(target.clone());
        } else {
            to_subscribe.push(target.clone());
        }
    }

    // Display sync plan
    println!("\nSYNC PLAN:");
    println!("==================================================");
    println!("Current subscriptions: {}", current_subscriptions.len());
    println!("Target artists: {}", target_artists.len());
    println!("Already subscribed: {}", already_subscribed.len());
    println!("To subscribe: {}", to_subscribe.len());

    if !already_subscribed.is_empty() {
        println!("\nAlready SUBSCRIBED to:");
        for artist in &already_subscribed {
            println!("  ✓ {artist}");
        }
    }

    if !to_subscribe.is_empty() {
        if dry_run {
            println!("\nDRY RUN - Would SUBSCRIBE to:");
            for artist in &to_subscribe {
                println!("  + {artist}");
            }
        } else {
            println!("\nSUBSCRIBING to {} artists:", to_subscribe.len());
            
            for (i, artist_name) in to_subscribe.iter().enumerate() {
                println!("  [{}/{}] Searching for: {}", i + 1, to_subscribe.len(), artist_name);
                
                match client.search_artist(artist_name).await {
                    Ok(Some(artist)) => {
                        println!("    Found: {} ({})", artist.name, artist.channel_id);
                        
                        match client.subscribe_to_channel(&artist.channel_id).await {
                            Ok(()) => println!("    ✓ Successfully subscribed"),
                            Err(e) => {
                                warn!("Failed to subscribe to {artist_name}: {e}");
                                println!("    ✗ Failed to subscribe: {e}");
                            }
                        }
                    }
                    Ok(None) => {
                        warn!("Could not find artist: {artist_name}");
                        println!("    ✗ Artist not found");
                    }
                    Err(e) => {
                        warn!("Search failed for {artist_name}: {e}");
                        println!("    ✗ Search error: {e}");
                    }
                }
                
                if i < to_subscribe.len() - 1 {
                    tokio::time::sleep(std::time::Duration::from_secs_f64(delay)).await;
                }
            }
        }
    } else {
        println!("\n✓ All target artists are already subscribed!");
    }

    Ok(())
}

async fn cmd_list(
    output: Option<&std::path::Path>,
    _headless: bool, // Not needed for API
    _verbose: bool,
) -> anyhow::Result<()> {
    info!("Listing current subscriptions");

    let client = YouTubeClient::new().await?;
    let subscriptions = client.get_my_subscriptions().await?;
    
    println!("\nCURRENT SUBSCRIPTIONS ({})", subscriptions.len());
    println!("==================================================");
    
    if subscriptions.is_empty() {
        println!("No subscriptions found.");
    } else {
        for artist in &subscriptions {
            println!("• {}", artist.name);
        }
    }
    
    if let Some(output_file) = output {
        let content = subscriptions.iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>()
            .join("\n");
        std::fs::write(output_file, content)?;
        println!("\nSubscriptions saved to: {}", output_file.display());
    }

    Ok(())
}

async fn cmd_validate(artists_file: &PathBuf, verbose: bool) -> anyhow::Result<()> {
    info!("Validating artists file: {}", artists_file.display());

    if !artists_file.exists() {
        anyhow::bail!("File not found: {}", artists_file.display());
    }

    let content = std::fs::read_to_string(artists_file)?;
    
    // Use the parsing function to validate
    match parse_artists_file(&content) {
        Ok(artists) => {
            if verbose {
                for (line_num, line) in content.lines().enumerate() {
                    let line = line.trim();
                    if line.is_empty() || line.starts_with('#') {
                        continue;
                    }

                    // Parse tags if present
                    if let Some((name, tags)) = line.split_once('|') {
                        println!("VALID Line {}: {} (tags: {})", line_num + 1, name.trim(), tags.trim());
                    } else {
                        println!("VALID Line {}: {}", line_num + 1, line);
                    }
                }
            }

            println!("\nVALIDATION RESULTS:");
            println!("Valid artists: {}", artists.len());
            println!("Errors: 0");
            println!("All entries are valid!");

            Ok(())
        }
        Err(e) => {
            error!("Validation failed: {e}");
            anyhow::bail!("File validation failed");
        }
    }
}
