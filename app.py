# ==========================================
# INDEXME — PERSONAL INFLATION AI DASHBOARD
# FINAL CLEAN WORKING VERSION (FIXED + COMPLETE)
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
    margin-bottom:20px;
}

.insight-box {
    background:#111827;
    padding:16px;
    border-radius:12px;
    border-left:5px solid #3b82f6;
    margin-bottom:16px;
}
</style>
""", unsafe_allow_html=True)

# ---------- TITLE ----------
st.markdown("""
<div class='dashboard-title'>
<h1>📈 IndexMe — Personal Inflation Tracker</h1>
<p>AI-driven inflation analytics</p>
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

# ---------- SIDEBAR ----------
st.sidebar.title("📊 Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Executive Dashboard",
        "📂 Category Analysis",
        "📦 Item Insights",
        "🧠 AI Insights",
        "💬 Smart Chat",
        "📋 Raw Data"
    ],
    key="main_nav"   # ✅ FIX duplicate ID error
)

year = st.sidebar.multiselect("Year", df["Year"].unique(), df["Year"].unique())
cat_sel = st.sidebar.multiselect("Category", df["CategoryName"].unique(), df["CategoryName"].unique())

items = df[df["CategoryName"].isin(cat_sel)]["ItemName"].unique()
item_sel = st.sidebar.multiselect("Items", items, items)

# ---------- FILTER ----------
filtered = df[
    (df["Year"].isin(year)) &
    (df["CategoryName"].isin(cat_sel)) &
    (df["ItemName"].isin(item_sel))
].copy()

if filtered.empty:
    st.warning("No data available for selected filters.")
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
cat = filtered.groupby("CategoryName", as_index=False).agg({
    "CurrentCost":"sum",
    "BaseCost":"sum"
})

cat["InflationRate"] = np.where(
    cat["BaseCost"] != 0,
    ((cat["CurrentCost"] - cat["BaseCost"]) / cat["BaseCost"]) * 100,
    0
)

top = cat.sort_values("InflationRate", ascending=False).iloc[0]

# ---------- ITEM (FIXED) ----------
item = filtered.groupby("ItemName", as_index=False).agg({
    "CurrentCost":"sum",
    "BaseCost":"sum"
})

item["BaseCost"] = item["BaseCost"].replace(0, np.nan)

item["Inflation"] = (
    (item["CurrentCost"] - item["BaseCost"]) /
    item["BaseCost"]
) * 100

item["Inflation"] = item["Inflation"].replace([np.inf, -np.inf], 0).fillna(0)
item["CurrentCost"] = item["CurrentCost"].fillna(0)

# ---------- SAVINGS ----------
filtered["MinPrice"] = filtered.groupby("CategoryName")["UnitPrice"].transform("min")
filtered["Savings"] = filtered["CurrentCost"] - (filtered["Quantity"]*filtered["MinPrice"])
savings = filtered["Savings"].sum()

# ---------- TREND ----------
trend = filtered.groupby("Month-Year").agg({"CurrentCost":"sum"}).reset_index()

# ---------- AI ----------
def smart_answer(q):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        context = f"""
Financial assistant.

Spend: ₹{total:,.2f}
PIR: {pir:.2f}%
CPI: {cpi:.2f}%
Gap: {gap:.2f}%
Top Category: {top['CategoryName']}
Savings: ₹{savings:,.2f}
"""

        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"system","content":context},
                {"role":"user","content":q}
            ],
            temperature=0.4,
            max_tokens=200
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"⚠ AI error: {str(e)}"


def ai_insights():
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        prompt = f"""
Problem:
Cause:
Recommendation:
Impact:

PIR:{pir}
CPI:{cpi}
Gap:{gap}
Top:{top['CategoryName']}
Savings:{savings}
"""

        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.3
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"

# ---------- PAGES ----------
if page=="🏠 Executive Dashboard":
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("💰 Spend",f"₹{total:,.0f}")
    c2.metric("📈 PIR",f"{pir:.2f}%")
    c3.metric("🏛 CPI",f"{cpi:.2f}%")
    c4.metric("📊 Gap",f"{gap:.2f}%")
    c5.metric("💡 Savings",f"₹{savings:,.0f}")

    st.plotly_chart(px.line(trend,x="Month-Year",y="CurrentCost"),use_container_width=True)

elif page=="📂 Category Analysis":
    st.plotly_chart(px.bar(cat,x="CategoryName",y="InflationRate"),use_container_width=True)

elif page=="📦 Item Insights":
    st.subheader("📦 Item Insights")

    for _,r in item.iterrows():
        inflation=float(r["Inflation"])
        spend=float(r["CurrentCost"])

        st.markdown(f"""
        <div class='insight-box'>
        <b>{r['ItemName']}</b><br>
        Inflation: {inflation:.2f}%<br>
        Spend: ₹{spend:,.2f}
        </div>
        """,unsafe_allow_html=True)

elif page=="🧠 AI Insights":
    st.subheader("🧠 AI Insights")

    show=st.checkbox("⚠ Show Disclaimer",True)

    if st.button("Generate AI Insights"):
        out=ai_insights()

        problem=cause=reco=impact=""

        for line in out.split("\n"):
            if "problem" in line.lower():
                problem=line.split(":",1)[-1]
            elif "cause" in line.lower():
                cause=line.split(":",1)[-1]
            elif "recommendation" in line.lower():
                reco=line.split(":",1)[-1]
            elif "impact" in line.lower():
                impact=line.split(":",1)[-1]

        col1,col2=st.columns(2)

        with col1:
            st.markdown(f"<div class='insight-box'><b>⚠ Problem</b><br>{problem}</div>",unsafe_allow_html=True)
            st.markdown(f"<div class='insight-box'><b>🔍 Cause</b><br>{cause}</div>",unsafe_allow_html=True)

        with col2:
            st.markdown(f"<div class='insight-box'><b>✅ Recommendation</b><br>{reco}</div>",unsafe_allow_html=True)
            st.markdown(f"<div class='insight-box'><b>💰 Impact</b><br>{impact}</div>",unsafe_allow_html=True)

    if show:
        st.warning("AI may be inaccurate")

elif page=="💬 Smart Chat":
    st.subheader("💬 Smart Chat")

    show=st.checkbox("⚠ Show Disclaimer",True)

    if "chat" not in st.session_state:
        st.session_state.chat=[]

    q=st.chat_input("Ask about your spending...")

    if q:
        with st.spinner("Thinking..."):
            ans=smart_answer(q)

        st.session_state.chat.append(("user",q))
        st.session_state.chat.append(("assistant",ans))

    for r,m in st.session_state.chat:
        with st.chat_message(r):
            st.markdown(m)

    if show:
        st.warning("AI may make mistakes")

elif page=="📋 Raw Data":
    st.dataframe(filtered)

# ---------- FOOTER ----------
st.markdown("---")
st.caption("📈 IndexMe Final Stable Version")
