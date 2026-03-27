const API_BASE_URL = 'http://localhost:8000/api';

async function apiRequest(endpoint, options = {}) {
    const headers = { ...options.headers };
    
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });
    
    if (response.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        if (!window.location.pathname.includes('login.html') && 
            !window.location.pathname.includes('register.html')) {
            window.location.href = 'login.html';
        }
        throw new Error('Session expired');
    }
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || error.message || 'Request error');
    }
    
    if (response.status === 204) return null;
    return response.json();
}

async function register(email, password) {
    const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Registration error');
    }
    
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify({ email }));
    return data;
}

async function login(email, password) {
    const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Login error');
    }
    
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify({ email: data.user.email }));
    return data;
}

async function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

async function getProfile() {
    return apiRequest('/me');
}

async function getCategories() {
    return apiRequest('/categories');
}

async function createCategory(name, description) {
    return apiRequest('/categories', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
    });
}

async function deleteCategory(id) {
    return apiRequest(`/categories/${id}`, { method: 'DELETE' });
}

async function getSets(categoryId = null) {
    const query = categoryId ? `?category_id=${categoryId}` : '';
    return apiRequest(`/sets${query}`);
}

async function createSet(formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/sets`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Error creating set');
    }
    return response.json();
}

async function deleteSet(id) {
    return apiRequest(`/sets/${id}`, { method: 'DELETE' });
}

async function getBadges(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.set_id) query.append('set_id', params.set_id);
    if (params.condition) query.append('condition', params.condition);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    const queryString = query.toString();
    return apiRequest(`/badges${queryString ? `?${queryString}` : ''}`);
}

async function getBadge(id) {
    return apiRequest(`/badges/${id}`);
}

async function createBadge(formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/badges`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Error creating badge');
    }
    return response.json();
}

async function updateBadge(id, formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/badges/${id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Error updating badge');
    }
    return response.json();
}

async function deleteBadge(id) {
    return apiRequest(`/badges/${id}`, { method: 'DELETE' });
}

async function addBadgePhoto(badgeId, formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/badges/${badgeId}/photos`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Error adding photo');
    }
    return response.json();
}

async function deletePhotoFromBadge(badgeId, photoId) {
    return apiRequest(`/badges/${badgeId}/photos/${photoId}`, { method: 'DELETE' });
}

async function makeMainPhoto(badgeId, photoId) {
    return apiRequest(`/badges/${badgeId}/photos/${photoId}/make-main`, { method: 'PUT' });
}

async function getTags() {
    return apiRequest('/tags');
}

async function generateTelegramCode() {
    return apiRequest('/telegram/generate-code', { method: 'POST' });
}

async function exportCollection(setId = null) {
    const query = setId ? `?set_id=${setId}` : '';
    return apiRequest(`/export${query}`);
}

async function requestPasswordReset(email) {
    const response = await fetch(`${API_BASE_URL}/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Ошибка отправки');
    }
    return response.json();
}

async function getAdminStats() {
    return apiRequest('/admin/stats');
}

async function getAdminUsers(search = '') {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return apiRequest(`/admin/users${query}`);
}

async function createAdminUser(email, password) {
    return apiRequest('/admin/users', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
}

async function deleteAdminUser(userId) {
    return apiRequest(`/admin/users/${userId}`, { method: 'DELETE' });
}