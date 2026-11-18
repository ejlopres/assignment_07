"""
1_Scrape.py — Part 1: scrape the rivals' menus into one dataset.

The owner picks the cafés, clicks Scrape, and sees what came back. The scraping
runs in a separate program (code/scrape_menus.py) started by runner.py.
"""

import os

import pandas as pd
import streamlit as st

from rivals import CAFES, MENUS_FILE, OUR_CAFE, run_scraper

st.title("Salt City: Scrape the Rivals")
st.markdown("Pick the cafés to scrape. Each run replaces the saved dataset.")

cafes = st.multiselect("Cafés", list(CAFES), default=list(CAFES), key="cafes")
if st.button("Scrape", key="scrape") and cafes:
    with st.spinner("Visiting each café — this takes a few seconds apiece..."):
        result = run_scraper(cafes)
    if result.returncode == 0:
        output = result.stdout.strip().splitlines()
        st.success(output[-1] if output else "Scraping finished.")
    else:
        st.error("The scraper failed.")
        st.code(result.stderr[-1500:])

if not os.path.exists(MENUS_FILE):
    st.info("No menus yet — pick the cafés and click Scrape.")
    st.stop()

menus = pd.read_csv(MENUS_FILE)
theirs = menus[menus["cafe"] != OUR_CAFE]

col1, col2, col3 = st.columns(3)
col1.metric("Cafés", theirs["cafe"].nunique())
col2.metric("Items", len(theirs[["cafe", "item"]].drop_duplicates()))
col3.metric("Rows", len(theirs))

st.dataframe(menus, hide_index=True)
st.download_button("Download the dataset", menus.to_csv(index=False),
                   file_name="menus.csv", mime="text/csv", key="download")
