// pages/add-badge.js
const urlParams = new URLSearchParams(window.location.search);
const presetSetId = urlParams.get('set_id');

let photoFiles = [];
let currentEditIndex = 0;
let mainPhotoIndex = 0;
let tagsAutocomplete = null;

async function loadSets() {
    try {
        const sets = await getSets();
        const select = document.getElementById('set_id');
        select.innerHTML = '<option value="">Выберите набор</option>';
        sets.forEach(set => {
            const option = document.createElement('option');
            option.value = set.id;
            option.textContent = `${set.name} (${set.collected_count || 0}/${set.total_count})`;
            select.appendChild(option);
        });
        if (presetSetId) select.value = presetSetId;
    } catch (error) {
        showError('Не удалось загрузить наборы');
    }
}

function initTagsAutocomplete() {
    tagsAutocomplete = new TagsAutocomplete('tagInput', 'tagsContainer', []);
}

function updateGallery() {
    const gallery = document.getElementById('photoGallery');
    if (!gallery) return;
    
    gallery.innerHTML = '';
    
    if (photoFiles.length === 0) {
        gallery.innerHTML = '<div style="color:#999; padding:10px;">Нет выбранных фото</div>';
        return;
    }
    
    photoFiles.forEach((file, idx) => {
        const url = URL.createObjectURL(file);
        const isMain = (idx === mainPhotoIndex);
        const isActive = (idx === currentEditIndex);
        
        const div = document.createElement('div');
        div.className = 'gallery-item' + (isActive ? ' active' : '');
        div.innerHTML = `
            <img src="${url}" alt="Фото ${idx+1}">
            <div class="gallery-badge ${isMain ? 'main' : ''}">${isMain ? '⭐' : (idx+1)}</div>
            <div class="gallery-overlay">
                <button class="edit-photo" data-idx="${idx}">✏️</button>
                <button class="set-main" data-idx="${idx}">★</button>
                <button class="remove-photo" data-idx="${idx}">🗑️</button>
            </div>
        `;
        
        div.addEventListener('click', (e) => {
            if (!e.target.classList.contains('edit-photo') && 
                !e.target.classList.contains('set-main') && 
                !e.target.classList.contains('remove-photo')) {
                currentEditIndex = idx;
                updateGallery();
            }
        });
        
        const editBtn = div.querySelector('.edit-photo');
        if (editBtn) {
            editBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openPhotoEditor(photoFiles[idx], async (editedFile) => {
                    photoFiles[idx] = editedFile;
                    updateGallery();
                    const dataTransfer = new DataTransfer();
                    photoFiles.forEach(f => dataTransfer.items.add(f));
                    document.getElementById('photos').files = dataTransfer.files;
                    showSuccess('Фото отредактировано', 'successMsg');
                });
            });
        }
        
        const setMainBtn = div.querySelector('.set-main');
        if (setMainBtn) {
            setMainBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                mainPhotoIndex = idx;
                updateGallery();
                showSuccess('Главное фото обновлено', 'successMsg');
            });
        }
        
        const removeBtn = div.querySelector('.remove-photo');
        if (removeBtn) {
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                photoFiles.splice(idx, 1);
                if (mainPhotoIndex >= photoFiles.length) mainPhotoIndex = Math.max(0, photoFiles.length - 1);
                if (currentEditIndex >= photoFiles.length) currentEditIndex = Math.max(0, photoFiles.length - 1);
                updateGallery();
                
                const dataTransfer = new DataTransfer();
                photoFiles.forEach(f => dataTransfer.items.add(f));
                document.getElementById('photos').files = dataTransfer.files;
            });
        }
        
        gallery.appendChild(div);
    });
}

// Обработчик загрузки фото
document.getElementById('photos')?.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    if (photoFiles.length + files.length > 5) {
        showError('Можно загрузить не более 5 фотографий');
        return;
    }
    photoFiles.push(...files);
    updateGallery();
});

// Отправка формы
document.getElementById('badgeForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('name', document.getElementById('name').value);
    
    const description = document.getElementById('description').value;
    if (description) formData.append('description', description);
    
    const year = document.getElementById('year').value;
    if (year) formData.append('year', year);
    
    const material = document.getElementById('material').value;
    if (material) formData.append('material', material);
    
    const condition = document.getElementById('condition').value;
    if (condition) formData.append('condition', condition);
    
    const setId = document.getElementById('set_id').value;
    if (!setId) { showError('Выберите набор'); return; }
    formData.append('set_id', setId);
    
    const tags = tagsAutocomplete ? tagsAutocomplete.getTags() : [];
    if (tags.length) {
        formData.append('tags', JSON.stringify(tags));
    }
    
    if (photoFiles.length === 0) { showError('Добавьте хотя бы одно фото'); return; }
    
    // Переупорядочиваем фото: главное первым
    const orderedPhotos = [...photoFiles];
    if (mainPhotoIndex !== 0) {
        const mainPhoto = orderedPhotos[mainPhotoIndex];
        orderedPhotos.splice(mainPhotoIndex, 1);
        orderedPhotos.unshift(mainPhoto);
    }
    
    for (let i = 0; i < orderedPhotos.length; i++) {
        formData.append('photos', orderedPhotos[i]);
    }
    
    try {
        const badge = await createBadge(formData);
        showSuccess('✅ Значок добавлен!', 'successMsg');
        setTimeout(() => window.location.href = `/html/collection/badge-detail.html?id=${badge.id}`, 1500);
    } catch (error) {
        showError(error.message);
    }
});

// Инициализация
checkAuth().then(() => {
    loadSets();
    initTagsAutocomplete();
});