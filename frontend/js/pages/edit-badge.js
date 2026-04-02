// pages/edit-badge.js
const badgeId = new URLSearchParams(window.location.search).get('id');
let existingPhotos = [];
let newPhotoFiles = [];
let mainPhotoId = null;
let tagsAutocomplete = null;
let currentTags = [];
let isSaving = false;

async function loadData() {
    if (!badgeId) { 
        window.location.href = '/html/collection/index.html'; 
        return; 
    }
    
    try {
        const badge = await getBadge(badgeId);
        
        // Заполняем основные поля
        document.getElementById('name').value = badge.name;
        document.getElementById('description').value = badge.description || '';
        document.getElementById('year').value = badge.year || '';
        document.getElementById('material').value = badge.material || '';
        document.getElementById('condition').value = badge.condition || '';
        
        // Загружаем теги
        currentTags = badge.tags || [];
        if (tagsAutocomplete) {
            tagsAutocomplete.setTags(currentTags);
        } else {
            initTagsAutocomplete();
        }
        
        // Загружаем фото
        existingPhotos = badge.photos || [];
        mainPhotoId = existingPhotos.find(p => p.is_main)?.id || existingPhotos[0]?.id;
        
        // Загружаем наборы
        await loadSets();
        if (badge.set_id) document.getElementById('set_id').value = badge.set_id;
        
        // Рендерим галереи
        renderExistingPhotos();
        renderNewPhotos();
        
    } catch (error) {
        console.error('Error loading badge:', error);
        showError('Ошибка загрузки: ' + error.message);
    }
}

function initTagsAutocomplete() {
    const container = document.getElementById('tagsContainer');
    if (!container) {
        console.error('tagsContainer not found');
        return;
    }
    
    container.innerHTML = '';
    tagsAutocomplete = new TagsAutocomplete('tagInput', 'tagsContainer', currentTags);
}

async function loadSets() {
    try {
        const sets = await getSets();
        const select = document.getElementById('set_id');
        if (!select) return;
        
        select.innerHTML = '<option value="">Выберите набор</option>';
        sets.forEach(set => {
            const option = document.createElement('option');
            option.value = set.id;
            option.textContent = `${set.name} (${set.collected_count || 0}/${set.total_count})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading sets:', error);
        showError('Не удалось загрузить наборы');
    }
}

function renderExistingPhotos() {
    const gallery = document.getElementById('existingPhotosGallery');
    if (!gallery) return;
    
    if (!existingPhotos.length) {
        gallery.innerHTML = '<div style="color:#999; padding:10px;">Нет фотографий</div>';
        return;
    }
    
    gallery.innerHTML = '';
    
    existingPhotos.forEach((photo, idx) => {
        const isMain = (photo.id === mainPhotoId);
        const div = document.createElement('div');
        div.className = 'gallery-item';
        
        const img = document.createElement('img');
        img.src = `http://localhost:8000${photo.file_path}`;
        
        const badge = document.createElement('div');
        badge.className = `gallery-badge ${isMain ? 'main' : ''}`;
        badge.textContent = isMain ? '⭐' : (idx + 1);
        
        const overlay = document.createElement('div');
        overlay.className = 'gallery-overlay';
        
        const editBtn = document.createElement('button');
        editBtn.textContent = '✏️';
        editBtn.onclick = async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            try {
                const resp = await fetch(`http://localhost:8000${photo.file_path}`);
                const blob = await resp.blob();
                const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
                
                openPhotoEditor(file, async (editedFile) => {
                    try {
                        await deletePhotoFromBadge(badgeId, photo.id);
                        const fd = new FormData();
                        fd.append('photo', editedFile);
                        const newPhoto = await addBadgePhoto(badgeId, fd);
                        
                        if (isMain && newPhoto && newPhoto.id) {
                            await makeMainPhoto(badgeId, newPhoto.id);
                        }
                        
                        await loadData();
                        showSuccess('Фото обновлено', 'successMsg');
                    } catch (err) {
                        console.error('Error saving edited photo:', err);
                        showError('Ошибка сохранения: ' + err.message);
                    }
                });
            } catch (err) {
                console.error('Error loading photo:', err);
                showError('Ошибка загрузки фото: ' + err.message);
            }
        };
        
        const setMainBtn = document.createElement('button');
        setMainBtn.textContent = '★';
        setMainBtn.onclick = async (e) => {
            e.preventDefault();
            e.stopPropagation();
            try {
                await makeMainPhoto(badgeId, photo.id);
                mainPhotoId = photo.id;
                renderExistingPhotos();
                showSuccess('Главное фото обновлено', 'successMsg');
            } catch (error) {
                console.error('Error setting main photo:', error);
                showError('Ошибка: ' + error.message);
            }
        };
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '🗑️';
        deleteBtn.onclick = async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!confirm('Удалить это фото?')) return;
            try {
                await deletePhotoFromBadge(badgeId, photo.id);
                existingPhotos = existingPhotos.filter(p => p.id !== photo.id);
                if (mainPhotoId === photo.id && existingPhotos.length) {
                    mainPhotoId = existingPhotos[0].id;
                }
                renderExistingPhotos();
                showSuccess('Фото удалено', 'successMsg');
            } catch (error) {
                console.error('Error deleting photo:', error);
                showError('Ошибка: ' + error.message);
            }
        };
        
        overlay.appendChild(editBtn);
        overlay.appendChild(setMainBtn);
        overlay.appendChild(deleteBtn);
        
        div.appendChild(img);
        div.appendChild(badge);
        div.appendChild(overlay);
        
        gallery.appendChild(div);
    });
}

function renderNewPhotos() {
    const gallery = document.getElementById('newPhotosGallery');
    if (!gallery) return;
    
    gallery.innerHTML = '';
    
    newPhotoFiles.forEach((file, idx) => {
        const div = document.createElement('div');
        div.className = 'gallery-item';
        
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        
        const badge = document.createElement('div');
        badge.className = 'gallery-badge';
        badge.textContent = `Н${idx + 1}`;
        
        const overlay = document.createElement('div');
        overlay.className = 'gallery-overlay';
        
        const editBtn = document.createElement('button');
        editBtn.textContent = '✏️';
        editBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            openPhotoEditor(file, async (editedFile) => {
                newPhotoFiles[idx] = editedFile;
                renderNewPhotos();
                showSuccess('Фото отредактировано', 'successMsg');
            });
        };
        
        const removeBtn = document.createElement('button');
        removeBtn.textContent = '🗑️';
        removeBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            newPhotoFiles.splice(idx, 1);
            renderNewPhotos();
        };
        
        overlay.appendChild(editBtn);
        overlay.appendChild(removeBtn);
        
        div.appendChild(img);
        div.appendChild(badge);
        div.appendChild(overlay);
        
        gallery.appendChild(div);
    });
}

// Инициализация после загрузки страницы
document.addEventListener('DOMContentLoaded', () => {
    // Обработчик выбора новых файлов
    const newPhotosInput = document.getElementById('newPhotos');
    if (newPhotosInput) {
        newPhotosInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            const totalFiles = existingPhotos.length + newPhotoFiles.length + files.length;
            
            if (totalFiles > 5) {
                showError('Максимум 5 фотографий на значок');
                newPhotosInput.value = '';
                return;
            }
            
            newPhotoFiles.push(...files);
            renderNewPhotos();
            newPhotosInput.value = '';
        });
    }
    
    // Обработчик формы
    const form = document.getElementById('badgeForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (isSaving) return;
            
            const name = document.getElementById('name').value.trim();
            if (!name) {
                showError('Введите название значка');
                return;
            }
            
            const setId = document.getElementById('set_id').value;
            if (!setId) {
                showError('Выберите набор');
                return;
            }
            
            isSaving = true;
            
            const fd = new FormData();
            fd.append('name', name);
            
            const description = document.getElementById('description').value;
            if (description) fd.append('description', description);
            
            const year = document.getElementById('year').value;
            if (year) fd.append('year', year);
            
            const material = document.getElementById('material').value;
            if (material) fd.append('material', material);
            
            const condition = document.getElementById('condition').value;
            if (condition) fd.append('condition', condition);
            
            fd.append('set_id', setId);
            
            const tags = tagsAutocomplete ? tagsAutocomplete.getTags() : [];
            if (tags.length) {
                fd.append('tags', JSON.stringify(tags));
            }
            
            newPhotoFiles.forEach(file => {
                fd.append('new_photos', file);
            });
            
            try {
                await updateBadge(badgeId, fd);
                showSuccess('✅ Значок сохранён!', 'successMsg');
                setTimeout(() => {
                    window.location.href = `/html/collection/badge-detail.html?id=${badgeId}`;
                }, 1500);
            } catch (error) {
                console.error('Update badge error:', error);
                showError(error.message);
                isSaving = false;
            }
        });
    }
    
    // Загружаем данные
    checkAuth().then(() => loadData());
});