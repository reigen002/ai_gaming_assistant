"""Dynamic web search tool for any RPG game"""
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from bs4 import BeautifulSoup
import requests
import os
import logging
import re

logger = logging.getLogger(__name__)

# Trusted English gaming wiki domains
ENGLISH_WIKI_DOMAINS = [
    'fandom.com', 'fextralife.com', 'ign.com', 'gamespot.com',
    'gamefaqs.gamespot.com', 'polygon.com', 'eurogamer.net',
    'pcgamer.com', 'rockpapershotgun.com', 'gamesradar.com'
]

# Domains to explicitly block (Chinese/non-English sites)
BLOCKED_DOMAINS = [
    'baidu.com', 'zhihu.com', 'bilibili.com', 'tieba.baidu.com',
    'jingyan.baidu.com', 'weibo.com', '163.com', 'qq.com',
    'tianya.cn', 'sohu.com', 'sina.com', 'douban.com', 'csdn.net',
    'jianshu.com', 'toutiao.com', 'youku.com', 'iqiyi.com',
    'acfun.cn', 'huya.com', 'douyu.com', 'taobao.com', 'tmall.com',
    'jd.com', 'xiaohongshu.com', 'meituan.com', 'dianping.com'
]

# Characters that indicate non-English content
NON_ENGLISH_CHARS = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff]')


class WebSearchInput(BaseModel):
    game_name: str = Field(description="Full game name (e.g., 'Hollow Knight', 'Elden Ring')")
    query: str = Field(description="Specific query about game mechanics, items, locations, etc.")


class WebSearchTool(BaseTool):
    name: str = "Web Search for Game Information"
    description: str = (
        "Search the web for RPG game guides, wikis, and walkthroughs. "
        "Works for ANY game - no pre-indexing required. "
        "Searches official wikis (Fandom, Fextralife), IGN, GameFAQs, and community guides. "
        "Use this to find current, accurate game information."
    )
    args_schema: type[BaseModel] = WebSearchInput

    _timeout: int = PrivateAttr(default=10)
    _max_results: int = PrivateAttr(default=10)
    _max_content_length: int = PrivateAttr(default=3000)

    def _is_english_site(self, url: str) -> bool:
        """Check if URL is from a trusted English gaming site"""
        url_lower = url.lower()
        # Block Chinese sites
        if any(blocked in url_lower for blocked in BLOCKED_DOMAINS):
            return False
        # Prefer English wiki sites
        return any(domain in url_lower for domain in ENGLISH_WIKI_DOMAINS)

    def _is_english_content(self, text: str) -> bool:
        """Check if content is primarily in English (not Chinese/Japanese/Korean/Russian)"""
        if not text:
            return False
        # Count non-English characters
        non_english_count = len(NON_ENGLISH_CHARS.findall(text))
        # If more than 10% non-English characters, skip it
        if len(text) > 0 and (non_english_count / len(text)) > 0.1:
            return False
        return True

    def _filter_english_results(self, results: list) -> list:
        """Filter results to only include English content"""
        filtered = []
        for r in results:
            url = r.get('href', '')
            title = r.get('title', '')
            body = r.get('body', '')

            # Skip blocked domains
            if any(blocked in url.lower() for blocked in BLOCKED_DOMAINS):
                continue

            # Skip if title or body contains non-English text
            if not self._is_english_content(title) or not self._is_english_content(body):
                continue

            filtered.append(r)
        return filtered

    def _search_with_serper(self, search_query: str) -> list:
        """Use Serper API for Google search results"""
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return []

        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "q": search_query,
                    "num": self._max_results,
                    "gl": "us",
                    "hl": "en",
                    "lr": "lang_en"  # Language restrict to English
                },
                timeout=self._timeout
            )
            data = response.json()

            results = []
            for item in data.get("organic", []):
                url = item.get("link", "")
                # Skip blocked domains
                if any(blocked in url.lower() for blocked in BLOCKED_DOMAINS):
                    continue
                results.append({
                    "title": item.get("title", ""),
                    "href": url,
                    "body": item.get("snippet", "")
                })
            return results[:self._max_results]
        except Exception as e:
            logger.warning(f"Serper API failed: {e}")
            return []

    def _search_with_duckduckgo(self, search_query: str) -> list:
        """Fallback to DuckDuckGo search with English-only results"""
        try:
            # Try the ddgs package first (new name)
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            ddgs = DDGS()
            results = list(ddgs.text(
                search_query,
                max_results=self._max_results,
                region='us-en',
                safesearch='moderate'
            ))

            if not results:
                # Try alternative: direct HTML scraping
                return self._search_duckduckgo_html(search_query)

            # Filter out blocked domains and non-English content
            filtered = []
            for r in results:
                url = r.get('href', '')
                title = r.get('title', '')
                body = r.get('body', '')

                if any(blocked in url.lower() for blocked in BLOCKED_DOMAINS):
                    continue
                if not self._is_english_content(title) or not self._is_english_content(body):
                    continue
                filtered.append(r)
            return filtered
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return self._search_duckduckgo_html(search_query)

    def _search_duckduckgo_html(self, search_query: str) -> list:
        """Fallback: scrape DuckDuckGo HTML results"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(search_query)}"
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            for result in soup.select('.result')[:self._max_results]:
                title_el = result.select_one('.result__title a')
                snippet_el = result.select_one('.result__snippet')
                if title_el:
                    href = title_el.get('href', '')
                    if any(blocked in href.lower() for blocked in BLOCKED_DOMAINS):
                        continue
                    title = title_el.get_text(strip=True)
                    body = snippet_el.get_text(strip=True) if snippet_el else ''
                    if self._is_english_content(title):
                        results.append({'title': title, 'href': href, 'body': body})
            return results
        except Exception as e:
            logger.warning(f"DuckDuckGo HTML fallback failed: {e}")
            return []

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        noise_patterns = [
            r'JavaScript is disabled.*?browser\.',
            r'Please enable JavaScript.*?proceed\.',
            r'A required part.*?different browser\.',
            r'Client Challenge',
            r'Loading\.\.\.',
            r'Sign in.*?account',
            r'Create.*?account',
            r'Advertisement',
            r'Skip to.*?content',
        ]
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        return text.strip()

    def _extract_wiki_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract content with wiki-specific selectors"""
        content = ""

        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside',
                            'iframe', 'noscript']):
            element.decompose()

        if "fandom.com" in url or "wikia.com" in url:
            for selector in ['.mw-parser-output', '#mw-content-text', '.page-content', 'article']:
                main_content = soup.select_one(selector)
                if main_content:
                    for unwanted in main_content.select('.portable-infobox, .navbox, .toc, .mbox, .infobox'):
                        unwanted.decompose()
                    paragraphs = main_content.find_all(['p', 'li', 'h2', 'h3'])
                    content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content) > 200:
                        break

        elif "fextralife.com" in url:
            for selector in ['#wiki-content-block', '.wiki-content', 'article', '.col-sm-12']:
                main_content = soup.select_one(selector)
                if main_content:
                    paragraphs = main_content.find_all(['p', 'li', 'h2', 'h3', 'td'])
                    content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content) > 200:
                        break

        elif "ign.com" in url:
            for selector in ['article', '.article-content', '.wiki-page', '.guide-content']:
                main_content = soup.select_one(selector)
                if main_content:
                    paragraphs = main_content.find_all(['p', 'li', 'h2', 'h3'])
                    content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content) > 200:
                        break

        if not content or len(content) < 200:
            for selector in ['article', 'main', '.content', '#content', '.post-content']:
                main_content = soup.select_one(selector)
                if main_content:
                    paragraphs = main_content.find_all(['p', 'li', 'h2', 'h3'])
                    content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if len(content) > 200:
                        break

            if not content or len(content) < 200:
                body = soup.find('body')
                if body:
                    paragraphs = body.find_all(['p', 'li'])
                    content = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])

        return self._clean_text(content)[:self._max_content_length]

    def search(self, game_name: str, query: str) -> list[dict]:
        """
        Perform the web search and return raw results suitable for indexing.
        Returns a list of dicts with keys: 'title', 'href', 'content'.
        """
        try:
            # Build search queries - prioritize game-specific wikis first
            game_lower = game_name.lower().replace(' ', '')

            # Game-specific wiki searches
            search_queries = [
                f"{game_name} {query} wiki",
                f"{game_name} {query} fandom",
                f"{game_name} {query} guide walkthrough",
            ]

            # Add game-specific fandom site if known
            if "hollow" in game_lower:
                search_queries.insert(0, f"site:hollowknight.fandom.com {query}")
            elif "elden" in game_lower:
                search_queries.insert(0, f"site:eldenring.wiki.fextralife.com {query}")
            elif "dark souls" in game_lower or "darksouls" in game_lower:
                search_queries.insert(0, f"site:darksouls.fandom.com {query}")

            all_results = []

            # Try each search query
            for sq in search_queries:
                # Try Serper first (Google results)
                results = self._search_with_serper(sq)
                if results:
                    # Filter to English content only
                    filtered = [r for r in results if self._is_english_content(r.get('title', '')) and self._is_english_content(r.get('body', ''))]
                    # Prioritize trusted wikis but don't exclude others
                    trusted = [r for r in filtered if self._is_english_site(r['href'])]
                    other = [r for r in filtered if not self._is_english_site(r['href']) and not any(blocked in r['href'].lower() for blocked in BLOCKED_DOMAINS)]
                    all_results.extend(trusted)
                    all_results.extend(other[:2])  # Add a few non-wiki results too
                    if trusted:
                        break

                # Try DuckDuckGo as fallback
                results = self._search_with_duckduckgo(sq)
                if results:
                    # Filter to English content only
                    filtered = [r for r in results if self._is_english_content(r.get('title', '')) and self._is_english_content(r.get('body', ''))]
                    trusted = [r for r in filtered if self._is_english_site(r['href'])]
                    other = [r for r in filtered if not self._is_english_site(r['href']) and not any(blocked in r['href'].lower() for blocked in BLOCKED_DOMAINS)]
                    all_results.extend(trusted)
                    all_results.extend(other[:2])
                    if trusted:
                        break

            # If still no results, try a broader search without site restrictions
            if not all_results:
                broad_query = f"{game_name} {query} english wiki guide"
                results = self._search_with_duckduckgo(broad_query)
                if results:
                    filtered = [r for r in results if self._is_english_content(r.get('title', '')) and self._is_english_content(r.get('body', ''))]
                    all_results.extend(filtered[:5])

            if not all_results:
                return []

            # Deduplicate
            seen_urls = set()
            unique_results = []
            for r in all_results:
                if r['href'] not in seen_urls:
                    seen_urls.add(r['href'])
                    unique_results.append(r)

            # Fetch and format results
            processed_results = []
            for result in unique_results[:3]:
                url = result['href']
                title = result['title']
                snippet = result['body']

                content = snippet
                try:
                    response = requests.get(
                        url,
                        timeout=self._timeout,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept-Language': 'en-US,en;q=0.9',
                        }
                    )
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        extracted = self._extract_wiki_content(soup, url)
                        # Only use extracted content if it's in English
                        if len(extracted) > 200 and self._is_english_content(extracted):
                            content = extracted
                        elif not self._is_english_content(extracted):
                            logger.warning(f"Skipping non-English content from {url}")
                            # Keep snippet if extraction failed/rejected but snippet is okay
                            if not self._is_english_content(snippet):
                                continue
                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")

                if len(content) > 50 and self._is_english_content(content):
                    processed_results.append({
                        "title": title,
                        "href": url,
                        "content": content
                    })

            return processed_results

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

    def _run(self, game_name: str, query: str) -> str:
        """Search web for game information dynamically"""
        results = self.search(game_name, query)
        
        if not results:
             return f"No English results found for '{game_name} {query}'. Please try rephrasing your query or check spelling."

        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"**[Source {i}: {result['title']}]**\n"
                f"URL: {result['href']}\n"
                f"Content:\n{result['content']}\n"
            )

        return "\n\n---\n\n".join(formatted_results)
