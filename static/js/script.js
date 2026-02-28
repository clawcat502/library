// Анимации и интерактивность
document.addEventListener('DOMContentLoaded', function() {
    // Закрытие flash сообщений
    const flashCloseButtons = document.querySelectorAll('.flash-close');
    flashCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.animation = 'slideInRight 0.3s ease-out reverse';
            setTimeout(() => {
                if (this.parentElement.parentElement) {
                    this.parentElement.remove();
                }
            }, 300);
        });
    });

    // Автозакрытие flash сообщений через 5 секунд
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            if (message.parentElement) {
                message.style.animation = 'slideInRight 0.3s ease-out reverse';
                setTimeout(() => {
                    if (message.parentElement) {
                        message.remove();
                    }
                }, 300);
            }
        }, 5000);
    });

    // Плавная прокрутка для якорных ссылок
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') {
                e.preventDefault();
                return;
            }
            
            if (href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    // Прокрутка с учетом фиксированного хедера
                    const headerHeight = document.querySelector('.header')?.offsetHeight || 80;
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Анимация появления элементов при скролле
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Наблюдаем за элементами с анимациями
    document.querySelectorAll('.animate-slide-up').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // Поиск с автодополнением
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        let searchTimeout;
        let currentSearchRequest = null;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            // Отменяем предыдущий запрос если он есть
            if (currentSearchRequest) {
                currentSearchRequest.abort();
            }
            
            searchTimeout = setTimeout(() => {
                const query = this.value.trim();
                if (query.length > 2) {
                    // Создаем новый AbortController для отмены запроса
                    const controller = new AbortController();
                    currentSearchRequest = controller;
                    
                    fetch(`/api/search?q=${encodeURIComponent(query)}`, {
                        signal: controller.signal
                    })
                        .then(response => {
                            if (!response.ok) throw new Error('Network response was not ok');
                            return response.json();
                        })
                        .then(books => {
                            showSearchSuggestions(books, query);
                            currentSearchRequest = null;
                        })
                        .catch(error => {
                            if (error.name !== 'AbortError') {
                                console.error('Search error:', error);
                                hideSearchSuggestions();
                            }
                            currentSearchRequest = null;
                        });
                } else {
                    hideSearchSuggestions();
                }
            }, 300);
        });

        // Обработка нажатия клавиш в поле поиска
        searchInput.addEventListener('keydown', function(e) {
            const suggestionsContainer = document.querySelector('.search-suggestions');
            const activeSuggestion = document.querySelector('.suggestion-item.highlight');
            
            if (e.key === 'ArrowDown' && suggestionsContainer && suggestionsContainer.style.display === 'block') {
                e.preventDefault();
                highlightNextSuggestion();
            } else if (e.key === 'ArrowUp' && suggestionsContainer && suggestionsContainer.style.display === 'block') {
                e.preventDefault();
                highlightPreviousSuggestion();
            } else if (e.key === 'Enter' && activeSuggestion) {
                e.preventDefault();
                activeSuggestion.click();
            } else if (e.key === 'Escape') {
                hideSearchSuggestions();
            }
        });

        // Закрытие подсказок при клике вне поиска
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-container')) {
                hideSearchSuggestions();
            }
        });
    }

    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            this.classList.toggle('active');
            navMenu.classList.toggle('active');
            
            // Анимация гамбургера в крестик
            const spans = this.querySelectorAll('span');
            if (this.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }

    // Закрытие мобильного меню при клике на ссылку
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                const hamburger = document.querySelector('.hamburger');
                const navMenu = document.querySelector('.nav-menu');
                
                if (hamburger && navMenu) {
                    hamburger.classList.remove('active');
                    navMenu.classList.remove('active');
                    
                    const spans = hamburger.querySelectorAll('span');
                    spans[0].style.transform = 'none';
                    spans[1].style.opacity = '1';
                    spans[2].style.transform = 'none';
                }
            }
        });
    });

    // Подтверждение действий для всех кнопок с подтверждением
    document.querySelectorAll('a[onclick*="confirm"]').forEach(link => {
        const originalOnClick = link.getAttribute('onclick');
        if (originalOnClick) {
            link.removeAttribute('onclick');
            link.addEventListener('click', function(e) {
                const confirmMatch = originalOnClick.match(/confirm\('([^']+)'/);
                if (confirmMatch) {
                    const message = confirmMatch[1];
                    if (!confirm(message)) {
                        e.preventDefault();
                    }
                }
            });
        }
    });

    // Инициализация tooltips
    initializeTooltips();
});

// Показ подсказок поиска
function showSearchSuggestions(books, query) {
    let suggestionsContainer = document.querySelector('.search-suggestions');
    
    if (!suggestionsContainer) {
        suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'search-suggestions';
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer) {
            searchContainer.appendChild(suggestionsContainer);
        } else {
            return;
        }
    }

    if (books.length === 0) {
        suggestionsContainer.innerHTML = '<div class="suggestion-item no-results">Ничего не найдено</div>';
    } else {
        suggestionsContainer.innerHTML = books.map((book, index) => `
            <div class="suggestion-item ${index === 0 ? 'highlight' : ''}" 
                 onclick="selectSuggestion('${book.title.replace(/'/g, "\\'")}')"
                 onmouseover="highlightSuggestion(this)">
                <strong>${escapeHtml(book.title)}</strong> - ${escapeHtml(book.author)}
            </div>
        `).join('');
    }
    
    suggestionsContainer.style.display = 'block';
}

// Скрытие подсказок поиска
function hideSearchSuggestions() {
    const suggestionsContainer = document.querySelector('.search-suggestions');
    if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }
}

// Выбор подсказки
function selectSuggestion(title) {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.value = title;
        hideSearchSuggestions();
        
        const searchForm = searchInput.closest('form');
        if (searchForm) {
            searchForm.submit();
        }
    }
}

// Функция для показа подсказки входа
function showLoginPrompt() {
    if (confirm('Для добавления в избранное необходимо войти в систему. Перейти на страницу входа?')) {
        window.location.href = '/login';
    }
}

// Подсветка следующей подсказки
function highlightNextSuggestion() {
    const suggestions = document.querySelectorAll('.suggestion-item:not(.no-results)');
    let currentIndex = -1;
    
    suggestions.forEach((suggestion, index) => {
        if (suggestion.classList.contains('highlight')) {
            currentIndex = index;
            suggestion.classList.remove('highlight');
        }
    });
    
    const nextIndex = (currentIndex + 1) % suggestions.length;
    if (suggestions[nextIndex]) {
        suggestions[nextIndex].classList.add('highlight');
        suggestions[nextIndex].scrollIntoView({ block: 'nearest' });
    }
}

// Подсветка предыдущей подсказки
function highlightPreviousSuggestion() {
    const suggestions = document.querySelectorAll('.suggestion-item:not(.no-results)');
    let currentIndex = -1;
    
    suggestions.forEach((suggestion, index) => {
        if (suggestion.classList.contains('highlight')) {
            currentIndex = index;
            suggestion.classList.remove('highlight');
        }
    });
    
    const prevIndex = currentIndex <= 0 ? suggestions.length - 1 : currentIndex - 1;
    if (suggestions[prevIndex]) {
        suggestions[prevIndex].classList.add('highlight');
        suggestions[prevIndex].scrollIntoView({ block: 'nearest' });
    }
}

// Подсветка подсказки при наведении
function highlightSuggestion(element) {
    document.querySelectorAll('.suggestion-item').forEach(item => {
        item.classList.remove('highlight');
    });
    element.classList.add('highlight');
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Инициализация tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[title]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const title = this.getAttribute('title');
            if (!title) return;
            
            const tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = title;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.position = 'fixed';
            tooltip.style.zIndex = '10000';
            tooltip.style.background = 'rgba(0, 0, 0, 0.8)';
            tooltip.style.color = 'white';
            tooltip.style.padding = '5px 10px';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '12px';
            tooltip.style.whiteSpace = 'nowrap';
            tooltip.style.pointerEvents = 'none';
            
            // Позиционирование tooltip
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            
            this.setAttribute('data-tooltip', title);
            this.removeAttribute('title');
            
            this.tooltipElement = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this.tooltipElement) {
                this.tooltipElement.remove();
                this.tooltipElement = null;
            }
            
            const originalTitle = this.getAttribute('data-tooltip');
            if (originalTitle) {
                this.setAttribute('title', originalTitle);
                this.removeAttribute('data-tooltip');
            }
        });
    });
}

// Добавляем стили для подсказок поиска и tooltips
const searchStyles = `
.search-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border-radius: 8px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    margin-top: 0.5rem;
    z-index: 1000;
    display: none;
    max-height: 300px;
    overflow-y: auto;
}

.suggestion-item {
    padding: 0.75rem 1rem;
    cursor: pointer;
    border-bottom: 1px solid #e5e7eb;
    transition: background-color 0.2s;
    font-size: 0.9rem;
}

.suggestion-item:last-child {
    border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.highlight {
    background-color: #f3f4f6;
}

.suggestion-item.no-results {
    color: #6b7280;
    cursor: default;
    font-style: italic;
}

.suggestion-item.no-results:hover {
    background-color: transparent;
}

.suggestion-item strong {
    color: var(--primary-color);
    font-weight: 600;
}

.search-container {
    position: relative;
}

.custom-tooltip {
    position: fixed;
    z-index: 10000;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
    pointer-events: none;
    animation: tooltipFadeIn 0.2s ease-out;
}

@keyframes tooltipFadeIn {
    from {
        opacity: 0;
        transform: translateY(5px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
`;

// Добавляем стили только если их еще нет
if (!document.querySelector('#search-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'search-styles';
    styleSheet.textContent = searchStyles;
    document.head.appendChild(styleSheet);
}

// Обработчик для изменения размера окна
window.addEventListener('resize', function() {
    // Скрываем мобильное меню при увеличении экрана
    if (window.innerWidth > 768) {
        const hamburger = document.querySelector('.hamburger');
        const navMenu = document.querySelector('.nav-menu');
        
        if (hamburger && navMenu) {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
            
            const spans = hamburger.querySelectorAll('span');
            spans[0].style.transform = 'none';
            spans[1].style.opacity = '1';
            spans[2].style.transform = 'none';
        }
    }
});

// Полифилл для IntersectionObserver если не поддерживается
if (!('IntersectionObserver' in window)) {
    console.warn('IntersectionObserver not supported, animations disabled');
    document.querySelectorAll('.animate-slide-up').forEach(el => {
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
    });
}

// Валидация email в реальном времени
function validateEmail(input) {
    const email = input.value;
    const validationDiv = document.getElementById('emailValidation');
    const emailGroup = document.getElementById('emailGroup');
    const saveBtn = document.getElementById('saveBtn');
    
    // Простая валидация формата email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!email) {
        validationDiv.className = 'email-validation invalid';
        validationDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> Email не может быть пустым';
        input.classList.add('error');
        input.classList.remove('valid');
        saveBtn.disabled = true;
    } else if (!emailRegex.test(email)) {
        validationDiv.className = 'email-validation invalid';
        validationDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> Введите корректный email';
        input.classList.add('error');
        input.classList.remove('valid');
        saveBtn.disabled = true;
    } else {
        validationDiv.className = 'email-validation valid';
        validationDiv.innerHTML = '<i class="fas fa-check-circle"></i> Email корректен';
        input.classList.remove('error');
        input.classList.add('valid');
        saveBtn.disabled = false;
    }
}

// Валидация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('email');
    if (emailInput) {
        validateEmail(emailInput);
    }
    
    // Предотвращаем повторную отправку формы
    const form = document.getElementById('profileForm');
    if (form) {
        form.addEventListener('submit', function() {
            const saveBtn = document.getElementById('saveBtn');
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';
        });
    }
});