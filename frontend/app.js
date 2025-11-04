// Конфигурация
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Состояние приложения
const state = {
    users: [],
    currentUser: null,
    currentPage: 1,
    pageSize: 10,
    searchQuery: '',
    allUsers: []
};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Загружаем пользователей
    loadUsers();
    
    // Устанавливаем обработчики событий
    setupEventListeners();
}

function setupEventListeners() {
    // Поиск пользователей
    document.getElementById('searchUser').addEventListener('input', (e) => {
        state.searchQuery = e.target.value.toLowerCase();
        filterAndDisplayUsers();
    });

    // Кнопки пагинации
    document.getElementById('prevPage').addEventListener('click', () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            filterAndDisplayUsers();
        }
    });

    document.getElementById('nextPage').addEventListener('click', () => {
        const totalPages = Math.ceil(state.users.length / state.pageSize);
        if (state.currentPage < totalPages) {
            state.currentPage++;
            filterAndDisplayUsers();
        }
    });

    // Обновить список пользователей
    document.getElementById('refreshUsers').addEventListener('click', () => {
        loadUsers();
    });

    // Генерация рекомендаций
    document.getElementById('generateRecommendations').addEventListener('click', () => {
        if (state.currentUser) {
            loadRecommendations(state.currentUser.user_id);
        }
    });
}

// Загрузка пользователей с сервера
async function loadUsers() {
    try {
        showLoading('usersList');
        
        const response = await fetch(`${API_BASE_URL}/users?limit=1000`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const users = await response.json();
        
        state.allUsers = users;
        state.users = users;
        state.currentPage = 1;
        
        filterAndDisplayUsers();
        
        showToast('Список пользователей обновлен', 'success');
    } catch (error) {
        console.error('Ошибка при загрузке пользователей:', error);
        showError('usersList', 'Не удалось загрузить список пользователей');
        showToast('Ошибка при загрузке пользователей', 'error');
    }
}

// Фильтрация и отображение пользователей
function filterAndDisplayUsers() {
    // Фильтруем пользователей по поисковому запросу
    state.users = state.allUsers.filter(user => 
        user.username.toLowerCase().includes(state.searchQuery) ||
        (user.email && user.email.toLowerCase().includes(state.searchQuery))
    );
    
    // Отображаем пользователей
    displayUsers();
    updatePagination();
}

// Отображение списка пользователей
function displayUsers() {
    const usersList = document.getElementById('usersList');
    
    if (state.users.length === 0) {
        usersList.innerHTML = '<div class="loading">Пользователи не найдены</div>';
        return;
    }
    
    const startIndex = (state.currentPage - 1) * state.pageSize;
    const endIndex = startIndex + state.pageSize;
    const pageUsers = state.users.slice(startIndex, endIndex);
    
    usersList.innerHTML = pageUsers.map(user => `
        <div class="user-item ${state.currentUser && state.currentUser.user_id === user.user_id ? 'active' : ''}" 
             data-user-id="${user.user_id}">
            <div class="user-item-name">${escapeHtml(user.username)}</div>
            ${user.email ? `<div class="user-item-email">${escapeHtml(user.email)}</div>` : ''}
        </div>
    `).join('');
    
    // Добавляем обработчики клика на пользователей
    document.querySelectorAll('.user-item').forEach(item => {
        item.addEventListener('click', () => {
            const userId = parseInt(item.dataset.userId);
            selectUser(userId);
        });
    });
}

// Обновление пагинации
function updatePagination() {
    const totalPages = Math.ceil(state.users.length / state.pageSize);
    
    document.getElementById('pageInfo').textContent = `Страница ${state.currentPage} из ${totalPages || 1}`;
    document.getElementById('prevPage').disabled = state.currentPage === 1;
    document.getElementById('nextPage').disabled = state.currentPage >= totalPages;
}

// Выбор пользователя
async function selectUser(userId) {
    try {
        // Обновляем активный элемент в списке
        document.querySelectorAll('.user-item').forEach(item => {
            item.classList.remove('active');
            if (parseInt(item.dataset.userId) === userId) {
                item.classList.add('active');
            }
        });
        
        // Загружаем данные пользователя
        const [user, statistics] = await Promise.all([
            fetch(`${API_BASE_URL}/users/${userId}`).then(r => r.json()),
            fetch(`${API_BASE_URL}/users/${userId}/statistics`).then(r => r.json())
        ]);
        
        state.currentUser = user;
        
        // Отображаем профиль пользователя
        displayUserProfile(user, statistics);
        
        // Скрываем пустое состояние и показываем детали
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('userDetails').style.display = 'block';
        
        // Очищаем рекомендации
        clearRecommendations();
        
    } catch (error) {
        console.error('Ошибка при загрузке пользователя:', error);
        showToast('Ошибка при загрузке данных пользователя', 'error');
    }
}

// Отображение профиля пользователя
function displayUserProfile(user, statistics) {
    // Аватар (первая буква имени)
    const avatar = user.username.charAt(0).toUpperCase();
    document.getElementById('userAvatar').textContent = avatar;
    
    // Основная информация
    document.getElementById('userName').textContent = user.username;
    document.getElementById('userEmail').textContent = user.email || 'Email не указан';
    
    // Мета-информация
    if (user.age) {
        document.getElementById('userAge').textContent = `🎂 ${user.age} ${getYearsWord(user.age)}`;
        document.getElementById('userAge').style.display = 'inline-block';
    } else {
        document.getElementById('userAge').style.display = 'none';
    }
    
    if (user.country) {
        document.getElementById('userCountry').textContent = `🌍 ${user.country}`;
        document.getElementById('userCountry').style.display = 'inline-block';
    } else {
        document.getElementById('userCountry').style.display = 'none';
    }
    
    const createdYear = new Date(user.created_at).getFullYear();
    document.getElementById('userSince').textContent = `📅 С ${createdYear}`;
    
    // Статистика
    document.getElementById('totalInteractions').textContent = statistics.total_interactions.toLocaleString();
    document.getElementById('uniqueTracks').textContent = statistics.unique_tracks.toLocaleString();
    document.getElementById('listenHours').textContent = statistics.total_listen_time_hours.toLocaleString();
    document.getElementById('favoriteGenre').textContent = statistics.favorite_genre || '—';
}

// Загрузка рекомендаций
async function loadRecommendations(userId) {
    try {
        const btn = document.getElementById('generateRecommendations');
        btn.disabled = true;
        btn.textContent = 'Генерация...';
        
        const recommendationsList = document.getElementById('recommendationsList');
        recommendationsList.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>Генерируем рекомендации...</p></div>';
        
        const response = await fetch(`${API_BASE_URL}/recommendations/${userId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        displayRecommendations(data);
        
        btn.disabled = false;
        btn.textContent = 'Сгенерировать рекомендации';
        
        showToast('Рекомендации успешно сгенерированы', 'success');
        
    } catch (error) {
        console.error('Ошибка при загрузке рекомендаций:', error);
        showError('recommendationsList', 'Не удалось загрузить рекомендации');
        showToast('Ошибка при генерации рекомендаций', 'error');
        
        const btn = document.getElementById('generateRecommendations');
        btn.disabled = false;
        btn.textContent = 'Сгенерировать рекомендации';
    }
}

// Отображение рекомендаций
function displayRecommendations(data) {
    const recommendationsList = document.getElementById('recommendationsList');
    const recommendationsMeta = document.getElementById('recommendationsMeta');
    
    // Мета-информация
    const algorithmNames = {
        'collaborative_filtering': 'Коллаборативная фильтрация',
        'popular_based': 'На основе популярности'
    };
    
    document.getElementById('algorithm').textContent = algorithmNames[data.algorithm] || data.algorithm;
    
    const generatedDate = new Date(data.generated_at);
    document.getElementById('generatedAt').textContent = `Создано: ${generatedDate.toLocaleString('ru-RU')}`;
    
    recommendationsMeta.style.display = 'flex';
    
    // Список рекомендаций
    if (data.recommendations.length === 0) {
        recommendationsList.innerHTML = '<div class="empty-recommendations"><p>Рекомендации не найдены</p></div>';
        return;
    }
    
    recommendationsList.innerHTML = data.recommendations.map((rec, index) => {
        const track = rec.track;
        const scorePercent = Math.round(rec.score * 100);
        
        return `
            <div class="recommendation-item">
                <div class="track-info">
                    <div class="track-title">${index + 1}. ${escapeHtml(track.title)}</div>
                    <div class="track-artist">🎤 ${escapeHtml(track.artist)}</div>
                    <div class="track-details">
                        ${track.album ? `<span>💿 ${escapeHtml(track.album)}</span>` : ''}
                        ${track.genre ? `<span>🎵 ${escapeHtml(track.genre)}</span>` : ''}
                        <span>⏱️ ${formatDuration(track.duration_seconds)}</span>
                        ${track.release_year ? `<span>📅 ${track.release_year}</span>` : ''}
                    </div>
                    ${rec.reason ? `<div class="track-reason">${escapeHtml(rec.reason)}</div>` : ''}
                </div>
                <div class="recommendation-score">
                    <div class="score-badge">${scorePercent}%</div>
                    <div class="score-label">релевантность</div>
                </div>
            </div>
        `;
    }).join('');
}

// Очистка рекомендаций
function clearRecommendations() {
    const recommendationsList = document.getElementById('recommendationsList');
    const recommendationsMeta = document.getElementById('recommendationsMeta');
    
    recommendationsList.innerHTML = '<div class="empty-recommendations"><p>Нажмите "Сгенерировать рекомендации", чтобы получить персонализированные рекомендации</p></div>';
    recommendationsMeta.style.display = 'none';
}

// Утилиты
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    element.innerHTML = '<div class="loading">Загрузка...</div>';
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="loading" style="color: var(--danger-color);">${message}</div>`;
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function getYearsWord(age) {
    const lastDigit = age % 10;
    const lastTwoDigits = age % 100;
    
    if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
        return 'лет';
    }
    
    if (lastDigit === 1) {
        return 'год';
    }
    
    if (lastDigit >= 2 && lastDigit <= 4) {
        return 'года';
    }
    
    return 'лет';
}

