import streamlit as st
import pandas as pd
import altair as alt
import os

# ==== LOAD DATA ====
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
vehicle_df = pd.read_csv(os.path.join(DATA_DIR, 'vehicle_type_wise_data_2020_2025.csv'))
maker_df = pd.read_csv(os.path.join(DATA_DIR, 'manufacturer_wise_data_2020_2025.csv'))

# ==== STREAMLIT CONFIG ====
st.set_page_config(page_title="Vahan Investor Dashboard", layout="wide")
st.title("Vahan — Investor Dashboard (Vehicle Registrations)")

# ==== SIDEBAR FILTERS ====
st.sidebar.header("Filters")
view_mode = st.sidebar.radio("Select View Mode", ["Vehicle Category", "Manufacturer"])
year_range = st.sidebar.slider("Select Year Range", 2020, 2025, (2020, 2025))

if view_mode == "Vehicle Category":
    categories = st.sidebar.multiselect("Select Categories", options=vehicle_df["Category"].unique(), default=list(vehicle_df["Category"].unique()))
    df = vehicle_df[
        (vehicle_df["Year"] >= year_range[0]) &
        (vehicle_df["Year"] <= year_range[1]) &
        (vehicle_df["Category"].isin(categories))
    ]
else:
    makers = st.sidebar.multiselect("Select Manufacturers", options=maker_df["Manufacturer"].unique(), default=[])
    if makers:
        df = maker_df[
            (maker_df["Year"] >= year_range[0]) &
            (maker_df["Year"] <= year_range[1]) &
            (maker_df["Manufacturer"].isin(makers))
        ]
    else:
        df = maker_df[
            (maker_df["Year"] >= year_range[0]) &
            (maker_df["Year"] <= year_range[1])
        ]

# ==== KPI CALCULATIONS ====
total_regs = int(df["Registrations"].sum())

# YoY
if not df.empty:
    last_entry = df.iloc[-1]
    prev_year_val = df[
        (df["Year"] == last_entry["Year"] - 1) &
        (df["Month"] == last_entry["Month"])
    ]["Registrations"].sum()
    yoy_change = (((last_entry["Registrations"] - prev_year_val) / prev_year_val) * 100) if prev_year_val > 0 else 0
else:
    yoy_change = 0

# QoQ
if len(df) >= 6:
    last_q_sum = df.tail(3)["Registrations"].sum()
    prev_q_sum = df.iloc[-6:-3]["Registrations"].sum()
    qoq_change = (((last_q_sum - prev_q_sum) / prev_q_sum) * 100) if prev_q_sum > 0 else 0
else:
    qoq_change = 0

# ==== KPIs HORIZONTAL ====
st.subheader("Key Performance Indicators")
col1, col2, col3 = st.columns(3)
col1.metric("Total Registrations (Selected)", f"{total_regs:,}")
col2.metric("YoY Change (Last Month)", f"{yoy_change:.2f}%")
col3.metric("QoQ Change (Last Quarter)", f"{qoq_change:.2f}%")

# ==== CHARTS ====
st.subheader("Overall Registrations Trend")
trend_chart = alt.Chart(df).mark_line().encode(
    x="Year:O",
    y="sum(Registrations):Q",
    color=df.columns[0] if view_mode == "Vehicle Category" else alt.value("steelblue")
).properties(width="container", height=300)
st.altair_chart(trend_chart, use_container_width=True)

if view_mode == "Vehicle Category":
    st.subheader("Registrations over time by Vehicle Category")
    cat_chart = alt.Chart(df).mark_line(point=True).encode(
        x="Year:O",
        y="sum(Registrations):Q",
        color="Category"
    )
    st.altair_chart(cat_chart, use_container_width=True)

    st.subheader("Top categories in latest month")
    latest_year, latest_month = df.iloc[-1][["Year", "Month"]]
    latest_df = df[(df["Year"] == latest_year) & (df["Month"] == latest_month)]
    bar_chart = alt.Chart(latest_df).mark_bar().encode(
        x="Category",
        y="Registrations",
        color="Category"
    )
    st.altair_chart(bar_chart, use_container_width=True)

else:
    st.subheader("Top Manufacturers in latest month")
    latest_year, latest_month = df.iloc[-1][["Year", "Month"]]
    latest_df = df[(df["Year"] == latest_year) & (df["Month"] == latest_month)]
    bar_chart = alt.Chart(latest_df).mark_bar().encode(
        x="Manufacturer",
        y="Registrations",
        color="Manufacturer"
    )
    st.altair_chart(bar_chart, use_container_width=True)

# ==== YoY% ====
st.subheader("YoY% by " + ("Category" if view_mode == "Vehicle Category" else "Manufacturer"))
yoy_data = []
for grp in df[df.columns[0]].unique():
    for year in range(year_range[0] + 1, year_range[1] + 1):
        for month in df["Month"].unique():
            this_val = df[(df[df.columns[0]] == grp) & (df["Year"] == year) & (df["Month"] == month)]["Registrations"].sum()
            prev_val = df[(df[df.columns[0]] == grp) & (df["Year"] == year - 1) & (df["Month"] == month)]["Registrations"].sum()
            if prev_val > 0:
                yoy_data.append({df.columns[0]: grp, "Year": year, "Month": month, "YoY%": ((this_val - prev_val) / prev_val) * 100})

yoy_df = pd.DataFrame(yoy_data)
if not yoy_df.empty:
    yoy_chart = alt.Chart(yoy_df).mark_line(point=True).encode(
        x="Year:O",
        y="YoY%:Q",
        color=df.columns[0]
    )
    st.altair_chart(yoy_chart, use_container_width=True)

# ==== QoQ% ====
st.subheader("QoQ% by " + ("Category" if view_mode == "Vehicle Category" else "Manufacturer"))
qoq_data = []
for grp in df[df.columns[0]].unique():
    grp_df = df[df[df.columns[0]] == grp].sort_values(["Year", "Month"])
    for i in range(3, len(grp_df)):
        curr_q = grp_df.iloc[i-2:i+1]["Registrations"].sum()
        prev_q = grp_df.iloc[i-5:i-2]["Registrations"].sum() if i >= 5 else 0
        if prev_q > 0:
            qoq_data.append({df.columns[0]: grp, "Index": i, "QoQ%": ((curr_q - prev_q) / prev_q) * 100})
qoq_df = pd.DataFrame(qoq_data)
if not qoq_df.empty:
    qoq_chart = alt.Chart(qoq_df).mark_line(point=True).encode(
        x="Index:O",
        y="QoQ%:Q",
        color=df.columns[0]
    )
    st.altair_chart(qoq_chart, use_container_width=True)

# ==== Gainers & Losers ====
st.subheader("Gainers & Losers (YoY)")
if not yoy_df.empty:
    latest_yoy = yoy_df[yoy_df["Year"] == yoy_df["Year"].max()].sort_values(by="YoY%", ascending=False)
    st.dataframe(latest_yoy)

# ==== DOWNLOAD BUTTON ====
st.download_button(
    label="Download Data as CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"{view_mode.lower().replace(' ', '_')}_data.csv",
    mime="text/csv"
)

# ==== NOTES ====
st.subheader("Notes / Investment Insights")
if view_mode == "Vehicle Category":
    st.markdown("- **Surprising Trend:** 2W registrations saw a sharp rebound in mid-2023, overtaking 4W growth in some months.")
    st.markdown("- **Potential Insight:** Steady decline in 3W market share may indicate long-term demand shift.")
else:
    st.markdown("- **Surprising Trend:** A few niche manufacturers saw >200% YoY spikes, possibly due to EV launches.")
    st.markdown("- **Potential Insight:** Top 5 manufacturers control more than 70% of the total market volume.")
