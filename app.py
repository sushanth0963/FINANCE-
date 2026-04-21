# ==========================================
# INDEXME — PERSONAL INFLATION AI DASHBOARD
# FINAL ENTERPRISE ADVANCED VERSION
# ==========================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from groq import Groq

# ==========================================# ==========================================
# INDEXME — PERSONAL INFLATION AI DASHBOARD
# FINAL ENTERPRISE ADVANCED VERSION (FULL AI FINAL FIX)
# ==========================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from groq import Groq

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="IndexMe AI Dashboard",
    layout="wide",
    page_icon="📈"
)

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #0b1220; color: white; }
.dashboard-title {
    padding: 20px; border-radius: 15px;
    background: linear-gradient(135deg,#111827,#0b1220);
    border: 1px solid #334155; margin-bottom: 20px;
}
.insight-box {
    background: #111827;
    padding: 16px;
    border-radius: 12px;
    border-left: 5px solid #3b82f6;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# TITLE
# ==========================================
st.markdown("""
<div class='dashboard-title'>
<h1>📈 IndexMe — Personal Inflation Tracker</h1>
<p>AI-driven inflation analytics for personal spending</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# LOAD DATA
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv("Price_Hike_Impact_DS.xlsx.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month-Year"] = df["Month-Year"].astype(str)
    return df

df = load_data()

# ==========================================
# SIDEBAR
# ==========================================
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
    ]
)

selected_year = st.sidebar.multiselect(
    "Select Year",
    sorted(df["Year"].unique()),
    default=sorted(df["Year"].unique())
)

selected_category = st.sidebar.multiselect(
    "Select Category",
    sorted(df["CategoryName"].unique()),
    default=sorted(df["CategoryName"].unique())
)

item_options = sorted(
    df[df["CategoryName"].isin(selected_category)]["ItemName"].unique()
)

selected_items = st.sidebar.multiselect(
    "Select Items",
    item_options,
    default=item_options
)

# ==========================================
# FILTER DATA
# ==========================================
filtered = df[
    (df["Year"].isin(selected_year)) &
    (df["CategoryName"].isin(selected_category)) &
    (df["ItemName"].isin(selected_items))
].copy()

if filtered.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ==========================================
# CALCULATIONS
# ==========================================
BASE_YEAR = 2023

base_df = df[df["Year"] == BASE_YEAR]
base_price_lookup = base_df.groupby("ItemName")["UnitPrice"].mean().to_dict()

filtered["BasePrice"] = filtered["ItemName"].map(base_price_lookup)
filtered["BasePrice"] = filtered["BasePrice"].fillna(filtered["UnitPrice"])

filtered["BaseCost"] = filtered["Quantity"] * filtered["BasePrice"]
filtered["CurrentCost"] = filtered["Quantity"] * filtered["UnitPrice"]

total_spend = filtered["CurrentCost"].sum()
base_spend = filtered["BaseCost"].sum()

pir = ((total_spend - base_spend) / base_spend) * 100 if base_spend else 0
national_cpi = filtered["NationalCPIValue"].mean()
inflation_gap = pir - national_cpi

# CATEGORY
cat = filtered.groupby("CategoryName").agg({
    "CurrentCost":"sum",
    "BaseCost":"sum"
}).reset_index()

cat["InflationRate"] = np.where(
    cat["BaseCost"] != 0,
    ((cat["CurrentCost"] - cat["BaseCost"]) / cat["BaseCost"]) * 100,
    0
)

top_driver = cat.sort_values("InflationRate", ascending=False).iloc[0]

# ITEM
item_analysis = filtered.groupby("ItemName").agg({
    "CurrentCost":"sum",
    "BaseCost":"sum"
}).reset_index()

item_analysis["ItemInflation"] = np.where(
    item_analysis["BaseCost"] != 0,
    ((item_analysis["CurrentCost"] - item_analysis["BaseCost"]) /
     item_analysis["BaseCost"]) * 100,
    0
)

# SAVINGS
filtered["MinCategoryPrice"] = filtered.groupby("CategoryName")["UnitPrice"].transform("min")
filtered["Savings"] = filtered["CurrentCost"] - (filtered["Quantity"] * filtered["MinCategoryPrice"])
substitution_savings = filtered["Savings"].sum()

# TREND
monthly_trend = filtered.groupby("Month-Year").agg({"CurrentCost":"sum"}).reset_index()

# ==========================================
# GROQ FUNCTIONS
# ==========================================
def generate_ai_insights():
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
Problem:
Cause:
Recommendation:
Impact:

PIR: {pir:.2f}
CPI: {national_cpi:.2f}
Gap: {inflation_gap:.2f}
Top Driver: {top_driver['CategoryName']}
Savings: {substitution_savings:.2f}
"""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3
    )

    return res.choices[0].message.content

def smart_answer(prompt):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    context = f"""
Financial assistant.

Spend: ₹{total_spend:,.2f}
PIR: {pir:.2f}%
CPI: {national_cpi:.2f}%
Gap: {inflation_gap:.2f}%
Top Category: {top_driver['CategoryName']}
Savings: ₹{substitution_savings:,.2f}
"""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":context},
            {"role":"user","content":prompt}
        ],
        temperature=0.4
    )

    return res.choices[0].message.content

# ==========================================
# PAGES
# ==========================================
if page == "🏠 Executive Dashboard":
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("💰 Spend", f"₹{total_spend:,.2f}")
    c2.metric("📈 PIR", f"{pir:.2f}%")
    c3.metric("🏛 CPI", f"{national_cpi:.2f}%")
    c4.metric("📊 Gap", f"{inflation_gap:.2f}%")
    c5.metric("💡 Savings", f"₹{substitution_savings:,.2f}")

    st.plotly_chart(px.line(monthly_trend,x="Month-Year",y="CurrentCost",markers=True),use_container_width=True)

elif page == "📂 Category Analysis":
    st.plotly_chart(px.bar(cat,x="CategoryName",y="InflationRate"),use_container_width=True)

elif page == "📦 Item Insights":
    for _, row in item_analysis.iterrows():
        st.markdown(f"""
        <div class='insight-box'>
        <b>{row['ItemName']}</b><br>
        Inflation: {row['ItemInflation']:.2f}%<br>
        Spend: ₹{row['CurrentCost']:,.2f}
        </div>
        """, unsafe_allow_html=True)

elif page == "🧠 AI Insights":
    st.subheader("🧠 AI Smart Executive Insights")

    show_warning = st.checkbox("⚠ Show AI Disclaimer", value=True)

    if st.button("Generate AI Insights"):

        output = generate_ai_insights()

        problem = cause = recommendation = impact = ""

        for line in output.split("\n"):
            if "problem" in line.lower():
                problem = line.split(":",1)[-1].strip()
            elif "cause" in line.lower():
                cause = line.split(":",1)[-1].strip()
            elif "recommendation" in line.lower():
                recommendation = line.split(":",1)[-1].strip()
            elif "impact" in line.lower():
                impact = line.split(":",1)[-1].strip()

        if not problem:
            problem = f"PIR vs CPI gap is {inflation_gap:.2f}%"
        if not cause:
            cause = f"{top_driver['CategoryName']} driving inflation"
        if not recommendation:
            recommendation = "Reduce high spending category"
        if not impact:
            impact = f"Save ₹{substitution_savings:,.2f}"

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"<div class='insight-box'><b>⚠ Problem</b><br>{problem}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='insight-box'><b>🔍 Cause</b><br>{cause}</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"<div class='insight-box'><b>✅ Recommendation</b><br>{recommendation}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='insight-box'><b>💰 Impact</b><br>{impact}</div>", unsafe_allow_html=True)

        if show_warning:
            st.warning("AI outputs may not be 100% accurate. Please review manually.")

elif page == "💬 Smart Chat":
    st.subheader("💬 AI Smart Chat")

    show_warning = st.checkbox("⚠ Show AI Disclaimer", value=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.chat_input("Ask about your spending...")

    if user_input:
        with st.spinner("Thinking..."):
            answer = smart_answer(user_input)

        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("assistant", answer))

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    if show_warning:
        st.warning("AI may make mistakes. Verify before decisions.")

elif page == "📋 Raw Data":
    st.dataframe(filtered)

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("📈 IndexMe AI Dashboard • FINAL AI VERSION")
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="IndexMe AI Dashboard",
    layout="wide",
    page_icon="📈"
)

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
.stApp {
    background-color: #0b1220;
    color: white;
}

.dashboard-title {
    padding: 20px;
    border-radius: 15px;
    background: linear-gradient(135deg,#111827,#0b1220);
    border: 1px solid #334155;
    margin-bottom: 20px;
}

.insight-box {
    background: #111827;
    padding: 16px;
    border-radius: 12px;
    border-left: 5px solid #3b82f6;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# TITLE
# ==========================================
st.markdown("""
<div class='dashboard-title'>
<h1>📈 IndexMe — Personal Inflation Tracker</h1>
<p>AI-driven inflation analytics for personal spending</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# LOAD DATA
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv("Price_Hike_Impact_DS.xlsx.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month-Year"] = df["Month-Year"].astype(str)
    return df

df = load_data()

# ==========================================
# SIDEBAR
# ==========================================
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
    ]
)

st.sidebar.markdown("---")

selected_year = st.sidebar.multiselect(
    "Select Year",
    sorted(df["Year"].unique()),
    default=sorted(df["Year"].unique())
)

selected_category = st.sidebar.multiselect(
    "Select Category",
    sorted(df["CategoryName"].unique()),
    default=sorted(df["CategoryName"].unique())
)

item_options = sorted(
    df[df["CategoryName"].isin(selected_category)]["ItemName"].unique()
)

selected_items = st.sidebar.multiselect(
    "Select Items",
    item_options,
    default=item_options
)

# ==========================================
# FILTER DATA
# ==========================================
filtered = df[
    (df["Year"].isin(selected_year)) &
    (df["CategoryName"].isin(selected_category)) &
    (df["ItemName"].isin(selected_items))
].copy()

if filtered.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# ==========================================
# BASE YEAR CALCULATIONS
# ==========================================
BASE_YEAR = 2023

base_df = df[df["Year"] == BASE_YEAR]

base_price_lookup = (
    base_df.groupby("ItemName")["UnitPrice"]
    .mean()
    .to_dict()
)

filtered["BasePrice"] = filtered["ItemName"].map(base_price_lookup)
filtered["BasePrice"] = filtered["BasePrice"].fillna(filtered["UnitPrice"])

filtered["BaseCost"] = filtered["Quantity"] * filtered["BasePrice"]
filtered["CurrentCost"] = filtered["Quantity"] * filtered["UnitPrice"]

# ==========================================
# KPI CALCULATIONS
# ==========================================
total_spend = filtered["CurrentCost"].sum()
base_spend = filtered["BaseCost"].sum()

pir = (
    ((total_spend - base_spend) / base_spend) * 100
    if base_spend != 0 else 0
)

national_cpi = filtered["NationalCPIValue"].mean()
inflation_gap = pir - national_cpi

needs_df = filtered[filtered["CategoryType"] == "Essential"]
wants_df = filtered[filtered["CategoryType"] != "Essential"]

needs_spend = needs_df["CurrentCost"].sum()
wants_spend = wants_df["CurrentCost"].sum()

needs_base = needs_df["BaseCost"].sum()
wants_base = wants_df["BaseCost"].sum()

needs_inflation = (
    ((needs_spend - needs_base) / needs_base) * 100
    if needs_base != 0 else 0
)

wants_inflation = (
    ((wants_spend - wants_base) / wants_base) * 100
    if wants_base != 0 else 0
)

# ==========================================
# CATEGORY ANALYSIS
# ==========================================
cat = (
    filtered.groupby(["CategoryName", "CategoryType"])
    .agg({
        "CurrentCost": "sum",
        "BaseCost": "sum"
    })
    .reset_index()
)

cat["InflationRate"] = np.where(
    cat["BaseCost"] != 0,
    ((cat["CurrentCost"] - cat["BaseCost"]) / cat["BaseCost"]) * 100,
    0
)

top_driver = cat.sort_values(
    "InflationRate",
    ascending=False
).iloc[0]

# ==========================================
# ITEM ANALYSIS
# ==========================================
item_analysis = (
    filtered.groupby("ItemName")
    .agg({
        "CurrentCost": "sum",
        "BaseCost": "sum"
    })
    .reset_index()
)

item_analysis["ItemInflation"] = np.where(
    item_analysis["BaseCost"] != 0,
    ((item_analysis["CurrentCost"] - item_analysis["BaseCost"]) /
     item_analysis["BaseCost"]) * 100,
    0
)

# ==========================================
# SAVINGS ANALYSIS
# ==========================================
filtered["MinCategoryPrice"] = (
    filtered.groupby("CategoryName")["UnitPrice"]
    .transform("min")
)

filtered["AlternativeSpend"] = (
    filtered["Quantity"] * filtered["MinCategoryPrice"]
)

filtered["Savings"] = (
    filtered["CurrentCost"] - filtered["AlternativeSpend"]
)

substitution_savings = filtered["Savings"].sum()

# ==========================================
# MONTHLY TREND
# ==========================================
monthly_trend = (
    filtered.groupby("Month-Year")
    .agg({"CurrentCost": "sum"})
    .reset_index()
)

monthly_change_pct = 0

if len(monthly_trend) >= 2:
    last = monthly_trend.iloc[-2]["CurrentCost"]
    curr = monthly_trend.iloc[-1]["CurrentCost"]

    if last != 0:
        monthly_change_pct = ((curr - last) / last) * 100

# ==========================================
# AI FUNCTION USING API KEY
# ==========================================
@st.cache_data(show_spinner=False)
def generate_ai_insights():
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
    Analyze these metrics and provide output in EXACT format:

    Insight:
    <one short sentence>

    Cause:
    <one short sentence>

    Recommendation:
    <one short sentence>

    Data:
    PIR: {pir:.2f}%
    CPI: {national_cpi:.2f}%
    Gap: {inflation_gap:.2f}%
    Top Driver: {top_driver['CategoryName']}
    Needs Inflation: {needs_inflation:.2f}%
    Wants Inflation: {wants_inflation:.2f}%
    Savings: ₹{substitution_savings:,.2f}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a financial BI analyst. Keep output simple and clear."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=200
    )

    return response.choices[0].message.content

# ==========================================
# SMART CHAT
# ==========================================
def smart_answer(prompt):
    q = prompt.lower()

    if "summary" in q:
        return f"""
### 📊 Executive Summary
- Total Spend: ₹{total_spend:,.2f}
- PIR: {pir:.2f}%
- CPI: {national_cpi:.2f}%
- Gap: {inflation_gap:.2f}%
"""

    return f"Current Personal Inflation Rate is {pir:.2f}%."

# ==========================================
# PAGE CONTENT
# ==========================================
if page == "🏠 Executive Dashboard":
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("💰 Total Spend", f"₹{total_spend:,.2f}")
    c2.metric("📈 PIR", f"{pir:.2f}%")
    c3.metric("🏛 CPI", f"{national_cpi:.2f}%")
    c4.metric("📊 Gap", f"{inflation_gap:.2f}%")
    c5.metric("💡 Savings", f"₹{substitution_savings:,.2f}")

    st.markdown(f"""
    <div class='insight-box'>
    <b>📌 Summary:</b><br>
    PIR is {inflation_gap:.2f}% {'above' if inflation_gap > 0 else 'below'} CPI<br><br>
    <b>💡 Action:</b><br>
    Focus on {top_driver['CategoryName']} expenses<br><br>
    <b>📈 Monthly Change:</b> {monthly_change_pct:.2f}%
    </div>
    """, unsafe_allow_html=True)

    comparison_df = pd.DataFrame({
        "Metric": ["PIR", "CPI"],
        "Value": [pir, national_cpi]
    })

    fig_compare = px.bar(
        comparison_df,
        x="Metric",
        y="Value",
        text="Value",
        title="PIR vs CPI Comparison"
    )
    st.plotly_chart(fig_compare, use_container_width=True)

    fig = px.line(
        monthly_trend,
        x="Month-Year",
        y="CurrentCost",
        markers=True,
        title="Monthly Spending Trend"
    )
    st.plotly_chart(fig, use_container_width=True)

elif page == "📂 Category Analysis":
    fig = px.treemap(
        cat,
        path=["CategoryType", "CategoryName"],
        values="CurrentCost",
        color="InflationRate"
    )
    st.plotly_chart(fig, use_container_width=True)

elif page == "📦 Item Insights":
    st.subheader("📦 Smart Item Recommendations")

    for _, row in item_analysis.iterrows():
        inflation = row["ItemInflation"]

        if inflation >= 25:
            risk = "🔴 High Risk"
            suggestion = "Switch brand / bulk purchase"
        elif inflation >= 10:
            risk = "🟠 Moderate Risk"
            suggestion = "Compare alternatives"
        else:
            risk = "🟢 Stable"
            suggestion = "Continue same pattern"

        st.markdown(f"""
        <div class='insight-box'>
            <b>{row['ItemName']}</b><br>
            Inflation: {inflation:.2f}%<br>
            Spend: ₹{row['CurrentCost']:,.2f}<br>
            Risk: {risk}<br>
            Suggestion: {suggestion}
        </div>
        """, unsafe_allow_html=True)

elif page == "🧠 AI Insights":
    st.subheader("🧠 AI Smart Executive Insights")

    if st.button("Generate AI Insights", use_container_width=True):

        # ------------------------------
        # BUSINESS LOGIC
        # ------------------------------
        if inflation_gap > 0:
            problem_text = (
                f"Your Personal Inflation Rate ({pir:.2f}%) is "
                f"{inflation_gap:.2f}% above National CPI "
                f"({national_cpi:.2f}%)."
            )
        else:
            problem_text = (
                f"Your PIR is performing better than CPI by "
                f"{abs(inflation_gap):.2f}%."
            )

        cause_text = (
            f"The major inflation driver is "
            f"{top_driver['CategoryName']} with "
            f"{top_driver['InflationRate']:.2f}% increase."
        )

        recommendation_text = (
            f"Focus on optimizing {top_driver['CategoryName']} "
            f"expenses by switching brands, bulk buying, or "
            f"reducing consumption frequency."
        )

        impact_text = (
            f"Potential savings opportunity: "
            f"₹{substitution_savings:,.2f}"
        )

        # ------------------------------
        # BOX LAYOUT
        # ------------------------------
        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"""
            <div class='insight-box'>
                <h4>⚠ Problem</h4>
                {problem_text}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class='insight-box'>
                <h4>🔍 Root Cause</h4>
                {cause_text}
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class='insight-box'>
                <h4>✅ Recommendation</h4>
                {recommendation_text}
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class='insight-box'>
                <h4>💰 Business Impact</h4>
                {impact_text}
            </div>
            """, unsafe_allow_html=True)

elif page == "📋 Raw Data":
    st.dataframe(filtered, use_container_width=True)

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("📈 IndexMe Finance Dashboard")
