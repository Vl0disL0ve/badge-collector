// pages/add-badge.js
let tagsAutocomplete = null;
let isSaving = false;
let currentSetId = null;

// Получаем set_id из URL если есть
const urlParams = new URLSearchParams(window.location.search);
const presetSetId = urlParams.get('set_id');

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
        
        // Если есть presetSetId, выбираем его
        if (presetSetId) {
            select.value = presetSetId;
            currentSetId = presetSetId;
        }
    } catch (error) {
        console.error('Error loading sets:', error);
        showError('Не удалось загрузить наборы');
    }
}

function initTagsAutocomplete() {
    const container = document.getElementById('tagsContainer');
    if (!container) {
        console.error('tagsContainer not found');
        return;
    }
    
    // Убедимся, что контейнер пуст
    container.innerHTML = '';
    
    tagsAutocomplete = new TagsAutocomplete('tagInput', 'tagsContainer', []);
}

// Глобальная переменная для файлов
let selectedFiles = [];

function renderPhotoGallery() {
    const gallery = document.getElementById('photoGallery');
    if (!gallery) return;
    
    gallery.innerHTML = '';
    
    selectedFiles.forEach((file, idx) => {
        const div = document.createElement('div');
        div.className = 'gallery-item';
        
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        
        const badge = document.createElement('div');
        badge.className = 'gallery-badge';
        badge.textContent = idx === 0 ? '⭐ Главное' : `${idx + 1}`;
        if (idx === 0) badge.classList.add('main');
        
        const overlay = document.createElement('div');
        overlay.className = 'gallery-overlay';
        
        const editBtn = document.createElement('button');
        editBtn.textContent = '✏️';
        editBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            openPhotoEditor(file, async (editedFile) => {
                selectedFiles[idx] = editedFile;
                renderPhotoGallery();
                showSuccess('Фото отредактировано', 'successMsg');
            });
        };
        
        const removeBtn = document.createElement('button');
        removeBtn.textContent = '🗑️';
        removeBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            selectedFiles.splice(idx, 1);
            renderPhotoGallery();
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
    // Инициализируем теги
    initTagsAutocomplete();
    
    // Загружаем наборы
    loadSets();
    
    // Обработчик выбора файлов
    const photoInput = document.getElementById('photos');
    if (photoInput) {
        photoInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            const totalFiles = selectedFiles.length + files.length;
            
            if (totalFiles > 5) {
                showError('Максимум 5 фотографий');
                photoInput.value = '';
                return;
            }
            
            selectedFiles.push(...files);
            renderPhotoGallery();
            photoInput.value = '';
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
            
            if (selectedFiles.length === 0) {
                showError('Добавьте хотя бы одну фотографию');
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
            
            // Получаем теги
            const tags = tagsAutocomplete ? tagsAutocomplete.getTags() : [];
            if (tags.length) {
                fd.append('tags', JSON.stringify(tags));
            }
            
            // Добавляем фото
            selectedFiles.forEach(file => {
                fd.append('photos', file);
            });
            
            try {
                const result = await createBadge(fd);
                showSuccess('✅ Значок успешно создан!', 'successMsg');
                setTimeout(() => {
                    window.location.href = `/html/collection/badge-detail.html?id=${result.id}`;
                }, 1500);
            } catch (error) {
                console.error('Create badge error:', error);
                showError(error.message);
                isSaving = false;
            }
        });
    }
});

// Проверка авторизации
checkAuth();