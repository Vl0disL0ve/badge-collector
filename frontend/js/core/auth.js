async function checkAuth() {
    const token = getToken();
    if (!token) {
        if (!window.location.pathname.includes('/auth/') && 
            !window.location.pathname.includes('forgot-password')) {
            window.location.href = '/html/auth/login.html';
        }
        return false;
    }
    
    try {
        const profile = await getProfile();
        return true;
    } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        if (!window.location.pathname.includes('/auth/')) {
            window.location.href = '/html/auth/login.html';
        }
        return false;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }
});