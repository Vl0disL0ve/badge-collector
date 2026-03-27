// Image Editor with ML functions
let currentImageUrl = null;
let currentImageFile = null;

async function processImage(file, autoRotate = true, removeBg = true) {
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('auto_rotate', autoRotate);
    formData.append('remove_bg', removeBg);
    
    const token = getToken();
    const response = await fetch('http://localhost:8000/api/process-image', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    
    if (!response.ok) {
        throw new Error('Ошибка обработки изображения');
    }
    
    return response.json();
}

async function rotateImage(file, angle) {
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('angle', angle);
    
    const token = getToken();
    const response = await fetch('http://localhost:8000/api/rotate-image', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    
    if (!response.ok) {
        throw new Error('Ошибка поворота изображения');
    }
    
    return response.json();
}

async function removeBackground(file) {
    const formData = new FormData();
    formData.append('photo', file);
    
    const token = getToken();
    const response = await fetch('http://localhost:8000/api/remove-background', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });
    
    if (!response.ok) {
        throw new Error('Ошибка удаления фона');
    }
    
    return response.json();
}