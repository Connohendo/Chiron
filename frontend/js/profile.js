/**
 * User Profile Management
 */

let currentUser = null;

async function loadProfile() {
    const userId = getUserId();
    if (!userId) {
        showMessage('Please create a user profile first', 'error');
        return;
    }

    try {
        const profile = await userAPI.getProfile(userId);
        populateProfileForm(profile);
        currentUser = { id: userId, profile };
    } catch (error) {
        console.error('Error loading profile:', error);
        showMessage('Error loading profile', 'error');
    }
}

function populateProfileForm(profile) {
    document.getElementById('user-location').value = profile.location || '';
    document.getElementById('user-skills').value = (profile.skills || []).join(', ');
    document.getElementById('experience-level').value = profile.experience_level || 'mid';
}

async function saveProfile() {
    const userId = getUserId();
    if (!userId) {
        // Create user first
        const email = document.getElementById('user-email').value;
        const name = document.getElementById('user-name').value;
        
        if (!email || !name) {
            showMessage('Please fill in email and name', 'error');
            return;
        }

        try {
            const user = await userAPI.create({ email, name });
            setUserId(user.id);
            userId = user.id;
        } catch (error) {
            showMessage('Error creating user: ' + error.message, 'error');
            return;
        }
    }

    const skillsText = document.getElementById('user-skills').value;
    const skills = skillsText.split(',').map(s => s.trim()).filter(s => s);

    const profileData = {
        location: document.getElementById('user-location').value,
        skills: skills,
        experience_level: document.getElementById('experience-level').value
    };

    try {
        await userAPI.updateProfile(userId, profileData);
        showMessage('Profile saved successfully!', 'success');
        currentUser = { id: userId, profile: profileData };
    } catch (error) {
        showMessage('Error saving profile: ' + error.message, 'error');
    }
}

async function handleResumeUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const userId = getUserId();
    if (!userId) {
        showMessage('Please save your profile first', 'error');
        return;
    }

    try {
        showMessage('Uploading and parsing resume...', 'success');
        const result = await userAPI.uploadResume(userId, file);
        showMessage('Resume parsed successfully!', 'success');
        
        // Update form with parsed data
        if (result.profile) {
            populateProfileForm(result.profile);
        }
    } catch (error) {
        showMessage('Error uploading resume: ' + error.message, 'error');
    }
}

function showMessage(message, type) {
    // Remove existing messages
    const existing = document.querySelector('.message');
    if (existing) existing.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    
    const section = document.getElementById('profile');
    section.insertBefore(messageDiv, section.firstChild);

    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', (e) => {
            e.preventDefault();
            saveProfile();
        });
    }

    const resumeUpload = document.getElementById('resume-upload');
    if (resumeUpload) {
        resumeUpload.addEventListener('change', handleResumeUpload);
    }

    // Try to load existing profile
    const userId = getUserId();
    if (userId) {
        loadProfile();
    }
});
