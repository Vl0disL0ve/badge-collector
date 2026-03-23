const API_BASE_URL = 'http://localhost:8000/api';

function getToken() {
    return localStorage.getItem('access_token');
}

async function apiRequest(endpoint, options = {}) {
    const headers = {
        ...options.headers,
    };
    
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
        throw new Error('Сессия истекла');
    }
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || error.message || 'Ошибка запроса');
    }
    
    if (response.status === 204) {
        return null;
    }
    
    return response.json();
}

// ========== АУТЕНТИФИКАЦИЯ ==========

async function register(email, password) {
    const response = await fetch(`${API_BASE_URL}/register?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`, {
        method: 'POST',
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Ошибка регистрации');
    }
    
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify({ email }));
    return data;
}

async function login(email, password) {
    const response = await fetch(`${API_BASE_URL}/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`, {
        method: 'POST',
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Ошибка входа');
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

// ========== КАТЕГОРИИ ==========

async function getCategories() {
    return apiRequest('/categories');
}

async function createCategory(name, description) {
    return apiRequest(`/categories?name=${encodeURIComponent(name)}&description=${encodeURIComponent(description)}`, {
        method: 'POST',
    });
}

// ========== НАБОРЫ ==========

async function getSets() {
    return apiRequest('/sets');
}

// ========== ЗНАЧКИ ==========

async function getBadges(params = {}) {
    const queryParams = new URLSearchParams();
    if (params.search) queryParams.append('search', params.search);
    if (params.category_id) queryParams.append('category_id', params.category_id);
    if (params.set_id) queryParams.append('set_id', params.set_id);
    if (params.condition) queryParams.append('condition', params.condition);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.offset) queryParams.append('offset', params.offset);
    
    const queryString = queryParams.toString();
    const endpoint = `/badges${queryString ? `?${queryString}` : ''}`;
    return apiRequest(endpoint);
}

async function getBadge(id) {
    return apiRequest(`/badges/${id}`);
}

async function createBadge(formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/badges`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Ошибка создания');
    }
    
    return response.json();
}

async function updateBadge(id, formData) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/badges/${id}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Ошибка обновления');
    }
    
    return response.json();
}

async function deleteBadge(id) {
    return apiRequest(`/badges/${id}`, { method: 'DELETE' });
}

// ========== ЭКСПОРТ ==========

async function exportCollection() {
    const response = await fetch(`${API_BASE_URL}/export`, {
        headers: {
            'Authorization': `Bearer ${getToken()}`,
        },
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Ошибка экспорта');
    }
    
    return response.json();
}