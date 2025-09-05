"""YouTube Music client for managing subscriptions."""

import logging
import time
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .models import Artist, SubscriptionStatus


logger = logging.getLogger(__name__)


class YouTubeMusicClient:
    """Client for interacting with YouTube Music."""
    
    def __init__(self, headless: bool = False, timeout: int = 10):
        """Initialize the YouTube Music client."""
        self.timeout = timeout
        self.driver = self._setup_driver(headless)
        self.base_url = "https://music.youtube.com"
        
    def _setup_driver(self, headless: bool) -> webdriver.Chrome:
        """Set up Chrome WebDriver."""
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Add user agent to appear more like a real browser
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        return webdriver.Chrome(options=options)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
    
    def navigate_to_music(self):
        """Navigate to YouTube Music."""
        logger.info("Navigating to YouTube Music")
        self.driver.get(self.base_url)
        time.sleep(2)  # Allow page to load
    
    def search_artist(self, artist_name: str) -> Optional[Artist]:
        """Search for an artist."""
        logger.info(f"Searching for artist: {artist_name}")
        
        try:
            search_url = f"{self.base_url}/search?q={artist_name.replace(' ', '+')}"
            self.driver.get(search_url)
            
            # Wait for search results
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ytmusic-shelf-renderer"))
            )
            
            # Look for artist results
            artist_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a[href*='/channel/'], a[href*='/artist/']"
            )
            
            for link in artist_links:
                link_text = link.get_attribute("title") or link.text
                if link_text and artist_name.lower() in link_text.lower():
                    artist_url = link.get_attribute("href")
                    # Extract artist ID from URL
                    artist_id = artist_url.split("/")[-1] if artist_url else None
                    
                    return Artist(
                        name=link_text,
                        id=artist_id,
                        url=artist_url,
                        status=SubscriptionStatus.UNKNOWN
                    )
            
            logger.warning(f"No artist found matching: {artist_name}")
            return None
            
        except TimeoutException:
            logger.error(f"Timeout searching for artist: {artist_name}")
            return None
        except Exception as e:
            logger.error(f"Error searching for artist {artist_name}: {e}")
            return None
    
    def subscribe_to_artist(self, artist: Artist) -> bool:
        """Subscribe to an artist."""
        logger.info(f"Subscribing to artist: {artist.name}")
        
        if not artist.url:
            logger.error(f"No URL for artist: {artist.name}")
            return False
        
        try:
            self.driver.get(artist.url)
            
            # Look for subscribe button
            subscribe_selectors = [
                "button[aria-label*='Subscribe']",
                "ytmusic-subscribe-button-renderer button",
                "paper-button[aria-label*='Subscribe']"
            ]
            
            for selector in subscribe_selectors:
                try:
                    subscribe_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    # Check if already subscribed
                    if "subscribed" in subscribe_btn.get_attribute("aria-label").lower():
                        logger.info(f"Already subscribed to: {artist.name}")
                        artist.status = SubscriptionStatus.SUBSCRIBED
                        return True
                    
                    subscribe_btn.click()
                    logger.info(f"Successfully subscribed to: {artist.name}")
                    artist.status = SubscriptionStatus.SUBSCRIBED
                    return True
                    
                except TimeoutException:
                    continue
            
            logger.warning(f"Could not find subscribe button for: {artist.name}")
            return False
            
        except Exception as e:
            logger.error(f"Error subscribing to {artist.name}: {e}")
            return False
    
    def get_subscriptions(self) -> List[Artist]:
        """Get all current subscriptions."""
        logger.info("Getting current subscriptions")
        
        try:
            subscriptions_url = f"{self.base_url}/library/artists"
            self.driver.get(subscriptions_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ytmusic-two-row-item-renderer, ytmusic-responsive-list-item-renderer"))
            )
            
            # Scroll to load all artists
            self._scroll_to_load_all()
            
            artists = []
            
            # Extract artist information
            artist_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "ytmusic-two-row-item-renderer, ytmusic-responsive-list-item-renderer"
            )
            
            for element in artist_elements:
                try:
                    # Get artist name
                    name_element = element.find_element(By.CSS_SELECTOR, ".title, .text-runs")
                    artist_name = name_element.text.strip()
                    
                    # Get artist URL
                    link_element = element.find_element(By.CSS_SELECTOR, "a")
                    artist_url = link_element.get_attribute("href")
                    
                    if artist_name and artist_url:
                        artist_id = artist_url.split("/")[-1] if artist_url else None
                        
                        artists.append(Artist(
                            name=artist_name,
                            id=artist_id,
                            url=artist_url,
                            status=SubscriptionStatus.SUBSCRIBED
                        ))
                        
                except (NoSuchElementException, AttributeError):
                    continue
            
            logger.info(f"Found {len(artists)} subscribed artists")
            return artists
            
        except Exception as e:
            logger.error(f"Error getting subscriptions: {e}")
            return []
    
    def _scroll_to_load_all(self):
        """Scroll to load all content on the page."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height