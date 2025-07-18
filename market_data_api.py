"""
Market Data API Integration for Loan Officer Banner
Fetches real-time mortgage rates, treasury yields, and related news
"""

import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class MarketDataAPI:
    """
    Handles fetching market data from free APIs for the loan officer banner
    """

    def __init__(self):
        self.fred_api_key = os.getenv("FRED_API_KEY")
        self.session = self._create_session()
        self.cache_duration = 900  # 15 minutes in seconds
        self.data_cache = {}

    def _create_session(self):
        """Create a requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.data_cache:
            return False

        cached_time = self.data_cache[cache_key].get("timestamp", 0)
        return time.time() - cached_time < self.cache_duration

    def _cache_data(self, cache_key: str, data: Dict) -> None:
        """Cache data with timestamp"""
        self.data_cache[cache_key] = {"data": data, "timestamp": time.time()}

    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get cached data if valid"""
        if self._is_cache_valid(cache_key):
            return self.data_cache[cache_key]["data"]
        return None

    def get_fred_data(self, series_id: str) -> Optional[Dict]:
        """
        Fetch data from FRED API

        Args:
            series_id: FRED series ID (e.g., 'DGS10', 'MORTGAGE30US')

        Returns:
            Dict with latest observation data
        """
        cache_key = f"fred_{series_id}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        if not self.fred_api_key:
            logger.warning("FRED API key not configured")
            return None

        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.fred_api_key,
                "file_type": "json",
                "limit": 10,  # Get last 10 observations
                "sort_order": "desc",
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            observations = data.get("observations", [])

            if not observations:
                logger.warning(f"No observations found for series {series_id}")
                return None

            # Get the most recent non-null observation
            latest_obs = None
            previous_obs = None

            for obs in observations:
                if obs["value"] != "." and obs["value"] is not None:
                    if latest_obs is None:
                        latest_obs = obs
                    elif previous_obs is None:
                        previous_obs = obs
                        break

            if not latest_obs:
                logger.warning(f"No valid observations found for series {series_id}")
                return None

            result = {
                "current_value": float(latest_obs["value"]),
                "current_date": latest_obs["date"],
                "previous_value": float(previous_obs["value"]) if previous_obs else None,
                "previous_date": previous_obs["date"] if previous_obs else None,
                "series_id": series_id,
                "updated_at": datetime.now().isoformat(),
            }

            self._cache_data(cache_key, result)
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching FRED data for {series_id}: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing FRED data for {series_id}: {e}")
            return None

    def get_treasury_yields(self) -> Optional[Dict]:
        """
        Fetch treasury yields from Treasury.gov API

        Returns:
            Dict with current treasury yields
        """
        cache_key = "treasury_yields"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        try:
            url = "https://api.fiscaldata.treasury.gov/services/api/v1/accounting/od/avg_interest_rates"
            params = {"filter": "record_type_cd:eq:AVG", "sort": "-record_date", "page[size]": "50"}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            records = data.get("data", [])

            if not records:
                logger.warning("No treasury yield data found")
                return None

            # Find 10-year treasury yield
            ten_year_yield = None
            for record in records:
                if (
                    "10" in record.get("security_desc", "").lower()
                    and "year" in record.get("security_desc", "").lower()
                ):
                    ten_year_yield = {
                        "value": float(record["avg_interest_rate_amt"]),
                        "date": record["record_date"],
                        "description": record["security_desc"],
                    }
                    break

            if not ten_year_yield:
                logger.warning("10-year treasury yield not found")
                return None

            result = {"ten_year_yield": ten_year_yield, "updated_at": datetime.now().isoformat()}

            self._cache_data(cache_key, result)
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching treasury yields: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing treasury yields: {e}")
            return None

    def get_mortgage_news(self) -> Optional[List[Dict]]:
        """
        Fetch mortgage-related news from RSS feeds

        Returns:
            List of news items with title, link, and date
        """
        cache_key = "mortgage_news"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        try:
            import feedparser

            # RSS feeds for mortgage news
            rss_feeds = [
                "https://www.mortgagenewsdaily.com/rss",
                "https://www.housingwire.com/feed/",
            ]

            news_items = []

            for feed_url in rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)

                    for entry in feed.entries[:3]:  # Get top 3 from each feed
                        news_items.append(
                            {
                                "title": entry.title,
                                "link": entry.link,
                                "published": entry.get("published", ""),
                                "summary": entry.get("summary", "")[:200] + "..."
                                if entry.get("summary")
                                else "",
                                "source": feed.feed.get("title", "Unknown"),
                            }
                        )

                except Exception as e:
                    logger.warning(f"Error parsing RSS feed {feed_url}: {e}")
                    continue

            # Sort by relevance (mortgage-related keywords)
            mortgage_keywords = ["mortgage", "rate", "fed", "housing", "loan", "refinance", "mbs"]

            def calculate_relevance(item):
                title_lower = item["title"].lower()
                return sum(1 for keyword in mortgage_keywords if keyword in title_lower)

            news_items.sort(key=calculate_relevance, reverse=True)

            # Return top 2 most relevant items
            result = news_items[:2]
            self._cache_data(cache_key, result)
            return result

        except ImportError:
            logger.warning("feedparser not installed - using fallback news")
            # Return fallback news items
            fallback_news = [
                {
                    "title": "View Current Mortgage Rates & Market Analysis",
                    "link": "https://www.mortgagenewsdaily.com/mortgage-rates",
                    "published": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "source": "Mortgage News Daily",
                },
                {
                    "title": "Browse Housing Wire - Industry News & Updates", 
                    "link": "https://www.housingwire.com/",
                    "published": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "source": "Housing Wire",
                },
            ]
            self._cache_data(cache_key, fallback_news)
            return fallback_news
        except Exception as e:
            logger.error(f"Error fetching mortgage news: {e}")
            return None

    def get_bankrate_mortgage_rate(self) -> Optional[Dict]:
        """
        Get mortgage rates from Bankrate - a reliable financial data source
        """
        try:
            # Try Bankrate's mortgage rates page
            url = "https://www.bankrate.com/mortgages/mortgage-rates/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            import re

            content = response.text

            # Look for mortgage rates in Bankrate's format
            patterns = [
                r"30-year fixed[^0-9]*?(\d+\.\d{2,3})%",
                r"30.*year.*fixed.*?(\d+\.\d{2,3})%",
                r"(\d+\.\d{2,3})%.*30.*year.*fixed",
                r"rate.*?(\d+\.\d{2,3})%.*30.*year",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        rate = float(match)
                        if 3.0 <= rate <= 15.0:  # Reasonable range
                            logger.info(f"Found mortgage rate from Bankrate: {rate}%")
                            return {
                                "current_value": rate,
                                "current_date": datetime.now().strftime("%Y-%m-%d"),
                                "previous_value": None,
                                "previous_date": None,
                                "series_id": "BANKRATE_30Y",
                                "updated_at": datetime.now().isoformat(),
                                "source": "Bankrate",
                            }
                    except ValueError:
                        continue

            logger.warning("Could not extract rate from Bankrate")
            return None

        except Exception as e:
            logger.error(f"Error fetching Bankrate rate: {e}")
            return None

    def get_current_mortgage_rate_fallback(self) -> Optional[Dict]:
        """
        Fallback method to get current mortgage rate from public sources
        when FRED API key is not available
        """
        try:
            # Try to get rate from Mortgage News Daily (they often have current rates on their main page)
            response = self.session.get(
                "https://www.mortgagenewsdaily.com/mortgage-rates", timeout=10
            )
            response.raise_for_status()

            # Look for rate patterns in the page content
            import re

            content = response.text

            # Look for common rate patterns like "6.72%" or "6.72 percent"
            rate_patterns = [
                r"30[- ]?year[^0-9]*?(\d+\.\d{2})%",
                r"30[- ]?year[^0-9]*?(\d+\.\d{2})\s*percent",
                r"(\d+\.\d{2})%[^0-9]*?30[- ]?year",
                r'class="rate"[^>]*>(\d+\.\d{2})',
                r'"current_rate"\s*:\s*"?(\d+\.\d{2})"?',
            ]

            for pattern in rate_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    try:
                        rate = float(matches[0])
                        if 3.0 <= rate <= 15.0:  # Sanity check for reasonable mortgage rates
                            logger.info(f"Found current mortgage rate via fallback: {rate}%")
                            return {
                                "current_value": rate,
                                "current_date": datetime.now().strftime("%Y-%m-%d"),
                                "previous_value": None,
                                "previous_date": None,
                                "series_id": "FALLBACK_MORTGAGE30US",
                                "updated_at": datetime.now().isoformat(),
                                "source": "Web Fallback",
                            }
                    except ValueError:
                        continue

            logger.warning("Could not extract mortgage rate from fallback source")
            return None

        except Exception as e:
            logger.error(f"Error in mortgage rate fallback: {e}")
            return None

    def get_market_summary(self) -> Dict:
        """
        Get comprehensive market summary for loan officer banner

        Returns:
            Dict with all market data formatted for display
        """
        summary = {
            "mortgage_rate_30y": None,
            "treasury_10y": None,
            "mbs_data": None,
            "news_headlines": [],
            "rate_trend": "stable",
            "last_updated": datetime.now().isoformat(),
            "data_sources": [],
        }

        # Try to get real data first, fall back to demo only if everything fails

        # Get 30-year mortgage rate - try multiple sources in order of reliability
        mortgage_data = None

        # First try: FRED API (most reliable if available)
        if self.fred_api_key:
            mortgage_data = self.get_fred_data("MORTGAGE30US")

        # Second try: Bankrate (reliable financial data source)
        if not mortgage_data:
            mortgage_data = self.get_bankrate_mortgage_rate()

        # Third try: Web scraping fallback
        if not mortgage_data:
            mortgage_data = self.get_current_mortgage_rate_fallback()

        if mortgage_data:
            current_rate = mortgage_data["current_value"]
            previous_rate = mortgage_data.get("previous_value")

            change = 0
            if previous_rate:
                change = current_rate - previous_rate

            summary["mortgage_rate_30y"] = {
                "current": current_rate,
                "previous": previous_rate,
                "change": change,
                "change_direction": "up" if change > 0 else "down" if change < 0 else "stable",
                "date": mortgage_data["current_date"],
            }
            source = mortgage_data.get("source", "Unknown")
            if source == "Web Fallback":
                summary["data_sources"].append("Web Scraping")
            elif source == "Bankrate":
                summary["data_sources"].append("Bankrate")
            elif source == "Freddie Mac PMMS":
                summary["data_sources"].append("Freddie Mac")
            else:
                summary["data_sources"].append("FRED")

        # Get 10-year treasury yield
        treasury_data = self.get_fred_data("DGS10")
        if treasury_data:
            current_yield = treasury_data["current_value"]
            previous_yield = treasury_data.get("previous_value")

            change = 0
            if previous_yield:
                change = current_yield - previous_yield

            summary["treasury_10y"] = {
                "current": current_yield,
                "previous": previous_yield,
                "change": change,
                "change_direction": "up" if change > 0 else "down" if change < 0 else "stable",
                "date": treasury_data["current_date"],
            }

        # Get MBS data (using a proxy - mortgage spreads)
        mbs_data = self.get_fred_data("MORTGAGE30US")  # We'll calculate spread vs treasury
        if mbs_data and summary["treasury_10y"]:
            mortgage_rate = mbs_data["current_value"]
            treasury_rate = summary["treasury_10y"]["current"]
            spread = mortgage_rate - treasury_rate

            summary["mbs_data"] = {
                "spread": spread,
                "description": f"Mortgage-Treasury Spread: {spread: .2f}%",
                "date": mbs_data["current_date"],
            }

        # Get news headlines
        news = self.get_mortgage_news()
        if news:
            summary["news_headlines"] = news
            summary["data_sources"].append("RSS Feeds")

        # Calculate overall trend
        trends = []
        if summary["mortgage_rate_30y"]:
            trends.append(summary["mortgage_rate_30y"]["change_direction"])
        if summary["treasury_10y"]:
            trends.append(summary["treasury_10y"]["change_direction"])

        if trends:
            up_count = trends.count("up")
            down_count = trends.count("down")

            if up_count > down_count:
                summary["rate_trend"] = "rising"
            elif down_count > up_count:
                summary["rate_trend"] = "falling"
            else:
                summary["rate_trend"] = "stable"
        else:
            # If no real trend data, use stable as fallback
            summary["rate_trend"] = "stable"

        # If we couldn't get any real data, use demo data as last resort
        if not summary["data_sources"]:
            logger.info("No real data sources available - using demo data")
            summary = {
                "mortgage_rate_30y": {
                    "current": 7.15,
                    "previous": 7.08,
                    "change": 0.07,
                    "change_direction": "up",
                    "date": "2025-07-16",
                },
                "treasury_10y": {
                    "current": 4.23,
                    "previous": 4.18,
                    "change": 0.05,
                    "change_direction": "up",
                    "date": "2025-07-16",
                },
                "mbs_data": {
                    "spread": 2.92,
                    "description": "Mortgage-Treasury Spread: 2.92%",
                    "date": "2025-07-16",
                },
                "news_headlines": [
                    {
                        "title": "View Current Mortgage Rates & Market Analysis",
                        "link": "https://www.mortgagenewsdaily.com/mortgage-rates",
                        "published": "2025-07-16T10:30:00Z",
                        "source": "Mortgage News Daily",
                    },
                    {
                        "title": "Browse Housing Wire - Industry News & Updates",
                        "link": "https://www.housingwire.com/",
                        "published": "2025-07-16T09:15:00Z",
                        "source": "Housing Wire",
                    },
                ],
                "rate_trend": "rising",
                "last_updated": datetime.now().isoformat(),
                "data_sources": ["Demo Data"],
            }

        return summary


# Global instance
market_data_api = MarketDataAPI()
