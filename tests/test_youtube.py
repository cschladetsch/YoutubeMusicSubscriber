"""Tests for YouTube Music client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ytmusic_manager.youtube import YouTubeMusicClient
from ytmusic_manager.models import Artist, SubscriptionStatus


class TestYouTubeMusicClient:
    """Tests for YouTubeMusicClient class."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock WebDriver."""
        driver = Mock()
        driver.get = Mock()
        driver.find_element = Mock()
        driver.find_elements = Mock()
        driver.execute_script = Mock()
        driver.quit = Mock()
        return driver
    
    @pytest.fixture
    def client(self, mock_driver):
        """Create client with mocked driver."""
        with patch('ytmusic_manager.youtube.webdriver.Chrome', return_value=mock_driver):
            client = YouTubeMusicClient(headless=True)
            yield client
    
    def test_client_initialization(self):
        """Test client initialization."""
        with patch('ytmusic_manager.youtube.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            client = YouTubeMusicClient(headless=True, timeout=15)
            
            assert client.timeout == 15
            assert client.driver == mock_driver
            assert client.base_url == "https://music.youtube.com"
    
    def test_context_manager(self, mock_driver):
        """Test client as context manager."""
        with patch('ytmusic_manager.youtube.webdriver.Chrome', return_value=mock_driver):
            with YouTubeMusicClient() as client:
                assert client.driver == mock_driver
            mock_driver.quit.assert_called_once()
    
    def test_navigate_to_music(self, client, mock_driver):
        """Test navigation to YouTube Music."""
        with patch('time.sleep'):
            client.navigate_to_music()
        
        mock_driver.get.assert_called_once_with("https://music.youtube.com")
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    def test_search_artist_success(self, mock_wait, client, mock_driver):
        """Test successful artist search."""
        # Mock search results
        mock_link = Mock()
        mock_link.get_attribute.side_effect = lambda attr: {
            'title': 'Test Artist',
            'href': 'https://music.youtube.com/artist/test_id'
        }.get(attr)
        mock_link.text = 'Test Artist'
        
        mock_driver.find_elements.return_value = [mock_link]
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        
        result = client.search_artist("Test Artist")
        
        assert result is not None
        assert result.name == "Test Artist"
        assert result.id == "test_id"
        assert result.url == "https://music.youtube.com/artist/test_id"
        assert result.status == SubscriptionStatus.UNKNOWN
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    def test_search_artist_not_found(self, mock_wait, client, mock_driver):
        """Test artist search when no results found."""
        mock_driver.find_elements.return_value = []
        
        result = client.search_artist("Unknown Artist")
        
        assert result is None
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    def test_search_artist_timeout(self, mock_wait, client, mock_driver):
        """Test artist search with timeout."""
        mock_wait_instance = Mock()
        mock_wait_instance.until.side_effect = TimeoutException()
        mock_wait.return_value = mock_wait_instance
        
        result = client.search_artist("Test Artist")
        
        assert result is None
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    def test_subscribe_to_artist_success(self, mock_wait, client, mock_driver):
        """Test successful artist subscription."""
        artist = Artist(name="Test Artist", url="https://music.youtube.com/artist/test")
        
        # Mock subscribe button
        mock_button = Mock()
        mock_button.get_attribute.return_value = "Subscribe to Test Artist"
        mock_button.click = Mock()
        
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_button
        mock_wait.return_value = mock_wait_instance
        
        result = client.subscribe_to_artist(artist)
        
        assert result is True
        assert artist.status == SubscriptionStatus.SUBSCRIBED
        mock_button.click.assert_called_once()
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    def test_subscribe_to_artist_already_subscribed(self, mock_wait, client, mock_driver):
        """Test subscribing to already subscribed artist."""
        artist = Artist(name="Test Artist", url="https://music.youtube.com/artist/test")
        
        # Mock subscribed button
        mock_button = Mock()
        mock_button.get_attribute.return_value = "Subscribed to Test Artist"
        
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_button
        mock_wait.return_value = mock_wait_instance
        
        result = client.subscribe_to_artist(artist)
        
        assert result is True
        assert artist.status == SubscriptionStatus.SUBSCRIBED
        mock_button.click.assert_not_called()
    
    def test_subscribe_to_artist_no_url(self, client):
        """Test subscribing to artist without URL."""
        artist = Artist(name="Test Artist")
        
        result = client.subscribe_to_artist(artist)
        
        assert result is False
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    def test_subscribe_to_artist_button_not_found(self, mock_wait, client, mock_driver):
        """Test subscribing when subscribe button not found."""
        artist = Artist(name="Test Artist", url="https://music.youtube.com/artist/test")
        
        mock_wait_instance = Mock()
        mock_wait_instance.until.side_effect = TimeoutException()
        mock_wait.return_value = mock_wait_instance
        
        result = client.subscribe_to_artist(artist)
        
        assert result is False
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    @patch('time.sleep')
    def test_get_subscriptions_success(self, mock_sleep, mock_wait, client, mock_driver):
        """Test getting current subscriptions."""
        # Mock artist elements
        mock_element1 = Mock()
        mock_name_element1 = Mock()
        mock_name_element1.text = "Artist 1"
        mock_link_element1 = Mock()
        mock_link_element1.get_attribute.return_value = "https://music.youtube.com/artist/id1"
        
        def mock_find_element1(by, selector):
            if ".title" in selector or ".text-runs" in selector:
                return mock_name_element1
            elif selector == "a":
                return mock_link_element1
            return Mock()
        mock_element1.find_element = mock_find_element1
        
        mock_element2 = Mock()
        mock_name_element2 = Mock()
        mock_name_element2.text = "Artist 2"
        mock_link_element2 = Mock()
        mock_link_element2.get_attribute.return_value = "https://music.youtube.com/artist/id2"
        
        def mock_find_element2(by, selector):
            if ".title" in selector or ".text-runs" in selector:
                return mock_name_element2
            elif selector == "a":
                return mock_link_element2
            return Mock()
        mock_element2.find_element = mock_find_element2
        
        mock_driver.find_elements.return_value = [mock_element1, mock_element2]
        
        # Mock scrolling behavior - get_height, scroll, get_height (stops)
        mock_driver.execute_script.side_effect = [1000, None, 1000]
        
        mock_wait_instance = Mock()
        mock_wait.return_value = mock_wait_instance
        
        result = client.get_subscriptions()
        
        assert len(result) == 2
        assert result[0].name == "Artist 1"
        assert result[0].id == "id1"
        assert result[0].status == SubscriptionStatus.SUBSCRIBED
        assert result[1].name == "Artist 2"
        assert result[1].id == "id2"
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    def test_get_subscriptions_empty(self, mock_wait, client, mock_driver):
        """Test getting subscriptions when none found."""
        mock_driver.find_elements.return_value = []
        mock_driver.execute_script.return_value = 1000  # Static height
        
        result = client.get_subscriptions()
        
        assert len(result) == 0
    
    @patch('ytmusic_manager.youtube.WebDriverWait')
    def test_get_subscriptions_element_error(self, mock_wait, client, mock_driver):
        """Test getting subscriptions with element errors."""
        # Mock element that raises exception
        mock_element = Mock()
        mock_element.find_element.side_effect = NoSuchElementException()
        
        mock_driver.find_elements.return_value = [mock_element]
        mock_driver.execute_script.return_value = 1000
        
        result = client.get_subscriptions()
        
        assert len(result) == 0
    
    @patch('time.sleep')
    def test_scroll_to_load_all(self, mock_sleep, client, mock_driver):
        """Test scrolling to load all content."""
        # Mock the sequence: get_height(1000) -> scroll(None) -> get_height(2000) -> scroll(None) -> get_height(2000)
        mock_driver.execute_script.side_effect = [1000, None, 2000, None, 2000]
        
        client._scroll_to_load_all()
        
        # Should scroll twice (until height stops changing)
        assert mock_driver.execute_script.call_count >= 3
        mock_sleep.assert_called()
    
    def test_setup_driver_headless(self):
        """Test driver setup in headless mode."""
        with patch('ytmusic_manager.youtube.webdriver.Chrome') as mock_chrome:
            with patch('ytmusic_manager.youtube.Options') as mock_options:
                mock_options_instance = Mock()
                mock_options.return_value = mock_options_instance
                
                YouTubeMusicClient(headless=True)
                
                mock_options_instance.add_argument.assert_any_call("--headless")
    
    def test_setup_driver_non_headless(self):
        """Test driver setup in non-headless mode."""
        with patch('ytmusic_manager.youtube.webdriver.Chrome') as mock_chrome:
            with patch('ytmusic_manager.youtube.Options') as mock_options:
                mock_options_instance = Mock()
                mock_options.return_value = mock_options_instance
                
                YouTubeMusicClient(headless=False)
                
                # Should not add --headless argument
                calls = mock_options_instance.add_argument.call_args_list
                headless_calls = [call for call in calls if '--headless' in str(call)]
                assert len(headless_calls) == 0