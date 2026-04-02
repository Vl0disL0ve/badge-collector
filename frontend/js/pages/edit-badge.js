// pages/edit-badge.js
const badgeId = new URLSearchParams(window.location.search).get('id');
let existingPhotos = [];
let newPhotoFiles = [];
let mainPhotoId = null;
let tagsAutocomplete = null;
let currentTags = [];

async function loadData() {
    if (!badgeId) { window.location.href = '/html/collection/index.html'; return; }
    try {
        const badge = await getBadge(badgeId);
        document.getElementById('name').value = badge.name;
        document.getElementById('description').value = badge.description || '';
        document.getElementById('year').value = badge.year || '';
        document.getElementById('material').value = badge.material || '';
        document.getElementById('condition').value = badge.condition || '';
        
        currentTags = badge.tags || [];
        if (tagsAutocomplete) {
            tagsAutocomplete.setTags(currentTags);
        } else {
            initTagsAutocomplete();
        }
        
        existingPhotos = badge.photos || [];
        mainPhotoId = existingPhotos.find(p => p.is_main)?.id || existingPhotos[0]?.id;
        
        await loadSets();
        if (badge.set_id) document.getElementById('set_id').value = badge.set_id;
        renderExistingPhotos();
    } catch (error) { showError('Ошибка загрузки: ' + error.message); }
}

function initTagsAutocomplete() {
    tagsAutocomplete = new TagsAutocomplete('tagInput', 'tagsContainer', currentTags);
}

async function loadSets() {
    try {
        const sets = await getSets();
        const select = document.getElementById('set_id');
        select.innerHTML = '<option value="">Выберите набор</option>';
        sets.forEach(set => select.add(new Option(`${set.name} (${set.collected_count || 0}/${set.total_count})`, set.id)));
    } catch (error) { showError('Не удалось загрузить наборы'); }
}

function renderExistingPhotos() {
    const gallery = document.getElementById('existingPhotosGallery');
    if (!existingPhotos.length) { gallery.innerHTML = '<div style="color:#999; padding:10px;">Нет фотографий</div>'; return; }
    gallery.innerHTML = '';
    existingPhotos.forEach((photo, idx) => {
        const isMain = (photo.id === mainPhotoId);
        const div = document.createElement('div');
        div.className = 'gallery-item';
        div.innerHTML = `
            <img src="http://localhost:8000${photo.file_path}">
            <div class="gallery-badge ${isMain ? 'main' : ''}">${isMain ? '⭐' : (idx+1)}</div>
            <div class="gallery-overlay">
                <a href="edit-photo.html?badge_id=${badgeId}&photo_id=${photo.id}" class="edit-existing" style="background:none;border:none;color:white;cursor:pointer;text-decoration:none;">✏️</a>
                <button class="set-main-existing" data-id="${photo.id}">★</button>
                <button class="delete-existing" data-id="${photo.id}">🗑️</button>
            </div>
        `;
        div.querySelector('.set-main-existing').onclick = async (e) => {
            e.stopPropagation();
            try {
                await makeMainPhoto(badgeId, photo.id);
                mainPhotoId = photo.id;
                renderExistingPhotos();
                showSuccess('Главное фото обновлено', 'successMsg');
            } catch (error) { showError('Ошибка: ' + error.message); }
        };
        div.querySelector('.delete-existing').onclick = async (e) => {
            e.stopPropagation();
            if (!confirm('Удалить это фото?')) return;
            try {
                await deletePhotoFromBadge(badgeId, photo.id);
                existingPhotos = existingPhotos.filter(p => p.id !== photo.id);
                if (mainPhotoId === photo.id && existingPhotos.length) mainPhotoId = existingPhotos[0].id;
                renderExistingPhotos();
                showSuccess('Фото удалено', 'successMsg');
            } catch (error) { showError('Ошибка: ' + error.message); }
        };
        gallery.appendChild(div);
    });
}

function renderNewPhotos() {
    const gallery = document.getElementById('newPhotosGallery');
    gallery.innerHTML = '';
    newPhotoFiles.forEach((file, idx) => {
        const div = document.createElement('div');
        div.className = 'gallery-item';
        div.innerHTML = `
            <img src="${URL.createObjectURL(file)}">
            <div class="gallery-badge">Н${idx+1}</div>
            <div class="gallery-overlay">
                <button class="remove-new" data-idx="${idx}">🗑️</button>
            </div>
        `;
        div.querySelector('.remove-new').onclick = () => { newPhotoFiles.splice(idx, 1); renderNewPhotos(); };
        gallery.appendChild(div);
    });
}

document.getElementById('badgeForm').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append('name', document.getElementById('name').value);
    if (document.getElementById('description').value) fd.append('description', document.getElementById('description').value);
    if (document.getElementById('year').value) fd.append('year', document.getElementById('year').value);
    if (document.getElementById('material').value) fd.append('material', document.getElementById('material').value);
    if (document.getElementById('condition').value) fd.append('condition', document.getElementById('condition').value);
    const setId = document.getElementById('set_id').value;
    if (!setId) { showError('Выберите набор'); return; }
    fd.append('set_id', setId);
    
    const tags = tagsAutocomplete ? tagsAutocomplete.getTags() : [];
    if (tags.length) fd.append('tags', JSON.stringify(tags));
    
    newPhotoFiles.forEach(f => fd.append('new_photos', f));
    try {
        await updateBadge(badgeId, fd);
        showSuccess('✅ Значок сохранён!', 'successMsg');
        setTimeout(() => window.location.href = `/html/collection/badge-detail.html?id=${badgeId}`, 1500);
    } catch (error) { showError(error.message); }
};

document.getElementById('newPhotos').onchange = (e) => {
    const files = Array.from(e.target.files);
    if (existingPhotos.length + newPhotoFiles.length + files.length > 5) { showError('Максимум 5 фото'); return; }
    newPhotoFiles.push(...files);
    renderNewPhotos();
    e.target.value = '';
};

checkAuth().then(() => { loadData(); });