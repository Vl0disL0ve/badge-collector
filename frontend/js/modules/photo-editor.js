// modules/photo-editor.js
let currentEditorFile = null;
let currentEditorCallback = null;
let currentEditorBadgeId = null;
let currentEditorPhotoId = null;
let currentRotationAngle = 0;

function openPhotoEditor(file, onSave, badgeId = null, photoId = null) {
    currentEditorFile = file;
    currentEditorCallback = onSave;
    currentEditorBadgeId = badgeId;
    currentEditorPhotoId = photoId;
    currentRotationAngle = 0;
    
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
}

function closePhotoEditor() {
    const modal = document.getElementById('photoEditorModal');
    if (modal) modal.style.display = 'none';
    currentEditorFile = null;
    currentEditorCallback = null;
    currentEditorBadgeId = null;
    currentEditorPhotoId = null;
    currentRotationAngle = 0;
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
    currentRotationAngle = 0;
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

// Обновление значения слайдера
document.getElementById('editorRotateSlider')?.addEventListener('input', (e) => {
    const angle = parseInt(e.target.value);
    const valueSpan = document.getElementById('editorRotateValue');
    if (valueSpan) valueSpan.textContent = `${angle}°`;
});

// Применить ручной поворот
document.getElementById('editorApplyRotate')?.addEventListener('click', async () => {
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
});

// Сброс поворота
document.getElementById('editorResetRotate')?.addEventListener('click', async () => {
    if (!currentEditorFile) return;
    showEditorLoader();
    try {
        // Сбрасываем, открывая оригинальное изображение заново
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('editorPreview').src = e.target.result;
        };
        reader.readAsDataURL(currentEditorFile);
        const slider = document.getElementById('editorRotateSlider');
        const valueSpan = document.getElementById('editorRotateValue');
        if (slider) slider.value = 0;
        if (valueSpan) valueSpan.textContent = '0°';
        showEditorSuccess('Поворот сброшен');
    } catch (error) {
        showEditorError('Ошибка: ' + error.message);
    }
    hideEditorLoader();
});

// Обработчики остальных кнопок
document.getElementById('editorAutoRotate')?.addEventListener('click', async () => {
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
});

document.getElementById('editorDetectAxis')?.addEventListener('click', async () => {
    if (!currentEditorFile) return;
    showEditorLoader();
    try {
        const result = await detectAxis(currentEditorFile);
        if (result.success) {
            // Устанавливаем значение слайдера на обнаруженный угол
            const slider = document.getElementById('editorRotateSlider');
            const valueSpan = document.getElementById('editorRotateValue');
            const detectedAngle = Math.round(result.angle);
            if (slider) slider.value = detectedAngle;
            if (valueSpan) valueSpan.textContent = `${detectedAngle}°`;
            
            showEditorSuccess(`Обнаружена ось: ${result.angle.toFixed(1)}°.\nИспользуйте "Применить поворот" для выравнивания.`);
        } else {
            showEditorError('Не удалось определить ось: ' + (result.message || 'неизвестная ошибка'));
        }
    } catch (error) {
        showEditorError('Ошибка: ' + error.message);
    }
    hideEditorLoader();
});

document.getElementById('editorRotateLeft')?.addEventListener('click', async () => {
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
});

document.getElementById('editorRotateRight')?.addEventListener('click', async () => {
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
});

document.getElementById('editorRemoveBg')?.addEventListener('click', async () => {
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
});

document.getElementById('editorSaveBtn')?.addEventListener('click', async () => {
    if (!currentEditorFile || !currentEditorCallback) return;
    showEditorLoader();
    try {
        await currentEditorCallback(currentEditorFile, currentEditorBadgeId, currentEditorPhotoId);
        closePhotoEditor();
        showEditorSuccess('Фото сохранено');
    } catch (error) {
        showEditorError('Ошибка сохранения: ' + error.message);
    }
    hideEditorLoader();
});

document.getElementById('editorCancelBtn')?.addEventListener('click', () => {
    closePhotoEditor();
});