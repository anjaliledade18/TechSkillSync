import requests
from typing import List, Optional

# === API Key ===
rapid_api_key = '77e7fc99a6msheff92dac84ce9cfp1acf97jsnb3fe49797b86'
rapid_api_host = 'jsearch.p.rapidapi.com'

#=== Search Jobs ===
def search_jobs_with_filters(
    job_name: str,
    skills: Optional[List[str]] = None,
    location: Optional[str] = None,
    experience_level: Optional[str] = None,
    employment_type: Optional[str] = None,
    remote_only: Optional[str] = None,  # "true" or "false"
    posted_on: Optional[str] = None,    # "today", "3days", etc.
    radius: Optional[int] = None,       # distance in km
    num_pages: Optional[int] = 1,
    country: Optional[str] = "us",
    api_key: Optional[str] = None
) -> List[dict]:
    if not job_name:
        raise ValueError("Job name is required.")

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": rapid_api_host
    }

    # === Build the search query string ===
    query = job_name.strip()
    if location and f"in {location.lower()}" not in job_name.lower():
        query += f" in {location.strip()}"
    if skills:
        query += " " + " ".join(skills)

    print("Final search query:", query)

    # === Build request parameters ===
    params = {
        "query": query,
        "page": "1",
        "num_pages": str(num_pages),
        "country": country
    }

    if experience_level:
        params["job_requirements"] = experience_level
    if employment_type:
        params["employment_types"] = employment_type
    if remote_only:
        params["work_from_home"] = remote_only
    if posted_on:
        params["date_posted"] = posted_on
    if radius:
        params["radius"] = str(radius)

    # === Send request ===
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Failed: {response.status_code} - {response.text}")
        return []


#=== Get Job IDs ===
def get_job_ids_from_search(jobs: List[dict]) -> List[str]:
    return [job.get("job_id") for job in jobs if job.get("job_id")]

def get_job_details_by_id(job_id: str) -> Optional[dict]:
    url = "https://jsearch.p.rapidapi.com/job-details"
    headers = {
        "X-RapidAPI-Key": rapid_api_key,
        "X-RapidAPI-Host": rapid_api_host
    }
    params = {"job_id": job_id}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        job = data.get("data", [None])[0]

        if job:
            return {
                "job_id": job.get("job_id"),
                "job_title": job.get("job_title"),
                "employer_name": job.get("employer_name"),
                "employer_website": job.get("employer_website"),
                "job_description": job.get("job_description"),
                "job_highlights": job.get("job_highlights"),
                "job_employment_type": job.get("job_employment_type"),
                "job_city": job.get("job_city"),
                "job_country": job.get("job_country"),
                "job_is_remote": job.get("job_is_remote"), 
                "job_apply_link": job.get("job_apply_link"),
                "job_posted_at_datetime_utc": job.get("job_posted_at_datetime_utc"),
            }

        return None
    else:
        print(f"Failed to fetch job details: {response.status_code} - {response.text}")
        return None

#=== Combine Job Text (Optional for NLP) ===
def combine_job_text_fields(
    job_title: Optional[str],
    job_description: Optional[str],
    job_highlights: Optional[List[str] or str] = None
) -> str:
    parts = []
    if job_title:
        parts.append(str(job_title))
    if job_description:
        parts.append(str(job_description))
    if job_highlights:
        if isinstance(job_highlights, list):
            parts.append(" ".join(str(h) for h in job_highlights))
        else:
            parts.append(str(job_highlights))
    return "\n".join(parts).strip()
