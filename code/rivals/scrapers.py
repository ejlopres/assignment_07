"""
scrapers.py — Part 1, Step 2: one scraper per rival café.

Each scraper is handed a Playwright `page` and returns a list of dicts, one per
menu item and size: {"cafe", "category", "item", "size", "price"}.
"""

from io import StringIO
from urllib.parse import urljoin

import pandas as pd

from .cleaning import card_rows, clean_price
from .settings import CANAL_SHOP, cafe_url


def scrape_lakeshore(page) -> list[dict]:
    """Lakeshore Lattes: section headings, each followed by a grid of menu cards."""
    page.goto(cafe_url("Lakeshore Lattes"))
    rows = []
    for heading in page.query_selector_all("h2.menu-section__title"):
        category = heading.inner_text()
        grid = heading.query_selector("~ div.menu-grid")
        for card in grid.query_selector_all("article.menu-card"):
            rows.extend(card_rows("Lakeshore Lattes", category, card.inner_text()))
    return rows


def scrape_hilltop(page) -> list[dict]:
    """Hilltop Grind: an <h2> and a <table> per category inside #menu."""
    page.goto(cafe_url("Hilltop Grind"))
    categories = [heading.inner_text() for heading in page.query_selector_all("#menu h2")]
    tables = pd.read_html(StringIO(page.content()))
    rows = []
    for category, table in zip(categories, tables):
        long = table.drop(columns="Description").melt(
            id_vars="Item", var_name="size", value_name="price")
        for item, size, price in long.itertuples(index=False):
            rows.append({"cafe": "Hilltop Grind", "category": category, "item": item,
                         "size": size, "price": clean_price(str(price))})
    return rows


def scrape_canal(page, shop: str = CANAL_SHOP) -> list[dict]:
    """Canal Street Coffee: choose a shop, load the whole menu, visit each item page."""
    base_url = cafe_url("Canal Street Coffee")
    page.goto(base_url)
    page.get_by_label("Choose your shop").select_option(shop)
    page.get_by_role("button", name="Show full menu").click()
    page.wait_for_selector("a.result-card")

    show_more = page.get_by_role("button", name="Show more")
    while show_more.is_visible():
        count = page.locator("a.result-card").count()
        show_more.click()
        page.wait_for_function(
            f"document.querySelectorAll('a.result-card').length > {count}")

    links = [card.get_attribute("href") for card in page.query_selector_all("a.result-card")]
    rows = []
    for href in links:
        page.goto(urljoin(base_url, href))
        page.wait_for_selector("#sizes")
        item = page.inner_text("#item-name").strip()
        category = page.inner_text("#item-category").split(" · ")[0].strip()
        for tr in page.query_selector_all("#sizes tbody tr"):
            size, price = [td.inner_text().strip() for td in tr.query_selector_all("td")]
            rows.append({"cafe": "Canal Street Coffee", "category": category, "item": item,
                         "size": size, "price": clean_price(price)})
    return rows
