// pages/admin.js
let registrationsChart = null;

async function checkAdminAccess() {
    try {
        const profile = await getProfile();
        if (!profile.is_admin) { 
            document.getElementById('accessError').style.display = 'block'; 
            return false; 
        }
        document.getElementById('adminContent').style.display = 'block';
        return true;
    } catch (error) { 
        document.getElementById('accessError').style.display = 'block'; 
        return false; 
    }
}

async function loadAdminStats() {
    try {
        const stats = await getAdminStats();
        document.getElementById('totalUsers').textContent = stats.total_users || 0;
        document.getElementById('totalBadges').textContent = stats.total_badges || 0;
        document.getElementById('totalSets').textContent = stats.total_sets || 0;
        document.getElementById('totalCategories').textContent = stats.total_categories || 0;
        if (stats.registrations && registrationsChart) {
            registrationsChart.data.datasets[0].data = stats.registrations.map(r => r.count);
            registrationsChart.data.labels = stats.registrations.map(r => r.date);
            registrationsChart.update();
        }
    } catch (error) { 
        console.error('Ошибка загрузки статистики:', error); 
    }
}

async function loadUsers(search = '') {
    const tableDiv = document.getElementById('usersTable');
    tableDiv.innerHTML = '<div class="loading">Загрузка...</div>';
    try {
        const users = await getAdminUsers(search);
        if (users.length === 0) { 
            tableDiv.innerHTML = '<div class="loading">📭 Пользователи не найдены</div>'; 
            return; 
        }
        tableDiv.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Email</th>
                        <th>Telegram</th>
                        <th>Статус</th>
                        <th>Дата</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(u => `
                        <tr>
                            <td>${u.id}</td>
                            <td>${escapeHtml(u.email)}</td>
                            <td>${u.telegram_id || '—'}</td>
                            <td>${u.is_admin ? '👑 Админ' : '👤 Пользователь'}</td>
                            <td>${new Date(u.created_at).toLocaleDateString('ru-RU')}</td>
                            <td>${!u.is_admin ? `<button class="delete-user" data-id="${u.id}" data-email="${escapeHtml(u.email)}">🗑️</button>` : '—'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        document.querySelectorAll('.delete-user').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (confirm(`Удалить пользователя "${btn.dataset.email}"?`)) {
                    try {
                        await deleteAdminUser(btn.dataset.id);
                        loadUsers(document.getElementById('userSearch').value);
                        loadAdminStats();
                    } catch (error) {
                        alert('Ошибка: ' + error.message);
                    }
                }
            });
        });
    } catch (error) { 
        tableDiv.innerHTML = `<div class="loading">❌ Ошибка: ${error.message}</div>`; 
    }
}

async function initChart() {
    const ctx = document.getElementById('registrationsChart').getContext('2d');
    registrationsChart = new Chart(ctx, { 
        type: 'line', 
        data: { 
            labels: [], 
            datasets: [{ 
                label: 'Новые пользователи', 
                data: [], 
                borderColor: '#667eea', 
                backgroundColor: 'rgba(102,126,234,0.1)', 
                tension: 0.4, 
                fill: true 
            }] 
        }, 
        options: { 
            responsive: true, 
            maintainAspectRatio: true 
        } 
    });
}

async function recalcFeatures(forCurrentUserOnly = false) {
    const btn = forCurrentUserOnly ? document.getElementById('recalcMyFeaturesBtn') : document.getElementById('recalcFeaturesBtn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ Обработка...';
    
    try {
        const result = forCurrentUserOnly ? await updateMyFeatures() : await updateAllFeatures();
        alert(result.message);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function openModal() {
    const modal = document.getElementById('addUserModal');
    if (modal) {
        modal.style.display = 'flex';
        document.getElementById('newUserEmail').value = '';
        document.getElementById('newUserPassword').value = '';
        const errorDiv = document.getElementById('modalError');
        if (errorDiv) errorDiv.style.display = 'none';
    }
}

function closeModal() {
    const modal = document.getElementById('addUserModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showModalError(message) {
    const errorDiv = document.getElementById('modalError');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

// Обработчики событий
document.getElementById('userSearch')?.addEventListener('input', (e) => loadUsers(e.target.value));
document.getElementById('addUserBtn')?.addEventListener('click', openModal);
document.getElementById('closeModalBtn')?.addEventListener('click', closeModal);
document.getElementById('recalcFeaturesBtn')?.addEventListener('click', () => recalcFeatures(false));
document.getElementById('recalcMyFeaturesBtn')?.addEventListener('click', () => recalcFeatures(true));

// Закрытие модалки при клике вне
document.getElementById('addUserModal')?.addEventListener('click', (e) => {
    if (e.target === document.getElementById('addUserModal')) {
        closeModal();
    }
});

// Создание пользователя
document.getElementById('addUserForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('newUserEmail').value.trim();
    const password = document.getElementById('newUserPassword').value;
    
    if (!email || !password) {
        showModalError('Заполните все поля');
        return;
    }
    
    if (password.length < 6) {
        showModalError('Пароль должен быть не менее 6 символов');
        return;
    }
    
    try {
        await createAdminUser(email, password);
        closeModal();
        loadUsers(document.getElementById('userSearch').value);
        loadAdminStats();
        // Показываем временное уведомление об успехе
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = '✅ Пользователь создан';
        successDiv.style.marginBottom = '1rem';
        const container = document.querySelector('.form-container');
        if (container) {
            container.prepend(successDiv);
            setTimeout(() => successDiv.remove(), 3000);
        }
    } catch (error) {
        console.error('Create user error:', error);
        showModalError(error.message);
    }
});

// Инициализация
checkAuth().then(async () => { 
    if (await checkAdminAccess()) { 
        await initChart(); 
        await loadAdminStats(); 
        await loadUsers(); 
    } 
});