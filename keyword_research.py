"""
Keyword Research Module
Provides comprehensive keyword analysis, clustering, and insights for SEO optimization.
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
import re
from collections import Counter
import math


# ---------- Keyword Extraction & Analysis ----------
def extract_keywords_from_text(text: str, min_length: int = 2) -> List[str]:
    """
    Extract individual words from text, filtering out common stopwords.
    Returns a list of cleaned keywords.
    """
    stopwords = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "he", "in", "is", "it", "its", "of", "on", "or", "that",
        "the", "to", "was", "will", "with", "the", "this", "but", "not",
        "you", "all", "can", "her", "what", "which", "who", "am", "have",
        "if", "me", "my", "these", "those", "your", "about", "could", "does"
    }
    
    # Convert to lowercase and split
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter stopwords and short words
    keywords = [w for w in words if w not in stopwords and len(w) >= min_length]
    
    return keywords


def analyze_keyword_frequency(keywords: List[str], top_n: int = 20) -> pd.DataFrame:
    """
    Analyze keyword frequency and return top keywords with counts and percentages.
    """
    if not keywords:
        return pd.DataFrame()
    
    counter = Counter(keywords)
    total = len(keywords)
    
    data = []
    for keyword, count in counter.most_common(top_n):
        percentage = (count / total) * 100
        data.append({
            "Keyword": keyword,
            "Frequency": count,
            "Percentage": round(percentage, 2)
        })
    
    return pd.DataFrame(data)


def generate_keyword_variations(keyword: str) -> List[str]:
    """
    Generate common keyword variations (singular, plural, question forms, etc.)
    """
    variations = [keyword]
    
    # Add plural form
    if not keyword.endswith('s'):
        variations.append(keyword + 's')
    
    # Add question forms
    variations.extend([
        f"what is {keyword}",
        f"how to {keyword}",
        f"best {keyword}",
        f"{keyword} tips",
        f"{keyword} guide",
        f"{keyword} tutorial",
        f"{keyword} tools",
    ])
    
    return variations


def estimate_keyword_difficulty(keyword: str, keyword_frequency: int, total_keywords: int) -> Dict[str, Any]:
    """
    Estimate keyword difficulty based on frequency and characteristics.
    Returns a difficulty assessment (Easy, Medium, Hard).
    """
    # Base difficulty from frequency (less frequent = harder)
    frequency_ratio = keyword_frequency / total_keywords if total_keywords > 0 else 0
    
    # Length multiplier (longer = easier to rank)
    word_count = len(keyword.split())
    length_multiplier = word_count * 0.1
    
    # Calculate difficulty score (0-100)
    difficulty_score = max(0, min(100, (1 - frequency_ratio) * 100 - length_multiplier * 10))
    
    # Determine difficulty level
    if difficulty_score < 30:
        level = "Easy"
        color = "green"
    elif difficulty_score < 60:
        level = "Medium"
        color = "yellow"
    else:
        level = "Hard"
        color = "red"
    
    return {
        "keyword": keyword,
        "difficulty_score": round(difficulty_score, 1),
        "level": level,
        "color": color,
        "word_count": word_count,
        "frequency_ratio": round(frequency_ratio, 4)
    }


# ---------- Keyword Clustering ----------
def cluster_related_keywords(keywords: List[str], similarity_threshold: float = 0.5) -> Dict[str, List[str]]:
    """
    Cluster keywords based on string similarity.
    Returns a dictionary with cluster leaders and their related keywords.
    """
    if not keywords:
        return {}
    
    # Simple clustering based on common substrings
    clusters = {}
    used = set()
    
    for keyword in sorted(keywords):
        if keyword in used:
            continue
        
        cluster = [keyword]
        used.add(keyword)
        
        # Find similar keywords
        for other in keywords:
            if other not in used and other != keyword:
                # Calculate Jaccard similarity of characters
                chars_key = set(keyword)
                chars_other = set(other)
                
                if chars_key and chars_other:
                    similarity = len(chars_key & chars_other) / len(chars_key | chars_other)
                    
                    if similarity >= similarity_threshold:
                        cluster.append(other)
                        used.add(other)
        
        if len(cluster) > 1:  # Only keep clusters with multiple items
            clusters[keyword] = cluster
    
    return clusters


# ---------- Keyword Intent Detection ----------
def categorize_keyword_intent(keyword: str) -> str:
    """
    Categorize keyword search intent: Informational, Navigational, or Transactional
    """
    keyword_lower = keyword.lower()
    
    # Informational indicators
    informational_terms = {
        "what", "how", "why", "when", "where", "guide", "tutorial", "tips",
        "best", "top", "learn", "understand", "explain", "definition", "vs",
        "comparison", "review", "article", "blog", "news"
    }
    
    # Transactional indicators
    transactional_terms = {
        "buy", "price", "coupon", "discount", "order", "shop", "sale",
        "deal", "offer", "purchase", "checkout", "cart", "cost", "fee"
    }
    
    # Navigational indicators
    navigational_terms = {
        "login", "signin", "sign up", "register", "facebook", "twitter",
        "instagram", "youtube", "app", "download", "official"
    }
    
    # Check for keywords
    for term in informational_terms:
        if term in keyword_lower:
            return "Informational"
    
    for term in transactional_terms:
        if term in keyword_lower:
            return "Transactional"
    
    for term in navigational_terms:
        if term in keyword_lower:
            return "Navigational"
    
    return "Mixed"


def analyze_keyword_intent_distribution(keywords: List[str]) -> pd.DataFrame:
    """
    Analyze the distribution of search intents across keywords.
    """
    intent_counts = {}
    keyword_intents = []
    
    for keyword in keywords:
        intent = categorize_keyword_intent(keyword)
        keyword_intents.append({"Keyword": keyword, "Intent": intent})
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    # Create summary dataframe
    summary_data = [
        {"Intent": intent, "Count": count, "Percentage": round((count / len(keywords)) * 100, 1)}
        for intent, count in intent_counts.items()
    ]
    
    return pd.DataFrame(keyword_intents), pd.DataFrame(summary_data)


# ---------- Keyword Opportunity Scoring ----------
def calculate_keyword_opportunity_score(
    keyword: str,
    frequency: int,
    total_keywords: int,
    current_rankings: int = 0
) -> Dict[str, Any]:
    """
    Calculate an opportunity score for a keyword (0-100).
    Higher scores = better optimization opportunities.
    """
    # Frequency score (how relevant is it to your site?)
    frequency_score = min(100, (frequency / total_keywords * 100) * 2) if total_keywords > 0 else 0
    
    # Length score (longer phrases often have better conversion)
    word_count = len(keyword.split())
    length_score = min(100, word_count * 15)
    
    # Already ranking adjustment (if already ranking, lower opportunity)
    ranking_penalty = current_rankings * 20
    
    # Combine scores with weights
    opportunity_score = (frequency_score * 0.4 + length_score * 0.4 - ranking_penalty * 0.2)
    opportunity_score = max(0, min(100, opportunity_score))
    
    return {
        "keyword": keyword,
        "opportunity_score": round(opportunity_score, 1),
        "frequency_component": round(frequency_score, 1),
        "length_component": round(length_score, 1),
        "rank_penalty": ranking_penalty,
        "priority": "High" if opportunity_score >= 70 else "Medium" if opportunity_score >= 40 else "Low"
    }


# ---------- Keyword Research Report Generation ----------
def generate_keyword_research_report(
    keywords: List[str],
    top_n: int = 50
) -> Dict[str, Any]:
    """
    Generate a comprehensive keyword research report.
    """
    if not keywords:
        return {
            "error": "No keywords provided",
            "total_keywords": 0
        }
    
    total_keywords = len(keywords)
    
    # Frequency analysis
    frequency_df = analyze_keyword_frequency(keywords, top_n=top_n)
    
    # Intent analysis
    intent_keywords_df, intent_summary_df = analyze_keyword_intent_distribution(
        frequency_df["Keyword"].tolist() if not frequency_df.empty else []
    )
    
    # Opportunity scoring
    opportunities = []
    for _, row in frequency_df.iterrows():
        score = calculate_keyword_opportunity_score(
            row["Keyword"],
            int(row["Frequency"]),
            total_keywords
        )
        opportunities.append(score)
    
    opportunities_df = pd.DataFrame(opportunities).sort_values("opportunity_score", ascending=False)
    
    # Clustering
    top_keywords = frequency_df["Keyword"].tolist() if not frequency_df.empty else []
    clusters = cluster_related_keywords(top_keywords)
    
    return {
        "total_keywords": total_keywords,
        "unique_keywords": len(set(keywords)),
        "frequency_analysis": frequency_df,
        "intent_analysis": intent_keywords_df,
        "intent_summary": intent_summary_df,
        "opportunity_analysis": opportunities_df,
        "clusters": clusters,
        "top_opportunity_keywords": opportunities_df.head(10) if not opportunities_df.empty else pd.DataFrame()
    }


# ---------- Streamlit UI Helper ----------
def render_streamlit_keyword_research_ui(st, keywords: List[str]):
    """
    Renders an interactive Streamlit UI for comprehensive keyword research.
    """
    st.subheader("🔍 Keyword Research Tool")
    st.markdown("Discover high-value keywords and optimization opportunities with TF-IDF analysis.")
    
    if not keywords:
        st.warning("⚠️ No keywords available for analysis. Run a crawl first.")
        return
    
    # Generate report
    report = generate_keyword_research_report(keywords, top_n=50)
    
    if "error" in report:
        st.error(f"❌ {report['error']}")
        return
    
    # Summary metrics
    st.markdown("**Research Summary**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Keywords Found", report["total_keywords"])
    with col2:
        st.metric("Unique Keywords", report["unique_keywords"])
    with col3:
        if not report["intent_summary"].empty:
            dominant_intent = report["intent_summary"].loc[report["intent_summary"]["Count"].idxmax(), "Intent"]
            st.metric("Dominant Intent", dominant_intent)
    with col4:
        st.metric("Clusters Identified", len(report["clusters"]))
    
    st.markdown("---")
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Frequency", 
        "Search Intent", 
        "Opportunities", 
        "Clusters",
        "Variations"
    ])
    
    with tab1:
        st.markdown("**Top Keywords by Frequency**")
        st.markdown("Keywords most frequently mentioned across your site content.")
        if not report["frequency_analysis"].empty:
            st.dataframe(report["frequency_analysis"], use_container_width=True)
        else:
            st.info("No frequency data available.")
    
    with tab2:
        st.markdown("**Search Intent Analysis**")
        st.markdown("Understand the type of search intent for each keyword.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            if not report["intent_analysis"].empty:
                st.dataframe(report["intent_analysis"], use_container_width=True, height=300)
        with col2:
            st.markdown("**Intent Distribution**")
            if not report["intent_summary"].empty:
                intent_chart = report["intent_summary"].set_index("Intent")["Count"]
                st.bar_chart(intent_chart)
    
    with tab3:
        st.markdown("**Keyword Opportunity Scores**")
        st.markdown("Ranked by optimization potential - higher scores = better opportunities.")
        
        if not report["opportunity_analysis"].empty:
            st.dataframe(
                report["opportunity_analysis"][["keyword", "opportunity_score", "priority"]],
                use_container_width=True
            )
            
            # Top opportunities highlight
            st.markdown("**🎯 Top Opportunities to Target**")
            top_opps = report["top_opportunity_keywords"]
            if not top_opps.empty:
                for idx, row in top_opps.head(5).iterrows():
                    priority_emoji = "🔴" if row["priority"] == "High" else "🟡" if row["priority"] == "Medium" else "🟢"
                    st.write(f"{priority_emoji} **{row['keyword']}** - Score: {row['opportunity_score']}")
        else:
            st.info("No opportunity data available.")
    
    with tab4:
        st.markdown("**Related Keyword Clusters**")
        st.markdown("Groups of similar keywords that target the same topic.")
        
        if report["clusters"]:
            for leader, related in list(report["clusters"].items())[:10]:
                with st.expander(f"📍 {leader} ({len(related)} keywords)"):
                    st.write("**Related keywords:**")
                    st.write(", ".join(related))
        else:
            st.info("No keyword clusters found. Try running analysis on more data.")
    
    with tab5:
        st.markdown("**Keyword Variations & Expansions**")
        st.markdown("Generate variations for better keyword coverage.")
        
        if not report["frequency_analysis"].empty:
            selected_keyword = st.selectbox(
                "Select a keyword to expand:",
                options=report["frequency_analysis"]["Keyword"].tolist(),
                key="keyword_expansion"
            )
            
            if selected_keyword:
                variations = generate_keyword_variations(selected_keyword)
                st.markdown(f"**Variations for:** `{selected_keyword}`")
                
                var_df = pd.DataFrame({
                    "Variation": variations,
                    "Type": ["Original"] + ["Plural", "Question", "Question", "Question", "Question", "Question", "Question"]
                })
                st.dataframe(var_df, use_container_width=True)
    
    st.markdown("---")
    
    # Export functionality
    st.markdown("**📥 Export Keyword Research**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not report["frequency_analysis"].empty:
            csv = report["frequency_analysis"].to_csv(index=False)
            st.download_button(
                "📄 Frequency Data",
                data=csv,
                file_name="keywords_frequency.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if not report["opportunity_analysis"].empty:
            csv = report["opportunity_analysis"].to_csv(index=False)
            st.download_button(
                "📊 Opportunities",
                data=csv,
                file_name="keywords_opportunities.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        if not report["intent_analysis"].empty:
            csv = report["intent_analysis"].to_csv(index=False)
            st.download_button(
                "🎯 Intent Analysis",
                data=csv,
                file_name="keywords_intent.csv",
                mime="text/csv",
                use_container_width=True
            )
