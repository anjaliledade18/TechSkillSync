import re
from bs4 import BeautifulSoup
from collections import Counter
from difflib import get_close_matches
import spacy

#Lightweight NLP pipeline (disable parsing/NER for speed)
light_preproces_nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

def preprocess_job_text(text: str, lemmatize: bool = True) -> str:
    if not isinstance(text, str):
        return ""

    print("\nRaw job text sample:", text[:200], "...\n")

    text = BeautifulSoup(text, "html.parser").get_text()
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", '', text)
    text = re.sub(r"[^a-z\s]", ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    doc = light_preproces_nlp(text)
    tokens = [
        token.lemma_ if lemmatize else token.text
        for token in doc
        if not token.is_stop and not token.is_punct and token.is_alpha
    ]

    cleaned = " ".join(tokens)
    print("Preprocessed text sample:", cleaned[:200], "...\n")
    return cleaned


def extract_skills_from_text(text: str, known_skills: list) -> list:
    words = text.split()
    print("\nExtracting skills from text...")
    print(f"Total words: {len(words)}")
    print(f"Checking for 'python' presence: {'python' in words}")
    print(f"Sample words: {words[:50]}...\n")

    skill_matches = []
    missed_skills = []

    for skill in known_skills:
        skill_tokens = skill.split()

        if all(token in words for token in skill_tokens):
            skill_matches.append(skill)
        else:
            # Fuzzy match fallback
            if get_close_matches(skill, words, n=1, cutoff=0.85):
                skill_matches.append(skill)
            else:
                missed_skills.append(skill)


    print(f"\nMatched skills (top 20): {skill_matches[:20]}")
    return sorted(set(skill_matches))  # deduplicate
