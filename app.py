
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
.kpi-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #0071CE;
    margin: 0;
}
.kpi-label {
    font-size: 0.75rem;
    color: #666;
    margin: 0.2rem 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #041E42;
    border-left: 4px solid #0071CE;
    padding-left: 0.7rem;
    margin: 1.2rem 0 0.8rem 0;
}
.stTabs [aria-selected="true"] {
    background-color: #0071CE !important;
    color: white !important;
    border-radius: 6px 6px 0 0;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    np.random.seed(42)
    n = 5000
    segs  = ["Champion","Loyal Customer","Potential Loyalist",
              "At-Risk","New Customer","Hibernating","Lost"]
    props = [0.15,0.20,0.18,0.20,0.12,0.10,0.05]
    cats  = ["Dairy & Eggs","Fresh Produce","Meat & Seafood",
             "Pantry & Dry Goods","Beverages","Household","Snacks & Cereal"]
    sample_rfm = pd.DataFrame({
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
    rfm    = pd.read_csv("rfm_segments.csv")    if os.path.exists("rfm_segments.csv")    else sample_rfm
    recs   = pd.read_csv("recommendations.csv") if os.path.exists("recommendations.csv") else pd.DataFrame()
    recipes= pd.read_csv("recipe_matches.csv")  if os.path.exists("recipe_matches.csv")  else pd.DataFrame()
    rules  = pd.read_csv("association_rules.csv")if os.path.exists("association_rules.csv")else pd.DataFrame()
    return rfm, recs, recipes, rules

rfm, recs, recipes, rules = load_data()

# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.title("🛒 SmartCart")
    st.caption("Walmart Grocery · RFM Analytics")
    st.markdown("---")
    st.subheader("Filters")
    all_segs = sorted(rfm["segment"].unique().tolist())
    sel_segs = st.multiselect("Segments", all_segs, default=all_segs)
    if "city" in rfm.columns:
        all_cities = sorted(rfm["city"].dropna().unique().tolist())
        sel_cities = st.multiselect("City", all_cities, default=all_cities)
    else:
        sel_cities = []
    loyalty_f = st.selectbox("Loyalty", ["All","Members Only","Non-Members"])
    st.markdown("---")
    st.caption("Masters Project · 2024")

filtered = rfm[rfm["segment"].isin(sel_segs)].copy()
if sel_cities and "city" in rfm.columns:
    filtered = filtered[filtered["city"].isin(sel_cities)]
if loyalty_f == "Members Only":
    filtered = filtered[filtered["loyalty_member"] == True]
elif loyalty_f == "Non-Members":
    filtered = filtered[filtered["loyalty_member"] == False]

# ── HEADER ───────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(90deg,#0071CE,#004F9A);
            padding:1.2rem 2rem;border-radius:10px;margin-bottom:1.5rem">
    <h1 style="color:white;font-size:1.8rem;font-weight:700;margin:0">
        🛒 SmartCart — Walmart Grocery Analytics
    </h1>
    <p style="color:#FFC220;font-size:0.9rem;margin:0.3rem 0 0">
        RFM Segmentation · Recommendations · Recipe Matching · Jan 2023–Dec 2024
    </p>
</div>""", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📊 Overview","👥 Segments","🔍 Customers",
    "🎯 Recommendations","🍳 Recipes"
])

# ── TAB 1: OVERVIEW ──────────────────────────────────────
with tab1:
    c1,c2,c3,c4,c5 = st.columns(5)
    kpis = [
        (len(filtered),               "#0071CE", "Total Customers"),
        (f"${filtered.monetary.mean():,.0f}", "#0071CE", "Avg Spend"),
        ((filtered.segment=="Champion").sum(), "#1D9E75", "Champions"),
        ((filtered.segment=="At-Risk").sum(),  "#E24B4A", "At-Risk"),
        (f"{filtered.frequency.mean():.1f}",   "#0071CE", "Avg Orders"),
    ]
    for col, (val, color, label) in zip([c1,c2,c3,c4,c5], kpis):
        with col:
            st.markdown(f"""<div class="kpi-card">
                <p class="kpi-value" style="color:{color}">{val:,}</p>
                <p class="kpi-label">{label}</p></div>""",
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    at_risk_n = (filtered.segment=="At-Risk").sum()
    champ_n   = (filtered.segment=="Champion").sum()
    st.warning(f"⚠ {at_risk_n:,} customers at risk — consider re-engagement campaign")
    st.success(f"✓ {champ_n:,} Champion customers driving highest revenue")
    st.info(f"↗ Recommendation engine ready for {len(recs):,} customers")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Segment distribution</div>', unsafe_allow_html=True)
        seg_df = filtered.segment.value_counts().reset_index()
        seg_df.columns = ["Segment","Count"]
        fig = px.bar(seg_df, x="Count", y="Segment", orientation="h",
                     color="Segment", color_discrete_map=SEG_COLORS,
                     text="Count", height=340)
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.update_layout(showlegend=False, margin=dict(l=0,r=60,t=10,b=10),
                          plot_bgcolor="white", paper_bgcolor="white",
                          yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">RFM scatter</div>', unsafe_allow_html=True)
        s = filtered.sample(min(3000,len(filtered)), random_state=42)
        fig2 = px.scatter(s, x="frequency", y="monetary", color="segment",
                          color_discrete_map=SEG_COLORS, opacity=0.5, height=340,
                          labels={"frequency":"Frequency","monetary":"Monetary ($)","segment":"Segment"})
        fig2.update_layout(margin=dict(l=0,r=0,t=10,b=10),
                           plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h",yanchor="bottom",y=1.02,font_size=9))
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="section-title">Avg spend per segment</div>', unsafe_allow_html=True)
        sp_df = filtered.groupby("segment")["monetary"].mean().reset_index()
        sp_df.columns = ["Segment","Avg Spend"]
        sp_df = sp_df.sort_values("Avg Spend")
        fig3 = px.bar(sp_df, x="Avg Spend", y="Segment", orientation="h",
                      color="Segment", color_discrete_map=SEG_COLORS,
                      text="Avg Spend", height=340)
        fig3.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig3.update_layout(showlegend=False, margin=dict(l=0,r=80,t=10,b=10),
                           plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown('<div class="section-title">Top grocery categories</div>', unsafe_allow_html=True)
        if "top_category" in filtered.columns:
            cat_df = filtered.top_category.value_counts().reset_index()
            cat_df.columns = ["Category","Count"]
            fig4 = px.pie(cat_df, values="Count", names="Category", hole=0.4,
                          height=340, color_discrete_sequence=px.colors.qualitative.Set2)
            fig4.update_layout(margin=dict(l=0,r=0,t=10,b=10), paper_bgcolor="white")
            fig4.update_traces(textinfo="percent+label", textfont_size=10)
            st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-title">RFM heatmap</div>', unsafe_allow_html=True)
    pivot = filtered.groupby(["r_score","f_score"])["monetary"].mean().unstack(fill_value=0).round(0)
    fig5  = px.imshow(pivot, color_continuous_scale="YlOrRd", text_auto=True, height=320,
                      labels=dict(x="Frequency Score →",y="Recency Score →",color="Avg Spend ($)"))
    fig5.update_layout(margin=dict(l=0,r=0,t=10,b=10), paper_bgcolor="white")
    st.plotly_chart(fig5, use_container_width=True)

# ── TAB 2: SEGMENTS ──────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">Segment summary table</div>', unsafe_allow_html=True)
    seg_tbl = filtered.groupby("segment").agg(
        Customers    =("customer_id","count"),
        Avg_Recency  =("recency","mean"),
        Avg_Orders   =("frequency","mean"),
        Avg_Spend    =("monetary","mean"),
        Total_Revenue=("monetary","sum"),
    ).round(1).reset_index()
    seg_tbl["% of Base"] = (seg_tbl["Customers"]/seg_tbl["Customers"].sum()*100).round(1)
    seg_tbl = seg_tbl.sort_values("Total_Revenue", ascending=False)
    st.dataframe(seg_tbl, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Marketing strategies</div>', unsafe_allow_html=True)
    STRAT = {
        "Champion":           ("🏆","#1D9E75","Reward & retain — exclusive loyalty rewards, early access, bundle discounts"),
        "Loyal Customer":     ("💙","#185FA5","Upsell — introduce premium lines, bundle offers, buy 2 get 1 promotions"),
        "Potential Loyalist": ("⭐","#7F77DD","Convert — personalised recs, loyalty programme sign-up incentive"),
        "At-Risk":            ("⚠️","#EF9F27","Re-engage — win-back email with coupon for their top category"),
        "New Customer":       ("🌱","#5DCAA5","Onboard — welcome discount, popular bundles, recipe ideas"),
        "Hibernating":        ("😴","#888780","Wake up — last chance email with 20% discount on top category"),
        "Lost":               ("❌","#E24B4A","Win-back — maximum discount offer, sunset if no response in 30 days"),
    }
    cols2 = st.columns(2)
    for i, (seg, (icon, color, desc)) in enumerate(STRAT.items()):
        cnt = len(filtered[filtered["segment"]==seg])
        with cols2[i%2]:
            st.markdown(f"""<div style="border:1px solid {color}33;border-left:4px solid {color};
                border-radius:8px;padding:10px 14px;margin-bottom:8px;background:{color}0a">
                <span style="font-size:14px">{icon}</span>
                <strong style="color:{color};margin-left:6px">{seg}</strong>
                <span style="float:right;font-size:11px;color:#666">{cnt:,} customers</span>
                <div style="font-size:11px;color:#444;margin-top:4px;line-height:1.5">{desc}</div>
            </div>""", unsafe_allow_html=True)

# ── TAB 3: CUSTOMERS ─────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">Customer explorer</div>', unsafe_allow_html=True)
    c_s1, c_s2, c_s3 = st.columns(3)
    with c_s1: search = st.text_input("Search Customer ID", placeholder="WMT_00001")
    with c_s2: seg_f  = st.selectbox("Segment", ["All"]+all_segs)
    with c_s3: sort_c = st.selectbox("Sort by", ["monetary","frequency","recency"])

    disp = ["customer_id","segment","recency","frequency","monetary",
            "r_score","f_score","m_score","top_category","avg_order_value"]
    disp = [c for c in disp if c in filtered.columns]
    t_df = filtered[disp].copy()
    t_df.columns = [c.replace("_"," ").title() for c in disp]
    if search: t_df = t_df[t_df["Customer Id"].str.contains(search.upper(),na=False)]
    if seg_f != "All": t_df = t_df[t_df["Segment"]==seg_f]
    sc = sort_c.replace("_"," ").title()
    if sc in t_df.columns: t_df = t_df.sort_values(sc, ascending=False)
    st.dataframe(t_df.head(500), use_container_width=True, hide_index=True)
    st.caption(f"Showing top 500 of {len(t_df):,} customers")

# ── TAB 4: RECOMMENDATIONS ───────────────────────────────
with tab4:
    st.markdown('<div class="section-title">Product recommendation engine</div>', unsafe_allow_html=True)
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if not recs.empty:
            cid = st.selectbox("Select customer", recs["customer_id"].unique()[:100])
            c_recs = recs[recs["customer_id"]==cid]
            if not c_recs.empty:
                st.markdown(f"**Recommendations for {cid}:**")
                for i in range(1,6):
                    col_n = f"rec_{i}"
                    if col_n in c_recs.columns:
                        val = c_recs.iloc[0][col_n]
                        if val and str(val).strip():
                            st.markdown(f"""<div style="background:#F0F7FF;border-left:3px solid #0071CE;
                                padding:8px 12px;border-radius:0 6px 6px 0;margin-bottom:6px;font-size:13px">
                                🛒 {val}</div>""", unsafe_allow_html=True)
        else:
            st.info("Generate recommendations.csv by running Cell 8 in Colab")
    with col_r2:
        if not rules.empty:
            st.markdown("**Frequently bought together:**")
            for _,row in rules.head(10).iterrows():
                st.markdown(f"""<div style="background:#F8F9FA;border:1px solid #e0e0e0;
                    padding:8px 12px;border-radius:6px;margin-bottom:6px;font-size:12px">
                    🛍 <strong>{str(row["product_1"])[:35]}</strong>
                    <span style="color:#0071CE"> → </span>
                    🛍 <strong>{str(row["product_2"])[:35]}</strong>
                    <span style="float:right;color:#1D9E75;font-weight:600">
                        {row["confidence"]:.0%}</span></div>""", unsafe_allow_html=True)
        else:
            st.info("Generate association_rules.csv by running Cell 7 in Colab")

# ── TAB 5: RECIPES ────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">Recipe matching engine</div>', unsafe_allow_html=True)
    if not recipes.empty:
        r_c1, r_c2 = st.columns([1,2])
        with r_c1:
            r_cid   = st.selectbox("Customer", recipes["customer_id"].unique()[:100])
            min_pct = st.slider("Min match %", 0, 100, 20)
        with r_c2:
            c_rec = recipes[
                (recipes["customer_id"]==r_cid) &
                (recipes["match_pct"]>=min_pct)
            ].sort_values("match_pct", ascending=False)
            if not c_rec.empty:
                for _,row in c_rec.iterrows():
                    pct   = row["match_pct"]
                    color = "#1D9E75" if pct>=70 else "#EF9F27" if pct>=40 else "#185FA5"
                    st.markdown(f"""<div style="border:1px solid #e0e0e0;border-radius:10px;
                        padding:12px 16px;margin-bottom:10px">
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                            <span style="font-size:20px">🍳</span>
                            <strong style="font-size:14px">{row["recipe_name"]}</strong>
                            <span style="margin-left:auto;background:{color};color:white;
                                         padding:2px 10px;border-radius:12px;font-size:11px;
                                         font-weight:600">{pct:.0f}% match</span>
                            <span style="font-size:11px;color:#666">⏱ {row["minutes"]} min</span>
                        </div>
                        <div style="font-size:11px">
                            <span style="color:#1D9E75">✓ Have: {str(row["have_items"])[:100]}</span><br>
                            <span style="color:#E24B4A">+ Need: {str(row["need_items"])[:100]}</span>
                        </div></div>""", unsafe_allow_html=True)
            else:
                st.info("No recipes above the minimum match threshold")
    else:
        st.info("Generate recipe_matches.csv by running Cell 9 in Colab")

st.markdown("---")
st.markdown("""<div style="text-align:center;color:#888;font-size:11px;padding:8px">
    SmartCart — Walmart Grocery RFM Analytics · Masters Project 2024 · Streamlit + Plotly
</div>""", unsafe_allow_html=True)
