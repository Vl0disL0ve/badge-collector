// pages/categories.js
let currentCategories = [];

async function loadCategoriesList() {
    const grid = document.getElementById('categoriesGrid');
    if (!grid) return;
    
    grid.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const categories = await getCategories();
        currentCategories = categories;
        
        if (categories.length === 0) {
            grid.innerHTML = '<div class="loading">📭 У вас пока нет категорий. Создайте первую!</div>';
            return;
        }
        
        grid.innerHTML = categories.map(cat => `
            <div class="badge-card">
                <div class="badge-image" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 3rem;">📁</span>
                </div>
                <div class="badge-info">
                    <h3>${escapeHtml(cat.name)}</h3>
                    <p style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">${escapeHtml(cat.description || 'Нет описания')}</p>
                    <div class="badge-meta">
                        <span>📦 Наборов: ${cat.sets_count || 0}</span>
                    </div>
                    <div class="badge-tags">
                        ${cat.sets && cat.sets.length > 0 
                            ? cat.sets.slice(0, 3).map(s => `<span class="badge-tag category-set" data-set-id="${s.id}" style="cursor: pointer;">📦 ${escapeHtml(s.name)}</span>`).join('')
                            : '<span class="badge-tag">📦 Нет наборов</span>'}
                    </div>
                    <div class="badge-actions">
                        <button class="edit-category" data-id="${cat.id}" data-name="${escapeHtml(cat.name)}" data-desc="${escapeHtml(cat.description || '')}">✏️</button>
                        <button class="delete-category" data-id="${cat.id}" data-name="${escapeHtml(cat.name)}">🗑️</button>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Обработчики удаления
        document.querySelectorAll('.delete-category').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const name = btn.dataset.name;
                if (confirm(`Удалить категорию "${name}"? Наборы в ней не будут удалены, но связь потеряется.`)) {
                    try {
                        await deleteCategory(id);
                        loadCategoriesList();
                    } catch (error) {
                        showError('Ошибка: ' + error.message);
                    }
                }
            });
        });
        
        // Обработчики редактирования
        document.querySelectorAll('.edit-category').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                const name = btn.dataset.name;
                const desc = btn.dataset.desc;
                openEditModal(id, name, desc);
            });
        });
        
        // Обработчики клика на набор внутри категории
        document.querySelectorAll('.category-set').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const setId = btn.dataset.setId;
                if (setId) {
                    window.location.href = `badges.html?set_id=${setId}`;
                }
            });
        });
        
    } catch (error) {
        grid.innerHTML = `<div class="loading">❌ Ошибка: ${error.message}</div>`;
    }
}

function openEditModal(id, name, description) {
    const modal = document.getElementById('editCategoryModal');
    const inputName = document.getElementById('editCategoryName');
    const inputDesc = document.getElementById('editCategoryDescription');
    const form = document.getElementById('editCategoryForm');
    
    inputName.value = name;
    inputDesc.value = description;
    
    form.onsubmit = async (e) => {
        e.preventDefault();
        const newName = inputName.value.trim();
        if (!newName) {
            showError('Введите название категории', 'modalError');
            return;
        }
        
        try {
            await updateCategory(id, {
                name: newName,
                description: inputDesc.value.trim() || null
            });
            modal.style.display = 'none';
            loadCategoriesList();
            showSuccess('Категория обновлена', 'createSuccess');
        } catch (error) {
            showError(error.message, 'modalError');
        }
    };
    
    modal.style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('editCategoryModal').style.display = 'none';
}

// Создание категории
document.getElementById('createCategoryForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('categoryName').value.trim();
    const description = document.getElementById('categoryDescription').value.trim();
    
    if (!name) {
        showError('Введите название категории', 'createError');
        return;
    }
    
    try {
        await createCategory({ name, description: description || null });
        document.getElementById('categoryName').value = '';
        document.getElementById('categoryDescription').value = '';
        loadCategoriesList();
        showSuccess('Категория создана', 'createSuccess');
    } catch (error) {
        showError(error.message, 'createError');
    }
});

// Закрытие модалки по клику вне
document.getElementById('editCategoryModal')?.addEventListener('click', (e) => {
    if (e.target === document.getElementById('editCategoryModal')) {
        closeEditModal();
    }
});

// Инициализация
checkAuth().then(loadCategoriesList);