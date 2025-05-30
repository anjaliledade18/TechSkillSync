import requests

APP_ID = '7b9c1c38'
APP_KEY = 'ff185f03d8911f04c567b500bbbaa741'


def search_adzuna_jobs(country, keyword, location, contract_type="", salary_min=0, salary_max=9999999, max_days_old=30, results_per_page=10):
    allowed_types = ["full_time", "part_time", "contract", "permanent"]
    if contract_type and contract_type not in allowed_types:
        raise ValueError("Invalid contract type")

    # Prepare API request
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": keyword,
        "where": location,
        "results_per_page": results_per_page,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "max_days_old": max_days_old,
        "content-type": "application/json",
        "category": "it-jobs"
    }

    if contract_type:
        params[contract_type] = 1

    # Send request and process
    response = requests.get(f"https://api.adzuna.com/v1/api/jobs/{country}/search/1", params=params)
    if response.status_code != 200:
        raise Exception("Failed to fetch jobs from Adzuna")

    raw_jobs = response.json().get("results", [])
    parsed_jobs = [{
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name", ""),
        "location": job.get("location", {}).get("display_name", ""),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "redirect_url": job.get("redirect_url"),
    } for job in raw_jobs]

    return parsed_jobs
