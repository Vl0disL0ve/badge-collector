// pages/edit-photo.js
const urlParams = new URLSearchParams(window.location.search);
const badgeId = urlParams.get('badge_id');
const photoId = urlParams.get('photo_id');
let currentFile = null;

async function load() {
    await checkAuth();
    if (!badgeId || !photoId) {
        alert('Не указан ID значка или фото');
        window.close();
        return;
    }

    try {
        const badge = await getBadge(badgeId);
        const photo = badge.photos?.find(p => p.id == photoId);
        if (!photo) throw new Error('Фото не найдено');

        document.getElementById('preview').src = `http://localhost:8000${photo.file_path}`;
        document.getElementById('loading').style.display = 'none';
        document.getElementById('preview').style.display = 'block';
        document.getElementById('tools').style.display = 'flex';
        document.getElementById('saveGroup').style.display = 'flex';

        const res = await fetch(`http://localhost:8000${photo.file_path}`);
        const blob = await res.blob();
        currentFile = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
    } catch (error) {
        document.getElementById('loading').innerHTML = `Ошибка: ${error.message}`;
    }
}

async function applyEdit(editFunction, ...args) {
    if (!currentFile) return;
    showLoader();
    try {
        const result = await editFunction(currentFile, ...args);
        if (result.success) {
            const url = result.processed_url || result.image_url;
            const blob = await (await fetch(`http://localhost:8000${url}`)).blob();
            currentFile = new File([blob], currentFile.name, { type: blob.type });
            const previewUrl = URL.createObjectURL(currentFile);
            document.getElementById('preview').src = previewUrl;
        }
    } catch (error) { alert('Ошибка: ' + error.message); }
    hideLoader();
}

async function detectAxisAndRotate() {
    if (!currentFile) return;
    showLoader();
    try {
        const result = await detectAxis(currentFile);
        if (result.success) {
            const rotateResult = await rotateCustom(currentFile, -result.angle);
            if (rotateResult.success) {
                const blob = await (await fetch(`http://localhost:8000${rotateResult.image_url}`)).blob();
                currentFile = new File([blob], currentFile.name, { type: blob.type });
                const previewUrl = URL.createObjectURL(currentFile);
                document.getElementById('preview').src = previewUrl;
                alert(`Обнаружена ось: ${result.angle.toFixed(1)}°, значок выровнен`);
            }
        } else {
            alert('Не удалось определить ось: ' + (result.message || 'неизвестная ошибка'));
        }
    } catch (error) { alert('Ошибка: ' + error.message); }
    hideLoader();
}

async function saveAndClose() {
    if (!currentFile) return;
    showLoader();
    try {
        const badge = await getBadge(badgeId);
        const oldPhoto = badge.photos?.find(p => p.id == photoId);
        const wasMain = oldPhoto?.is_main || false;
        
        await deletePhotoFromBadge(badgeId, photoId);
        
        const fd = new FormData();
        fd.append('photo', currentFile);
        const newPhoto = await addBadgePhoto(badgeId, fd);
        
        if (wasMain && newPhoto && newPhoto.id) {
            await makeMainPhoto(badgeId, newPhoto.id);
        }
        
        alert('Фото сохранено!');
        window.location.href = `/html/badges/edit-badge.html?id=${badgeId}`;
    } catch (error) {
        alert('Ошибка сохранения: ' + error.message);
    }
    hideLoader();
}

function showLoader() { document.body.style.cursor = 'wait'; document.querySelectorAll('button').forEach(b => b.disabled = true); }
function hideLoader() { document.body.style.cursor = 'default'; document.querySelectorAll('button').forEach(b => b.disabled = false); }

document.getElementById('autoBtn').onclick = () => applyEdit(processImage, true, false);
document.getElementById('leftBtn').onclick = () => applyEdit(rotateImage, -90);
document.getElementById('rightBtn').onclick = () => applyEdit(rotateImage, 90);
document.getElementById('bgBtn').onclick = () => applyEdit(removeBackground);
document.getElementById('axisBtn').onclick = detectAxisAndRotate;
document.getElementById('saveBtn').onclick = saveAndClose;
document.getElementById('cancelBtn').onclick = () => window.location.href = `/html/badges/edit-badge.html?id=${badgeId}`;

load();