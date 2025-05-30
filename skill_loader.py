import pandas as pd
import re

#=== Preprocessing helpers ===
def preprocess(text):
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s*\([^)]*\)', '', text).strip()
    return text

def remove_bracketed_words(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r'\s*\([^)]*\)', '', text).strip()

#=== Main loader ===
def load_known_skills(esco_path: str, tool_map_path: str) -> list:
    """
    Load and clean skills from ESCO taxonomy and tool mapping files.

    Args:
        esco_path (str): Path to the ESCO taxonomy CSV file
        tool_map_path (str): Path to the tool mapping CSV file

    Returns:
        list: Cleaned, deduplicated set of known skills
    """
    esco_df = pd.read_csv(esco_path)
    tool_df = pd.read_csv(tool_map_path)

    #Clean and explode ESCO skill columns
    skill_cols = [
        "Essential Skills (Skill)", "Essential Skills (Knowledge)",
        "Optional Skills (Skill)", "Optional Skills (Knowledge)"
    ]
    esco_df[skill_cols] = esco_df[skill_cols].fillna("")
    for col in skill_cols:
        esco_df[col] = esco_df[col].apply(lambda x: x.split(", ") if isinstance(x, str) else [])
        esco_df = esco_df.explode(col)

    #Rename and preprocess
    esco_df = esco_df.rename(columns={
        "Essential Skills (Skill)": "Essential Skill",
        "Essential Skills (Knowledge)": "Essential Knowledge",
        "Optional Skills (Skill)": "Optional Skill",
        "Optional Skills (Knowledge)": "Optional Knowledge"
    })

    #Preprocess each skill list
    for col in ["Essential Skill", "Essential Knowledge", "Optional Skill", "Optional Knowledge"]:
        esco_df[col] = esco_df[col].apply(
            lambda x: preprocess(remove_bracketed_words(x)) if isinstance(x, str) else ""
        )

    #Combine all ESCO skills
    all_esco_skills = (
        esco_df["Essential Skill"].dropna().tolist() +
        esco_df["Essential Knowledge"].dropna().tolist() +
        esco_df["Optional Skill"].dropna().tolist() +
        esco_df["Optional Knowledge"].dropna().tolist()
    )

    #Clean tool mapping skills
    tool_df["Skill"] = tool_df["Skill"].apply(
        lambda x: preprocess(remove_bracketed_words(x)) if isinstance(x, str) else ""
    )
    tool_skills = tool_df["Skill"].dropna().tolist()

    #Combine and deduplicate
    all_skills = set(all_esco_skills + tool_skills)
    return sorted(skill for skill in all_skills if skill)
