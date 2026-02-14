/**
 * API Client - Fetch wrapper for all backend endpoints
 */

const API_BASE_URL = '/api';

// Store current user ID (in production, this would come from authentication)
let currentUserId = null;

function setUserId(userId) {
    currentUserId = userId;
}

function getUserId() {
    if (!currentUserId) {
        // Try to get from localStorage
        currentUserId = localStorage.getItem('userId');
    }
    return currentUserId;
}

async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || `HTTP error! status: ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// User API
const userAPI = {
    create: async (userData) => {
        const user = await apiRequest('/users/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        if (user.id) {
            setUserId(user.id);
            localStorage.setItem('userId', user.id);
        }
        return user;
    },
    getProfile: async (userId) => {
        return apiRequest(`/users/profile?user_id=${userId}`);
    },
    updateProfile: async (userId, profileData) => {
        return apiRequest(`/users/profile?user_id=${userId}`, {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    },
    uploadResume: async (userId, file) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiRequest(`/users/profile/upload-resume?user_id=${userId}`, {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    }
};

// Jobs API
const jobsAPI = {
    getSuggestions: async (userId, limit = 20) => {
        return apiRequest(`/jobs/suggestions?user_id=${userId}&limit=${limit}`);
    },
    getJob: async (jobId) => {
        return apiRequest(`/jobs/${jobId}`);
    },
    search: async (searchData) => {
        return apiRequest('/jobs/search', {
            method: 'POST',
            body: JSON.stringify(searchData)
        });
    }
};

// Applications API
const applicationsAPI = {
    getAll: async (userId, status = null) => {
        const url = status 
            ? `/applications/?user_id=${userId}&status=${status}`
            : `/applications/?user_id=${userId}`;
        return apiRequest(url);
    },
    create: async (applicationData) => {
        return apiRequest('/applications/', {
            method: 'POST',
            body: JSON.stringify(applicationData)
        });
    },
    update: async (applicationId, updateData) => {
        return apiRequest(`/applications/${applicationId}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    },
    updateStatus: async (applicationId, status) => {
        return apiRequest(`/applications/${applicationId}/status?status=${status}`, {
            method: 'PUT'
        });
    },
    delete: async (applicationId) => {
        return apiRequest(`/applications/${applicationId}`, {
            method: 'DELETE'
        });
    }
};

// Emails API
const emailsAPI = {
    getAuthUrl: async () => {
        return apiRequest('/emails/connect');
    },
    sync: async (userId, token = null) => {
        const url = token
            ? `/emails/sync?user_id=${userId}&credentials_token=${token}`
            : `/emails/sync?user_id=${userId}`;
        return apiRequest(url, { method: 'POST' });
    },
    getLogs: async (userId, applicationId = null) => {
        const url = applicationId
            ? `/emails/logs?user_id=${userId}&application_id=${applicationId}`
            : `/emails/logs?user_id=${userId}`;
        return apiRequest(url);
    }
};

// Cover Letters API
const coverLettersAPI = {
    generate: async (requestData) => {
        return apiRequest('/cover-letters/generate', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
    },
    getByApplication: async (applicationId) => {
        return apiRequest(`/cover-letters/${applicationId}`);
    },
    update: async (coverLetterId, content) => {
        return apiRequest(`/cover-letters/${coverLetterId}`, {
            method: 'PUT',
            body: JSON.stringify({ content })
        });
    },
    improve: async (coverLetterId, feedback) => {
        return apiRequest(`/cover-letters/${coverLetterId}/improve?feedback=${encodeURIComponent(feedback)}`, {
            method: 'POST'
        });
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        userAPI,
        jobsAPI,
        applicationsAPI,
        emailsAPI,
        coverLettersAPI,
        setUserId,
        getUserId
    };
}
