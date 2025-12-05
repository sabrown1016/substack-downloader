import os
import time
import json
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from dotenv import load_dotenv

from urllib.parse import urlparse, unquote

load_dotenv()

class SubstackScraper:
    def __init__(self, base_url, cookie=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        if cookie:
            # Decode cookie if it's URL encoded (e.g. starts with s%3A)
            cookie = unquote(cookie)
            
            # Set cookie for the specific domain of the newsletter
            # This handles custom domains (e.g. robkhenderson.com) where .substack.com cookies are not sent
            domain = urlparse(base_url).netloc
            
            # Custom domains (like robkhenderson.com) use 'connect.sid'
            # Substack subdomains (like read.substack.com) use 'substack.sid'
            cookie_name = 'substack.sid' if 'substack.com' in domain else 'connect.sid'
            
            self.session.cookies.set(cookie_name, cookie, domain=domain)

    def load_session_file(self, session_file):
        """Load session (cookies) from a Playwright JSON export."""
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            # Update User-Agent
            if 'user_agent' in data:
                self.session.headers.update({'User-Agent': data['user_agent']})
            
            # Load Cookies
            if 'cookies' in data:
                for cookie in data['cookies']:
                    # We only care about the name/value and domain matching
                    # Requests wants a specific format, but setting simple dicts often works
                    self.session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie['domain'],
                        path=cookie['path']
                    )
            print(f"Loaded session from {session_file}")
            return True
        except Exception as e:
            print(f"Error loading session file: {e}")
            return False

    def get_archive(self, limit=12, offset=0):
        """Fetch list of posts from the archive API."""
        url = f"{self.base_url}/api/v1/archive"
        params = {
            'sort': 'new',
            'search': '',
            'offset': offset,
            'limit': limit
        }
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching archive: {e}")
            return []

    def get_post(self, slug):
        """Fetch full post content."""
        url = f"{self.base_url}/api/v1/posts/{slug}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching post {slug}: {e}")
            return None

    def save_post(self, post, output_dir):
        """Save post content to file."""
        if not post:
            return

        date = post.get('post_date', '').split('T')[0]
        slug = post.get('slug', 'unknown')
        title = post.get('title', 'Untitled')
        
        # Create filename safely
        safe_slug = "".join([c for c in slug if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).rstrip()
        filename_base = f"{date}_{safe_slug}"
        
        # Save HTML content
        html_content = post.get('body_html', '')
        if html_content:
            with open(os.path.join(output_dir, f"{filename_base}.html"), 'w') as f:
                # Wrap in simple HTML template for readability
                full_html = f"<html><head><title>{title}</title></head><body><h1>{title}</h1>{html_content}</body></html>"
                f.write(full_html)


    def scrape(self, output_dir="archive", limit=None, skip_podcasts=False):
        """Main scraping loop."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Starting scrape for {self.base_url}...")
        
        offset = 0
        batch_size = 12
        total_fetched = 0
        
        while True:
            if limit and total_fetched >= limit:
                break
                
            batch_limit = batch_size
            if limit and (limit - total_fetched) < batch_size:
                batch_limit = limit - total_fetched

            print(f"Fetching posts {offset} to {offset + batch_limit}...")
            posts = self.get_archive(limit=batch_limit, offset=offset)
            
            if not posts:
                break
                
            for post_summary in tqdm(posts):
                if limit and total_fetched >= limit:
                    break
                    
                slug = post_summary.get('slug')
                if not slug:
                    continue

                # Check if it's a podcast
                is_podcast = post_summary.get('type') == 'podcast' or post_summary.get('podcast_url') is not None
                if skip_podcasts and is_podcast:
                    print(f"Skipping podcast: {slug}")
                    continue
                    
                # Small delay to be nice
                time.sleep(1)
                
                full_post = self.get_post(slug)
                if full_post:
                    self.save_post(full_post, output_dir)
                    total_fetched += 1
            
            # Since we might skip posts, we can't just rely on total_fetched for offset
            # We must consistently move the offset by the number of posts fetched from API
            offset += len(posts)
            
            if len(posts) < batch_limit:  # No more posts (checked against what we asked for)
                break

        print(f"Scraping complete. Downloaded {total_fetched} posts.")

def main():
    parser = argparse.ArgumentParser(description="Scrape a Substack newsletter.")
    parser.add_argument("--url", required=True, help="Base URL of the Substack (e.g., https://read.substack.com)")
    parser.add_argument("--cookie", help="substack.sid cookie (optional, overrides .env)")
    parser.add_argument("--limit", type=int, help="Limit number of posts to scrape")
    parser.add_argument("--skip-podcasts", action="store_true", help="Skip downloading podcast episodes")
    
    args = parser.parse_args()

    # Priority:
    # 1. Command line cookie
    # 2. Session file (from login.py)
    # 3. .env cookie
    
    cookie = args.cookie
    
    # Priority for session file:
    # 1. substack_session_{domain}.json
    # 2. substack_session.json
    
    from urllib.parse import urlparse
    domain = urlparse(args.url).netloc
    
    session_file_specific = f"substack_session_{domain}.json"
    session_file_default = "substack_session.json"
    
    scraper = SubstackScraper(args.url, cookie)
    
    if not cookie:
        if os.path.exists(session_file_specific):
            scraper.load_session_file(session_file_specific)
        elif os.path.exists(session_file_default):
             scraper.load_session_file(session_file_default)
        else:
             cookie = os.getenv("SUBSTACK_SID")
             if cookie:
                 scraper = SubstackScraper(args.url, cookie)
    
    # Create a nice output directory name from the URL
    from urllib.parse import urlparse
    domain = urlparse(args.url).netloc
    output_dir = os.path.join("archive", domain)
    
    scraper.scrape(output_dir=output_dir, limit=args.limit, skip_podcasts=args.skip_podcasts)

if __name__ == "__main__":
    main()
