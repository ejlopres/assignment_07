"""
matching.py — Part 2: which of their items are ours?

The code proposes (fuzzy scores) and the owner decides; her saved decisions win.
"""

import re
import unicodedata

import pandas as pd
from rapidfuzz import fuzz, process

from .settings import (
    AUTO_MATCH,
    DECISION_COLUMNS,
    FILLER_WORDS,
    NEW_ITEM,
    OUR_CAFE,
    REVIEW,
)


def normalize_name(name: str) -> str:
    """A menu name reduced to the words that tell items apart."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    words = [word for word in text.split() if word not in FILLER_WORDS]
    return " ".join(words)


def top_candidates(name: str, choices: list[str], limit: int = 3) -> list[tuple]:
    """The `limit` choices most like `name`, best first, as (choice, score) pairs."""
    if not choices:
        return []
    normalized = [normalize_name(choice) for choice in choices]
    found = process.extract(normalize_name(name), normalized,
                            scorer=fuzz.token_sort_ratio, limit=limit)
    return [(choices[index], round(score)) for _match, score, index in found]


def match_band(score: float) -> str:
    """How sure a score is: "auto", "review" or "unlikely"."""
    if score >= AUTO_MATCH:
        return "auto"
    if score >= REVIEW:
        return "review"
    return "unlikely"


def match_items(menus: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    """One row per rival item: what it is called on our list, and who decided."""
    ours = menus[menus["cafe"] == OUR_CAFE]
    pool = dict(zip(ours["item"], ours["kind"]))
    answers = {(row["cafe"], row["item"]): row["matched_to"]
               for row in decisions.to_dict("records")}
    theirs = menus[menus["cafe"] != OUR_CAFE]
    rivals = theirs[["cafe", "item", "kind"]].drop_duplicates()

    rows = []
    for cafe, item, kind in rivals.itertuples(index=False):
        choices = [name for name, name_kind in pool.items() if name_kind == kind]
        suggestions = top_candidates(item, choices)
        score = suggestions[0][1] if suggestions else 0
        if (cafe, item) in answers:
            status = "owner"
            answer = answers[(cafe, item)]
            matched_to = item if answer == NEW_ITEM else answer
        elif score >= AUTO_MATCH:
            status = "auto"
            matched_to = suggestions[0][0]
        else:
            status = "unreviewed"
            matched_to = None
        if matched_to is not None and matched_to not in pool:
            pool[matched_to] = kind
        rows.append({"cafe": cafe, "item": item, "kind": kind, "status": status,
                     "matched_to": matched_to, "score": score,
                     "suggestions": suggestions})
    return pd.DataFrame(rows, columns=["cafe", "item", "kind", "status", "matched_to",
                                       "score", "suggestions"])


def record_decision(decisions: pd.DataFrame, cafe: str, item: str,
                    matched_to: str) -> pd.DataFrame:
    """`decisions` with the owner's answer for (cafe, item), replacing an old one."""
    kept = decisions[~((decisions["cafe"] == cafe) & (decisions["item"] == item))]
    new = pd.DataFrame([{"cafe": cafe, "item": item, "matched_to": matched_to}],
                       columns=DECISION_COLUMNS)
    if kept.empty:
        return new
    return pd.concat([kept[DECISION_COLUMNS], new], ignore_index=True)
