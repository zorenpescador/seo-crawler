import re
from collections import Counter
from typing import Dict, List

from bs4 import BeautifulSoup

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "had",
    "has", "have", "he", "her", "here", "his", "i", "in", "into", "is", "it", "its",
    "me", "my", "of", "on", "or", "our", "ours", "she", "so", "that", "the", "their",
    "them", "there", "these", "they", "this", "those", "to", "was", "we", "were",
    "what", "when", "where", "which", "who", "will", "with", "would", "you", "your",
    "yours", "can", "could", "do", "does", "did", "not", "now", "than", "then", "very",
    "http", "https", "www"
}


def normalize_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    if isinstance(raw_text, str):
        text = raw_text
    else:
        text = str(raw_text)

    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _count_syllables(word: str) -> int:
    word = word.lower().strip(".!,;:()[]{}")
    if len(word) <= 3:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith(("es", "ed")) and count > 1:
        count -= 1
    return max(1, count)


def analyze_content(text: str, target_keyword: str = "") -> Dict[str, object]:
    cleaned = normalize_text(text)
    words = re.findall(r"[A-Za-z][A-Za-z'\-]+", cleaned)
    words_lower = [w.lower() for w in words]
    filtered_words = [w for w in words_lower if w not in STOP_WORDS and len(w) > 2]

    sentences = re.split(r"(?<=[.!?])\s+", cleaned) if cleaned else []
    paragraphs = [p for p in re.split(r"\n\s*\n", cleaned) if p.strip()] if cleaned else []

    word_count = len(words)
    unique_word_count = len(set(filtered_words))
    sentence_count = max(1, len([s for s in sentences if s.strip()]))
    paragraph_count = len(paragraphs)
    avg_sentence_length = round(word_count / sentence_count, 1) if word_count else 0

    syllable_count = sum(_count_syllables(w) for w in words)
    flesch_score = round(206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count), 1) if word_count else 0
    reading_time = max(1, round(word_count / 200))

    keyword_counter = Counter(filtered_words)
    top_keywords = [
        {"term": term, "count": count}
        for term, count in keyword_counter.most_common(10)
    ]

    target_keyword_normalized = target_keyword.strip().lower() if target_keyword else ""
    target_keyword_count = 0
    if target_keyword_normalized:
        target_keyword_count = sum(1 for word in words_lower if word == target_keyword_normalized)

    return {
        "cleaned_text": cleaned,
        "word_count": word_count,
        "unique_word_count": unique_word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "avg_sentence_length": avg_sentence_length,
        "reading_time_minutes": reading_time,
        "flesch_reading_ease": flesch_score,
        "top_keywords": top_keywords,
        "target_keyword": target_keyword_normalized,
        "target_keyword_count": target_keyword_count,
    }


def render_streamlit_content_analyzer_ui(st, content: str, source_name: str = "Content", target_keyword: str = ""):
    st.subheader("🧠 Content Analyzer")
    st.markdown("Analyze readability, keyword density, and structure from pasted text or crawl content.")

    if not content or not str(content).strip():
        st.info("Paste or select content to begin analysis.")
        return

    analysis = analyze_content(content, target_keyword=target_keyword)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Words", analysis["word_count"])
    with col2:
        st.metric("Unique Terms", analysis["unique_word_count"])
    with col3:
        st.metric("Reading Time", f"~{analysis['reading_time_minutes']} min")
    with col4:
        st.metric("Readability", f"{analysis['flesch_reading_ease']}")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Structure**")
        st.write({
            "Sentences": analysis["sentence_count"],
            "Paragraphs": analysis["paragraph_count"],
            "Average Sentence Length": analysis["avg_sentence_length"],
            "Source": source_name,
        })
    with col_b:
        st.markdown("**Target Keyword**")
        if analysis["target_keyword"]:
            st.write({
                "Keyword": analysis["target_keyword"],
                "Occurrences": analysis["target_keyword_count"],
            })
        else:
            st.info("Enter a target keyword to see its frequency.")

        st.markdown("**Top Keywords**")
        if analysis["top_keywords"]:
            st.dataframe(
                {
                    "Term": [item["term"] for item in analysis["top_keywords"]],
                    "Count": [item["count"] for item in analysis["top_keywords"]],
                },
                width="stretch",
            )
        else:
            st.info("No keyword terms found.")
