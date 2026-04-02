// pages/sets.js
let allCategories = [];
let selectedCategoryIds = [];
let editSelectedCategoryIds = [];
let currentEditSetId = null;

let detectedBadges = [];
let currentSetPhotoFile = null;
let currentSetPhotoUrl = null;
let rectCanvas = null;
let rectCtx = null;
let rectImg = null;
let isDrawing = false;
let startX, startY;

async function loadAllCategories() {
    try {
        allCategories = await getCategories();
        renderCategorySelectors();
    } catch (error) {
        console.error('Error loading categories:', error);
        allCategories = [];
    }
}

function renderCategorySelectors() {
    const selectedContainer = document.getElementById('selectedCategories');
    const availableContainer = document.getElementById('availableCategories');
    if (selectedContainer && availableContainer) {
        renderSelectedCategories(selectedContainer, selectedCategoryIds);
        renderAvailableCategories(availableContainer, selectedCategoryIds);
    }
}

function renderSelectedCategories(container, selectedIds) {
    const selectedCats = allCategories.filter(c => selectedIds.includes(c.id));
    container.innerHTML = selectedCats.length === 0 
        ? '<div style="color:#999;">Нет выбранных категорий</div>'
        : selectedCats.map(cat => `
            <span class="category-chip">
                ${escapeHtml(cat.name)}
                <span class="remove" onclick="removeCategoryFromSet(${cat.id})">×</span>
            </span>
        `).join('');
}

function renderAvailableCategories(container, selectedIds) {
    const availableCats = allCategories.filter(c => !selectedIds.includes(c.id));
    container.innerHTML = availableCats.length === 0
        ? '<div style="color:#999;">Нет доступных категорий</div>'
        : availableCats.map(cat => `
            <span class="category-option" onclick="addCategoryToSet(${cat.id})">
                ${escapeHtml(cat.name)}
            </span>
        `).join('');
}

function addCategoryToSet(categoryId) {
    if (!selectedCategoryIds.includes(categoryId)) {
        selectedCategoryIds.push(categoryId);
        renderCategorySelectors();
    }
}

function removeCategoryFromSet(categoryId) {
    selectedCategoryIds = selectedCategoryIds.filter(id => id !== categoryId);
    renderCategorySelectors();
}

function renderEditCategorySelectors() {
    const selectedContainer = document.getElementById('editSelectedCategories');
    const availableContainer = document.getElementById('editAvailableCategories');
    if (selectedContainer && availableContainer) {
        const selectedCats = allCategories.filter(c => editSelectedCategoryIds.includes(c.id));
        selectedContainer.innerHTML = selectedCats.length === 0 
            ? '<div style="color:#999;">Нет выбранных категорий</div>'
            : selectedCats.map(cat => `
                <span class="category-chip">
                    ${escapeHtml(cat.name)}
                    <span class="remove" onclick="removeEditCategory(${cat.id})">×</span>
                </span>
            `).join('');
        
        const availableCats = allCategories.filter(c => !editSelectedCategoryIds.includes(c.id));
        availableContainer.innerHTML = availableCats.length === 0
            ? '<div style="color:#999;">Нет доступных категорий</div>'
            : availableCats.map(cat => `
                <span class="category-option" onclick="addEditCategory(${cat.id})">
                    ${escapeHtml(cat.name)}
                </span>
            `).join('');
    }
}

function addEditCategory(categoryId) {
    if (!editSelectedCategoryIds.includes(categoryId)) {
        editSelectedCategoryIds.push(categoryId);
        renderEditCategorySelectors();
    }
}

function removeEditCategory(categoryId) {
    editSelectedCategoryIds = editSelectedCategoryIds.filter(id => id !== categoryId);
    renderEditCategorySelectors();
}

async function loadSets() {
    const grid = document.getElementById('setsGrid');
    grid.innerHTML = '<div class="loading">Загрузка...</div>';
    try {
        const sets = await getSets();
        if (sets.length === 0) {
            grid.innerHTML = '<div class="loading">📭 У вас пока нет наборов</div>';
            return;
        }
        grid.innerHTML = sets.map(set => `
            <div class="badge-card">
                <div class="badge-image">
                    ${set.photo_path ? `<img src="http://localhost:8000${set.photo_path}" alt="${escapeHtml(set.name)}">` : '<span style="font-size: 3rem;">📦</span>'}
                </div>
                <div class="badge-info">
                    <h3>${escapeHtml(set.name)}</h3>
                    <p>${escapeHtml(set.description || '')}</p>
                    <div class="badge-meta"><span>📊 ${set.collected_count || 0}/${set.total_count}</span></div>
                    <div class="badge-actions">
                        <a href="badges.html?set_id=${set.id}">🏷️ Открыть</a>
                        <button class="edit-set" data-id="${set.id}" data-name="${escapeHtml(set.name)}" data-desc="${escapeHtml(set.description || '')}" data-total="${set.total_count}" data-categories='${JSON.stringify(set.categories || [])}'>✏️</button>
                        <button class="delete-set" data-id="${set.id}">🗑️</button>
                    </div>
                </div>
            </div>
        `).join('');
        
        document.querySelectorAll('.delete-set').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (confirm('Удалить набор?')) {
                    await deleteSet(btn.dataset.id);
                    loadSets();
                }
            });
        });
        
        document.querySelectorAll('.edit-set').forEach(btn => {
            btn.addEventListener('click', () => {
                const categories = JSON.parse(btn.dataset.categories) || [];
                editSelectedCategoryIds = categories.map(c => c.id);
                currentEditSetId = btn.dataset.id;
                openEditModal(btn.dataset.id, btn.dataset.name, btn.dataset.desc, btn.dataset.total);
            });
        });
    } catch (error) {
        grid.innerHTML = `<div class="loading">❌ ${error.message}</div>`;
    }
}

function openEditModal(id, name, desc, total) {
    const modal = document.getElementById('editSetModal');
    document.getElementById('editSetName').value = name;
    document.getElementById('editSetDescription').value = desc;
    document.getElementById('editSetTotal').value = total;
    renderEditCategorySelectors();
    document.getElementById('editSetForm').onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData();
        fd.append('name', document.getElementById('editSetName').value);
        fd.append('description', document.getElementById('editSetDescription').value);
        fd.append('total_count', parseInt(document.getElementById('editSetTotal').value));
        fd.append('category_ids', JSON.stringify(editSelectedCategoryIds));
        await updateSet(id, fd);
        modal.style.display = 'none';
        loadSets();
        showSuccess('Набор обновлён');
    };
    modal.style.display = 'flex';
}

function closeEditModal() { 
    document.getElementById('editSetModal').style.display = 'none'; 
}

// ========== ДЕТЕКЦИЯ ==========
document.getElementById('setPhoto')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    currentSetPhotoFile = file;
    currentSetPhotoUrl = URL.createObjectURL(file);
    
    const section = document.getElementById('detectionSection');
    const statusDiv = document.getElementById('detectionStatus');
    section.style.display = 'block';
    statusDiv.className = 'status status-info';
    statusDiv.textContent = '🔍 Анализ фото, поиск значков...';
    
    try {
        const result = await detectBadgesOnSet(file);
        
        if (result.success && result.badges_count > 0) {
            detectedBadges = result.badges;
            statusDiv.className = 'status status-success';
            statusDiv.textContent = `✅ Найдено ${result.badges_count} значков. Выделите мышкой, чтобы добавить новые, или удалите лишние.`;
            drawCanvas();
            renderBadgeList();
        } else {
            detectedBadges = [];
            statusDiv.className = 'status status-error';
            statusDiv.textContent = `❌ Значки не найдены: ${result.message || 'попробуйте другое фото'}`;
            drawCanvas();
            renderBadgeList();
        }
    } catch (error) {
        console.error('Detection error:', error);
        detectedBadges = [];
        statusDiv.className = 'status status-error';
        statusDiv.textContent = `❌ Ошибка: ${error.message}`;
        drawCanvas();
        renderBadgeList();
    }
});

function drawCanvas() {
    const canvas = document.getElementById('rectCanvas');
    if (!canvas) return;
    rectCanvas = canvas;
    rectCtx = canvas.getContext('2d');
    
    const img = new Image();
    img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        rectCtx.drawImage(img, 0, 0);
        rectImg = img;
        
        detectedBadges.forEach((b, idx) => {
            rectCtx.strokeStyle = '#667eea';
            rectCtx.lineWidth = 3;
            rectCtx.strokeRect(b.x, b.y, b.width, b.height);
            rectCtx.fillStyle = 'rgba(102,126,234,0.2)';
            rectCtx.fillRect(b.x, b.y, b.width, b.height);
            
            rectCtx.font = `bold ${Math.min(24, Math.floor(b.height / 3))}px sans-serif`;
            rectCtx.fillStyle = '#667eea';
            rectCtx.fillRect(b.x + 2, b.y + 2, 30, 30);
            rectCtx.fillStyle = '#ffffff';
            rectCtx.fillText(`${idx + 1}`, b.x + 5, b.y + 25);
        });
    };
    img.src = currentSetPhotoUrl;
}

function renderBadgeList() {
    const list = document.getElementById('badgeList');
    if (!list) return;
    
    if (detectedBadges.length === 0) {
        list.innerHTML = '<div style="text-align:center; padding:1rem; color:#999;">Нет значков. Выделите область на фото, чтобы добавить.</div>';
        return;
    }
    
    list.innerHTML = detectedBadges.map((b, i) => `
        <div class="badge-item" data-idx="${i}">
            <span style="font-weight:bold; background:#667eea; color:white; width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center; border-radius:50%;">${i+1}</span>
            <input type="text" class="badge-name" value="${escapeHtml(b.name)}" data-idx="${i}">
            <button class="remove-badge" data-idx="${i}">🗑️</button>
        </div>
    `).join('');
    
    document.querySelectorAll('.badge-name').forEach(inp => {
        inp.addEventListener('change', (e) => {
            const idx = parseInt(e.target.dataset.idx);
            detectedBadges[idx].name = e.target.value;
            drawCanvas();
        });
    });
    
    document.querySelectorAll('.remove-badge').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.idx);
            detectedBadges.splice(idx, 1);
            drawCanvas();
            renderBadgeList();
        });
    });
}

// ========== РИСОВАНИЕ НА CANVAS ==========
document.getElementById('rectCanvas')?.addEventListener('mousedown', (e) => {
    if (!rectCanvas) return;
    const rect = e.target.getBoundingClientRect();
    const scaleX = rectCanvas.width / rect.width;
    const scaleY = rectCanvas.height / rect.height;
    startX = (e.clientX - rect.left) * scaleX;
    startY = (e.clientY - rect.top) * scaleY;
    isDrawing = true;
});

document.getElementById('rectCanvas')?.addEventListener('mousemove', (e) => {
    if (!isDrawing || !rectCanvas) return;
    const rect = e.target.getBoundingClientRect();
    const scaleX = rectCanvas.width / rect.width;
    const scaleY = rectCanvas.height / rect.height;
    const currX = (e.clientX - rect.left) * scaleX;
    const currY = (e.clientY - rect.top) * scaleY;
    
    rectCtx.clearRect(0, 0, rectCanvas.width, rectCanvas.height);
    rectCtx.drawImage(rectImg, 0, 0);
    detectedBadges.forEach(b => {
        rectCtx.strokeStyle = '#667eea';
        rectCtx.strokeRect(b.x, b.y, b.width, b.height);
        rectCtx.fillStyle = 'rgba(102,126,234,0.2)';
        rectCtx.fillRect(b.x, b.y, b.width, b.height);
    });
    rectCtx.strokeStyle = '#10b981';
    rectCtx.setLineDash([5,5]);
    rectCtx.strokeRect(startX, startY, currX - startX, currY - startY);
    rectCtx.setLineDash([]);
});

document.getElementById('rectCanvas')?.addEventListener('mouseup', (e) => {
    if (!isDrawing) return;
    isDrawing = false;
    const rect = e.target.getBoundingClientRect();
    const scaleX = rectCanvas.width / rect.width;
    const scaleY = rectCanvas.height / rect.height;
    const endX = (e.clientX - rect.left) * scaleX;
    const endY = (e.clientY - rect.top) * scaleY;
    const x = Math.min(startX, endX);
    const y = Math.min(startY, endY);
    const w = Math.abs(endX - startX);
    const h = Math.abs(endY - startY);
    if (w > 20 && h > 20) {
        detectedBadges.push({ 
            id: detectedBadges.length, 
            name: `Значок ${detectedBadges.length+1}`, 
            x: Math.floor(x), 
            y: Math.floor(y), 
            width: Math.floor(w), 
            height: Math.floor(h) 
        });
        drawCanvas();
        renderBadgeList();
        const statusDiv = document.getElementById('detectionStatus');
        statusDiv.className = 'status status-success';
        statusDiv.textContent = `✅ Добавлен значок. Всего: ${detectedBadges.length}`;
        setTimeout(() => {
            statusDiv.className = 'status status-info';
            statusDiv.textContent = `📌 ${detectedBadges.length} значков. Выделяйте области для добавления.`;
        }, 2000);
    }
});

// ========== СОХРАНЕНИЕ ЗНАЧКОВ ==========
async function saveBadgesToSet(setId) {
    let saved = 0;
    for (let i = 0; i < detectedBadges.length; i++) {
        const b = detectedBadges[i];
        try {
            const fd = new FormData();
            fd.append('photo', currentSetPhotoFile);
            fd.append('x', b.x);
            fd.append('y', b.y);
            fd.append('width', b.width);
            fd.append('height', b.height);
            
            const crop = await fetch('http://localhost:8000/api/crop-image', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${getToken()}` },
                body: fd
            });
            const cropRes = await crop.json();
            
            if (cropRes.success) {
                const imgBlob = await fetch(`http://localhost:8000${cropRes.image_url}`).then(r => r.blob());
                const badgeFd = new FormData();
                badgeFd.append('name', b.name);
                badgeFd.append('set_id', setId);
                badgeFd.append('photos', imgBlob, `badge_${i+1}.jpg`);
                await createBadge(badgeFd);
                saved++;
            }
        } catch (err) { 
            console.error('Error saving badge:', err); 
        }
    }
    return saved;
}

// ========== СОЗДАНИЕ НАБОРА ==========
document.getElementById('createSetForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fd = new FormData();
    fd.append('name', document.getElementById('setName').value);
    fd.append('description', document.getElementById('setDescription').value);
    fd.append('total_count', parseInt(document.getElementById('totalCount').value));
    fd.append('category_ids', JSON.stringify(selectedCategoryIds));
    
    if (currentSetPhotoFile) {
        fd.append('photo', currentSetPhotoFile);
    }
    
    try {
        const newSet = await createSet(fd);
        
        if (detectedBadges.length > 0) {
            const saved = await saveBadgesToSet(newSet.id);
            showSuccess(`Сохранено ${saved} из ${detectedBadges.length} значков`, 'createSuccess');
        }
        
        document.getElementById('setName').value = '';
        document.getElementById('setDescription').value = '';
        document.getElementById('totalCount').value = '';
        document.getElementById('setPhoto').value = '';
        selectedCategoryIds = [];
        detectedBadges = [];
        currentSetPhotoFile = null;
        currentSetPhotoUrl = null;
        document.getElementById('detectionSection').style.display = 'none';
        renderCategorySelectors();
        loadSets();
        
    } catch (error) {
        console.error('Create set error:', error);
        showError(error.message, 'createError');
    }
});

document.getElementById('saveDetectedBtn')?.addEventListener('click', () => {
    if (detectedBadges.length > 0) {
        showSuccess(`Подготовлено ${detectedBadges.length} значков. Сохранятся при создании набора.`);
    } else {
        showError('Нет значков для сохранения');
    }
});

document.getElementById('editSetModal')?.addEventListener('click', (e) => {
    if (e.target === document.getElementById('editSetModal')) closeEditModal();
});

checkAuth().then(async () => {
    await loadAllCategories();
    loadSets();
});