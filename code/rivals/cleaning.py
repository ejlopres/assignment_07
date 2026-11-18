"""
cleaning.py — Part 1, Step 1: turn scraped text into clean values.

Plain Python, no browser: prices, menu-card lines, price lines and one card's rows.
"""

import re

# Lines on a menu card that are decoration, not data.
NOISE = {"NEW!", "NEW", "V", "GF"}


def clean_price(text: str) -> float:
    """A price as a number: "$4.75" -> 4.75, " $1,029.00 " -> 1029.0."""
    return float(text.replace("$", "").replace(",", "").strip())


def clean_card_lines(text: str) -> list[str]:
    """The useful lines of a menu card, in order, without blanks, badges or tags."""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if all(word in NOISE for word in line.split()):
            continue
        lines.append(line)
    return lines


def parse_price_line(line: str) -> list[tuple[str, float]]:
    """Every (size, price) pair on a price line; a price with no size is "Each"."""
    pairs = []
    for size, price in re.findall(r"([SML])?\s*(\$[\d.,]+)", line):
        pairs.append((size or "Each", clean_price(price)))
    return pairs


def card_rows(cafe: str, category: str, card_text: str) -> list[dict]:
    """One row per size for one menu card."""
    lines = clean_card_lines(card_text)
    item = lines[0]
    price_line = next(line for line in lines if "$" in line)
    return [
        {"cafe": cafe, "category": category, "item": item, "size": size, "price": price}
        for size, price in parse_price_line(price_line)
    ]
