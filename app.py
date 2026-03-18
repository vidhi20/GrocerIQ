import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(
    page_title="SmartCart — Walmart RFM Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

SEG_COLORS = {
    "Champion":           "#1D9E75",
    "Loyal Customer":     "#185FA5",
    "Potential Loyalist": "#7F77DD",
    "At-Risk":            "#EF9F27",
    "New Customer":       "#5DCAA5",
    "Cannot Lose":        "#D85A30",
    "Hibernating":        "#888780",
    "Lost":               "#E24B4A",
}

st.markdown("""
<style>
.kpi-card{background:white;border:1px solid #e0e0e0;border-radius:10px;
  padding:1rem 1.2rem;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:0.5rem}
.kpi-value{font-size:1.9rem;font-weight:700;margin:0}
.kpi-label{font-size:0.72rem;color:#666;margin:0.2rem 0 0 0;
  text-transform:uppercase;letter-spacing:0.05em}
.section-title{font-size:1rem;font-weight:600;color:#041E42;
  border-left:4px solid #0071CE;padding-left:0.7rem;margin:1.2rem 0 0.8rem 0}
.recipe-card{border:1px solid #e0e0e0;border-radius:10px;
  padding:14px 16px;margin-bottom:12px;background:white}
.yt-btn{display:inline-block;background:#FF0000;color:white;
  padding:6px 14px;border-radius:6px;font-size:12px;font-weight:600;
  text-decoration:none;margin-top:8px}
.yt-btn:hover{background:#CC0000;color:white}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────
def youtube_url(recipe_name):
    """Generate YouTube search URL for a recipe — no API key needed."""
    query = str(recipe_name).replace(" ", "+") + "+recipe"
    return f"https://www.youtube.com/results?search_query={query}"

def safe_str(val, default=""):
    """Convert value to string, replacing nan/None with default."""
    if val is None:
        return default
    s = str(val).strip()
    return default if s.lower() in ("nan", "none", "") else s

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ── DATA CLEANING ─────────────────────────────────────────────────
def clean_rfm(df):
    df = df.copy()
    str_cols = ["customer_id","segment","top_category","city",
                "gender","age_group","cluster_name","top_product"]
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].fillna("Unknown").astype(str)
            df[c] = df[c].replace({"nan":"Unknown","None":"Unknown","":"Unknown"})
    num_cols = ["recency","frequency","monetary","r_score",
                "f_score","m_score","avg_order_value","total_items"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "loyalty_member" in df.columns:
        df["loyalty_member"] = df["loyalty_member"].fillna(False)
    return df

def clean_recipes(df):
    if df.empty:
        return df
    df = df.copy()
    df["recipe_name"] = df["recipe_name"].apply(lambda x: safe_str(x, "Unknown Recipe"))
    df["match_pct"]   = df["match_pct"].apply(lambda x: safe_float(x, 0.0))
    df["have_items"]  = df["have_items"].apply(lambda x: safe_str(x, ""))
    df["need_items"]  = df["need_items"].apply(lambda x: safe_str(x, ""))
    df["minutes"]     = pd.to_numeric(df["minutes"], errors="coerce").fillna(30).astype(int)
    df["youtube_url"] = df["recipe_name"].apply(youtube_url)
    df = df[df["recipe_name"] != "Unknown Recipe"]
    return df

def clean_recs(df):
    if df.empty:
        return df
    df = df.copy()
    for i in range(1, 6):
        c = f"rec_{i}"
        if c in df.columns:
            df[c] = df[c].apply(lambda x: safe_str(x, ""))
    return df

def clean_rules(df):
    if df.empty:
        return df
    df = df.copy()
    for c in ["product_1","product_2"]:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: safe_str(x, ""))
    for c in ["support","confidence","lift"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df = df[(df["product_1"].str.len() > 0) & (df["product_2"].str.len() > 0)]
    return df


# ── DATA LOADING ──────────────────────────────────────────────────
@st.cache_data
def load_data():
    def make_sample():
        np.random.seed(42)
        n     = 5000
        segs  = ["Champion","Loyal Customer","Potential Loyalist",
                 "At-Risk","New Customer","Hibernating","Lost"]
        props = [0.15,0.20,0.18,0.20,0.12,0.10,0.05]
        cats  = ["Dairy & Eggs","Fresh Produce","Meat & Seafood",
                 "Pantry & Dry Goods","Beverages","Household","Snacks & Cereal"]
        return pd.DataFrame({
            "customer_id":     [f"WMT_{i:05d}" for i in range(n)],
            "recency":         np.random.exponential(30,n).astype(int),
            "frequency":       np.random.poisson(8,n)+1,
            "monetary":        np.round(np.random.exponential(200,n),2),
            "r_score":         np.random.randint(1,6,n),
            "f_score":         np.random.randint(1,6,n),
            "m_score":         np.random.randint(1,6,n),
            "segment":         np.random.choice(segs,n,p=props),
            "top_category":    np.random.choice(cats,n),
            "avg_order_value": np.round(np.random.exponential(50,n),2),
            "city":            np.random.choice(["Chicago","Evanston","Oak Park"],n),
            "loyalty_member":  np.random.choice([True,False],n),
            "age_group":       np.random.choice(["18-24","25-34","35-44","45-54","55-64","65+"],n),
            "gender":          np.random.choice(["Male","Female","Non-Binary"],n),
        })

    rfm     = pd.read_csv("rfm_segments.csv")     if os.path.exists("rfm_segments.csv")     else make_sample()
    recs    = pd.read_csv("recommendations.csv")  if os.path.exists("recommendations.csv")  else pd.DataFrame()
    recipes = pd.read_csv("recipe_matches.csv")   if os.path.exists("recipe_matches.csv")   else pd.DataFrame()
    rules   = pd.read_csv("association_rules.csv")if os.path.exists("association_rules.csv")else pd.DataFrame()

    rfm     = clean_rfm(rfm)
    recs    = clean_recs(recs)
    recipes = clean_recipes(recipes)
    rules   = clean_rules(rules)

    return rfm, recs, recipes, rules

rfm, recs, recipes, rules = load_data()


# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("🛒 SmartCart")
    st.caption("Walmart Grocery · RFM Analytics")
    st.markdown("---")
    st.subheader("Filters")
    all_segs   = sorted(rfm["segment"].unique().tolist())
    sel_segs   = st.multiselect("Segments", all_segs, default=all_segs)
    all_cities = sorted(rfm["city"].dropna().unique().tolist()) if "city" in rfm.columns else []
    sel_cities = st.multiselect("City", all_cities, default=all_cities) if all_cities else []
    loyalty_f  = st.selectbox("Loyalty", ["All","Members Only","Non-Members"])
    st.markdown("---")
    st.caption("SmartCart · Project · 2024")


# ── FILTER ────────────────────────────────────────────────────────
filtered = rfm[rfm["segment"].isin(sel_segs)].copy()
if sel_cities and "city" in rfm.columns:
    filtered = filtered[filtered["city"].isin(sel_cities)]
if loyalty_f == "Members Only" and "loyalty_member" in filtered.columns:
    filtered = filtered[filtered["loyalty_member"] == True]
elif loyalty_f == "Non-Members" and "loyalty_member" in filtered.columns:
    filtered = filtered[filtered["loyalty_member"] == False]


# ── KPI VARS ──────────────────────────────────────────────────────
total_customers = len(filtered)
avg_spend       = float(filtered["monetary"].mean()) if total_customers > 0 else 0.0
avg_frequency   = float(filtered["frequency"].mean()) if total_customers > 0 else 0.0
champions       = int((filtered["segment"] == "Champion").sum())
at_risk         = int((filtered["segment"] == "At-Risk").sum())


# ── HEADER ────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(90deg,#0071CE,#004F9A);
            padding:1.2rem 2rem;border-radius:10px;margin-bottom:1.5rem">
  <h1 style="color:white;font-size:1.8rem;font-weight:700;margin:0">
    🛒 SmartCart — Walmart Grocery Analytics
  </h1>
  <p style="color:#FFC220;font-size:0.9rem;margin:0.3rem 0 0 0">
    RFM Segmentation · Recommendations · Recipe Matching · Jan 2023 – Dec 2024
  </p>
</div>
""", unsafe_allow_html=True)


# ── TABS ──────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📊 Overview","👥 Segments","🔍 Customers",
    "🎯 Recommendations","🍳 Recipes"
])


# ================================================================
# TAB 1 — OVERVIEW
# ================================================================
with tab1:
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi_data = [
        (c1, f"{total_customers:,}",  "#0071CE", "Total Customers"),
        (c2, f"${avg_spend:,.0f}",    "#0071CE", "Avg Total Spend"),
        (c3, f"{champions:,}",        "#1D9E75", "Champions"),
        (c4, f"{at_risk:,}",          "#E24B4A", "At-Risk"),
        (c5, f"{avg_frequency:.1f}",  "#0071CE", "Avg Orders"),
    ]
    for col, val, color, label in kpi_data:
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'<p class="kpi-value" style="color:{color}">{val}</p>'
                f'<p class="kpi-label">{label}</p></div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    at_risk_pct = (at_risk/total_customers*100) if total_customers > 0 else 0
    champ_pct   = (champions/total_customers*100) if total_customers > 0 else 0
    st.warning(f"⚠ {at_risk:,} customers ({at_risk_pct:.1f}%) at risk — consider re-engagement campaign")
    st.success(f"✓ {champions:,} Champion customers ({champ_pct:.1f}%) driving highest revenue")
    st.info(f"↗ Recommendation engine active for {len(recs):,} customers")
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Segment distribution</div>', unsafe_allow_html=True)
        seg_df = filtered["segment"].value_counts().reset_index()
        seg_df.columns = ["Segment","Count"]
        fig1 = px.bar(seg_df,x="Count",y="Segment",orientation="h",
                      color="Segment",color_discrete_map=SEG_COLORS,
                      text="Count",height=340)
        fig1.update_traces(texttemplate="%{text:,}",textposition="outside")
        fig1.update_layout(showlegend=False,margin=dict(l=0,r=60,t=10,b=10),
                           plot_bgcolor="white",paper_bgcolor="white",
                           yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig1,use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">RFM scatter</div>', unsafe_allow_html=True)
        sdf = filtered.sample(min(3000,len(filtered)),random_state=42)
        fig2 = px.scatter(sdf,x="frequency",y="monetary",color="segment",
                          color_discrete_map=SEG_COLORS,opacity=0.5,height=340,
                          labels={"frequency":"Frequency","monetary":"Monetary ($)","segment":"Segment"})
        fig2.update_layout(margin=dict(l=0,r=0,t=10,b=10),
                           plot_bgcolor="white",paper_bgcolor="white",
                           legend=dict(orientation="h",yanchor="bottom",y=1.02,font_size=9))
        st.plotly_chart(fig2,use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="section-title">Average spend per segment</div>', unsafe_allow_html=True)
        sp_df = filtered.groupby("segment")["monetary"].mean().reset_index()
        sp_df.columns = ["Segment","Avg Spend"]
        sp_df = sp_df.sort_values("Avg Spend")
        fig3 = px.bar(sp_df,x="Avg Spend",y="Segment",orientation="h",
                      color="Segment",color_discrete_map=SEG_COLORS,
                      text="Avg Spend",height=340)
        fig3.update_traces(texttemplate="$%{text:,.0f}",textposition="outside")
        fig3.update_layout(showlegend=False,margin=dict(l=0,r=80,t=10,b=10),
                           plot_bgcolor="white",paper_bgcolor="white")
        st.plotly_chart(fig3,use_container_width=True)

    with col_d:
        st.markdown('<div class="section-title">Top grocery categories</div>', unsafe_allow_html=True)
        if "top_category" in filtered.columns:
            cat_df = filtered["top_category"].value_counts().reset_index()
            cat_df.columns = ["Category","Count"]
            cat_df = cat_df[cat_df["Category"] != "Unknown"]
            fig4 = px.pie(cat_df,values="Count",names="Category",hole=0.4,height=340,
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig4.update_layout(margin=dict(l=0,r=0,t=10,b=10),paper_bgcolor="white")
            fig4.update_traces(textinfo="percent+label",textfont_size=10)
            st.plotly_chart(fig4,use_container_width=True)

    st.markdown('<div class="section-title">RFM heatmap</div>', unsafe_allow_html=True)
    if "r_score" in filtered.columns and "f_score" in filtered.columns:
        pivot = filtered.groupby(["r_score","f_score"])["monetary"].mean().unstack(fill_value=0).round(0)
        fig5  = px.imshow(pivot,color_continuous_scale="YlOrRd",text_auto=True,height=320,
                          labels=dict(x="Frequency Score (1→5)",
                                      y="Recency Score (1→5)",
                                      color="Avg Spend ($)"))
        fig5.update_layout(margin=dict(l=0,r=0,t=10,b=10),paper_bgcolor="white")
        st.plotly_chart(fig5,use_container_width=True)


# ================================================================
# TAB 2 — SEGMENTS
# ================================================================
with tab2:
    st.markdown('<div class="section-title">Segment summary</div>', unsafe_allow_html=True)
    seg_tbl = filtered.groupby("segment").agg(
        Customers     = ("customer_id","count"),
        Avg_Recency   = ("recency","mean"),
        Avg_Orders    = ("frequency","mean"),
        Avg_Spend     = ("monetary","mean"),
        Total_Revenue = ("monetary","sum"),
    ).round(1).reset_index()
    seg_tbl["Pct_of_Base"] = (
        seg_tbl["Customers"]/seg_tbl["Customers"].sum()*100
    ).round(1)
    seg_tbl = seg_tbl.sort_values("Total_Revenue",ascending=False)
    st.dataframe(seg_tbl,use_container_width=True,hide_index=True)

    st.markdown('<div class="section-title">Marketing strategy per segment</div>', unsafe_allow_html=True)
    STRAT = {
        "Champion":           ("🏆","#1D9E75","Reward & retain","Exclusive loyalty rewards, early access, bundle discounts."),
        "Loyal Customer":     ("💙","#185FA5","Upsell","Premium product lines, bundle offers, buy 2 get 1 promotions."),
        "Potential Loyalist": ("⭐","#7F77DD","Convert to loyal","Personalised grocery recs. Loyalty programme sign-up incentive."),
        "At-Risk":            ("⚠️","#EF9F27","Re-engage urgently","Win-back email with coupon for top category. Show recipe suggestions."),
        "New Customer":       ("🌱","#5DCAA5","Onboard & nurture","Welcome email with first-order discount. Popular bundles."),
        "Hibernating":        ("😴","#888780","Wake them up","Last chance email with 20% discount on top category."),
        "Lost":               ("❌","#E24B4A","Win-back or sunset","Final win-back campaign. Sunset if no response in 30 days."),
    }
    cols_s = st.columns(2)
    for i,(seg,(icon,color,action,desc)) in enumerate(STRAT.items()):
        cnt = len(filtered[filtered["segment"]==seg])
        with cols_s[i%2]:
            st.markdown(
                f'<div style="border:1px solid {color}33;border-left:4px solid {color};'
                f'border-radius:8px;padding:10px 14px;margin-bottom:10px;background:{color}0a">'
                f'<span style="font-size:14px">{icon}</span>'
                f'<strong style="color:{color};margin-left:6px">{seg}</strong>'
                f'<span style="float:right;font-size:11px;color:#666">{cnt:,} customers</span>'
                f'<div style="font-size:12px;font-weight:600;color:#333;margin-top:5px">{action}</div>'
                f'<div style="font-size:11px;color:#555;line-height:1.5;margin-top:3px">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# ================================================================
# TAB 3 — CUSTOMERS
# ================================================================
with tab3:
    st.markdown('<div class="section-title">Customer explorer</div>', unsafe_allow_html=True)
    cs1,cs2,cs3 = st.columns(3)
    with cs1: search_id  = st.text_input("Search Customer ID",placeholder="WMT_00001")
    with cs2: seg_filter = st.selectbox("Segment",["All"]+all_segs)
    with cs3: sort_by    = st.selectbox("Sort by",["monetary","frequency","recency"])

    disp = [c for c in ["customer_id","segment","recency","frequency","monetary",
                         "r_score","f_score","m_score","top_category","avg_order_value"]
            if c in filtered.columns]
    tdf  = filtered[disp].copy()

    # Replace any remaining nulls in display table
    tdf = tdf.fillna({"recency":0,"frequency":0,"monetary":0,
                       "r_score":0,"f_score":0,"m_score":0,"avg_order_value":0})
    tdf = tdf.fillna("")
    tdf.columns = [c.replace("_"," ").title() for c in disp]

    if search_id:
        tdf = tdf[tdf["Customer Id"].str.contains(search_id.upper(),na=False)]
    if seg_filter != "All":
        tdf = tdf[tdf["Segment"] == seg_filter]
    sc = sort_by.replace("_"," ").title()
    if sc in tdf.columns:
        tdf = tdf.sort_values(sc,ascending=False)

    st.dataframe(tdf.head(500),use_container_width=True,hide_index=True)
    st.caption(f"Showing top 500 of {len(tdf):,} customers")


# ================================================================
# TAB 4 — RECOMMENDATIONS
# ================================================================
with tab4:
    st.markdown('<div class="section-title">Product recommendation engine</div>', unsafe_allow_html=True)
    col_r1,col_r2 = st.columns(2)

    with col_r1:
        if not recs.empty:
            cid = st.selectbox("Select a customer",
                               options=recs["customer_id"].unique()[:100])
            cr  = recs[recs["customer_id"]==cid]
            if not cr.empty:
                st.markdown(f"**Top recommendations for {cid}:**")
                for i in range(1,6):
                    cn  = f"rec_{i}"
                    if cn in cr.columns:
                        val = safe_str(cr.iloc[0][cn])
                        if val:
                            st.markdown(
                                f'<div style="background:#F0F7FF;border-left:3px solid #0071CE;'
                                f'padding:8px 12px;border-radius:0 6px 6px 0;'
                                f'margin-bottom:6px;font-size:13px">🛒 {val}</div>',
                                unsafe_allow_html=True
                            )
        else:
            st.info("Upload recommendations.csv to see product recommendations.")

    with col_r2:
        if not rules.empty:
            st.markdown("**Frequently bought together:**")
            for _,row in rules.head(10).iterrows():
                p1   = safe_str(row["product_1"])
                p2   = safe_str(row["product_2"])
                conf = safe_float(row["confidence"])
                if p1 and p2:
                    st.markdown(
                        f'<div style="background:#F8F9FA;border:1px solid #e0e0e0;'
                        f'padding:8px 12px;border-radius:6px;margin-bottom:6px;font-size:12px">'
                        f'🛍 <strong>{p1[:35]}</strong>'
                        f'<span style="color:#0071CE"> → </span>'
                        f'🛍 <strong>{p2[:35]}</strong>'
                        f'<span style="float:right;color:#1D9E75;font-weight:600">'
                        f'{conf:.0%} confidence</span></div>',
                        unsafe_allow_html=True
                    )
        else:
            st.info("Upload association_rules.csv to see basket analysis.")


# ================================================================
# TAB 5 — RECIPES  (with YouTube links + no null values)
# ================================================================
with tab5:
    st.markdown('<div class="section-title">Recipe matching engine</div>', unsafe_allow_html=True)

    if not recipes.empty:
        rc1,rc2 = st.columns([1,2])

        with rc1:
            rcid = st.selectbox(
                "Select customer",
                options=recipes["customer_id"].unique()[:100]
            )
            minp = st.slider("Minimum match %", 0, 100, 20)
            st.markdown("---")
            st.markdown("""
            <div style="font-size:11px;color:#666;line-height:1.7">
                <strong>Match % explained:</strong><br>
                🟢 70%+ = Cook it tonight<br>
                🟡 40–70% = Almost there<br>
                🔵 Under 40% = Few ingredients match
            </div>""", unsafe_allow_html=True)

        with rc2:
            cr2 = recipes[
                (recipes["customer_id"] == rcid) &
                (recipes["match_pct"] >= minp)
            ].sort_values("match_pct", ascending=False)

            if cr2.empty:
                st.info("No recipes found above the minimum match threshold. Try lowering the slider.")
            else:
                for _, row in cr2.iterrows():
                    pct        = safe_float(row["match_pct"])
                    name       = safe_str(row["recipe_name"], "Unknown Recipe")
                    have       = safe_str(row["have_items"])
                    need       = safe_str(row["need_items"])
                    mins       = int(safe_float(row["minutes"], 30))
                    yt_url     = safe_str(row.get("youtube_url",""), youtube_url(name))
                    badge_col  = "#1D9E75" if pct>=70 else "#EF9F27" if pct>=40 else "#185FA5"

                    # Have / Need display — skip if empty
                    have_html = (
                        f'<div style="font-size:11px;color:#1D9E75;margin-top:5px">'
                        f'✓ Have: {have}</div>'
                    ) if have else ""

                    need_html = (
                        f'<div style="font-size:11px;color:#E24B4A;margin-top:3px">'
                        f'+ Still need: {need}</div>'
                    ) if need else (
                        '<div style="font-size:11px;color:#1D9E75;margin-top:3px">'
                        '✓ You have everything!</div>'
                    )

                    st.markdown(f"""
                    <div class="recipe-card">
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                            <span style="font-size:22px">🍳</span>
                            <strong style="font-size:14px;color:#041E42">{name}</strong>
                            <span style="margin-left:auto;background:{badge_col};color:white;
                                         padding:3px 12px;border-radius:12px;
                                         font-size:11px;font-weight:600">
                                {pct:.0f}% match
                            </span>
                            <span style="font-size:11px;color:#888">⏱ {mins} min</span>
                        </div>
                        {have_html}
                        {need_html}
                        <a href="{yt_url}" target="_blank" class="yt-btn">
                            ▶ Watch on YouTube
                        </a>
                    </div>""", unsafe_allow_html=True)

    else:
        st.info("Upload recipe_matches.csv to see recipe suggestions.")
        st.markdown("""
        **How recipes are matched:**
        1. We look at each customer's top purchased grocery items
        2. We compare those items against 230,000+ real recipes
        3. Recipes are ranked by how many ingredients the customer already has
        4. Clicking 'Watch on YouTube' searches for a video of that recipe
        """)


# ── FOOTER ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#888;font-size:11px;padding:8px 0">'
    'SmartCart — Walmart Grocery RFM Analytics · Project 2024 · '
    'Built with Python · Streamlit · Plotly'
    '</div>',
    unsafe_allow_html=True
)
