/**
 * Cover Letter Generator
 */

let currentCoverLetter = null;
let coverLetterVersions = [];

async function loadApplicationsForCoverLetter() {
    const userId = getUserId();
    if (!userId) return;

    try {
        const apps = await applicationsAPI.getAll(userId);
        const select = document.getElementById('cover-letter-application');
        if (!select) return;

        select.innerHTML = '<option value="">Select Application</option>';
        apps.forEach(app => {
            if (app.job) {
                const option = document.createElement('option');
                option.value = app.id;
                option.textContent = `${app.job.title} at ${app.job.company}`;
                select.appendChild(option);
            }
        });
    } catch (error) {
        console.error('Error loading applications:', error);
    }
}

async function generateCoverLetter() {
    const applicationId = document.getElementById('cover-letter-application').value;
    if (!applicationId) {
        alert('Please select an application');
        return;
    }

    const tone = document.getElementById('cover-letter-tone').value;
    const length = document.getElementById('cover-letter-length').value;

    try {
        const preview = document.getElementById('cover-letter-preview');
        if (preview) {
            preview.textContent = 'Generating cover letter...';
        }

        const coverLetter = await coverLettersAPI.generate({
            application_id: parseInt(applicationId),
            tone: tone,
            length: length
        });

        currentCoverLetter = coverLetter;
        displayCoverLetter(coverLetter);
        loadCoverLetterVersions(parseInt(applicationId));
    } catch (error) {
        alert('Error generating cover letter: ' + error.message);
        const preview = document.getElementById('cover-letter-preview');
        if (preview) {
            preview.textContent = '';
        }
    }
}

function displayCoverLetter(coverLetter) {
    const preview = document.getElementById('cover-letter-preview');
    if (!preview) return;

    preview.textContent = coverLetter.content;
    
    // Add edit button
    const editBtn = document.createElement('button');
    editBtn.className = 'btn btn-primary';
    editBtn.textContent = 'Edit';
    editBtn.style.marginTop = '1rem';
    editBtn.onclick = () => editCoverLetter(coverLetter.id);
    
    // Remove existing edit button
    const existingBtn = preview.querySelector('button');
    if (existingBtn) existingBtn.remove();
    
    preview.appendChild(editBtn);
}

function editCoverLetter(coverLetterId) {
    const preview = document.getElementById('cover-letter-preview');
    if (!preview || !currentCoverLetter) return;

    const textarea = document.createElement('textarea');
    textarea.value = currentCoverLetter.content;
    textarea.style.width = '100%';
    textarea.style.minHeight = '400px';
    textarea.style.fontFamily = 'inherit';
    textarea.style.padding = '1rem';
    textarea.style.border = '1px solid #ddd';
    textarea.style.borderRadius = '4px';

    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-primary';
    saveBtn.textContent = 'Save Changes';
    saveBtn.style.marginTop = '1rem';
    saveBtn.onclick = async () => {
        try {
            const updated = await coverLettersAPI.update(coverLetterId, textarea.value);
            currentCoverLetter = updated;
            displayCoverLetter(updated);
            showCoverLetterMessage('Cover letter updated!', 'success');
        } catch (error) {
            showCoverLetterMessage('Error updating cover letter: ' + error.message, 'error');
        }
    };

    preview.innerHTML = '';
    preview.appendChild(textarea);
    preview.appendChild(saveBtn);
}

async function loadCoverLetterVersions(applicationId) {
    try {
        const versions = await coverLettersAPI.getByApplication(applicationId);
        coverLetterVersions = versions;
        displayVersions(versions);
    } catch (error) {
        console.error('Error loading versions:', error);
    }
}

function displayVersions(versions) {
    const container = document.getElementById('cover-letter-versions');
    if (!container) return;

    if (versions.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = '<h3>Previous Versions</h3>';
    versions.forEach(version => {
        const versionDiv = document.createElement('div');
        versionDiv.className = 'application-card';
        versionDiv.style.marginBottom = '1rem';
        versionDiv.innerHTML = `
            <div><strong>Version ${version.version}</strong> - ${new Date(version.generated_date).toLocaleDateString()}</div>
            <button class="btn btn-secondary" onclick="loadVersion(${version.id})" style="margin-top: 0.5rem; font-size: 0.85rem; padding: 0.5rem;">Load This Version</button>
        `;
        container.appendChild(versionDiv);
    });
}

async function loadVersion(coverLetterId) {
    const version = coverLetterVersions.find(v => v.id === coverLetterId);
    if (version) {
        currentCoverLetter = version;
        displayCoverLetter(version);
    }
}

function showCoverLetterMessage(message, type) {
    const container = document.querySelector('#cover-letters .cover-letters-container');
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

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-cover-letter');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateCoverLetter);
    }

    // Load applications when section is shown
    const coverLettersSection = document.getElementById('cover-letters');
    if (coverLettersSection) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (!coverLettersSection.classList.contains('hidden')) {
                    loadApplicationsForCoverLetter();
                }
            });
        });
        observer.observe(coverLettersSection, { attributes: true, attributeFilter: ['class'] });
    }
});
