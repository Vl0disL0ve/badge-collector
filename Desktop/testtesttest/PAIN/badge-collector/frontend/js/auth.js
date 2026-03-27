// getToken уже определён в utils.js, но если нет — добавим
if (typeof getToken === 'undefined') {
    window.getToken = function() {
        return localStorage.getItem('access_token');
    };
}

async function checkAuth() {
    const token = getToken();
    if (!token) {
        if (!window.location.pathname.includes('login.html') && 
            !window.location.pathname.includes('register.html') &&
            !window.location.pathname.includes('forgot-password.html')) {
            window.location.href = 'login.html';
        }
        return false;
    }
    
    try {
        const profile = await getProfile();
        return true;
    } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        if (!window.location.pathname.includes('login.html')) {
            window.location.href = 'login.html';
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