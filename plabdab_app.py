#!/usr/bin/env python3
"""
PLAbDab Local App — Search paired antibody sequences by target/antigen.
"""
import streamlit as st
import pandas as pd
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data-dev"
PAIRED_CSV = DATA_DIR / "paired_sequences_2024-08-28.csv.gz"
MODELS_DIR = DATA_DIR / "models"


@st.cache_data
def load_data():
    df = pd.read_csv(PAIRED_CSV, compression="gzip")
    df["has_model"] = df["model"].apply(
        lambda m: "Yes" if isinstance(m, str) and m != "FAILED" else "No"
    )
    df["targets_mentioned"] = df["targets_mentioned"].fillna("")
    df["reference_title"] = df["reference_title"].fillna("")
    df["heavy_definition"] = df["heavy_definition"].fillna("")
    df["light_definition"] = df["light_definition"].fillna("")
    return df


SEARCH_COLS = ["targets_mentioned", "reference_title", "heavy_definition", "light_definition"]


def _term_mask(df, term):
    """Match a single term with word boundaries across search columns."""
    pattern = r"\b" + re.escape(term) + r"\b"
    mask = pd.Series(False, index=df.index)
    for col in SEARCH_COLS:
        mask |= df[col].str.contains(pattern, case=False, na=False)
    return mask


def _tokenize(query):
    """Split query into tokens, preserving quoted phrases."""
    tokens = []
    for m in re.finditer(r'"([^"]+)"|(\S+)', query):
        tokens.append(m.group(1) if m.group(1) is not None else m.group(2))
    return tokens


def search(df, query):
    q = query.strip()
    if not q:
        return df.head(0)

    tokens = _tokenize(q)
    if not tokens:
        return df.head(0)

    # Parse boolean expression: terms joined by AND (default), OR, NOT
    # e.g. "CD5 AND EGFR", "CD5 OR CD20", "CD5 NOT CD55"
    mask = None
    op = "AND"
    for tok in tokens:
        upper = tok.upper()
        if upper in ("AND", "OR", "NOT"):
            op = upper
            continue
        term_mask = _term_mask(df, tok)
        if mask is None:
            mask = ~term_mask if op == "NOT" else term_mask
        elif op == "AND":
            mask &= term_mask
        elif op == "OR":
            mask |= term_mask
        elif op == "NOT":
            mask &= ~term_mask
        op = "AND"  # reset to default

    if mask is None:
        return df.head(0)
    results = df[mask].copy()
    # Rank by relevance: fewer total targets = more specific match
    results["_target_count"] = results["targets_mentioned"].str.count(";") + 1
    results = results.sort_values("_target_count").drop(columns="_target_count")
    return results


# --- UI ---

st.set_page_config(page_title="PLAbDab Search", layout="wide")
st.title("PLAbDab — Target Search")

df = load_data()
st.caption(f"Database: **{len(df):,}** paired antibody sequences")

query = st.text_input(
    "Search by target / antigen",
    placeholder='e.g. CD5, EGFR OR HER2, "HIV-1" NOT gp41 …',
)

DETAIL_CSS = """
<style>
.detail-table { width: 100%; border-collapse: collapse; font-family: monospace; font-size: 14px; }
.detail-table td { padding: 8px 12px; vertical-align: top; border-bottom: 1px solid #eee; }
.detail-table td:first-child { white-space: nowrap; font-weight: bold; width: 220px; color: #555; }
.detail-table td:last-child { word-break: break-all; }
</style>
"""


def render_detail(row):
    plabdab_url = "https://opig.stats.ox.ac.uk/webapps/plabdab/"
    heavy_ncbi_url = f"https://www.ncbi.nlm.nih.gov/protein/{row['heavy_ID']}"
    light_ncbi_url = f"https://www.ncbi.nlm.nih.gov/protein/{row['light_ID']}"
    fields = [
        ("Reference title", row["reference_title"]),
        ("Reference authors", row["reference_authors"]),
        ("PLAbDab", f'<a href="{plabdab_url}" target="_blank">{plabdab_url}</a>'),
        ("Heavy chain accession", f'<a href="{heavy_ncbi_url}" target="_blank">{row["heavy_ID"]}</a>'),
        ("Light chain accession", f'<a href="{light_ncbi_url}" target="_blank">{row["light_ID"]}</a>'),
        ("Heavy chain", row["heavy_sequence"]),
        ("Light chain", row["light_sequence"]),
        ("Heavy chain definition", row["heavy_definition"]),
        ("Light chain definition", row["light_definition"]),
        ("Organism", row["organism"]),
        ("Targets mentioned", row["targets_mentioned"]),
        ("Update date", row["update_date"]),
    ]
    rows_html = "".join(
        f"<tr><td>{label}</td><td>{val}</td></tr>" for label, val in fields
    )
    return f"{DETAIL_CSS}<table class='detail-table'>{rows_html}</table>"


if query.strip():
    results = search(df, query)
    st.subheader(f"{len(results):,} results for \"{query}\"")

    if results.empty:
        st.info("No matches found. Try a different keyword.")
    else:
        show_n = min(len(results), 50)
        if len(results) > show_n:
            st.caption(f"Showing first {show_n} of {len(results):,} results")

        for _, row in results.head(show_n).iterrows():
            target = row["targets_mentioned"] or "(no target)"
            label = f"**{row['ID']}** · {row['organism']} · {target}"
            with st.expander(label):
                st.markdown(render_detail(row), unsafe_allow_html=True)
else:
    # Show overview stats when no search query
    st.markdown("---")
    st.subheader("Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        has_target = (df["targets_mentioned"] != "").sum()
        st.metric("With known target", f"{has_target:,}")
    with col2:
        st.metric("Unique organisms", df["organism"].nunique())
    with col3:
        has_model = (df["has_model"] == "Yes").sum()
        st.metric("With 3D model", f"{has_model:,}")

    # Top targets
    targets = df[df["targets_mentioned"] != ""]["targets_mentioned"].value_counts().head(20)
    st.markdown("**Top 20 targets**")
    st.dataframe(targets.reset_index().rename(columns={"index": "Target", "count": "Count"}), use_container_width=True)
