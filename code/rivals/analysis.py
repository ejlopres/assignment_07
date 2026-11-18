"""
analysis.py — Part 3: where are we high or low, and what are we missing?
"""

import pandas as pd

from .settings import (
    ABOVE_ALL,
    ABOVE_AVERAGE,
    AT_AVERAGE,
    BELOW_ALL,
    BELOW_AVERAGE,
    OUR_CAFE,
    SIZES,
)


def add_canonical(menus: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """`menus` plus a `canonical` column: ours keep their name, rivals use `matched_to`."""
    lookup = (matches[["cafe", "item", "matched_to"]]
              .drop_duplicates(["cafe", "item"])
              .rename(columns={"matched_to": "canonical"}))
    out = menus.merge(lookup, on=["cafe", "item"], how="left")
    out["canonical"] = out["canonical"].where(out["cafe"] != OUR_CAFE, out["item"])
    return out


def price_table(menus: pd.DataFrame) -> pd.DataFrame:
    """Price per (canonical item, size) per café.  *(Provided.)*

    Rows are (`canonical`, `size`), sizes in menu order (S, M, L, Each); columns
    are the cafés; values are prices. Rows with no canonical name (not reviewed
    yet) are left out.
    """
    known = menus.dropna(subset=["canonical"])
    table = known.pivot_table(index=["canonical", "size"], columns="cafe",
                              values="price", aggfunc="first")
    order = {size: rank for rank, size in enumerate(SIZES)}
    return table.sort_index(key=lambda level: level.map(order) if level.name == "size"
                            else level)


def price_position(ours: float, low: float, average: float, high: float) -> str:
    """Where our price stands against the rivals' lowest, average and highest price."""
    if ours < low:
        return BELOW_ALL
    if ours > high:
        return ABOVE_ALL
    if ours < average:
        return BELOW_AVERAGE
    if ours > average:
        return ABOVE_AVERAGE
    return AT_AVERAGE


def compare_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Our price next to every rival's, for every item and size we both sell."""
    rivals = [cafe for cafe in prices.columns if cafe != OUR_CAFE]
    table = prices.reset_index().rename(columns={OUR_CAFE: "our_price"})
    table.columns.name = None
    table = table[table["our_price"].notna() & table[rivals].notna().any(axis=1)].copy()
    low = table[rivals].min(axis=1)
    high = table[rivals].max(axis=1)
    table["rival_avg"] = table[rivals].mean(axis=1).round(2)
    table["our_position"] = [
        price_position(ours, lo, avg, hi)
        for ours, lo, avg, hi in zip(table["our_price"], low, table["rival_avg"], high)
    ]
    columns = ["canonical", "size", "our_price", *rivals, "rival_avg", "our_position"]
    return table[columns].reset_index(drop=True)


def gap_analysis(menus: pd.DataFrame) -> pd.DataFrame:
    """Which items only we sell, which only rivals sell, and which we both do."""
    known = menus.dropna(subset=["canonical"])
    ours = known[known["cafe"] == OUR_CAFE][["canonical", "kind"]].drop_duplicates()
    theirs = (known[known["cafe"] != OUR_CAFE]
              .groupby(["canonical", "kind"])["cafe"]
              .agg(rivals="nunique", sold_by=lambda cafes: ", ".join(sorted(set(cafes))))
              .reset_index())
    gaps = pd.merge(ours, theirs, on=["canonical", "kind"], how="outer", indicator=True)
    labels = {"left_only": "only us", "right_only": "only them", "both": "both"}
    gaps["where"] = gaps["_merge"].astype(str).map(labels)
    gaps["rivals"] = gaps["rivals"].fillna(0).astype(int)
    gaps["sold_by"] = gaps["sold_by"].fillna("")
    rank = {"only them": 0, "only us": 1, "both": 2}
    gaps["_order"] = gaps["where"].map(rank)
    gaps = gaps.sort_values(["_order", "rivals", "canonical"],
                            ascending=[True, False, True])
    return gaps[["canonical", "kind", "where", "rivals", "sold_by"]].reset_index(drop=True)
