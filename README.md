# TechSkillSync – Skill Gap Analyser

TechSkillSync is a Flask-based web application that helps users identify skill gaps for specific IT jobs by matching user-entered skills or resume content with structured job and skills taxonomies (ESCO/ANZSCO) and real-world job ads.

---

## Features

- Extract skills from manual entry or uploaded/pasted resumes
- Match user skills to ESCO/ANZSCO job roles
- Compare user skills against job ad requirements
- Live job search using JSearch API
- View missing skills directly from job postings

---

## Setup Instructions

### 1. Clone or download the project

Navigate to your desired folder, then run:

```bash
git clone https://github.com/yourusername/techskillsync.git
cd techskillsync
```

Or manually download and unzip the project folder.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

- On **Windows**:
  ```bash
  venv\Scripts\activate
  ```

- On **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Download spaCy model (one-time only)

```bash
python -m spacy download en_core_web_sm
```

---

## How to Run

From the activated virtual environment, run:

```bash
Go to CMD
type CD path to project folder. E.g. CD C:\Users\nick_\Desktop\University\Autumn 25\36118 Applied Natural Language Processing\Assignments\Assignment 2\techskillsyncsite
Type venv\Scripts\activate
Type python app.py

```

You should see output like:

```
Flask is running this file...
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

---

## Access the Web App

Open your browser and go to:

```
http://127.0.0.1:5000
```

---

## Troubleshooting

- If `venv\Scripts\activate` doesn't work, ensure you are using the Command Prompt or PowerShell (not Git Bash).
- If ports are blocked or the server doesn’t load, try a different port by editing `app.py` like:

```python
app.run(debug=True, port=5050)
```

---

## Folder Structure

```
techskillsync/
│
├── static/
│   └── styles.css, script.js, positions.js
├── templates/
│   └── index.html, positions.html, home.html
├── data/
│   └── ESCO skill taxonomy dataset.csv, tool_mapping.csv
├── app.py
├── skill_matcher.py
├── resume_extraction.py
├── skill_loader.py
├── jsearch_api.py
├── requirements.txt
└── README.md
```

---
