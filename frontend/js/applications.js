/**
 * Application Tracking Dashboard
 */

let applications = [];

async function loadApplications() {
    const userId = getUserId();
    if (!userId) {
        showApplicationsMessage('Please create a user profile first', 'error');
        return;
    }

    try {
        applications = await applicationsAPI.getAll(userId);
        displayApplications(applications);
    } catch (error) {
        console.error('Error loading applications:', error);
        showApplicationsMessage('Error loading applications: ' + error.message, 'error');
    }
}

function displayApplications(apps) {
    const activeList = document.getElementById('applications-active');
    const interestedList = document.getElementById('applications-interested');
    const closedList = document.getElementById('applications-closed');

    if (activeList) activeList.innerHTML = '';
    if (interestedList) interestedList.innerHTML = '';
    if (closedList) closedList.innerHTML = '';

    apps.forEach(app => {
        const card = createApplicationCard(app);
        const status = app.status || 'active';
        
        if (status === 'active' && activeList) {
            activeList.appendChild(card);
        } else if (status === 'interested' && interestedList) {
            interestedList.appendChild(card);
        } else if (status === 'closed' && closedList) {
            closedList.appendChild(card);
        }
    });
}

function createApplicationCard(application) {
    const card = document.createElement('div');
    card.className = 'application-card';
    
    const jobTitle = application.job?.title || 'Unknown Position';
    const company = application.job?.company || 'Unknown Company';
    const date = application.applied_date || 'Date not set';
    
    card.innerHTML = `
        <h4>${escapeHtml(jobTitle)}</h4>
        <div class="company">${escapeHtml(company)}</div>
        <div class="date">Applied: ${escapeHtml(date)}</div>
        ${application.notes ? `<div class="notes">${escapeHtml(application.notes.substring(0, 100))}</div>` : ''}
        <div class="actions" style="margin-top: 0.5rem;">
            <button class="btn btn-secondary" onclick="updateApplicationStatus(${application.id}, 'interested')" style="font-size: 0.85rem; padding: 0.5rem;">Mark Interested</button>
            <button class="btn btn-danger" onclick="deleteApplication(${application.id})" style="font-size: 0.85rem; padding: 0.5rem;">Delete</button>
        </div>
    `;
    
    return card;
}

async function createApplication() {
    const userId = getUserId();
    if (!userId) {
        alert('Please create a user profile first');
        return;
    }

    const jobTitle = document.getElementById('app-job-title').value;
    const company = document.getElementById('app-company').value;
    const status = document.getElementById('app-status').value;
    const date = document.getElementById('app-date').value;
    const notes = document.getElementById('app-notes').value;

    if (!jobTitle || !company) {
        alert('Please fill in job title and company');
        return;
    }

    try {
        const applicationData = {
            user_id: userId,
            job_title: jobTitle,
            company: company,
            status: status,
            applied_date: date || null,
            notes: notes || null,
            manual_entry: true
        };

        await applicationsAPI.create(applicationData);
        showApplicationsMessage('Application added successfully!', 'success');
        
        // Reset form
        document.getElementById('application-form').reset();
        document.getElementById('application-form-container').classList.add('hidden');
        
        // Reload applications
        loadApplications();
    } catch (error) {
        showApplicationsMessage('Error creating application: ' + error.message, 'error');
    }
}

async function updateApplicationStatus(applicationId, status) {
    try {
        await applicationsAPI.updateStatus(applicationId, status);
        showApplicationsMessage('Application status updated!', 'success');
        loadApplications();
    } catch (error) {
        showApplicationsMessage('Error updating status: ' + error.message, 'error');
    }
}

async function deleteApplication(applicationId) {
    if (!confirm('Are you sure you want to delete this application?')) {
        return;
    }

    try {
        await applicationsAPI.delete(applicationId);
        showApplicationsMessage('Application deleted!', 'success');
        loadApplications();
    } catch (error) {
        showApplicationsMessage('Error deleting application: ' + error.message, 'error');
    }
}

async function syncEmails() {
    const userId = getUserId();
    if (!userId) {
        alert('Please create a user profile first');
        return;
    }

    try {
        showApplicationsMessage('Syncing emails...', 'success');
        const result = await emailsAPI.sync(userId);
        showApplicationsMessage(result.message || 'Emails synced successfully!', 'success');
        loadApplications();
    } catch (error) {
        showApplicationsMessage('Error syncing emails: ' + error.message, 'error');
    }
}

function showApplicationsMessage(message, type) {
    const container = document.querySelector('#applications .applications-container');
    if (!container) return;

    const existing = container.querySelector('.message');
    if (existing) existing.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    container.insertBefore(messageDiv, container.firstChild);

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
    const addBtn = document.getElementById('add-application-btn');
    if (addBtn) {
        addBtn.addEventListener('click', () => {
            document.getElementById('application-form-container').classList.remove('hidden');
        });
    }

    const cancelBtn = document.getElementById('cancel-application');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            document.getElementById('application-form-container').classList.add('hidden');
            document.getElementById('application-form').reset();
        });
    }

    const form = document.getElementById('application-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            createApplication();
        });
    }

    const syncBtn = document.getElementById('sync-emails-btn');
    if (syncBtn) {
        syncBtn.addEventListener('click', syncEmails);
    }

    // Load applications when section is shown
    const applicationsSection = document.getElementById('applications');
    if (applicationsSection) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (!applicationsSection.classList.contains('hidden')) {
                    loadApplications();
                }
            });
        });
        observer.observe(applicationsSection, { attributes: true, attributeFilter: ['class'] });
    }
});
