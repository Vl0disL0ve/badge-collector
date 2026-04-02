function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function getToken() {
    return localStorage.getItem('access_token');
}

function showError(message, elementId = 'errorMsg') {
    const div = document.getElementById(elementId);
    if (div) {
        div.textContent = message;
        div.style.display = 'block';
        setTimeout(() => div.style.display = 'none', 5000);
    } else {
        alert(message);
    }
}

function showSuccess(message, elementId = 'successMsg') {
    const div = document.getElementById(elementId);
    if (div) {
        div.textContent = message;
        div.style.display = 'block';
        setTimeout(() => div.style.display = 'none', 3000);
    }
}