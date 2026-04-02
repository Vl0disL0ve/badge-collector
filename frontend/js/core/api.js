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
        if (!window.location.pathname.includes('/auth/')) {
            window.location.href = '/html/auth/login.html';
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

// ========== AUTH ==========
async function register(email, password) {
    const data = await apiRequest('/register', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify({ email }));
    return data;
}

async function login(email, password) {
    const data = await apiRequest('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify({ email: data.user.email }));
    return data;
}

async function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/html/auth/login.html';
}

async function getProfile() {
    return apiRequest('/me');
}

// ========== CATEGORIES ==========
async function getCategories() {
    return apiRequest('/categories');
}

async function getCategory(id) {
    return apiRequest(`/categories/${id}`);
}

async function createCategory(data) {
    return apiRequest('/categories', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function updateCategory(id, data) {
    return apiRequest(`/categories/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

async function deleteCategory(id) {
    return apiRequest(`/categories/${id}`, { method: 'DELETE' });
}

// ========== SETS ==========
async function getSets(categoryId = null) {
    const query = categoryId ? `?category_id=${categoryId}` : '';
    return apiRequest(`/sets${query}`);
}

async function getSet(id) {
    return apiRequest(`/sets/${id}`);
}

async function createSet(formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/sets`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Error creating set');
    }
    return response.json();
}

async function updateSet(id, formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/sets/${id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Error updating set');
    }
    return response.json();
}

async function deleteSet(id) {
    return apiRequest(`/sets/${id}`, { method: 'DELETE' });
}

// ========== BADGES ==========
async function getBadges(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.set_id) query.append('set_id', params.set_id);
    if (params.condition) query.append('condition', params.condition);
    if (params.tag_id) query.append('tag_id', params.tag_id);
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
        body: formData
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
        body: formData
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

// ========== PHOTOS ==========
async function addBadgePhoto(badgeId, formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/badges/${badgeId}/photos`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
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

// ========== TAGS ==========
async function getTags() {
    return apiRequest('/tags');
}

async function updateTag(id, data) {
    return apiRequest(`/tags/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

async function deleteTag(id) {
    return apiRequest(`/tags/${id}`, { method: 'DELETE' });
}

// ========== SIMILARITY ==========
async function getSimilarBadges(badgeId, threshold = 0.75) {
    return apiRequest(`/badges/${badgeId}/similar?threshold=${threshold}`);
}

async function updateBadgeFeatures(badgeId) {
    return apiRequest(`/badges/${badgeId}/update-features`, { method: 'POST' });
}

async function updateAllFeatures() {
    return apiRequest('/badges/update-all-features', { method: 'POST' });
}

async function updateMyFeatures() {
    return apiRequest('/badges/update-my-features', { method: 'POST' });
}

// ========== ML ==========
async function processImage(file, autoRotate = true, removeBg = true) {
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('auto_rotate', autoRotate);
    formData.append('remove_bg', removeBg);
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/process-image`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!response.ok) throw new Error('Ошибка обработки');
    return response.json();
}

async function rotateImage(file, angle) {
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('angle', angle);
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/rotate-image`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!response.ok) throw new Error('Ошибка поворота');
    return response.json();
}

async function removeBackground(file) {
    const formData = new FormData();
    formData.append('photo', file);
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/remove-background`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!response.ok) throw new Error('Ошибка удаления фона');
    return response.json();
}

async function detectAxis(file) {
    const formData = new FormData();
    formData.append('photo', file);
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/detect-axis`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!response.ok) throw new Error('Ошибка определения оси');
    return response.json();
}

async function rotateCustom(file, angle) {
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('angle', angle);
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/rotate-custom`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!response.ok) throw new Error('Ошибка поворота');
    return response.json();
}

async function detectBadgesOnSet(file) {
    const formData = new FormData();
    formData.append('photo', file);
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/detect-badges`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (!response.ok) throw new Error('Ошибка детекции');
    return response.json();
}

// ========== EXPORT ==========
async function exportCollection(setId = null, columns = 3) {
    const params = new URLSearchParams();
    if (setId) {
        params.append('set_id', String(setId));
    }
    if (columns) {
        params.append('columns', String(columns));
    }
    const queryString = params.toString();
    const url = `/export${queryString ? `?${queryString}` : ''}`;
    console.log('Export URL:', url); // Для отладки
    return apiRequest(url);
}

// ========== ADMIN ==========
async function getAdminStats() {
    return apiRequest('/admin/stats');
}

async function getAdminUsers(search = '') {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return apiRequest(`/admin/users${query}`);
}

async function createAdminUser(email, password) {
    const token = getToken();
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/admin/users`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    
    if (!response.ok) {
        let errorMessage = 'Error creating user';
        try {
            const error = await response.json();
            errorMessage = error.detail || error.message || errorMessage;
        } catch (e) {
            errorMessage = `Server error: ${response.status}`;
        }
        throw new Error(errorMessage);
    }
    return response.json();
}

async function deleteAdminUser(userId) {
    return apiRequest(`/admin/users/${userId}`, { method: 'DELETE' });
}

// ========== TELEGRAM ==========
async function generateTelegramCode() {
    return apiRequest('/telegram/generate-code', { method: 'POST' });
}