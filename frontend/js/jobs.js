/**
 * Job Suggestions Display
 */

let jobs = [];

async function loadJobSuggestions() {
    const userId = getUserId();
    if (!userId) {
        showJobsMessage('Please create a user profile first', 'error');
        return;
    }

    try {
        showJobsMessage('Loading job suggestions...', 'success');
        jobs = await jobsAPI.getSuggestions(userId, 20);
        displayJobs(jobs);
        showJobsMessage(`Found ${jobs.length} job suggestions`, 'success');
    } catch (error) {
        console.error('Error loading jobs:', error);
        showJobsMessage('Error loading job suggestions: ' + error.message, 'error');
    }
}

function displayJobs(jobsToDisplay) {
    const jobsList = document.getElementById('jobs-list');
    if (!jobsList) return;

    if (jobsToDisplay.length === 0) {
        jobsList.innerHTML = '<p>No jobs found. Try adjusting your profile or search criteria.</p>';
        return;
    }

    jobsList.innerHTML = jobsToDisplay.map(job => `
        <div class="job-card">
            <h3>${escapeHtml(job.title)}</h3>
            <div class="company">${escapeHtml(job.company)}</div>
            <div class="location">${escapeHtml(job.location || 'Location not specified')}</div>
            ${job.match_score ? `<div class="match-score">Match: ${Math.round(job.match_score)}%</div>` : ''}
            ${job.salary_range ? `<div class="salary">${escapeHtml(job.salary_range)}</div>` : ''}
            <div class="description">${escapeHtml((job.description || '').substring(0, 200))}...</div>
            <div class="actions">
                <button class="btn btn-primary" onclick="applyToJob(${job.id})">Apply</button>
                <button class="btn btn-secondary" onclick="viewJobDetails(${job.id})">Details</button>
            </div>
        </div>
    `).join('');
}

async function applyToJob(jobId) {
    const userId = getUserId();
    if (!userId) {
        alert('Please create a user profile first');
        return;
    }

    try {
        const applicationData = {
            user_id: userId,
            job_id: jobId,
            status: 'active',
            manual_entry: false
        };
        await applicationsAPI.create(applicationData);
        alert('Application added successfully!');
        // Refresh applications if on that page
        if (typeof loadApplications === 'function') {
            loadApplications();
        }
    } catch (error) {
        alert('Error creating application: ' + error.message);
    }
}

async function viewJobDetails(jobId) {
    try {
        const job = await jobsAPI.getJob(jobId);
        alert(`Job Details:\n\nTitle: ${job.title}\nCompany: ${job.company}\nLocation: ${job.location}\n\nDescription:\n${job.description}`);
    } catch (error) {
        alert('Error loading job details: ' + error.message);
    }
}

function filterJobs() {
    const searchTerm = document.getElementById('job-search').value.toLowerCase();
    const filtered = jobs.filter(job => 
        job.title.toLowerCase().includes(searchTerm) ||
        job.company.toLowerCase().includes(searchTerm) ||
        (job.description || '').toLowerCase().includes(searchTerm)
    );
    displayJobs(filtered);
}

function showJobsMessage(message, type) {
    const jobsContainer = document.querySelector('#jobs .jobs-container');
    if (!jobsContainer) return;

    const existing = jobsContainer.querySelector('.message');
    if (existing) existing.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    jobsContainer.insertBefore(messageDiv, jobsContainer.firstChild);

    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refresh-jobs');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadJobSuggestions);
    }

    const searchInput = document.getElementById('job-search');
    if (searchInput) {
        searchInput.addEventListener('input', filterJobs);
    }

    // Load jobs when section is shown
    const jobsSection = document.getElementById('jobs');
    if (jobsSection) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (!jobsSection.classList.contains('hidden') && jobs.length === 0) {
                    loadJobSuggestions();
                }
            });
        });
        observer.observe(jobsSection, { attributes: true, attributeFilter: ['class'] });
    }
});
