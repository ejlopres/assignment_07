"""
menus.py — Part 1, Step 3: three scrapes and our own menu, as one dataset.

    cafe  category  kind  item  size  price
"""

import pandas as pd

from .settings import (
    CATEGORIES_FILE,
    MENU_COLUMNS,
    OUR_CAFE,
    OUR_MENU_FILE,
)

ROW_COLUMNS = ["cafe", "category", "item", "size", "price"]


def load_our_menu() -> pd.DataFrame:
    """Salt City Coffee's menu with the scrapers' five columns.  *(Provided.)*"""
    ours = pd.read_csv(OUR_MENU_FILE)
    return pd.DataFrame({
        "cafe": OUR_CAFE,
        "category": ours["category"],
        "item": ours["item"],
        "size": ours["size"],
        "price": ours["price"],
    })


def menus_table(rows: list[dict]) -> pd.DataFrame:
    """Scraped rows as a DataFrame with exactly the five scraper columns, in order."""
    return pd.DataFrame(rows, columns=ROW_COLUMNS)


def add_kinds(menus: pd.DataFrame, categories: pd.DataFrame) -> pd.DataFrame:
    """`menus` plus a `kind` column looked up by (`cafe`, `category`)."""
    keys = ["cafe", "category"]
    lookup = categories[[*keys, "kind"]].drop_duplicates(keys)
    return menus.merge(lookup, on=["cafe", "category"], how="left")


def build_dataset(rival_rows: list[dict]) -> pd.DataFrame:
    """The whole dataset: our menu first, then the rivals' rows, with kinds added."""
    combined = pd.concat([load_our_menu(), menus_table(rival_rows)], ignore_index=True)
    with_kinds = add_kinds(combined, pd.read_csv(CATEGORIES_FILE))
    return with_kinds[MENU_COLUMNS].reset_index(drop=True)
