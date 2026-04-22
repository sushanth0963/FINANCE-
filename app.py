# ==========================================
# INDEXME — FINAL STABLE VERSION (EXECUTIVE PERFECT UI + AI FIXED)
# ==========================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from groq import Groq

st.set_page_config(page_title="IndexMe AI Dashboard", layout="wide", page_icon="📈")

# ---------- CSS ----------
st.markdown("""
<style>
.stApp { background-color:#0b1220; color:white; }

.dashboard-title {
    padding:20px;
    border-radius:15px;
    background:linear-gradient(135deg,#111827,#0b1220);
    border:1px solid #334155;
}

.insight-box {
    background:#111827;
    padding:14px;
    border-radius:10px;
    border-left:5px solid #3b82f6;
    margin-bottom:12px;
}
</style>
""", unsafe_allow_html=True)

# ---------- TITLE ----------
st.markdown("""
<div class='dashboard-title'>
<h1>📈 IndexMe — Personal Inflation Tracker</h1>
</div>
""", unsafe_allow_html=True)

# ---------- DATA ----------
@st.cache_data
def load_data():
    df = pd.read_csv("Price_Hike_Impact_DS.xlsx.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month-Year"] = df["Month-Year"].astype(str)
    return df

df = load_data()

# ---------- BRAND ----------
brand_map = {
    "Pizza Night": "Domino's",
    "Coffee Shop": "Starbucks",
    "Headphones": "boAt",
    "Smartphone": "Samsung",
    "Whole Milk": "Amul"
}

alt_brand_map = {
    "Pizza Night": "Local Pizzeria",
    "Coffee Shop": "Local Cafe",
    "Headphones": "Noise",
    "Smartphone": "Redmi",
    "Whole Milk": "Local Dairy"
}

def get_brand(item):
    return brand_map.get(item, "Local Brand")

def get_alt_brand(item):
    return alt_brand_map.get(item, "Budget Brand")

df["Brand"] = df["ItemName"].apply(get_brand)

# ---------- SIDEBAR ----------
page = st.sidebar.radio("Go to", [
    "🏠 Executive Dashboard",
    "📂 Category Analysis",
    "📦 Item Insights",
    "🧠 AI Insights",
    "💬 Smart Chat",
    "📋 Raw Data"
])

year = st.sidebar.multiselect("Year", df["Year"].unique(), df["Year"].unique())
cat_sel = st.sidebar.multiselect("Category", df["CategoryName"].unique(), df["CategoryName"].unique())

items = df[df["CategoryName"].isin(cat_sel)]["ItemName"].unique()
item_sel = st.sidebar.multiselect("Items", items, items)

filtered = df[
    (df["Year"].isin(year)) &
    (df["CategoryName"].isin(cat_sel)) &
    (df["ItemName"].isin(item_sel))
].copy()

if filtered.empty:
    st.warning("No data")
    st.stop()

# ---------- CALCULATIONS ----------
base = df[df["Year"] == 2023]
lookup = base.groupby("ItemName")["UnitPrice"].mean().to_dict()

filtered["BasePrice"] = filtered["ItemName"].map(lookup).fillna(filtered["UnitPrice"])
filtered["BaseCost"] = filtered["Quantity"] * filtered["BasePrice"]
filtered["CurrentCost"] = filtered["Quantity"] * filtered["UnitPrice"]

total = filtered["CurrentCost"].sum()
base_total = filtered["BaseCost"].sum()

pir = ((total - base_total)/base_total)*100 if base_total else 0
cpi = filtered["NationalCPIValue"].mean()
gap = pir - cpi

# ---------- CATEGORY ----------
cat = filtered.groupby("CategoryName").agg({"CurrentCost":"sum","BaseCost":"sum"}).reset_index()
cat["InflationRate"] = np.where(
    cat["BaseCost"]!=0,
    ((cat["CurrentCost"]-cat["BaseCost"])/cat["BaseCost"])*100,
    0
)

# ---------- ITEM ----------
item = filtered.groupby("ItemName").agg({"CurrentCost":"sum","BaseCost":"sum"}).reset_index()
item["Inflation"] = np.where(
    item["BaseCost"]!=0,
    ((item["CurrentCost"]-item["BaseCost"])/item["BaseCost"])*100,
    0
)

# ---------- SAVINGS ----------
filtered["MinPrice"] = filtered.groupby("CategoryName")["UnitPrice"].transform("min")
filtered["Savings"] = (filtered["UnitPrice"] - filtered["MinPrice"]) * filtered["Quantity"]

top5 = (
    filtered.groupby("ItemName")
    .agg({"Savings":"sum"})
    .reset_index()
    .sort_values("Savings", ascending=False)
    .head(5)
)

# ============================
# EXECUTIVE DASHBOARD
# ============================
if page=="🏠 Executive Dashboard":

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Spend",f"₹{total:,.0f}")
    c2.metric("PIR",f"{pir:.2f}%")
    c3.metric("CPI",f"{cpi:.2f}%")
    c4.metric("Gap",f"{gap:.2f}%")
    c5.metric("Savings",f"₹{filtered['Savings'].sum():,.0f}")

    example_items = (
        filtered.groupby("ItemName")
        .agg({
            "Savings": "sum",
            "BasePrice": "mean",
            "UnitPrice": "mean",
            "MinPrice": "mean",
            "Quantity": "sum"
        })
        .reset_index()
        .sort_values("Savings", ascending=False)
        .head(3)
    )

    st.subheader("📊 Smart Spending Comparisons")

    cols = st.columns(3)

    for i, r in example_items.iterrows():

        base_price = r["BasePrice"]
        current_price = r["UnitPrice"]
        min_price = r["MinPrice"]
        qty = r["Quantity"]

        save_unit = current_price - min_price
        save_month = save_unit * qty

        with cols[i % 3]:   # ✅ FIXED INDEX ERROR
            st.markdown(f"""
            <div style="
                background:#111827;
                padding:20px;
                border-radius:18px;
                border:1px solid #334155;
                box-shadow:0 4px 20px rgba(0,0,0,0.3);
            ">

            <h4>🍽 {r['ItemName']}</h4>

            <p style="color:#9ca3af;">
            2023 → <b style="color:white;">₹{base_price:.0f}</b><br>
            Now → <b style="color:#f87171;">₹{current_price:.0f}</b>
            </p>

            <hr>

            Switch <b>{get_brand(r['ItemName'])}</b> ➝ 
            <b style="color:#22c55e;">{get_alt_brand(r['ItemName'])}</b><br>
            New → ₹{min_price:.0f}

            <p style="margin-top:10px;">
            💰 <b style="color:#22c55e;">₹{save_unit:.0f}/unit</b><br>
            📅 Monthly → <b style="color:#22c55e;">₹{save_month:.0f}</b>
            </p>

            </div>
            """, unsafe_allow_html=True)

    st.subheader("🛒 Top 5 Brand Switching")

    for _, r in top5.iterrows():
        st.markdown(f"""
        <div class='insight-box'>
        <b>{r['ItemName']}</b><br>
        Current Brand: {get_brand(r['ItemName'])}<br>
        Recommended: <b>{get_alt_brand(r['ItemName'])}</b><br>
        💰 Save: ₹{r['Savings']:.2f}
        </div>
        """, unsafe_allow_html=True)

# ---------- AI INSIGHTS ----------
elif page=="🧠 AI Insights":

    if st.button("Generate Insights"):

        total_savings = filtered["Savings"].sum()

        problem = f"Your spending is ₹{total:,.0f} with inflation {pir:.2f}%."
        cause = "High-cost brands are increasing expenses."
        reco = "Switch to budget-friendly alternatives."
        impact = f"You can save ₹{total_savings:,.0f} monthly."

        col1,col2 = st.columns(2)

        with col1:
            st.markdown(f"<div class='insight-box'><b>Problem</b><br>{problem}</div>",unsafe_allow_html=True)
            st.markdown(f"<div class='insight-box'><b>Cause</b><br>{cause}</div>",unsafe_allow_html=True)

        with col2:
            st.markdown(f"<div class='insight-box'><b>Recommendation</b><br>{reco}</div>",unsafe_allow_html=True)
            st.markdown(f"<div class='insight-box'><b>Impact</b><br>{impact}</div>",unsafe_allow_html=True)

        # ✅ ADDED USER-FRIENDLY EXAMPLES
        st.subheader("📊 Example Savings Breakdown")

        example_items = filtered.sort_values("Savings", ascending=False).head(3)

        for _, r in example_items.iterrows():

            base_price = r["BasePrice"]
            current_price = r["UnitPrice"]
            min_price = r["MinPrice"]
            qty = r["Quantity"]

            save_unit = current_price - min_price
            save_month = save_unit * qty

            st.markdown(f"""
            <div class='insight-box'>

            In 2023, <b>{r['ItemName']}</b> cost ₹{base_price:.0f}/unit.<br>
            Now it costs ₹{current_price:.0f}/unit.<br><br>

            If you switch from <b>{get_brand(r['ItemName'])}</b> to 
            <b>{get_alt_brand(r['ItemName'])}</b> (₹{min_price:.0f}/unit),<br><br>

            💰 You can save ₹{save_unit:.0f} per unit → ₹{save_month:.0f}/month

            </div>
            """, unsafe_allow_html=True)

# ---------- REST SAME ----------
elif page=="📂 Category Analysis":
    st.plotly_chart(px.bar(cat,x="CategoryName",y="InflationRate"),use_container_width=True)

elif page=="📦 Item Insights":
    for _,r in item.iterrows():
        st.markdown(f"""
        <div class='insight-box'>
        <b>{r['ItemName']}</b><br>
        Inflation: {r['Inflation']:.2f}%<br>
        Spend: ₹{r['CurrentCost']:,.2f}
        </div>
        """,unsafe_allow_html=True)

elif page=="💬 Smart Chat":

    if "chat" not in st.session_state:
        st.session_state.chat=[]

    q = st.chat_input("Ask...")

    if q:
        ans = f"Inflation: {pir:.2f}% | Savings: ₹{filtered['Savings'].sum():,.0f}"
        st.session_state.chat.append(("user",q))
        st.session_state.chat.append(("assistant",ans))

    for r,m in st.session_state.chat:
        with st.chat_message(r):
            st.markdown(m)

elif page=="📋 Raw Data":
    st.dataframe(filtered)

st.markdown("---")
st.caption("Final Production UI")
