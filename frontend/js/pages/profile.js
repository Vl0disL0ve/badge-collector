// pages/profile.js
async function loadProfile() {
    try {
        const profile = await getProfile();
        document.getElementById('userEmail').value = profile.email;
        document.getElementById('userCreatedAt').value = new Date(profile.created_at).toLocaleDateString('ru-RU');
        document.getElementById('telegramId').value = profile.telegram_id || 'Не привязан';
        document.getElementById('telegramStatus').innerHTML = profile.telegram_id 
            ? '<span style="color: green;">✅ Telegram привязан</span>' 
            : '<span style="color: orange;">⚠️ Telegram не привязан</span>';
        if (profile.is_admin) document.getElementById('adminPanel').style.display = 'block';
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
        showError('Не удалось загрузить профиль');
    }
}

async function loadStats() {
    try {
        const categories = await getCategories();
        const sets = await getSets();
        
        let badgesTotal = 0;
        try {
            const badgesData = await getBadges({ limit: 1, offset: 0 });
            badgesTotal = badgesData.total || 0;
        } catch (e) {
            console.error('Error loading badges count:', e);
            badgesTotal = 0;
        }
        
        let tagsTotal = 0;
        try {
            const tags = await getTags();
            tagsTotal = tags.length || 0;
        } catch (e) {
            console.error('Error loading tags:', e);
            tagsTotal = 0;
        }
        
        document.getElementById('statsCategories').textContent = categories.length || 0;
        document.getElementById('statsSets').textContent = sets.length || 0;
        document.getElementById('statsBadges').textContent = badgesTotal;
        document.getElementById('statsTags').textContent = tagsTotal;
    } catch (error) {
        console.error('Ошибка статистики:', error);
        document.getElementById('statsCategories').textContent = '—';
        document.getElementById('statsSets').textContent = '—';
        document.getElementById('statsBadges').textContent = '—';
        document.getElementById('statsTags').textContent = '—';
    }
}

async function loadExportSets() {
    try {
        const sets = await getSets();
        const select = document.getElementById('exportSetId');
        if (!select) return;
        
        select.innerHTML = '<option value="">📦 Все значки</option>';
        sets.forEach(set => {
            const option = document.createElement('option');
            option.value = set.id;
            option.textContent = `${set.name} (${set.collected_count || 0}/${set.total_count})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Ошибка загрузки наборов:', error);
    }
}

document.getElementById('generateCodeBtn')?.addEventListener('click', async () => {
    try {
        const result = await generateTelegramCode();
        const codeValue = document.getElementById('telegramCodeValue');
        const codeDiv = document.getElementById('telegramCode');
        if (codeValue) codeValue.textContent = result.code;
        if (codeDiv) codeDiv.style.display = 'block';
        setTimeout(() => {
            if (codeDiv) codeDiv.style.display = 'none';
        }, 15000);
    } catch (error) {
        console.error('Telegram code error:', error);
        alert('Ошибка: ' + error.message);
    }
});

// Новый экспорт с параметром колонок
document.getElementById('exportBtn')?.addEventListener('click', async () => {
    const setId = document.getElementById('exportSetId')?.value;
    const columnsInput = document.getElementById('exportColumns');
    const columns = columnsInput ? parseInt(columnsInput.value) : 3;
    
    if (isNaN(columns) || columns < 1 || columns > 6) {
        alert('Количество колонок должно быть от 1 до 6');
        return;
    }
    
    try {
        const result = await exportCollection(setId, columns);
        if (result.file_url) {
            window.open(`http://localhost:8000${result.file_url}`, '_blank');
        }
    } catch (error) {
        console.error('Export error:', error);
        alert('Ошибка экспорта: ' + error.message);
    }
});

document.getElementById('adminBtn')?.addEventListener('click', () => {
    window.location.href = 'admin.html';
});

checkAuth().then(() => { 
    loadProfile(); 
    loadStats(); 
    loadExportSets(); 
});