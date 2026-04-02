// modules/photo-editor.js
let currentEditorFile = null;
let currentEditorCallback = null;
let isEditorOpen = false;

function openPhotoEditor(file, onSave) {
    console.log('openPhotoEditor called', file);
    currentEditorFile = file;
    currentEditorCallback = onSave;
    isEditorOpen = true;
    
    const modal = document.getElementById('photoEditorModal');
    const preview = document.getElementById('editorPreview');
    const errorDiv = document.getElementById('editorError');
    const successDiv = document.getElementById('editorSuccess');
    const slider = document.getElementById('editorRotateSlider');
    const valueSpan = document.getElementById('editorRotateValue');
    
    if (errorDiv) errorDiv.style.display = 'none';
    if (successDiv) successDiv.style.display = 'none';
    if (slider) slider.value = 0;
    if (valueSpan) valueSpan.textContent = '0°';
    
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
    };
    reader.readAsDataURL(file);
    
    modal.style.display = 'flex';
    console.log('Modal opened');
}

function closePhotoEditor() {
    const modal = document.getElementById('photoEditorModal');
    if (modal) modal.style.display = 'none';
    currentEditorFile = null;
    currentEditorCallback = null;
    isEditorOpen = false;
    console.log('Modal closed');
}

function showEditorError(message) {
    const errorDiv = document.getElementById('editorError');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => errorDiv.style.display = 'none', 5000);
    }
}

function showEditorSuccess(message) {
    const successDiv = document.getElementById('editorSuccess');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        setTimeout(() => successDiv.style.display = 'none', 3000);
    }
}

function showEditorLoader() {
    document.body.style.cursor = 'wait';
    const btns = document.querySelectorAll('#photoEditorModal button');
    btns.forEach(b => b.disabled = true);
    const slider = document.getElementById('editorRotateSlider');
    if (slider) slider.disabled = true;
}

function hideEditorLoader() {
    document.body.style.cursor = 'default';
    const btns = document.querySelectorAll('#photoEditorModal button');
    btns.forEach(b => b.disabled = false);
    const slider = document.getElementById('editorRotateSlider');
    if (slider) slider.disabled = false;
}

async function updateEditorPreview(newFile) {
    currentEditorFile = newFile;
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('editorPreview').src = e.target.result;
    };
    reader.readAsDataURL(newFile);
    
    const slider = document.getElementById('editorRotateSlider');
    const valueSpan = document.getElementById('editorRotateValue');
    if (slider) slider.value = 0;
    if (valueSpan) valueSpan.textContent = '0°';
}

// Блокировка Enter при открытой модалке
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && isEditorOpen) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Enter blocked during modal open');
        return false;
    }
});

// Закрытие модалки по клику на фон
const modalElement = document.getElementById('photoEditorModal');
if (modalElement) {
    modalElement.addEventListener('click', (e) => {
        if (e.target === modalElement) {
            closePhotoEditor();
        }
    });
}

// ========== ОБРАБОТЧИКИ С ПОЛНЫМ ПРЕДОТВРАЩЕНИЕМ ВСПЛЫТИЯ ==========

function createSafeHandler(handler) {
    return async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await handler();
    };
}

// Автовыравнивание
document.getElementById('editorAutoRotate')?.addEventListener('click', createSafeHandler(async () => {
    if (!currentEditorFile) return;
    showEditorLoader();
    try {
        const result = await processImage(currentEditorFile, true, false);
        if (result.success) {
            const url = `http://localhost:8000${result.processed_url}`;
            const resp = await fetch(url);
            const blob = await resp.blob();
            const newFile = new File([blob], currentEditorFile.name, { type: blob.type });
            await updateEditorPreview(newFile);
            showEditorSuccess('Автовыравнивание выполнено');
        }
    } catch (error) {
        showEditorError('Ошибка: ' + error.message);
    }
    hideEditorLoader();
}));

// Определение оси
document.getElementById('editorDetectAxis')?.addEventListener('click', createSafeHandler(async () => {
    if (!currentEditorFile) return;
    showEditorLoader();
    try {
        const result = await detectAxis(currentEditorFile);
        if (result.success) {
            const slider = document.getElementById('editorRotateSlider');
            const valueSpan = document.getElementById('editorRotateValue');
            if (slider) slider.value = Math.round(result.angle);
            if (valueSpan) valueSpan.textContent = `${Math.round(result.angle)}°`;
            showEditorSuccess(`Обнаружена ось: ${result.angle.toFixed(1)}°. Нажмите "Применить" для выравнивания.`);
        } else {
            showEditorError('Не удалось определить ось: ' + (result.message || 'неизвестная ошибка'));
        }
    } catch (error) {
        showEditorError('Ошибка: ' + error.message);
    }
    hideEditorLoader();
}));

// Поворот влево
document.getElementById('editorRotateLeft')?.addEventListener('click', createSafeHandler(async () => {
    if (!currentEditorFile) return;
    showEditorLoader();
    try {
        const result = await rotateImage(currentEditorFile, -90);
        if (result.success) {
            const url = `http://localhost:8000${result.image_url}`;
            const resp = await fetch(url);
            const blob = await resp.blob();
            const newFile = new File([blob], currentEditorFile.name, { type: blob.type });
            await updateEditorPreview(newFile);
            showEditorSuccess('Поворот на -90° выполнен');
        }
    } catch (error) {
        showEditorError('Ошибка: ' + error.message);
    }
    hideEditorLoader();
}));

// Поворот вправо
document.getElementById('editorRotateRight')?.addEventListener('click', createSafeHandler(async () => {
    if (!currentEditorFile) return;
    showEditorLoader();
    try {
        const result = await rotateImage(currentEditorFile, 90);
        if (result.success) {
            const url = `http://localhost:8000${result.image_url}`;
            const resp = await fetch(url);
            const blob = await resp.blob();
            const newFile = new File([blob], currentEditorFile.name, { type: blob.type });
            await updateEditorPreview(newFile);
            showEditorSuccess('Поворот на +90° выполнен');
        }
    } catch (error) {
        showEditorError('Ошибка: ' + error.message);
    }
    hideEditorLoader();
}));

// Удаление фона
document.getElementById('editorRemoveBg')?.addEventListener('click', createSafeHandler(async () => {
    if (!currentEditorFile) return;
    showEditorLoader();
    try {
        const result = await removeBackground(currentEditorFile);
        if (result.success) {
            const url = `http://localhost:8000${result.image_url}`;
            const resp = await fetch(url);
            const blob = await resp.blob();
            const newFile = new File([blob], currentEditorFile.name, { type: blob.type });
            await updateEditorPreview(newFile);
            showEditorSuccess('Фон удалён');
        }
    } catch (error) {
        showEditorError('Ошибка: ' + error.message);
    }
    hideEditorLoader();
}));

// Слайдер ручного поворота
document.getElementById('editorRotateSlider')?.addEventListener('input', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const angle = parseInt(e.target.value);
    const valueSpan = document.getElementById('editorRotateValue');
    if (valueSpan) valueSpan.textContent = `${angle}°`;
});

// Применить ручной поворот
document.getElementById('editorApplyRotate')?.addEventListener('click', createSafeHandler(async () => {
    if (!currentEditorFile) return;
    const slider = document.getElementById('editorRotateSlider');
    const angle = parseInt(slider.value);
    
    if (angle === 0) {
        showEditorError('Угол поворота 0°');
        return;
    }
    
    showEditorLoader();
    try {
        const result = await rotateCustom(currentEditorFile, angle);
        if (result.success) {
            const url = `http://localhost:8000${result.image_url}`;
            const resp = await fetch(url);
            const blob = await resp.blob();
            const newFile = new File([blob], currentEditorFile.name, { type: blob.type });
            await updateEditorPreview(newFile);
            showEditorSuccess(`Поворот на ${angle}° выполнен`);
        }
    } catch (error) {
        showEditorError('Ошибка поворота: ' + error.message);
    }
    hideEditorLoader();
}));

// Сброс поворота
document.getElementById('editorResetRotate')?.addEventListener('click', createSafeHandler(async () => {
    if (!currentEditorFile) return;
    const slider = document.getElementById('editorRotateSlider');
    const valueSpan = document.getElementById('editorRotateValue');
    if (slider) slider.value = 0;
    if (valueSpan) valueSpan.textContent = '0°';
    showEditorSuccess('Поворот сброшен');
}));

// Сохранение
document.getElementById('editorSaveBtn')?.addEventListener('click', createSafeHandler(async () => {
    if (!currentEditorFile || !currentEditorCallback) {
        console.error('No file or callback');
        return;
    }
    showEditorLoader();
    try {
        await currentEditorCallback(currentEditorFile);
        closePhotoEditor();
        showEditorSuccess('Фото сохранено');
    } catch (error) {
        console.error('Save error:', error);
        showEditorError('Ошибка сохранения: ' + error.message);
    }
    hideEditorLoader();
}));

// Отмена
document.getElementById('editorCancelBtn')?.addEventListener('click', createSafeHandler(() => {
    closePhotoEditor();
}));