// pages/index.js
let currentPage = 1;
let totalPages = 1;
let currentFilters = { search: '', set_id: '', condition: '', tag_id: '' };
let tagFilterAutocomplete = null;

const conditionMap = {
    excellent: 'Отличное',
    good: 'Хорошее',
    average: 'Среднее',
    poor: 'Плохое',
};

// Класс для фильтрации по одному тегу
class SingleTagFilter {
    constructor(containerId, onSelect) {
        this.container = document.getElementById(containerId);
        this.selectedTagId = null;
        this.selectedTagName = null;
        this.onSelect = onSelect;
        this.allTags = [];
        this.init();
    }

    async init() {
        await this.loadTags();
        this.render();
    }

    async loadTags() {
        try {
            this.allTags = await getTags();
        } catch (error) {
            console.error('Error loading tags:', error);
            this.allTags = [];
        }
    }

    render() {
        this.container.innerHTML = `
            <div style="position: relative;">
                <input type="text" id="tagFilterInput" placeholder="🏷️ Фильтр по тегу..." 
                       style="width: 100%; padding: 0.6rem 1rem; border: 1px solid #ddd; border-radius: 8px;">
                <div id="tagFilterSuggestions" style="position: absolute; top: 100%; left: 0; right: 0; background: white; 
                            border: 1px solid #ddd; border-radius: 8px; max-height: 200px; overflow-y: auto; 
                            display: none; z-index: 1000;"></div>
            </div>
        `;

        this.input = document.getElementById('tagFilterInput');
        this.suggestionsDiv = document.getElementById('tagFilterSuggestions');

        if (this.selectedTagName) {
            this.input.value = this.selectedTagName;
        }

        this.input.addEventListener('input', (e) => this.onInput(e));
        this.input.addEventListener('blur', () => setTimeout(() => this.hideSuggestions(), 200));
    }

    onInput(e) {
        const query = e.target.value.trim().toLowerCase();
        
        if (query.length < 1) {
            this.hideSuggestions();
            return;
        }

        const suggestions = this.allTags
            .filter(tag => tag.name.toLowerCase().includes(query))
            .slice(0, 10);

        this.showSuggestions(suggestions);
    }

    showSuggestions(suggestions) {
        if (!this.suggestionsDiv) return;

        if (suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }

        this.suggestionsDiv.innerHTML = suggestions.map(tag => `
            <div class="tag-suggestion-item" data-id="${tag.id}" data-name="${escapeHtml(tag.name)}"
                 style="padding: 8px 12px; cursor: pointer; font-size: 14px;">
                ${escapeHtml(tag.name)}
            </div>
        `).join('');

        this.suggestionsDiv.style.display = 'block';

        document.querySelectorAll('.tag-suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                const tagId = parseInt(item.dataset.id);
                const tagName = item.dataset.name;
                this.selectTag(tagId, tagName);
            });
        });
    }

    hideSuggestions() {
        if (this.suggestionsDiv) {
            this.suggestionsDiv.style.display = 'none';
        }
    }

    selectTag(tagId, tagName) {
        this.selectedTagId = tagId;
        this.selectedTagName = tagName;
        this.input.value = tagName;
        this.hideSuggestions();
        if (this.onSelect) {
            this.onSelect(tagId);
        }
    }

    clear() {
        this.selectedTagId = null;
        this.selectedTagName = null;
        this.input.value = '';
        if (this.onSelect) {
            this.onSelect(null);
        }
    }
}

async function loadCategories() {
    try {
        const categories = await getCategories();
        const select = document.getElementById('categoryFilter');
        select.innerHTML = '<option value="">📂 Все категории</option>' +
            categories.map(cat => `<option value="${cat.id}">${escapeHtml(cat.name)}</option>`).join('');
        select.addEventListener('change', (e) => {
            currentFilters.set_id = '';
            document.getElementById('setFilter').value = '';
            loadSets(e.target.value);
            currentFilters.category_id = e.target.value;
            currentPage = 1;
            loadBadges();
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadSets(categoryId = null) {
    try {
        const sets = await getSets(categoryId);
        const select = document.getElementById('setFilter');
        select.innerHTML = '<option value="">📦 Все наборы</option>' +
            sets.map(set => `<option value="${set.id}">${escapeHtml(set.name)} (${set.collected_count}/${set.total_count})</option>`).join('');
        select.addEventListener('change', (e) => {
            currentFilters.set_id = e.target.value;
            currentPage = 1;
            loadBadges();
        });
    } catch (error) {
        console.error('Error loading sets:', error);
    }
}

function updateTagFilter(tagId) {
    currentFilters.tag_id = tagId || '';
    currentPage = 1;
    loadBadges();
}

function resetAllFilters() {
    currentFilters = { search: '', set_id: '', condition: '', tag_id: '' };
    currentPage = 1;
    
    document.getElementById('searchInput').value = '';
    document.getElementById('conditionFilter').value = '';
    document.getElementById('setFilter').value = '';
    document.getElementById('categoryFilter').value = '';
    
    if (tagFilterAutocomplete) {
        tagFilterAutocomplete.clear();
    }
    
    loadBadges();
}

async function loadBadges() {
    const params = {
        offset: (currentPage - 1) * 12,
        limit: 12,
    };
    if (currentFilters.search) params.search = currentFilters.search;
    if (currentFilters.set_id) params.set_id = currentFilters.set_id;
    if (currentFilters.condition) params.condition = currentFilters.condition;
    if (currentFilters.tag_id) params.tag_id = currentFilters.tag_id;
    
    const grid = document.getElementById('badgesGrid');
    grid.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await getBadges(params);
        const badges = response.items || [];
        const total = response.total || 0;
        totalPages = Math.ceil(total / 12) || 1;
        
        if (badges.length === 0) {
            grid.innerHTML = '<div class="empty-message" style="color:#1f2937;background:white;border-radius:12px;padding:2rem;text-align:center;">✨ В коллекции пока нет значков. Добавьте первый через "Добавить значок"</div>';
            return;
        }
        
        grid.innerHTML = badges.map(badge => {
            const photoUrl = badge.main_photo_url ? `http://localhost:8000${badge.main_photo_url}` : null;
            const tagsHtml = badge.tags && badge.tags.length > 0 
                ? `<div class="badge-tags">${badge.tags.slice(0, 3).map(t => `<span class="badge-tag">#${escapeHtml(t)}</span>`).join('')}</div>`
                : '';
            
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
                        ${tagsHtml}
                        <div class="badge-actions">
                            <a href="badge-detail.html?id=${badge.id}">👁️</a>
                            <a href="/html/badges/edit-badge.html?id=${badge.id}">✏️</a>
                            <button class="delete-badge" data-id="${badge.id}">🗑️</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
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
        if (currentPage > 1) { currentPage--; loadBadges(); }
    });
    
    document.getElementById('nextPage')?.addEventListener('click', () => {
        if (currentPage < totalPages) { currentPage++; loadBadges(); }
    });
    
    document.querySelectorAll('[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            currentPage = parseInt(btn.dataset.page);
            loadBadges();
        });
    });
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
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
        resetBtn.addEventListener('click', resetAllFilters);
    }
    
    tagFilterAutocomplete = new SingleTagFilter('tagFilterContainer', updateTagFilter);
    
    checkAuth().then(() => {
        loadCategories();
        loadSets();
        loadBadges();
    });
});