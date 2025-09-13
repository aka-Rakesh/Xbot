"""
Bounty site scraper for the Twitter Bounty Bot.
Handles fetching and parsing bounty data from target websites.
"""
import requests
import time
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright
from .config import BOUNTY_SITE_URL
from .utils import get_user_agent, log_with_context

logger = logging.getLogger(__name__)

class BountyScraper:
    """Scraper for bounty sites using requests/BeautifulSoup or Playwright."""
    
    def __init__(self, site_url: str = None):
        self.site_url = site_url or BOUNTY_SITE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def fetch_bounties_requests(self) -> List[Dict]:
        """
        Fetch bounties using requests and BeautifulSoup.
        Use this for sites with server-side rendered content.
        
        Returns:
            List of bounty dictionaries with id, title, url, description
        """
        try:
            log_with_context(logging.INFO, "Fetching bounties", site_url=self.site_url)
            response = self.session.get(self.site_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            bounties = []
            
            # Look for elements containing 'thread', 'twitter', or similar bounty-related terms
            bounty_elements = []
            
            # Try multiple selectors for different site structures
            selectors = [
                # Look for elements with classes containing bounty-related words
                '[class*="bounty"]', '[class*="task"]', '[class*="job"]', '[class*="opportunity"]',
                '[class*="thread"]', '[class*="twitter"]', '[class*="social"]', '[class*="post"]',
                # Look for elements with text content containing these words
                'div:contains("thread")', 'div:contains("twitter")', 'div:contains("bounty")',
                'article:contains("thread")', 'article:contains("twitter")', 'article:contains("bounty")',
                # Generic card/item selectors
                '.card', '.item', '.post', '.bounty', '.task', '.job'
            ]
            
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    bounty_elements.extend(elements)
                except:
                    continue
            
            # Remove duplicates while preserving order
            seen = set()
            bounty_elements = [elem for elem in bounty_elements if elem not in seen and not seen.add(elem)]
            
            for element in bounty_elements:
                try:
                    # Extract bounty data - customize these selectors
                    link = element.select_one('a')
                    if not link:
                        continue
                    
                    href = link.get('href', '')
                    if not href.startswith('http'):
                        href = self.site_url.rstrip('/') + '/' + href.lstrip('/')
                    
                    title = link.get_text(strip=True)
                    bounty_id = self._extract_bounty_id(href, title)
                    
                    # Try to extract description
                    description = ''
                    desc_element = element.select_one('.description, .summary, .bounty-desc')
                    if desc_element:
                        description = desc_element.get_text(strip=True)
                    
                    if bounty_id and title:
                        bounties.append({
                            'id': bounty_id,
                            'title': title,
                            'url': href,
                            'description': description,
                            'scraped_at': int(time.time())
                        })
                        
                except Exception as e:
                    log_with_context(logging.WARNING, "Error parsing bounty element", error=str(e))
                    continue
            
            log_with_context(logging.INFO, "Successfully scraped bounties", count=len(bounties))
            return bounties
            
        except requests.RequestException as e:
            log_with_context(logging.ERROR, "Failed to fetch bounties", error=str(e))
            raise
        except Exception as e:
            log_with_context(logging.ERROR, "Unexpected error in scraper", error=str(e))
            raise
    
    def fetch_bounties_playwright(self) -> List[Dict]:
        """
        Fetch bounties using Playwright for JavaScript-heavy sites.
        Use this when the content is rendered client-side.
        
        Returns:
            List of bounty dictionaries with id, title, url, description
        """
        try:
            log_with_context(logging.INFO, "Fetching bounties with Playwright", site_url=self.site_url)
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Set user agent
                page.set_extra_http_headers({'User-Agent': get_user_agent()})
                
                # Navigate to the page
                page.goto(self.site_url, wait_until='networkidle')
                
                # Wait for page to load and look for elements containing bounty-related terms
                page.wait_for_load_state('networkidle', timeout=15000)
                
                # Try to find elements with bounty-related content
                try:
                    page.wait_for_selector('div, article, section', timeout=5000)
                except:
                    pass  # Continue even if no specific elements found
                
                # Extract bounty data by looking for elements containing 'thread', 'twitter', etc.
                bounties = page.evaluate("""
                    () => {
                        const keywords = ['thread', 'twitter', 'bounty', 'task', 'job', 'opportunity', 'social', 'post', 'content', 'writing', 'article', 'blog', 'tweet', 'social media', 'marketing', 'promotion'];
                        const allElements = document.querySelectorAll('div, article, section, li');
                        const bountyElements = [];
                        
                        allElements.forEach(el => {
                            const text = el.textContent.toLowerCase();
                            const hasKeyword = keywords.some(keyword => text.includes(keyword));
                            
                            // Filter out navigation, header, and CSS elements
                            const isNavigation = text.includes('login') || text.includes('sign up') || 
                                               text.includes('become a sponsor') || text.includes('nprogress') ||
                                               text.includes('pointer-events') || text.includes('background:') ||
                                               text.includes('filter') || text.includes('sort') ||
                                               text.includes('category') || text.includes('status') ||
                                               el.tagName === 'NAV' || el.tagName === 'HEADER' ||
                                               el.classList.contains('nav') || el.classList.contains('header') ||
                                               el.classList.contains('filter') || el.classList.contains('sort');
                            
                            if (hasKeyword && el.textContent.trim().length > 20 && !isNavigation) {
                                const link = el.querySelector('a') || el.closest('a');
                                if (link && link.href && !link.href.includes('javascript:')) {
                                    bountyElements.push({
                                        href: link.href,
                                        title: link.textContent.trim() || el.textContent.trim(),
                                        description: el.textContent.trim(),
                                        elementText: el.textContent.trim()
                                    });
                                }
                            }
                        });
                        
                        return bountyElements.slice(0, 20); // Limit to first 20 results
                    }
                """)
                
                browser.close()
                
                # Process the extracted data
                processed_bounties = []
                for bounty_data in bounties:
                    bounty_id = self._extract_bounty_id(bounty_data['href'], bounty_data['title'])
                    if bounty_id and bounty_data['title']:
                        processed_bounties.append({
                            'id': bounty_id,
                            'title': bounty_data['title'],
                            'url': bounty_data['href'],
                            'description': bounty_data['description'],
                            'scraped_at': int(time.time())
                        })
                
                log_with_context(logging.INFO, "Successfully scraped bounties with Playwright", count=len(processed_bounties))
                return processed_bounties
                
        except Exception as e:
            log_with_context(logging.ERROR, "Failed to fetch bounties with Playwright", error=str(e))
            raise
    
    def _extract_bounty_id(self, url: str, title: str) -> str:
        """
        Extract a unique bounty ID from URL or title.
        
        Args:
            url: Bounty URL
            title: Bounty title
            
        Returns:
            Unique bounty identifier
        """
        # Try to extract ID from URL path
        if '/' in url:
            path_parts = url.rstrip('/').split('/')
            # Look for numeric ID or slug in the last part
            last_part = path_parts[-1]
            if last_part.isdigit():
                return last_part
            elif '-' in last_part or '_' in last_part:
                return last_part
        
        # Fallback: create ID from title hash
        import hashlib
        return hashlib.md5(title.encode()).hexdigest()[:12]
    
    def fetch_bounties(self, use_playwright: bool = False) -> List[Dict]:
        """
        Main method to fetch bounties.
        
        Args:
            use_playwright: Whether to use Playwright instead of requests
            
        Returns:
            List of bounty dictionaries
        """
        if use_playwright:
            return self.fetch_bounties_playwright()
        else:
            return self.fetch_bounties_requests()

# Convenience function for backward compatibility
def fetch_bounties(site_url: str = None, use_playwright: bool = False) -> List[Dict]:
    """
    Fetch bounties from the specified site.
    
    Args:
        site_url: URL of the bounty site
        use_playwright: Whether to use Playwright for JavaScript-heavy sites
        
    Returns:
        List of bounty dictionaries
    """
    scraper = BountyScraper(site_url)
    return scraper.fetch_bounties(use_playwright)
