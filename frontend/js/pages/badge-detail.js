// pages/badge-detail.js
const urlParams = new URLSearchParams(window.location.search);
const badgeId = urlParams.get('id');

const conditionMap = {
    excellent: 'Отличное',
    good: 'Хорошее',
    average: 'Среднее',
    poor: 'Плохое',
};

async function loadBadgeDetail() {
    if (!badgeId) {
        document.getElementById('badgeDetail').innerHTML = '<div class="error">ID значка не указан</div>';
        return;
    }
    
    try {
        const badge = await getBadge(badgeId);
        renderBadgeDetail(badge);
        loadSimilarBadges();
    } catch (error) {
        document.getElementById('badgeDetail').innerHTML = `<div class="error">❌ Ошибка: ${error.message}</div>`;
    }
}

async function loadSimilarBadges() {
    const section = document.getElementById('similarBadgesSection');
    const grid = document.getElementById('similarBadgesGrid');
    if (!section) return;
    
    try {
        const result = await getSimilarBadges(badgeId, 0.75);
        
        if (result.similar && result.similar.length > 0) {
            section.style.display = 'block';
            grid.innerHTML = result.similar.map(b => `
                <div class="badge-card">
                    <div class="badge-image">
                        ${b.main_photo_url ? `<img src="http://localhost:8000${b.main_photo_url}" alt="${escapeHtml(b.name)}">` : '<span style="font-size: 3rem;">🏷️</span>'}
                    </div>
                    <div class="badge-info">
                        <h3>${escapeHtml(b.name.length > 25 ? b.name.substring(0, 22) + '...' : b.name)}</h3>
                        <div class="badge-meta">
                            <span class="similarity-badge" style="background: #10b981; font-size: 0.8rem;">🎯 ${b.similarity}% совпадение</span>
                        </div>
                        <div class="badge-actions">
                            <a href="badge-detail.html?id=${b.id}" class="btn-outline" style="text-decoration: none; font-size: 0.8rem; padding: 0.4rem 0.8rem;">👁️ Открыть</a>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            section.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading similar badges:', error);
        section.style.display = 'none';
    }
}

async function setMainPhoto(photoId) {
    try {
        await makeMainPhoto(badgeId, photoId);
        loadBadgeDetail();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

async function deletePhoto(photoId) {
    if (confirm('Удалить это фото?')) {
        try {
            await deletePhotoFromBadge(badgeId, photoId);
            loadBadgeDetail();
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    }
}

async function editPhoto(photoId) {
    try {
        const badge = await getBadge(badgeId);
        const photo = badge.photos?.find(p => p.id == photoId);
        if (!photo) throw new Error('Фото не найдено');
        
        const res = await fetch(`http://localhost:8000${photo.file_path}`);
        const blob = await res.blob();
        const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
        
        // Исправлено: колбэк принимает только один аргумент (editedFile)
        openPhotoEditor(file, async (editedFile) => {
            const wasMain = photo.is_main || false;
            
            await deletePhotoFromBadge(badgeId, photoId);
            
            const fd = new FormData();
            fd.append('photo', editedFile);
            const newPhoto = await addBadgePhoto(badgeId, fd);
            
            if (wasMain && newPhoto && newPhoto.id) {
                await makeMainPhoto(badgeId, newPhoto.id);
            }
            
            loadBadgeDetail();
        });
        
    } catch (error) {
        console.error('Error editing photo:', error);
        alert('Ошибка: ' + error.message);
    }
}

async function addPhoto(file) {
    if (!file) return;
    
    try {
        const currentBadge = await getBadge(badgeId);
        if (currentBadge.photos && currentBadge.photos.length >= 5) {
            alert('Максимум 5 фотографий на значок');
            return;
        }
        
        openPhotoEditor(file, async (editedFile) => {
            const fd = new FormData();
            fd.append('photo', editedFile);
            await addBadgePhoto(badgeId, fd);
            loadBadgeDetail();
        });
    } catch (error) {
        console.error('Error adding photo:', error);
        alert('Ошибка: ' + error.message);
    }
}

function renderBadgeDetail(badge) {
    const mainPhotoUrl = badge.main_photo_url ? `http://localhost:8000${badge.main_photo_url}` : null;
    
    const photosHtml = badge.photos && badge.photos.length > 0 ? `
        <div class="detail-photos">
            <h3>📸 Все фотографии (${badge.photos.length}/5)</h3>
            <div class="photos-grid">
                ${badge.photos.map(photo => `
                    <div class="detail-photo">
                        <img src="http://localhost:8000${photo.file_path}" alt="Фото">
                        <div class="photo-overlay">
                            ${!photo.is_main ? `<button onclick="setMainPhoto(${photo.id})">⭐ Главное</button>` : '<span style="color: gold;">★ Главное</span>'}
                            <button onclick="editPhoto(${photo.id})">✏️</button>
                            <button onclick="deletePhoto(${photo.id})" style="color: #ef4444;">🗑️</button>
                        </div>
                    </div>
                `).join('')}
            </div>
            ${badge.photos.length < 5 ? `
                <button onclick="document.getElementById('addPhotoInput').click()" class="btn-secondary" style="margin-top: 1rem;">➕ Добавить фото</button>
                <input type="file" id="addPhotoInput" accept="image/jpeg,image/png" style="display: none;" onchange="addPhoto(this.files[0])">
            ` : '<p style="color: #f59e0b; margin-top: 1rem;">⚠️ Достигнут лимит фотографий (5/5)</p>'}
        </div>
    ` : `
        <div class="detail-photos">
            <h3>📸 Фотографии</h3>
            <p>📷 Нет фотографий</p>
            <button onclick="document.getElementById('addPhotoInput').click()" class="btn-secondary" style="margin-top: 1rem;">➕ Добавить фото</button>
            <input type="file" id="addPhotoInput" accept="image/jpeg,image/png" style="display: none;" onchange="addPhoto(this.files[0])">
        </div>
    `;
    
    const tagsHtml = badge.tags && badge.tags.length > 0 
        ? `<div class="badge-tags" style="margin-top: 1rem;">${badge.tags.map(t => `<span class="badge-tag">#${escapeHtml(t)}</span>`).join('')}</div>`
        : '';
    
    const html = `
        <div class="detail-header">
            <h2>${escapeHtml(badge.name)}</h2>
            <div class="detail-actions">
                <button id="editBtn" class="btn-secondary">✏️ Редактировать</button>
                <button id="deleteBtn" class="btn-danger">🗑️ Удалить</button>
            </div>
        </div>
        
        <div class="detail-content">
            <div class="detail-main-photo">
                ${mainPhotoUrl ? `<img src="${mainPhotoUrl}" alt="${escapeHtml(badge.name)}">` : '<div class="no-photo">🏷️ Нет фото</div>'}
            </div>
            
            <div class="detail-info">
                <div class="info-row"><span class="info-label">Название:</span><span class="info-value">${escapeHtml(badge.name)}</span></div>
                <div class="info-row"><span class="info-label">Описание:</span><span class="info-value">${escapeHtml(badge.description) || '—'}</span></div>
                <div class="info-row"><span class="info-label">Год:</span><span class="info-value">${badge.year || '—'}</span></div>
                <div class="info-row"><span class="info-label">Материал:</span><span class="info-value">${escapeHtml(badge.material) || '—'}</span></div>
                <div class="info-row"><span class="info-label">Состояние:</span><span class="info-value">${conditionMap[badge.condition] || badge.condition || '—'}</span></div>
                <div class="info-row"><span class="info-label">Набор:</span><span class="info-value">${badge.set_name || `ID: ${badge.set_id}`}</span></div>
                <div class="info-row"><span class="info-label">Добавлен:</span><span class="info-value">${new Date(badge.created_at).toLocaleDateString('ru-RU')}</span></div>
                ${tagsHtml}
            </div>
        </div>
        ${photosHtml}
    `;
    
    document.getElementById('badgeDetail').innerHTML = html;
    
    document.getElementById('deleteBtn')?.addEventListener('click', async () => {
        if (confirm('Удалить этот значок?')) {
            await deleteBadge(badgeId);
            window.location.href = 'index.html';
        }
    });
    
    document.getElementById('editBtn')?.addEventListener('click', () => {
        window.location.href = `/html/badges/edit-badge.html?id=${badgeId}`;
    });
}

checkAuth().then(loadBadgeDetail);