let currentPage = 1;
let totalPages = 1;
let currentFilters = { search: '', category_id: '', condition: '' };

async function loadBadges() {
    const params = {
        offset: (currentPage - 1) * 10,
        limit: 10,
    };
    if (currentFilters.search) params.search = currentFilters.search;
    if (currentFilters.category_id) params.category_id = currentFilters.category_id;
    if (currentFilters.condition) params.condition = currentFilters.condition;
    
    const grid = document.getElementById('badgesGrid');
    if (!grid) return;
    
    grid.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await getBadges(params);
        
        // Бэкенд возвращает {total, items, limit, offset}
        const badges = response.items || [];
        const total = response.total || 0;
        
        totalPages = Math.ceil(total / 10) || 1;
        
        if (badges.length === 0) {
            grid.innerHTML = '<div class="loading">✨ В коллекции пока нет значков. Добавьте первый через "Добавить значок"</div>';
            return;
        }
        
        // Здесь badges ТОЧНО массив, потому что мы взяли response.items
        grid.innerHTML = badges.map(badge => renderBadgeCard(badge)).join('');
        
        // Обработчики удаления
        document.querySelectorAll('.delete-badge').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = btn.dataset.id;
                if (confirm('Удалить этот значок?')) {
                    await deleteBadge(id);
                    loadBadges();
                }
            });
        });
        
        renderPagination();
        
    } catch (error) {
        console.error('Error loading badges:', error);
        grid.innerHTML = `<div class="loading">❌ Ошибка: ${error.message}</div>`;
    }
}

function renderBadgeCard(badge) {
    const photoUrl = badge.photo_url ? `http://localhost:8000${badge.photo_url}` : null;
    
    const conditionMap = {
        excellent: 'Отличное',
        good: 'Хорошее',
        average: 'Среднее',
        poor: 'Плохое',
    };
    
    return `
        <div class="badge-card">
            <div class="badge-image">
                ${photoUrl ? `<img src="${photoUrl}" alt="${escapeHtml(badge.name)}">` : '<span style="font-size: 48px;">🏷️</span>'}
            </div>
            <div class="badge-info">
                <h3 title="${escapeHtml(badge.name)}">${escapeHtml(badge.name.length > 30 ? badge.name.substring(0, 27) + '...' : badge.name)}</h3>
                <div class="badge-meta">
                    ${badge.year ? `<span>${badge.year}</span>` : ''}
                    ${badge.condition ? `<span>${conditionMap[badge.condition] || badge.condition}</span>` : ''}
                </div>
                <div class="badge-actions">
                    <a href="badge-detail.html?id=${badge.id}">👁️</a>
                    <a href="add-badge.html?id=${badge.id}">✏️</a>
                    <button class="delete-badge" data-id="${badge.id}">🗑️</button>
                </div>
            </div>
        </div>
    `;
}

function renderPagination() {
    const container = document.getElementById('pagination');
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = '';
        return;
    }
    
    let html = '<button id="prevPage" ' + (currentPage === 1 ? 'disabled' : '') + '>←</button>';
    
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }
    
    html += '<button id="nextPage" ' + (currentPage === totalPages ? 'disabled' : '') + '>→</button>';
    container.innerHTML = html;
    
    document.getElementById('prevPage')?.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadBadges();
        }
    });
    
    document.getElementById('nextPage')?.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadBadges();
        }
    });
    
    document.querySelectorAll('[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            currentPage = parseInt(btn.dataset.page);
            loadBadges();
        });
    });
}

async function loadCategories() {
    try {
        const categories = await getCategories();
        const select = document.getElementById('categoryFilter');
        if (select) {
            select.innerHTML = '<option value="">📂 Все категории</option>' +
                categories.map(cat => `<option value="${cat.id}">${escapeHtml(cat.name)}</option>`).join('');
            
            select.addEventListener('change', (e) => {
                currentFilters.category_id = e.target.value;
                currentPage = 1;
                loadBadges();
            });
        }
    } catch (error) {
        console.error('Ошибка загрузки категорий:', error);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем авторизацию
    const token = localStorage.getItem('access_token');
    if (!token && !window.location.pathname.includes('login.html') && !window.location.pathname.includes('register.html')) {
        window.location.href = 'login.html';
        return;
    }
    
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                currentFilters.search = e.target.value;
                currentPage = 1;
                loadBadges();
            }, 500);
        });
    }
    
    const conditionFilter = document.getElementById('conditionFilter');
    if (conditionFilter) {
        conditionFilter.addEventListener('change', (e) => {
            currentFilters.condition = e.target.value;
            currentPage = 1;
            loadBadges();
        });
    }
    
    const resetBtn = document.getElementById('resetFiltersBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            currentFilters = { search: '', category_id: '', condition: '' };
            currentPage = 1;
            if (searchInput) searchInput.value = '';
            if (conditionFilter) conditionFilter.value = '';
            const catFilter = document.getElementById('categoryFilter');
            if (catFilter) catFilter.value = '';
            loadBadges();
        });
    }
    
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
            try {
                const result = await exportCollection();
                if (result.file_url) {
                    window.open(`http://localhost:8000${result.file_url}`, '_blank');
                } else {
                    alert('Ошибка: не получен URL файла');
                }
            } catch (error) {
                alert('Ошибка экспорта: ' + error.message);
            }
        });
    }
    
    // Загружаем категории и значки
    loadCategories();
    loadBadges();
});