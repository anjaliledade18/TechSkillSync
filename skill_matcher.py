import pandas as pd
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

#=== Basic Clean Preprocessing ===
def preprocess(text):
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    cleaned_text = re.sub(r'\s*\([^)]*\)', '', text).strip()

    return cleaned_text

def remove_bracketed_words(text):
    if not isinstance(text, str):
        return ""
    
    #Remove all content inside brackets (including brackets)
    cleaned_text = re.sub(r'\s*\([^)]*\)', '', text).strip()
    
    return cleaned_text


#=== Load ESCO dataset ===
esco_df = pd.read_csv("data/ESCO skill taxonomy dataset.csv")
skill_cols = [
    "Essential Skills (Skill)", "Essential Skills (Knowledge)",
    "Optional Skills (Skill)", "Optional Skills (Knowledge)"
]
esco_df[skill_cols] = esco_df[skill_cols].fillna("")
for col in skill_cols:
    esco_df[col] = esco_df[col].apply(lambda x: x.split(", ") if isinstance(x, str) else [])
    esco_df = esco_df.explode(col)

esco_df = esco_df.rename(columns={
    "Occupation Title": "Job Role",
    "ESCO Code": "ESCO Code",
    "Description": "Job Description",
    "Alternative Labels": "Alternative Titles",
    "Essential Skills (Skill)": "Essential Skill",
    "Essential Skills (Knowledge)": "Essential Knowledge",
    "Optional Skills (Skill)": "Optional Skill",
    "Optional Skills (Knowledge)": "Optional Knowledge"
})

columns_to_preprocess = ["Essential Skill", "Essential Knowledge", "Optional Skill", "Optional Knowledge"]
for col in columns_to_preprocess:
    esco_df[col] = esco_df[col].apply(preprocess)

#=== Create skill sets ===
all_esco_skills = set(
    esco_df["Essential Skill"].dropna().tolist() +
    esco_df["Essential Knowledge"].dropna().tolist() +
    esco_df["Optional Skill"].dropna().tolist() +
    esco_df["Optional Knowledge"].dropna().tolist()
)

#=== Load Tool Mapping ===
tool_df = pd.read_csv("data/tool_mapping.csv")
tool_df["Skill"] = tool_df["Skill"].apply(preprocess)
tool_df["Mapped Category"] = tool_df["Mapped Category"].apply(preprocess)

tool_skills = tool_df["Skill"].tolist()
tool_to_category_map = tool_df.set_index("Skill")["Mapped Category"].to_dict()

#=== Embedding setup ===
model = SentenceTransformer('all-MiniLM-L6-v2')
esco_skills = list(all_esco_skills)
esco_embeddings = model.encode(esco_skills)
tool_embeddings = model.encode(tool_skills)

#=== Cosine match fallback to tool category ===
def match_user_skill_to_tool_category(user_skill, threshold=0.7):
    user_cleaned = preprocess(user_skill)
    user_embedding = model.encode([user_cleaned])[0]
    sims = cosine_similarity([user_embedding], tool_embeddings)[0]
    best_idx = sims.argmax()
    best_score = float(sims[best_idx])
    best_tool = tool_skills[best_idx]
    if best_score >= threshold:
        return tool_to_category_map.get(best_tool), best_score
    return None, None

#=== Match user skill to ESCO or fallback category ===
def match_user_skills(user_skills, threshold=0.7, top_k=1):
    matched_skills = []
    cleaned_user_skills = [preprocess(skill) for skill in user_skills]
    user_embeddings = model.encode(cleaned_user_skills)
    records = []
    general_categories = []
    for i, user_emb in enumerate(user_embeddings):
        sims = cosine_similarity([user_emb], esco_embeddings)[0]
        top_indices = sims.argsort()[::-1][:top_k]
        best_idx = top_indices[0]
        best_score = round(float(sims[best_idx]), 3)
        original_skill = user_skills[i]
        tool_category, score = match_user_skill_to_tool_category(original_skill, threshold)

        if best_score >= threshold:
            matched_skill = esco_skills[best_idx]
        else:
            matched_skill = tool_category if tool_category else "No Match"
            if score:
                best_score = round(score, 3)

        matched_skills.append(matched_skill)
        general_categories.append(tool_category if tool_category else "No Match")
        records.append({
            "User Skill": original_skill,
            "Matched Skill": matched_skill,
            "Cosine Similarity": best_score
        })

    df = pd.DataFrame(records)
    print("\nMatching Results")
    print(df.to_markdown(index=False))
    return df, matched_skills, general_categories

#=== Match Matched Skills to Jobs ===
def match_skills_job(matched_skills):
    matched_skills = set(preprocess(skill) for skill in matched_skills if skill != "No Match")
    if not matched_skills:
        return pd.DataFrame(columns=["Job Role", "Matched Skills Count", "Alternative Titles"])

    esco_df["All Skills"] = (
        esco_df["Essential Skill"].fillna("").astype(str) + ", " +
        esco_df["Essential Knowledge"].fillna("").astype(str) + ", " +
        esco_df["Optional Skill"].fillna("").astype(str) + ", " +
        esco_df["Optional Knowledge"].fillna("").astype(str)
    )

    job_skills_df = (
        esco_df.groupby(["Job Role", "Job Description"])["All Skills"]
        .apply(lambda skills: set(
            s.strip().lower() for line in skills for s in line.split(",") if s.strip()
        ))
        .reset_index(name="All Skills Set")
    )

    #Match count
    job_skills_df["Matched Skills Count"] = job_skills_df["All Skills Set"].apply(
        lambda skills: len(matched_skills.intersection(skills))
    )

    #Only jobs with > 0 matches
    job_skills_df = job_skills_df[job_skills_df["Matched Skills Count"] > 0]

    #Get top matches
    max_count = job_skills_df["Matched Skills Count"].max()
    top_jobs = job_skills_df[job_skills_df["Matched Skills Count"] == max_count]

    #Merge in Alternative Titles
    alt_titles_df = esco_df[["Job Role", "Alternative Titles"]].drop_duplicates()
    top_jobs = top_jobs.merge(alt_titles_df, on="Job Role", how="left")

    #Format top 3 alt titles
    def format_alt_titles(text):
        if pd.isna(text): return ""
        titles = [t.strip() for t in text.split(",") if t.strip()]
        return ", ".join(titles[:3])  # show only first 3

    top_jobs["Alternative Titles"] = top_jobs["Alternative Titles"].apply(format_alt_titles)

    return top_jobs[["Job Role", "Matched Skills Count", "Alternative Titles"]]

#Load the dataset
file_path = "data/ESCO skill taxonomy dataset.csv"
df = pd.read_csv(file_path)

df = df[["Occupation Title", "Description", "Alternative Labels","Essential Skills (Knowledge)", "Optional Skills (Knowledge)"]]

#Function to split and get first 10 skills
def extract_top_10_skills(skill_str):
    skills = [s.strip() for s in skill_str.split(',')]
    return skills[:10]

#Apply to column
df['Optional Skills (Knowledge)'] = df['Optional Skills (Knowledge)'].apply(extract_top_10_skills)
df['Essential Skills (Knowledge)'] = df['Essential Skills (Knowledge)'].apply(extract_top_10_skills)

def clean_skill_list(skill_list):
    if isinstance(skill_list, list):
        return [preprocess(remove_bracketed_words(skill)) for skill in skill_list]
    return skill_list

columns_to_clean = ["Essential Skills (Knowledge)", "Optional Skills (Knowledge)"]

for col in columns_to_clean:
    df[col] = df[col].apply(clean_skill_list)

def merge_unique_skills(row):
    essential = row["Essential Skills (Knowledge)"]
    optional = row["Optional Skills (Knowledge)"]

    # Merge the two lists and keep only unique values
    combined = set(essential or []) | set(optional or [])
    return list(combined)

#Create a new column with merged unique skills
df["All Skills (Knowledge)"] = df.apply(merge_unique_skills, axis=1)

df = df[["Occupation Title", "Description", "Alternative Labels","All Skills (Knowledge)"]]

top_skills_df = df.copy()
#=== Skill Gap Analysis ===
def compare_skills_to_job(job_title, matched_user_skills):
    cleaned_skills = set(preprocess(skill) for skill in matched_user_skills if skill != "No Match")

    #Match by occupation title or alternative labels
    rows = top_skills_df[
        (top_skills_df["Occupation Title"].str.lower() == job_title.lower()) |
        top_skills_df["Alternative Labels"].fillna("").str.lower().str.contains(job_title.lower())
    ]

    if rows.empty:
        return f"Error: Job '{job_title}' not found."

    #Extract the merged skill list (All Skills)
    all_skills = []
    for skill_list in rows["All Skills (Knowledge)"].dropna():
        if isinstance(skill_list, list):
            all_skills.extend(skill_list)

    #Keep top 10 unique cleaned required skills
    top_10_required = [preprocess(s) for s in all_skills[:10]]
    top_10_required = list(dict.fromkeys(top_10_required)) 

    missing = list(set(top_10_required) - cleaned_skills)
    return pd.DataFrame(missing, columns=["Missing Skills"])

#=== Job Titles for Dropdown ===
def get_all_jobs():
    return sorted(esco_df['Job Role'].dropna().unique().tolist())
