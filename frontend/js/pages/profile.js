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
    } catch (error) { console.error('Ошибка загрузки профиля:', error); }
}

async function loadStats() {
    try {
        const categories = await getCategories();
        const sets = await getSets();
        const badgesData = await getBadges({ limit: 1000 });
        const tags = await getTags();
        document.getElementById('statsCategories').textContent = categories.length;
        document.getElementById('statsSets').textContent = sets.length;
        document.getElementById('statsBadges').textContent = badgesData.total || 0;
        document.getElementById('statsTags').textContent = tags.length;
    } catch (error) { console.error('Ошибка статистики:', error); }
}

async function loadExportSets() {
    try {
        const sets = await getSets();
        const select = document.getElementById('exportSetId');
        select.innerHTML = '<option value="">📦 Все значки</option>';
        sets.forEach(set => {
            const option = document.createElement('option');
            option.value = set.id;
            option.textContent = `${set.name} (${set.collected_count || 0}/${set.total_count})`;
            select.appendChild(option);
        });
    } catch (error) { console.error('Ошибка загрузки наборов:', error); }
}

document.getElementById('generateCodeBtn').addEventListener('click', async () => {
    try {
        const result = await generateTelegramCode();
        document.getElementById('telegramCodeValue').textContent = result.code;
        document.getElementById('telegramCode').style.display = 'block';
        setTimeout(() => document.getElementById('telegramCode').style.display = 'none', 15000);
    } catch (error) { alert('Ошибка: ' + error.message); }
});

document.getElementById('exportBtn').addEventListener('click', async () => {
    const setId = document.getElementById('exportSetId').value;
    try {
        const result = await exportCollection(setId);
        if (result.file_url) {
            window.open(`http://localhost:8000${result.file_url}`, '_blank');
        }
    } catch (error) {
        alert('Ошибка экспорта: ' + error.message);
    }
});

document.getElementById('adminBtn')?.addEventListener('click', () => window.location.href = 'admin.html');

checkAuth().then(() => { loadProfile(); loadStats(); loadExportSets(); });