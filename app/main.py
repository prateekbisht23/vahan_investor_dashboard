# app/main.py
import os
import math
import pandas as pd
import streamlit as st
import altair as alt

# ---------- CONFIG ----------
st.set_page_config(page_title="Vehicle Registration Dashboard", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ---------- HELPERS ----------
MONTH_MAP = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
}

def _safe_int(x):
    try:
        return int(x)
    except Exception:
        return x

@st.cache_data
def load_data(data_dir: str):
    # Vehicle type-wise
    v = pd.read_csv(os.path.join(data_dir, 'vehicle_type_wise_data_2020_2025.csv'))
    v['Month'] = v['Month'].map(MONTH_MAP).astype(int)
    v['Year'] = v['Year'].astype(int)
    v['Registrations'] = v['Registrations'].astype(int)
    v['YearMonth'] = pd.to_datetime(
        pd.DataFrame({'year': v['Year'], 'month': v['Month'], 'day': 1})
    )

    # Manufacturer-wise
    m = pd.read_csv(os.path.join(data_dir, 'manufacturer_wise_data_2020_2025.csv'))
    m['Month'] = m['Month'].map(MONTH_MAP).astype(int)
    m['Year'] = m['Year'].astype(int)
    m['Registrations'] = m['Registrations'].astype(int)
    m['YearMonth'] = pd.to_datetime(
        pd.DataFrame({'year': m['Year'], 'month': m['Month'], 'day': 1})
    )
    return v, m

def pct_change(series: pd.Series, periods: int):
    """Robust % change that returns NaN where base is 0 or missing."""
    result = series.pct_change(periods=periods)
    # Replace inf/-inf produced by division by zero with NaN
    result = result.replace([math.inf, -math.inf], pd.NA)
    return result * 100

def compute_growth_monthly(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: rows are monthly totals with columns [YearMonth, Registrations].
    Output: adds YoY% and QoQ% per month.
    """
    df = monthly_df.sort_values('YearMonth').copy()
    df['YoY%'] = pct_change(df['Registrations'], 12)
    df['QoQ%'] = pct_change(df['Registrations'], 3)
    return df

def compute_group_growth(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """
    Compute YoY/QoQ per group (Category or Manufacturer).
    Expects df with [Year, Month, YearMonth, Registrations, group_col].
    """
    out = []
    for grp, g in df.groupby(group_col):
        g = g.sort_values('YearMonth').copy()
        g['YoY%'] = pct_change(g['Registrations'], 12)
        g['QoQ%'] = pct_change(g['Registrations'], 3)
        out.append(g)
    if not out:
        return df.assign(**{'YoY%': pd.NA, 'QoQ%': pd.NA})
    return pd.concat(out, ignore_index=True)

def aggregate_monthly_total(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to single monthly total across whatever rows are present."""
    return (df.groupby('YearMonth', as_index=False)['Registrations']
            .sum()
            .sort_values('YearMonth'))

def kpi_for_selection(df: pd.DataFrame):
    """
    KPIs over the filtered selection:
      - Total Registrations (sum over the whole selected period)
      - Latest YoY% & QoQ% computed on the aggregated monthly total
    """
    if df.empty:
        return 0, None, None
    monthly = aggregate_monthly_total(df)
    growth = compute_growth_monthly(monthly)
    latest = growth.iloc[-1] if len(growth) else None
    total_regs = int(df['Registrations'].sum())
    yoy = (None if latest is None else (None if pd.isna(latest['YoY%']) else float(latest['YoY%'])))
    qoq = (None if latest is None else (None if pd.isna(latest['QoQ%']) else float(latest['QoQ%'])))
    return total_regs, yoy, qoq

def fmt_pct(x):
    return "—" if (x is None or pd.isna(x)) else f"{x:.2f}%"

def plot_trend(df: pd.DataFrame, color_col: str, title: str):
    if df.empty:
        return alt.Chart(pd.DataFrame({'Notice': ['No data']})).mark_text().encode(text='Notice')
    return (alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X('YearMonth:T', title='Month'),
            y=alt.Y('Registrations:Q', title='Registrations'),
            color=alt.Color(f'{color_col}:N', title=color_col),
            tooltip=[color_col, alt.Tooltip('Year:Q'), alt.Tooltip('Month:Q'),
                     alt.Tooltip('Registrations:Q', format=','),
                     alt.Tooltip('YoY%:Q', format='.2f'),
                     alt.Tooltip('QoQ%:Q', format='.2f')]
        )
        .properties(title=title)
        .interactive())

def plot_pie(df: pd.DataFrame, category_col: str, value_col: str, title: str):
    if df.empty:
        return alt.Chart(pd.DataFrame({'Notice': ['No data']})).mark_text().encode(text='Notice')
    return (alt.Chart(df)
        .mark_arc()
        .encode(
            theta=alt.Theta(f'{value_col}:Q', stack=True),
            color=alt.Color(f'{category_col}:N', title=category_col),
            tooltip=[category_col, alt.Tooltip(value_col, format=',')]
        )
        .properties(title=title))

# ---------- LOAD ----------
vehicle_df, manufacturer_df = load_data(DATA_DIR)

# ---------- SIDEBAR NAV + FILTERS ----------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["📊 Overview", "🚙 Vehicle Type Analysis", "🏭 Manufacturer Analysis"])

st.sidebar.header("Filters")
min_year = min(int(vehicle_df['Year'].min()), int(manufacturer_df['Year'].min()))
max_year = max(int(vehicle_df['Year'].max()), int(manufacturer_df['Year'].max()))
year_range = st.sidebar.slider("Year Range", min_year, max_year, (min_year, max_year))

category_options = sorted(vehicle_df['Category'].dropna().unique().tolist())
manufacturer_options = sorted(manufacturer_df['Manufacturer'].dropna().unique().tolist())

selected_categories = st.sidebar.multiselect(
    "Vehicle Categories", options=category_options, default=category_options
)
selected_manufacturers = st.sidebar.multiselect(
    "Manufacturers (optional filter)", options=manufacturer_options, default=[]
)

# Apply filters
vehicle_filtered = vehicle_df[
    (vehicle_df['Year'] >= year_range[0]) &
    (vehicle_df['Year'] <= year_range[1]) &
    (vehicle_df['Category'].isin(selected_categories))
].copy()

manufacturer_filtered = manufacturer_df[
    (manufacturer_df['Year'] >= year_range[0]) &
    (manufacturer_df['Year'] <= year_range[1])
].copy()
if selected_manufacturers:
    manufacturer_filtered = manufacturer_filtered[
        manufacturer_filtered['Manufacturer'].isin(selected_manufacturers)
    ].copy()

# ---------- PAGES ----------
if page == "📊 Overview":
    st.title("🚗 Vehicle Registrations — Overview")

    # KPIs computed from the aggregated monthly total across categories
    total_regs, yoy, qoq = kpi_for_selection(vehicle_filtered)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Registrations (Selected Period)", f"{total_regs:,}")
    c2.metric("Latest YoY (Aggregated)", fmt_pct(yoy))
    c3.metric("Latest QoQ (Aggregated)", fmt_pct(qoq))
    c4.metric("Period", f"{year_range[0]}–{year_range[1]}")

    # Category market share (entire selected period)
    st.subheader("Market Share — Vehicle Categories")
    cat_share = (vehicle_filtered.groupby('Category', as_index=False)['Registrations']
                 .sum()
                 .sort_values('Registrations', ascending=False))
    st.altair_chart(plot_pie(cat_share, 'Category', 'Registrations', "Vehicle Category Market Share"),
                    use_container_width=True)

    # Manufacturer market share (Top 10 within the selected filter)
    st.subheader("Market Share — Manufacturers (Top 10)")
    manu_share = (manufacturer_filtered.groupby('Manufacturer', as_index=False)['Registrations']
                  .sum()
                  .sort_values('Registrations', ascending=False)
                  .head(10))
    st.altair_chart(plot_pie(manu_share, 'Manufacturer', 'Registrations', "Top 10 Manufacturers"),
                    use_container_width=True)

    # Overall trend (aggregated monthly registrations across categories)
    st.subheader("Overall Trend (Aggregated Monthly Total)")
    overall_monthly = aggregate_monthly_total(vehicle_filtered)
    overall_growth = compute_growth_monthly(overall_monthly)
    st.altair_chart(
        alt.Chart(overall_growth).mark_line(point=True).encode(
            x='YearMonth:T',
            y=alt.Y('Registrations:Q', title='Registrations'),
            tooltip=[alt.Tooltip('YearMonth:T'), alt.Tooltip('Registrations:Q', format=','),
                     alt.Tooltip('YoY%:Q', format='.2f'), alt.Tooltip('QoQ%:Q', format='.2f')]
        ).properties(title="Total Registrations per Month (All Selected Categories)").interactive(),
        use_container_width=True
    )

elif page == "🚙 Vehicle Type Analysis":
    st.title("🚙 Vehicle Type Analysis")

    # KPIs for selected categories (aggregate across selected categories)
    vt_total, vt_yoy, vt_qoq = kpi_for_selection(vehicle_filtered)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Registrations (Selected Categories)", f"{vt_total:,}")
    c2.metric("Latest YoY (Aggregated)", fmt_pct(vt_yoy))
    c3.metric("Latest QoQ (Aggregated)", fmt_pct(vt_qoq))
    c4.metric("Categories", f"{len(selected_categories)} selected")

    # Per-category growth trends
    vt_growth = compute_group_growth(vehicle_filtered, 'Category')
    st.subheader("Trend by Vehicle Category")
    st.altair_chart(
        plot_trend(vt_growth, 'Category', "Registrations by Category (with YoY/QoQ tooltips)"),
        use_container_width=True
    )

    # Category share pie
    st.subheader("Market Share — Selected Categories")
    vt_share = (vehicle_filtered.groupby('Category', as_index=False)['Registrations']
                .sum()
                .sort_values('Registrations', ascending=False))
    st.altair_chart(plot_pie(vt_share, 'Category', 'Registrations', "Market Share (Selected Categories)"),
                    use_container_width=True)

    # Summary table
    st.subheader("Growth Summary (Vehicle Type)")
    st.dataframe(
        vt_growth[['Category', 'Year', 'Month', 'Registrations', 'YoY%', 'QoQ%']]
        .sort_values(['Category', 'Year', 'Month']),
        use_container_width=True
    )

elif page == "🏭 Manufacturer Analysis":
    st.title("🏭 Manufacturer Analysis")

    # KPIs aggregated across selected manufacturers (or all, if none selected)
    mf_total, mf_yoy, mf_qoq = kpi_for_selection(manufacturer_filtered)
    selected_count = len(selected_manufacturers) if selected_manufacturers else len(manufacturer_options)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Registrations (Selected Manufacturers)", f"{mf_total:,}")
    c2.metric("Latest YoY (Aggregated)", fmt_pct(mf_yoy))
    c3.metric("Latest QoQ (Aggregated)", fmt_pct(mf_qoq))
    c4.metric("Manufacturers", f"{selected_count} in view")

    # Per-manufacturer growth trends
    mf_growth = compute_group_growth(manufacturer_filtered, 'Manufacturer')
    st.subheader("Trend by Manufacturer")
    st.altair_chart(
        plot_trend(mf_growth, 'Manufacturer', "Registrations by Manufacturer (with YoY/QoQ tooltips)"),
        use_container_width=True
    )

    # Manufacturer share pie (Top 10 within current selection)
    st.subheader("Market Share — Top 10 Manufacturers (Selected)")
    mf_share = (manufacturer_filtered.groupby('Manufacturer', as_index=False)['Registrations']
                .sum()
                .sort_values('Registrations', ascending=False)
                .head(10))
    st.altair_chart(plot_pie(mf_share, 'Manufacturer', 'Registrations', "Top 10 Manufacturers"),
                    use_container_width=True)

    # Summary table
    st.subheader("Growth Summary (Manufacturer)")
    st.dataframe(
        mf_growth[['Manufacturer', 'Year', 'Month', 'Registrations', 'YoY%', 'QoQ%']]
        .sort_values(['Manufacturer', 'Year', 'Month']),
        use_container_width=True
    )

# ---------- FOOTNOTE ----------
st.caption(
    "Notes: YoY compares to the same month last year (t vs t-12). "
    "QoQ compares to three months prior (t vs t-3). "
    "If the comparison period has 0 or missing registrations, growth is shown as —."
)
