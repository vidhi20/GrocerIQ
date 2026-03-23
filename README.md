# SmartCart

# 🛒 SmartCart — Walmart Grocery RFM Analytics & Recommendation System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-F7931E?logo=scikit-learn)
![License](https://img.shields.io/badge/License-MIT-green)

> An end-to-end data science project that segments Walmart grocery customers using RFM analysis and K-Means clustering, then delivers personalised product recommendations and recipe suggestions based on purchase history.

---

## 🌐 Live Demo

👉 **[groceriq.streamlit.app](https://groceriq.streamlit.app)**

---

## 📌 Problem Statement

Grocery retailers like Walmart serve millions of customers with vastly different shopping behaviours. Without customer segmentation, marketing campaigns are generic and ineffective. This project answers three business questions:

1. **Who are our most valuable customers?** — RFM segmentation identifies Champions, Loyal Customers, At-Risk shoppers, and more
2. **What should we recommend to each customer?** — Collaborative filtering surfaces products they are likely to buy next
3. **What can they cook with what they already buy?** — A recipe matching engine links grocery purchases to real recipes and YouTube tutorials

---

## 🎯 Features

| Feature | Description |
|---|---|
| 📊 RFM Scoring | Every customer scored 1–5 on Recency, Frequency and Monetary value |
| 👥 K-Means Clustering | Customers grouped into data-driven clusters with elbow curve + silhouette analysis |
| 🔁 Collaborative Filtering | Item-based cosine similarity recommends top 5 products per customer |
| 🛍 Basket Analysis | Apriori-style association rules surface frequently bought together items |
| 🍳 Recipe Matching | TF-IDF vectorized matching links customer baskets to 230K+ Food.com recipes |
| ▶ YouTube Integration | Every recipe card links directly to a YouTube search for that recipe |
| 📈 Interactive Dashboard | 5-tab Streamlit app with Plotly charts, filters, and customer explorer |

---

## 🗂 Project Structure

```
smartcart-rfm/
│
├── app.py                    # Main Streamlit dashboard
├── requirements.txt          # Python dependencies
│
├── data/
│   └── processed/
│       ├── rfm_segments.csv          # RFM scores + segment labels per customer
│       ├── recommendations.csv       # Top 5 product recommendations per customer
│       ├── recipe_matches.csv        # Top 3 recipe matches per customer
│       └── association_rules.csv     # Frequently bought together pairs
│
└── notebooks/
    ├── 01_data_generation.ipynb      # Generate synthetic Walmart dataset
    ├── 02_data_cleaning.ipynb        # Clean and prepare data
    ├── 03_rfm_scoring.ipynb          # Calculate R, F, M scores
    ├── 04_kmeans_clustering.ipynb    # K-Means with elbow + silhouette
    ├── 05_visualisations.ipynb       # RFM charts for dashboard
    ├── 06_basket_analysis.ipynb      # Association rules
    ├── 07_recommendations.ipynb      # Collaborative filtering
    ├── 08_recipe_matching.ipynb      # TF-IDF recipe engine
    └── 09_deployment.ipynb           # Write app.py + deploy to Streamlit
```

---

## 📊 Dashboard Tabs

### 📊 Overview
- 5 KPI cards — total customers, average spend, champions, at-risk count, average orders
- Smart alerts for at-risk customers and champion growth
- Segment distribution bar chart
- RFM scatter plot — frequency vs monetary coloured by segment
- Average spend per segment
- Top grocery category breakdown (pie chart)
- RFM heatmap — recency score vs frequency score

### 👥 Segments
- Full summary table with customer counts, average R/F/M, and total revenue per segment
- Colour-coded marketing strategy cards for all 7 segments

### 🔍 Customers
- Searchable, filterable, sortable customer table
- Shows RFM scores, segment, top category, and average order value

### 🎯 Recommendations
- Per-customer top 5 product recommendations (collaborative filtering)
- Frequently bought together product pairs (basket analysis)

### 🍳 Recipes
- Per-customer recipe cards ranked by basket match percentage
- Green / orange / blue badges showing match level
- Shows exactly which ingredients the customer already has vs still needs
- **YouTube button on every card** — one click searches for the recipe video

---

## 🧠 Methodology

### RFM Scoring
Each customer is scored 1–5 on three dimensions using quantile-based scoring:

| Metric | Definition | Score direction |
|---|---|---|
| **Recency** | Days since last purchase | Lower = better (score 5) |
| **Frequency** | Number of unique orders | Higher = better (score 5) |
| **Monetary** | Total spend across all orders | Higher = better (score 5) |

Customers are then labelled into 7 segments based on score combinations:

| Segment | Criteria | Strategy |
|---|---|---|
| Champion | R≥4, F≥4, M≥4 | Reward and retain |
| Loyal Customer | R≥3, F≥3, M≥3 | Upsell to premium |
| Potential Loyalist | R≥3, F≥2 | Convert to loyal |
| New Customer | R≥4, F≤2 | Onboard and nurture |
| At-Risk | R≤2, F≥3, M≥3 | Re-engage urgently |
| Hibernating | Other | Wake-up campaign |
| Lost | R≤2, F≤2, M≤2 | Win-back or sunset |

### K-Means Clustering
- Features scaled using `StandardScaler` to equalise R, F, M weights
- Optimal K selected using elbow curve (inertia) and silhouette score
- Final model uses K=4 clusters labelled by monetary rank

### Collaborative Filtering
- User-item purchase matrix built from top 150 products across 10,000 customers
- Product-product cosine similarity computed using `sklearn.metrics.pairwise`
- Top 5 unseen products recommended per customer

### Recipe Matching Engine
- Old approach: loop through every recipe per customer → 12+ minutes
- New approach: TF-IDF vectorized matrix multiplication → under 2 minutes
- Customer basket keywords extracted from product names (brand stopwords removed)
- All 2,000 customers matched against filtered Food.com recipes in batch mode

---

## 📦 Dataset

| Dataset | Source | Purpose |
|---|---|---|
| Walmart Grocery Transactions | Generated with Python (Jan 2023–Dec 2024) | RFM scoring, basket analysis, recommendations |
| Food.com Recipes | [Kaggle — shuyangli94](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions) | Recipe matching engine |

**Note on synthetic data:** Customer transaction data was generated using simulation-based methodology (Jordon et al., 2022) incorporating real Walmart product names, validated category pricing, and realistic purchasing frequency distributions. This approach follows established practice in retail analytics research where customer-level transaction data is legally protected under GDPR and CCPA.

> Jordon, J. et al. (2022). *Synthetic Data — what, why and how?* Royal Statistical Society / Alan Turing Institute.



## 🛠 Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.10 | Core language |
| pandas + numpy | Data manipulation |
| scikit-learn | K-Means, StandardScaler, TF-IDF, cosine similarity |
| Streamlit | Web dashboard |
| Plotly Express | Interactive charts |
| Google Colab | Notebook execution environment |

---

## 📈 Key Results

- **50,000 customers** segmented across 7 RFM groups
- **Champions (15%)** generate significantly higher average spend than Lost customers
- **K=4 clusters** confirmed by both elbow curve and silhouette score
- **Collaborative filtering** generates top-5 recommendations for 10,000 customers
- **Recipe engine** matches customer baskets to 230K+ recipes in under 2 minutes

---

## 🔮 Future Work

- Integrate real-time transaction data via Walmart Open API
- Add time-series analysis to detect seasonal purchasing trends
- Implement matrix factorisation (SVD) for improved recommendation accuracy
- Add email campaign simulation for at-risk segment re-engagement
- Extend recipe matching with nutritional scoring and dietary filters

---

## 👤 Author

**[Vidhi Parekh]**
Masters in Data Science · The University of Texas at Austin · 2025-2027

