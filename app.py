import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from skill_matcher import (
    match_user_skills,
    match_skills_job,
    esco_skills,
    compare_skills_to_job,
    get_all_jobs
)
from jsearch_api import (
    search_jobs_with_filters,
    get_job_ids_from_search,
    get_job_details_by_id,
    combine_job_text_fields
)
from skill_extraction import preprocess_job_text, extract_skills_from_text
from skill_loader import load_known_skills                          
from resume_extraction import extract_skills_from_file_or_text

UPLOAD_DIR = "temp_uploads"  #safer folder name

rapid_api_key = '77e7fc99a6msheff92dac84ce9cfp1acf97jsnb3fe49797b86'

app = Flask(__name__)
print("\u2705 Flask is running this file...")

# Load once at startup
known_skills = load_known_skills(
    "data/ESCO skill taxonomy dataset.csv",
    "data/tool_mapping.csv"
)

# === Page Routes ===

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/skill_matcher')
def skill_matcher():
    return render_template('index.html')

@app.route('/positions')
def positions():
    return render_template('positions.html')

#=== API Routes ===

@app.route('/skills')
def get_skills():
    return jsonify(sorted(esco_skills))

@app.route('/match', methods=['POST'])
def match():
    data = request.get_json()
    user_skills = data.get('skills', [])

    df, matched_skills_only, general_categories = match_user_skills(user_skills)
    jobs_df = match_skills_job(matched_skills_only)

    job_matches = []
    for _, row in jobs_df.iterrows():
        job_title = row.get("Job Role", "N/A").title()
        alt_titles_raw = row.get("Alternative Titles", "")
        if pd.notna(alt_titles_raw) and isinstance(alt_titles_raw, str):
            alt_titles = [alt.strip() for alt in alt_titles_raw.split(",") if alt.strip()]
            alt_titles = ", ".join(alt_titles[:3]) if alt_titles else "N/A"
        else:
            alt_titles = "N/A"

        job_matches.append({
            "title": job_title,
            "matched_count": row.get("Matched Skills Count", 0),
            "alt_titles": alt_titles
        })

    return jsonify({
        "matched_pairs": df[["User Skill", "Matched Skill"]].values.tolist(),
        "job_matches": job_matches
    })

@app.route('/compare_skills', methods=['POST'])
def compare_skills():
    data = request.get_json()
    job_title = data.get('job', '')
    user_skills = data.get('skills', [])

    try:
        _, matched_skills, general_categories = match_user_skills(user_skills)
        all_skills = matched_skills + general_categories
        cleaned_matched_skills = [s for s in all_skills if s != "No Match"]

        df = compare_skills_to_job(job_title, cleaned_matched_skills)

        if isinstance(df, str):
            return jsonify({ "error": df }), 400

        return jsonify({ "missing_skills": df["Missing Skills"].tolist() })

    except Exception as e:
        return jsonify({ "error": str(e) }), 500

@app.route('/all_jobs')
def all_jobs():
    return jsonify(get_all_jobs())

@app.route('/positions/search', methods=['POST'])
def positions_search():
    data = request.get_json()
    try:
        jobs = search_jobs_with_filters(
            country=data.get("country", "us"),
            job_name=data.get("job_name", ""),
            skills=data.get("skills", []),
            location=data.get("location", ""),
            experience_level=data.get("experience_level", ""),
            employment_type=data.get("employment_type", ""),
            remote_only=data.get("remote_only", ""),
            posted_on=data.get("posted_on", ""),
            radius=data.get("radius", None),
            num_pages=data.get("num_pages", 1),
            api_key=rapid_api_key
        )

        job_ids = get_job_ids_from_search(jobs)[:5]
        detailed_jobs = [get_job_details_by_id(job_id) for job_id in job_ids if job_id]

        return jsonify({ "jobs": detailed_jobs })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({ "error": str(e) }), 500

@app.route('/extract_skills', methods=['POST'])
def extract_skills():
    if 'resume_file' in request.files:
        uploaded_file = request.files['resume_file']
        if uploaded_file.filename == '':
            return jsonify({ "error": "No file selected." }), 400

        try:
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            save_path = os.path.join(UPLOAD_DIR, uploaded_file.filename)
            uploaded_file.save(save_path)

            skills = extract_skills_from_file_or_text(save_path, known_skills)
            os.remove(save_path)
            return jsonify({ "skills": skills })
        except Exception as e:
            print("Error processing uploaded resume:", e)
            return jsonify({ "error": "Failed to extract skills from file." }), 500

    if request.is_json:
        data = request.get_json()

        #Handle pasted resume text
        if "resume_text" in data:
            try:
                skills = extract_skills_from_file_or_text(data["resume_text"], known_skills)
                return jsonify({ "skills": skills })
            except Exception as e:
                print("Error processing resume text:", e)
                return jsonify({ "error": "Failed to extract skills from text." }), 500

        #Handle job ad text
        elif "job_title" in data or "job_description" in data:
            job_title = data.get("job_title", "")
            job_description = data.get("job_description", "")
            job_highlights = data.get("job_highlights", [])
            
            combined_text = combine_job_text_fields(job_title, job_description, job_highlights)
            preprocessed = preprocess_job_text(combined_text)
            try:
                skills = extract_skills_from_text(preprocessed, known_skills)
                return jsonify({ "skills": skills })
            except Exception as e:
                print("Error processing job ad text:", e)
                return jsonify({ "error": "Failed to extract skills from job ad." }), 500

    return jsonify({ "error": "No valid input provided." }), 400


if __name__ == '__main__':
    app.run(debug=True)
