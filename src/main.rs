use clap::{Parser, Subcommand};
use log::{info, error, warn};
use std::path::PathBuf;
use std::collections::HashSet;
use colored::*;

mod youtube;
use youtube::{YouTubeClient, parse_artists_file};

fn format_subscriber_count(count: u64) -> String {
    use colored::*;
    
    let formatted = if count >= 10_000_000 {
        // 10M+ - Diamond tier
        let val = count as f64 / 1_000_000.0;
        format!("{:.1}M", val).bright_magenta().bold()
    } else if count >= 1_000_000 {
        // 1M+ - Platinum tier  
        let val = count as f64 / 1_000_000.0;
        format!("{:.1}M", val).bright_cyan().bold()
    } else if count >= 500_000 {
        // 500K+ - Gold tier
        let val = count as f64 / 1_000.0;
        format!("{:.0}K", val).bright_yellow().bold()
    } else if count >= 100_000 {
        // 100K+ - Silver tier
        let val = count as f64 / 1_000.0;
        format!("{:.0}K", val).bright_white().bold()
    } else if count >= 10_000 {
        // 10K+ - Bronze tier
        let val = count as f64 / 1_000.0;
        format!("{:.0}K", val).yellow()
    } else if count >= 1_000 {
        // 1K+ - Growing
        let val = count as f64 / 1_000.0;
        format!("{:.0}K", val).green()
    } else {
        // Sub-1K - Starting out
        format!("{}", count).bright_black()
    };
    
    formatted.to_string()
}

fn truncate_description(desc: &str, verbose: bool) -> String {
    if verbose || desc.len() <= 120 {
        desc.to_string()
    } else {
        format!("{}...", &desc[..117])
    }
}

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
        /// Artists file path (optional, uses config.json if not specified)
        #[arg(long)]
        artists_file: Option<PathBuf>,

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
        
        /// Artists file path (optional, uses config.json if not specified)
        #[arg(long)]
        artists_file: Option<PathBuf>,
        
        /// Update artist info from API (ignores cache)
        #[arg(long)]
        update_artist_info: bool,
    },
    /// Validate artists file format
    Validate {
        /// Artists file path (required for validation)
        #[arg(long, default_value = "artists.txt")]
        artists_file: PathBuf,
    },
    /// Open a subscription in YouTube Music by number
    Goto {
        /// Subscription number to open
        number: usize,
        
        /// Artists file path (optional, uses config.json if not specified)
        #[arg(long)]
        artists_file: Option<PathBuf>,
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
        "warn"
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
                artists_file.as_deref(),
                actual_dry_run,
                delay,
                interactive,
                !cli.show_browser,
                cli.verbose,
            )
            .await
        }
        Commands::List { output, artists_file, update_artist_info } => {
            cmd_list(output.as_deref(), artists_file.as_deref(), update_artist_info, !cli.show_browser, cli.verbose).await
        }
        Commands::Validate { artists_file } => {
            cmd_validate(&artists_file, cli.verbose).await
        }
        Commands::Goto { number, artists_file } => {
            cmd_goto(number, artists_file.as_deref(), cli.verbose).await
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
    artists_file: Option<&std::path::Path>,
    dry_run: bool,
    delay: f64,
    _interactive: bool,
    _headless: bool, // Not needed for API
    _verbose: bool,
) -> anyhow::Result<()> {
    let source = if let Some(file) = artists_file {
        format!("file: {}", file.display())
    } else {
        "config.json".to_string()
    };
    
    info!(
        "Starting sync {} (source: {}, delay: {}s)",
        if dry_run { "(DRY RUN)" } else { "" },
        source,
        delay
    );

    // Initialize YouTube client and get target artists
    let client = YouTubeClient::new().await?;
    let target_artists = if let Some(file_path) = artists_file {
        if !file_path.exists() {
            anyhow::bail!("Artists file not found: {}", file_path.display());
        }
        
        // Parse artists file
        let content = std::fs::read_to_string(file_path)?;
        let parsed_artists = parse_artists_file(&content)?;
        info!("Loaded {} target artists from {}", parsed_artists.len(), file_path.display());
        parsed_artists
    } else {
        // Use config artists
        let config_artists = client.get_config_artists().clone();
        info!("Loaded {} target artists from config.json", config_artists.len());
        config_artists
    };

    // Client already initialized above
    
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
    println!("\n{}", "SYNC PLAN:".bright_cyan().bold());
    println!("{}", "==================================================".bright_cyan());
    println!("Current subscriptions: {}", current_subscriptions.len().to_string().bright_white().bold());
    println!("Target artists: {}", target_artists.len().to_string().bright_white().bold());
    println!("Already subscribed: {}", already_subscribed.len().to_string().bright_green().bold());
    println!("To subscribe: {}", to_subscribe.len().to_string().bright_yellow().bold());

    if !already_subscribed.is_empty() {
        println!("\n{}", "Already SUBSCRIBED to:".bright_green().bold());
        for artist in &already_subscribed {
            println!("  {} {}", "✓".bright_green().bold(), artist.bright_white());
        }
    }

    if !to_subscribe.is_empty() {
        if dry_run {
            println!("\n{}", "DRY RUN - Would SUBSCRIBE to:".bright_yellow().bold());
            for artist in &to_subscribe {
                println!("  {} {}", "+".bright_yellow().bold(), artist.bright_white());
            }
        } else {
            println!("\n{} {} {}", "SUBSCRIBING to".bright_blue().bold(), to_subscribe.len().to_string().bright_white().bold(), "artists:".bright_blue().bold());
            
            for (i, artist_name) in to_subscribe.iter().enumerate() {
                println!("  {} {} {}", format!("[{current}/{total}]", current = i + 1, total = to_subscribe.len()).bright_black(), "Searching for:".bright_black(), artist_name.bright_white().bold());
                
                match client.search_artist(artist_name).await {
                    Ok(Some(artist)) => {
                        println!("    {} {} {}", "Found:".bright_green(), artist.name.bright_white().bold(), format!("({channel_id})", channel_id = artist.channel_id).bright_black());
                        
                        match client.subscribe_to_channel(&artist.channel_id).await {
                            Ok(()) => println!("    {} {}", "✓".bright_green().bold(), "Successfully subscribed".bright_green()),
                            Err(e) => {
                                warn!("Failed to subscribe to {artist_name}: {e}");
                                println!("    {} {}: {error}", "✗".bright_red().bold(), "Failed to subscribe".bright_red(), error = e.to_string().red());
                            }
                        }
                    }
                    Ok(None) => {
                        warn!("Could not find artist: {artist_name}");
                        println!("    {} {}", "✗".bright_red().bold(), "Artist not found".bright_red());
                    }
                    Err(e) => {
                        warn!("Search failed for {artist_name}: {e}");
                        println!("    {} {}: {error}", "✗".bright_red().bold(), "Search error".bright_red(), error = e.to_string().red());
                    }
                }
                
                if i < to_subscribe.len() - 1 {
                    tokio::time::sleep(std::time::Duration::from_secs_f64(delay)).await;
                }
            }
        }
    } else {
        println!("\n{} {}", "✓".bright_green().bold(), "All target artists are already subscribed!".bright_green().bold());
    }

    Ok(())
}

async fn cmd_list(
    output: Option<&std::path::Path>,
    artists_file: Option<&std::path::Path>,
    update_artist_info: bool,
    _headless: bool, // Not needed for API
    _verbose: bool,
) -> anyhow::Result<()> {
    info!("Listing current subscriptions");

    let client = YouTubeClient::new().await?;
    let mut offset = 0;
    let limit = 50; // Show more at once with higher quotas
    let mut all_subscriptions = Vec::new();
    let mut total_channels = 0;
    
    loop {
        let (subscriptions, has_more, total) = client.get_subscriptions_with_pagination(offset, limit, artists_file, update_artist_info, _verbose).await?;
        
        // Set total_channels on first iteration
        if offset == 0 {
            total_channels = total;
        }
        
        if subscriptions.is_empty() && offset == 0 {
            println!("{}", "No subscriptions found.".bright_yellow());
            break;
        }
        
        // Display current batch
        if offset == 0 {
            println!();
        }
        
        for (i, artist) in subscriptions.iter().enumerate() {
            let global_index = offset + i + 1;
            let info = match (&artist.description, artist.subscriber_count) {
                (Some(desc), Some(count)) => {
                    let truncated_desc = truncate_description(desc, _verbose);
                    format!("({truncated_desc} - {subs} subs)", subs = format_subscriber_count(count))
                },
                (Some(desc), None) => {
                    let truncated_desc = truncate_description(desc, _verbose);
                    format!("({truncated_desc})")
                },
                (None, Some(count)) => format!("({subs} subs)", subs = format_subscriber_count(count)),
                (None, None) => String::new(),
            };
            let number = format!("{}.", global_index).bright_cyan().bold();
            let name = artist.name.bright_white();
            let info_styled = info.bright_black();
            println!("{number} {name} {info_styled}");
        }
        
        all_subscriptions.extend(subscriptions);
        
        if !has_more {
            break;
        }
        
        // Ask user if they want to continue
        print!("\n{} {} {} {}", 
               "Show next".bright_cyan(), 
               limit.to_string().bright_white().bold(),
               "artists?".bright_cyan(),
               "[Y/n]:".bright_yellow());
        std::io::Write::flush(&mut std::io::stdout())?;
        
        let mut input = String::new();
        std::io::stdin().read_line(&mut input)?;
        let input = input.trim().to_lowercase();
        
        if input == "n" || input == "no" {
            break;
        }
        
        offset += limit;
        println!(); // Add spacing
    }
    
    println!("\n{found}/{total} {text}", 
             found = all_subscriptions.len().to_string().bright_white().bold(),
             total = total_channels.to_string().bright_white().bold(),
             text = "Subscriptions shown".bright_green());
    
    if let Some(output_file) = output {
        let content = all_subscriptions.iter()
            .map(|a| a.name.clone())
            .collect::<Vec<_>>()
            .join("\n");
        std::fs::write(output_file, content)?;
        println!("{} {}", "Subscriptions saved to:".bright_green(), output_file.display().to_string().bright_white().bold());
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
                        println!("{} {}: {} {}", "VALID Line".bright_green(), (line_num + 1).to_string().bright_white().bold(), name.trim().bright_white().bold(), format!("(tags: {tags})", tags = tags.trim()).bright_black());
                    } else {
                        println!("{} {}: {}", "VALID Line".bright_green(), (line_num + 1).to_string().bright_white().bold(), line.bright_white().bold());
                    }
                }
            }

            println!("\n{} {}", "Valid artists:".bright_green(), artists.len().to_string().bright_white().bold());
            println!("{} {}", "Errors:".bright_green(), "0".bright_green().bold());
            println!("{}", "All entries are valid!".bright_green().bold());

            Ok(())
        }
        Err(e) => {
            error!("Validation failed: {e}");
            anyhow::bail!("File validation failed");
        }
    }
}

async fn cmd_goto(
    number: usize,
    artists_file: Option<&std::path::Path>,
    _verbose: bool,
) -> anyhow::Result<()> {
    if number == 0 {
        anyhow::bail!("Subscription numbers start from 1, not 0");
    }
    
    info!("Opening subscription number {number}");

    let client = YouTubeClient::new().await?;
    
    // Get all subscriptions to find the one at the requested index
    let (all_subscriptions, _, total_count) = client.get_subscriptions_with_pagination(0, 1000, artists_file, false, _verbose).await?;
    
    if number > total_count {
        anyhow::bail!("Invalid subscription number. Available subscriptions: 1-{total_count}");
    }
    
    if let Some(artist) = all_subscriptions.get(number - 1) {
        let youtube_music_url = format!("https://music.youtube.com/channel/{}", artist.channel_id);
        
        let opening = "Opening".bright_green();
        let name = artist.name.bright_white().bold();
        let url = format!("({})", youtube_music_url).bright_black();
        println!("{opening} {name} {url}");
        
        // Open the URL in the default browser
        if let Err(e) = webbrowser::open(&youtube_music_url) {
            anyhow::bail!("Failed to open browser: {e}");
        }
        
        info!("Successfully opened {name} in browser", name = artist.name);
        Ok(())
    } else {
        anyhow::bail!("Could not find subscription number {number}")
    }
}
