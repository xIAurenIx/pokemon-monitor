import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_sold_listings(search_query: str, max_pages: int = 3) -> list[dict]:
    """
    Scrapes eBay UK sold listings for a given search query.
    Returns a list of raw transaction dicts.
    """
    results = []

    for page in range(1, max_pages + 1):
        url = (
            f"https://www.ebay.co.uk/sch/i.html"
            f"?_nkw={requests.utils.quote(search_query)}"
            f"&LH_Sold=1&LH_Complete=1&_pgn={page}"
        )

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[eBay] Request failed for page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(".s-item")

        if not items:
            break

        for item in items:
            parsed = _parse_item(item)
            if parsed:
                results.append(parsed)

        time.sleep(1.5)  # polite delay between pages

    print(f"[eBay] Found {len(results)} listings for: {search_query}")
    return results


def _parse_item(item) -> dict | None:
    """Extract fields from a single eBay search result item."""
    try:
        # Title
        title_el = item.select_one(".s-item__title")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        if title == "Shop on eBay":  # skip the first ghost item eBay always injects
            return None

        # Price — strip £ and commas, convert to float
        price_el = item.select_one(".s-item__price")
        if not price_el:
            return None
        price_text = price_el.get_text(strip=True)
        price = _parse_price(price_text)
        if price is None:
            return None

        # Item ID and URL
        link_el = item.select_one(".s-item__link")
        if not link_el:
            return None
        url = link_el["href"].split("?")[0]
        item_id = _extract_item_id(url)
        if not item_id:
            return None

        # Date sold
        date_el = item.select_one(".s-item__endedDate") or item.select_one(".POSITIVE")
        date_sold = _parse_date(date_el.get_text(strip=True)) if date_el else datetime.utcnow()

        return {
            "transaction_id": f"ebay_{item_id}",
            "sale_price_gbp": price,
            "date_sold": date_sold,
            "listing_title": title,
            "url": url,
            "marketplace": "ebay",
        }

    except Exception as e:
        print(f"[eBay] Failed to parse item: {e}")
        return None


def _parse_price(text: str) -> float | None:
    """Extract a float from a price string like £44.99 or £40.00 to £50.00."""
    # If it's a range, take the lower bound
    match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    if match:
        return float(match.group())
    return None


def _extract_item_id(url: str) -> str | None:
    match = re.search(r"/itm/(\d+)", url)
    return match.group(1) if match else None


def _parse_date(text: str) -> datetime:
    """Parse eBay date strings — falls back to now if unrecognised."""
    formats = ["%d %b %Y", "%b %d, %Y", "%d-%b-%y"]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return datetime.utcnow()
