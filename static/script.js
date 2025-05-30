let selectedSkills = new Set();

// DOM elements
const skillInput = document.getElementById('skillInput');
const selectedSkillsDiv = document.getElementById('selectedSkills');
const suggestionsBox = document.getElementById('suggestions');
const matchedSkillsTable = document.getElementById('matchedSkillsTable');
const jobMatchesList = document.getElementById('jobMatchesList');
const jobDropdown = document.getElementById('jobDropdown');
const missingSkillsList = document.getElementById('missingSkillsList');
const jobSourceRadios = document.getElementsByName("jobSource");
const resumeText = document.getElementById('resumeText');
const resumeFile = document.getElementById('resumeFile');
const cvExtractedSkills = document.getElementById('cvExtractedSkills');
const inputMode = document.getElementById('inputMode');
const manualSection = document.getElementById('manualSection');
const resumeSection = document.getElementById('resumeSection');
const runComparisonBtn = document.getElementById('runComparisonBtn');
const extractCVBtn = document.getElementById('extractCVBtn');

suggestionsBox.classList.add('hidden');
let hintList = [];

fetch('/skills')
  .then(res => res.json())
  .then(data => { hintList = data; })
  .catch(err => console.error("\u274C Failed to load skill suggestions:", err));

inputMode.addEventListener('change', () => {
  const mode = inputMode.value;
  manualSection.style.display = mode === 'manual' ? 'block' : 'none';
  resumeSection.style.display = mode === 'resume' ? 'block' : 'none';
});

function updateSelectedSkillsDisplay() {
  selectedSkillsDiv.innerHTML = '';
  selectedSkills.forEach(skill => {
    const tag = document.createElement('div');
    tag.className = 'tag';
    tag.innerText = skill;
    tag.onclick = () => {
      selectedSkills.delete(skill);
      updateSelectedSkillsDisplay();
      updateMatching();
    };
    selectedSkillsDiv.appendChild(tag);
  });
}

function toProperCase(text) {
  return text.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function updateMatching() {
  fetch('/match', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skills: Array.from(selectedSkills) })
  })
  .then(res => res.json())
  .then(data => {
    const { matched_pairs, job_matches } = data;
    matchedSkillsTable.innerHTML = `<tr><th>Entered Skill</th><th>Matched ESCO Skill</th></tr>`;
    matched_pairs.forEach(([userSkill, matchedSkill]) => {
      matchedSkillsTable.innerHTML += `<tr><td>${userSkill}</td><td>${matchedSkill}</td></tr>`;
    });

    jobMatchesList.innerHTML = '';
    job_matches.forEach(job => {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${job.title}</strong> (${job.matched_count} skills matched)<br><em>Alternative Titles:</em> ${job.alt_titles || "N/A"}`;
      jobMatchesList.appendChild(li);
    });

    jobDropdown.innerHTML = `<option value="">-- Select a job --</option>`;
    const mode = Array.from(jobSourceRadios).find(r => r.checked)?.value || 'matched';

    if (mode === "matched") {
      job_matches.forEach(job => {
        const opt = document.createElement('option');
        opt.value = job.title;
        opt.textContent = job.title;
        jobDropdown.appendChild(opt);
      });
    } else {
      fetch('/all_jobs')
        .then(res => res.json())
        .then(jobs => {
          jobs.forEach(job => {
            const opt = document.createElement('option');
            opt.value = job;
            opt.textContent = job;
            jobDropdown.appendChild(opt);
          });
        })
        .catch(err => console.error("\u274C Failed to load all jobs:", err));
    }
  })
  .catch(err => {
    console.error("\u274C Error fetching matches:", err);
    matchedSkillsTable.innerHTML = `<tr><td colspan="2">Server error – please try again later.</td></tr>`;
  });
}

function addSkillsFromInput() {
  const input = skillInput.value;
  const skills = input.split(',').map(s => s.trim()).filter(s => s && !Array.from(selectedSkills).map(sk => sk.toLowerCase()).includes(s.toLowerCase()));
  skills.forEach(skill => selectedSkills.add(skill));
  skillInput.value = '';
  suggestionsBox.innerHTML = '';
  suggestionsBox.classList.add('hidden');
  updateSelectedSkillsDisplay();
  updateMatching();
}

function extractSkillsFromCV() {
  const text = resumeText.value.trim();
  const file = resumeFile.files[0];
  cvExtractedSkills.innerHTML = '<p>⏳ Extracting...</p>';

  if (text) {
    fetch('/extract_skills', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_text: text })
    })
    .then(res => res.json())
    .then(data => handleExtractedSkills(data.skills))
    .catch(() => { cvExtractedSkills.innerHTML = '<p>Error extracting from pasted text.</p>'; });
  } else if (file) {
    const formData = new FormData();
    formData.append("resume_file", file);

    fetch('/extract_skills', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => handleExtractedSkills(data.skills))
    .catch(() => { cvExtractedSkills.innerHTML = '<p>Error extracting from file.</p>'; });
  } else {
    cvExtractedSkills.innerHTML = '<p>Please upload or paste your resume first.</p>';
  }
}

function handleExtractedSkills(skills) {
  if (!skills.length) {
    cvExtractedSkills.innerHTML = '<p>No skills found.</p>';
    return;
  }

  cvExtractedSkills.innerHTML = '';
  skills.forEach(skill => {
    selectedSkills.add(skill);
    const tag = document.createElement('div');
    tag.className = 'tag';
    tag.innerText = skill;
    tag.onclick = () => {
      selectedSkills.delete(skill);
      updateSelectedSkillsDisplay();
      handleExtractedSkills(Array.from(selectedSkills));
      updateMatching();
    };
    cvExtractedSkills.appendChild(tag);
  });

  updateSelectedSkillsDisplay();
  updateMatching();
}

skillInput.addEventListener('input', () => {
  const input = skillInput.value.toLowerCase().trim();
  suggestionsBox.innerHTML = '';
  if (!input) {
    suggestionsBox.classList.add('hidden');
    return;
  }
  const matches = hintList.filter(skill => skill.includes(input)).slice(0, 6);
  if (!matches.length) {
    const item = document.createElement('div');
    item.className = 'autocomplete-item';
    item.textContent = 'No suggestions found';
    suggestionsBox.appendChild(item);
  } else {
    matches.forEach(skill => {
      const item = document.createElement('div');
      item.className = 'autocomplete-item';
      item.textContent = skill;
      item.onclick = () => {
        selectedSkills.add(skill);
        skillInput.value = '';
        suggestionsBox.innerHTML = '';
        suggestionsBox.classList.add('hidden');
        updateSelectedSkillsDisplay();
        updateMatching();
      };
      suggestionsBox.appendChild(item);
    });
  }
  suggestionsBox.classList.remove('hidden');
});

skillInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    addSkillsFromInput();
  }
});

document.addEventListener('click', (e) => {
  if (!suggestionsBox.contains(e.target) && e.target !== skillInput) {
    suggestionsBox.innerHTML = '';
    suggestionsBox.classList.add('hidden');
  }
});

function runComparison() {
  const selectedJob = jobDropdown.value;
  if (!selectedJob) return;

  fetch('/compare_skills', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      job: selectedJob,
      skills: Array.from(selectedSkills)
    })
  })
  .then(res => res.json())
  .then(data => {
    missingSkillsList.innerHTML = '';
    if (data.missing_skills?.length) {
      data.missing_skills.forEach(skill => {
        const li = document.createElement('li');
        li.textContent = toProperCase(skill);
        missingSkillsList.appendChild(li);
      });
    } else {
      missingSkillsList.innerHTML = '<li>No missing skills!</li>';
    }
  })
  .catch(err => {
    console.error("Error running skill comparison:", err);
    missingSkillsList.innerHTML = '<li>Comparison failed.</li>';
  });
}

runComparisonBtn?.addEventListener('click', (e) => {
  e.preventDefault();
  runComparison();
});

extractCVBtn?.addEventListener('click', (e) => {
  e.preventDefault();
  extractSkillsFromCV();
});

jobSourceRadios.forEach(radio => {
  radio.addEventListener('change', () => {
    updateMatching();
  });
});

function goToPositionsPage() {
  const skillsArray = Array.from(selectedSkills);
  sessionStorage.setItem("userSkills", JSON.stringify(skillsArray));
  window.location.href = "/positions";
}
