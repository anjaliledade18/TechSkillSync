document.getElementById('jobSearchForm').addEventListener('submit', function (e) {
  e.preventDefault();

  const jobName = document.getElementById('jobName').value.trim();
  const country = document.getElementById('country').value;
  const location = document.getElementById('location').value.trim();
  const experience = document.getElementById('experience').value;
  const employmentType = document.getElementById('employmentType').value;
  const remoteOnly = document.getElementById('remoteOnly').value;
  const postedOn = document.getElementById('postedOn').value;
  const radius = parseInt(document.getElementById('radius').value) || null;
  const numPages = parseInt(document.getElementById('numPages').value) || 1;

  const params = {
    country,
    job_name: jobName,
    location,
    experience_level: experience,
    employment_type: employmentType,
    remote_only: remoteOnly,
    posted_on: postedOn,
    radius,
    num_pages: numPages
  };

  fetch('/positions/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
    .then(res => res.json())
    .then(data => {
      const jobList = document.getElementById('jobList');
      jobList.innerHTML = '';

      let userSkills = [];
      try {
        const stored = sessionStorage.getItem("userSkills");
        userSkills = stored ? JSON.parse(stored).map(s => s.toLowerCase()) : [];
      } catch (e) {
        console.warn("Could not load user skills from sessionStorage");
      }

      if (data.jobs && data.jobs.length > 0) {
        data.jobs.forEach(job => {
          const li = document.createElement('li');
          li.style.listStyle = 'none';

          // Log job for debug
          console.log("Job data:", job);

          const isRemote = job.job_is_remote ?? job.isRemote ?? null;
          let remoteInfo = '';
          if (isRemote === true) {
            remoteInfo = '<p><strong>Remote:</strong>Yes</p>';
          } else if (isRemote === false) {
            remoteInfo = '<p><strong>Remote:</strong>No</p>';
          }

          li.innerHTML = `
            <div class="job-card">
              <h3>${job.job_title}</h3>
              <div class="job-skills">
                <strong>Skills Found:</strong>
                <ul class="extracted-skills"><li>Loading...</li></ul>
              </div>
              <p><strong>Company:</strong> ${job.employer_name || 'N/A'}</p>
              <p><strong>Location:</strong> ${job.job_city || 'N/A'}, ${job.job_country || ''}</p>
              <p><strong>Employment Type:</strong> ${job.job_employment_type || 'N/A'}</p>
              ${remoteInfo}
              <p><strong>Posted:</strong> ${new Date(job.job_posted_at_datetime_utc).toLocaleDateString()}</p>
              <p><strong>Description:</strong></p>
              <div class="description">${job.job_description || 'No description available'}</div>
              <a href="${job.job_apply_link}" target="_blank" class="apply-button">Apply Here</a>
            </div>
          `;

          jobList.appendChild(li);

          // Extract and compare skills
          fetch('/extract_skills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              job_title: job.job_title,
              job_description: job.job_description,
              job_highlights: job.job_highlights
            })
          })
            .then(res => res.json())
            .then(data => {
              const skillUl = li.querySelector('.extracted-skills');
              if (data.skills && data.skills.length > 0) {
                const foundSkills = data.skills.map(s => s.toLowerCase());
                const matchingSkills = foundSkills.filter(skill => userSkills.includes(skill));
                const missingSkills = foundSkills.filter(skill => !userSkills.includes(skill));

                skillUl.innerHTML = `
                  <li><strong>Extracted Skills:</strong> ${data.skills.join(', ')}</li>
                  <li><strong>Matching Skills:</strong> ${matchingSkills.length ? matchingSkills.join(', ') : 'None'}</li>
                  <li><strong>Missing Skills:</strong> ${missingSkills.length ? missingSkills.join(', ') : 'None'}</li>
                `;
              } else {
                skillUl.innerHTML = '<li>No skills found</li>';
              }
            })
            .catch(() => {
              const skillUl = li.querySelector('.extracted-skills');
              skillUl.innerHTML = '<li>Error extracting skills</li>';
            });
        });
      } else {
        jobList.innerHTML = '<li>No jobs found. Try adjusting your filters.</li>';
      }
    })
    .catch(err => {
      console.error(err);
      document.getElementById('jobList').innerHTML = '<li>Error fetching jobs. Please try again later.</li>';
    });
});
