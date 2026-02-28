from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'school_library_secret_key_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Константы для файлов
USERS_FILE = 'users.json'
BOOKS_FILE = 'books.json'

def create_file_if_not_exists(filename, default_data):
    """Создает файл если он не существует"""
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        print(f"Создан файл: {filename}")
    return True

def load_data(filename):
    """Загружает данные из JSON файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Ошибка загрузки {filename}: {e}")
        return None

def save_data(filename, data):
    """Сохраняет данные в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения {filename}: {e}")
        return False

def ensure_available_field(books):
    """Добавляет поле available во все книги, если его нет"""
    updated = False
    for book in books:
        if 'available' not in book:
            book['available'] = True
            updated = True
    if updated:
        save_data(BOOKS_FILE, books)
        print("Добавлено поле 'available' в книги")
    return books

def initialize_application():
    """Инициализирует приложение - создает файлы и тестовые данные"""
    print("Инициализация приложения...")
    
    # Создаем файлы если их нет
    create_file_if_not_exists(USERS_FILE, {})
    create_file_if_not_exists(BOOKS_FILE, [])
    
    # Загружаем книги
    books = load_data(BOOKS_FILE)
    if not books or len(books) == 0:
        print("ВНИМАНИЕ: Файл books.json пуст или не найден!")
        books = []
        save_data(BOOKS_FILE, books)
    else:
        # Добавляем поле available, если его нет
        books = ensure_available_field(books)
    
    # Загружаем пользователей
    users = load_data(USERS_FILE)
    if not users or len(users) == 0:
        users = {
            'admin': {
                'email': 'admin@school509.ru',
                'password': generate_password_hash('admin123'),
                'full_name': 'Администратор Библиотеки',
                'grade': '11',
                'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reading_books': [],
                'reading_dates': {},
                'reading_history': [],
                'history_dates': {},
                'favorites': [],
                'notifications': {
                    'new_books': True,
                    'return_reminders': True,
                    'recommendations': False
                }
            }
        }
        save_data(USERS_FILE, users)
        print("Создан тестовый пользователь: admin / admin123")
    
    print(f"Загружено книг: {len(books)}")
    print(f"Загружено пользователей: {len(users)}")
    return users, books

# Инициализируем приложение один раз при запуске
users_data, books_data = initialize_application()

# Фильтры для шаблонов
@app.template_filter('to_date')
def to_date_filter(s):
    """Конвертирует строку в дату"""
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except:
        try:
            return datetime.strptime(s, '%Y-%m-%d')
        except:
            return datetime.now()

@app.template_filter('date_add_days')
def date_add_days_filter(d, days):
    """Добавляет дни к дате"""
    try:
        if isinstance(d, str):
            d = datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        return (d + timedelta(days=days)).strftime('%d.%m.%Y')
    except:
        return d

@app.template_filter('format_date')
def format_date_filter(d):
    """Форматирует дату"""
    try:
        if isinstance(d, str):
            d = datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
        return d.strftime('%d.%m.%Y')
    except:
        return d

# Маршруты приложения
@app.route('/')
def index():
    """Главная страница"""
    # Список ID рекомендованных книг
    recommended_ids = [5, 26, 14]  # ID: 5 - Капитанская дочка, 26 - Судьба человека, 14 - Преступление и наказание
    
    # Получаем рекомендованные книги по ID
    featured_books = []
    for book_id in recommended_ids:
        book = next((b for b in books_data if b['id'] == book_id), None)
        if book:
            featured_books.append(book)
    
    # Если какие-то книги не найдены, добавляем первые три из каталога
    if len(featured_books) < 3:
        for book in books_data[:3]:
            if book not in featured_books:
                featured_books.append(book)
        featured_books = featured_books[:3]
    
    return render_template('index.html',
                         featured_books=featured_books,
                         user=session.get('user'),
                         total_books=len(books_data))

@app.route('/catalog')
def catalog():
    """Страница каталога книг"""
    theme = request.args.get('theme', '')
    search = request.args.get('search', '')
    
    filtered_books = books_data
    
    if search:
        filtered_books = [book for book in books_data 
                         if search.lower() in book['title'].lower() 
                         or search.lower() in book['author'].lower()]
    
    if theme:
        # Фильтрация по теме (проверяем, входит ли искомая тема в массив тем книги)
        filtered_books = [book for book in filtered_books 
                         if any(theme.lower() in t.lower() for t in book['theme'])]
    
    # Получаем все уникальные темы из всех книг (для выпадающего списка)
    all_themes = []
    for book in books_data:
        all_themes.extend(book['theme'])
    themes = sorted(list(set(all_themes)))
    
    # Проверяем избранные книги и читаемые книги для текущего пользователя
    user_favorites = []
    user_reading = []
    if 'user' in session:
        current_users = load_data(USERS_FILE) or {}
        user_data = current_users.get(session['user']['username'], {})
        user_favorites = user_data.get('favorites', [])
        user_reading = user_data.get('reading_books', [])
    
    return render_template('catalog.html', 
                         books=filtered_books,
                         themes=themes,
                         search_query=search,
                         selected_theme=theme,
                         user=session.get('user'),
                         user_favorites=user_favorites,
                         user_reading=user_reading)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    """Страница детальной информации о книге"""
    book = next((b for b in books_data if b['id'] == book_id), None)
    if not book:
        flash('Книга не найдена', 'error')
        return redirect(url_for('catalog'))
    
    # Проверяем, есть ли книга в избранном и читаемых у пользователя
    is_favorite = False
    is_reading = False
    if 'user' in session:
        current_users = load_data(USERS_FILE) or {}
        user_data = current_users.get(session['user']['username'], {})
        user_favorites = user_data.get('favorites', [])
        user_reading = user_data.get('reading_books', [])
        is_favorite = book_id in user_favorites
        is_reading = book_id in user_reading
    
    return render_template('book_detail.html', 
                         book=book,
                         user=session.get('user'),
                         is_favorite=is_favorite,
                         is_reading=is_reading)

@app.route('/add_to_favorites/<int:book_id>')
def add_to_favorites(book_id):
    """Добавляет книгу в избранное"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    current_users = load_data(USERS_FILE) or {}
    username = session['user']['username']
    
    if username not in current_users:
        flash('Ошибка: пользователь не найден', 'error')
        return redirect(url_for('catalog'))
    
    # Добавляем книгу в избранное
    if 'favorites' not in current_users[username]:
        current_users[username]['favorites'] = []
    
    if book_id not in current_users[username]['favorites']:
        current_users[username]['favorites'].append(book_id)
        save_data(USERS_FILE, current_users)
        flash('Книга добавлена в избранное!', 'success')
    else:
        flash('Книга уже в избранном', 'info')
    
    return redirect(request.referrer or url_for('catalog'))

@app.route('/remove_from_favorites/<int:book_id>')
def remove_from_favorites(book_id):
    """Удаляет книгу из избранного"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    current_users = load_data(USERS_FILE) or {}
    username = session['user']['username']
    
    if username not in current_users:
        flash('Ошибка: пользователь не найден', 'error')
        return redirect(url_for('catalog'))
    
    # Удаляем книгу из избранного
    if 'favorites' in current_users[username] and book_id in current_users[username]['favorites']:
        current_users[username]['favorites'].remove(book_id)
        save_data(USERS_FILE, current_users)
        flash('Книга удалена из избранного', 'info')
    
    return redirect(request.referrer or url_for('profile'))

@app.route('/toggle_reading/<int:book_id>')
def toggle_reading(book_id):
    """Переключает статус чтения книги"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    current_users = load_data(USERS_FILE) or {}
    username = session['user']['username']
    
    if username not in current_users:
        flash('Ошибка: пользователь не найден', 'error')
        return redirect(url_for('catalog'))
    
    # Проверяем существование книги
    book = next((b for b in books_data if b['id'] == book_id), None)
    if not book:
        flash('Книга не найдена', 'error')
        return redirect(url_for('catalog'))
    
    # Инициализируем списки если их нет
    if 'reading_books' not in current_users[username]:
        current_users[username]['reading_books'] = []
    if 'reading_dates' not in current_users[username]:
        current_users[username]['reading_dates'] = {}
    if 'reading_history' not in current_users[username]:
        current_users[username]['reading_history'] = []
    if 'history_dates' not in current_users[username]:
        current_users[username]['history_dates'] = {}
    
    # Проверяем, читает ли пользователь эту книгу сейчас
    if book_id in current_users[username]['reading_books']:
        # Завершаем чтение - перемещаем в историю
        current_users[username]['reading_books'].remove(book_id)
        
        # Сохраняем дату завершения
        current_users[username]['history_dates'][str(book_id)] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Добавляем в историю чтения, если там еще нет
        if book_id not in current_users[username]['reading_history']:
            current_users[username]['reading_history'].append(book_id)
        
        # Удаляем дату начала чтения
        if str(book_id) in current_users[username]['reading_dates']:
            del current_users[username]['reading_dates'][str(book_id)]
        
        flash(f'Вы завершили чтение книги "{book["title"]}". Книга добавлена в историю!', 'success')
    else:
        # Начинаем чтение
        current_users[username]['reading_books'].append(book_id)
        current_users[username]['reading_dates'][str(book_id)] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        flash(f'Вы начали читать книгу "{book["title"]}"', 'success')
    
    save_data(USERS_FILE, current_users)
    return redirect(request.referrer or url_for('catalog'))

@app.route('/toggle_book_status/<int:book_id>')
def toggle_book_status(book_id):
    """Меняет статус книги (только для администратора)"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    # Проверяем, что пользователь - администратор
    if session['user']['username'] != 'admin':
        flash('Эта функция доступна только администратору', 'error')
        return redirect(request.referrer or url_for('catalog'))
    
    # Находим книгу
    book_index = next((i for i, b in enumerate(books_data) if b['id'] == book_id), None)
    if book_index is None:
        flash('Книга не найдена', 'error')
        return redirect(request.referrer or url_for('catalog'))
    
    # Переключаем статус
    books_data[book_index]['available'] = not books_data[book_index]['available']
    save_data(BOOKS_FILE, books_data)
    
    status = "Доступна" if books_data[book_index]['available'] else "На руках"
    flash(f'Статус книги "{books_data[book_index]["title"]}" изменен на "{status}"', 'success')
    
    return redirect(request.referrer or url_for('catalog'))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Очищает историю чтения"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    current_users = load_data(USERS_FILE) or {}
    username = session['user']['username']
    
    if username not in current_users:
        flash('Ошибка: пользователь не найден', 'error')
        return redirect(url_for('profile'))
    
    # Получаем подтверждение
    confirmation = request.form.get('confirmation')
    
    if confirmation != 'ОЧИСТИТЬ ИСТОРИЮ':
        flash('Неправильное подтверждение. История не очищена.', 'error')
        return redirect(url_for('profile'))
    
    # Очищаем историю чтения
    current_users[username]['reading_history'] = []
    current_users[username]['history_dates'] = {}
    
    save_data(USERS_FILE, current_users)
    flash('История чтения успешно очищена!', 'success')
    
    return redirect(url_for('profile'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    """Обновляет данные профиля"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    current_users = load_data(USERS_FILE) or {}
    username = session['user']['username']
    
    if username not in current_users:
        flash('Ошибка: пользователь не найден', 'error')
        return redirect(url_for('profile'))
    
    # Получаем данные из формы
    full_name = request.form.get('full_name')
    new_email = request.form.get('email')
    current_email = current_users[username].get('email')
    
    # Проверяем, изменился ли email
    if new_email != current_email:
        # Проверяем, не занят ли новый email другим пользователем
        email_exists = False
        for user, user_data in current_users.items():
            if user != username and user_data.get('email') == new_email:
                email_exists = True
                break
        
        if email_exists:
            flash('Этот email уже используется другим пользователем', 'error')
            return redirect(url_for('profile'))
    
    # Обновляем данные
    if full_name:
        current_users[username]['full_name'] = full_name
        session['user']['full_name'] = full_name
    
    if new_email:
        current_users[username]['email'] = new_email
    
    save_data(USERS_FILE, current_users)
    flash('Профиль успешно обновлен!', 'success')
    
    return redirect(url_for('profile'))

@app.route('/update_notifications', methods=['POST'])
def update_notifications():
    """Обновляет настройки уведомлений"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    current_users = load_data(USERS_FILE) or {}
    username = session['user']['username']
    
    if username not in current_users:
        flash('Ошибка: пользователь не найден', 'error')
        return redirect(url_for('profile'))
    
    # Получаем настройки из формы
    new_books_notification = request.form.get('new_books') == 'on'
    return_reminders = request.form.get('return_reminders') == 'on'
    recommendations = request.form.get('recommendations') == 'on'
    
    # Сохраняем настройки
    if 'notifications' not in current_users[username]:
        current_users[username]['notifications'] = {}
    
    current_users[username]['notifications'] = {
        'new_books': new_books_notification,
        'return_reminders': return_reminders,
        'recommendations': recommendations
    }
    
    save_data(USERS_FILE, current_users)
    flash('Настройки уведомлений обновлены!', 'success')
    
    return redirect(url_for('profile'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        full_name = request.form['full_name']
        grade = request.form['grade']
        
        # Загружаем актуальные данные
        current_users = load_data(USERS_FILE) or {}
        
        # Проверка совпадения паролей
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html', 
                                 form_data=request.form,
                                 email_error=False,
                                 username_error=False)
        
        # Проверка уникальности username
        if username in current_users:
            flash('Пользователь с таким именем уже существует', 'error')
            return render_template('register.html', 
                                 form_data=request.form,
                                 email_error=False,
                                 username_error=True)
        
        # Проверка уникальности email
        email_exists = False
        for user_data in current_users.values():
            if user_data.get('email') == email:
                email_exists = True
                break
        
        if email_exists:
            flash('Пользователь с таким email уже зарегистрирован', 'error')
            return render_template('register.html', 
                                 form_data=request.form,
                                 email_error=True,
                                 username_error=False)
        
        # Создаем нового пользователя
        current_users[username] = {
            'email': email,
            'password': generate_password_hash(password),
            'full_name': full_name,
            'grade': grade,
            'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'reading_books': [],
            'reading_dates': {},
            'reading_history': [],
            'history_dates': {},
            'favorites': [],
            'notifications': {
                'new_books': True,
                'return_reminders': True,
                'recommendations': False
            }
        }
        
        if save_data(USERS_FILE, current_users):
            # Автоматически входим после регистрации
            session['user'] = {
                'username': username,
                'full_name': full_name, 
                'grade': grade
            }
            session.permanent = True
            flash(f'Регистрация успешна! Добро пожаловать, {full_name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ошибка при сохранении данных', 'error')
    
    # GET запрос - показываем форму
    return render_template('register.html', 
                         form_data={},
                         email_error=False,
                         username_error=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        current_users = load_data(USERS_FILE) or {}
        user = current_users.get(username)
        
        if user and check_password_hash(user['password'], password):
            session['user'] = {
                'username': username,
                'full_name': user['full_name'],
                'grade': user['grade']
            }
            session.permanent = True
            flash(f'Добро пожаловать, {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('user', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    """Личный кабинет"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    current_users = load_data(USERS_FILE) or {}
    user_data = current_users.get(session['user']['username'])
    
    if not user_data:
        flash('Ошибка загрузки профиля', 'error')
        return redirect(url_for('logout'))
    
    # Гарантируем наличие всех полей
    if 'notifications' not in user_data:
        user_data['notifications'] = {
            'new_books': True,
            'return_reminders': True,
            'recommendations': False
        }
    
    if 'reading_dates' not in user_data:
        user_data['reading_dates'] = {}
    
    if 'history_dates' not in user_data:
        user_data['history_dates'] = {}
    
    if 'reading_history' not in user_data:
        user_data['reading_history'] = []
    
    # Загружаем книги которые читает сейчас
    reading_books_info = []
    for book_id in user_data.get('reading_books', []):
        book = next((b for b in books_data if b['id'] == book_id), None)
        if book:
            reading_books_info.append(book)
    
    # Загружаем историю чтения
    history_books_info = []
    for book_id in user_data.get('reading_history', []):
        book = next((b for b in books_data if b['id'] == book_id), None)
        if book:
            history_books_info.append({
                'book': book,
                'date': user_data.get('history_dates', {}).get(str(book_id), user_data.get('registered_at'))
            })
    
    # Загружаем избранные книги
    favorite_books_info = []
    for book_id in user_data.get('favorites', []):
        book = next((b for b in books_data if b['id'] == book_id), None)
        if book:
            favorite_books_info.append(book)
    
    return render_template('profile.html',
                         user=session['user'],
                         user_data=user_data,
                         reading_books=reading_books_info,
                         history_books=history_books_info,
                         favorite_books=favorite_books_info)

@app.route('/about')
def about():
    """Страница 'О нас'"""
    return render_template('about.html', user=session.get('user'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Страница контактов"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        flash(f'Спасибо, {name}! Ваше сообщение отправлено.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', user=session.get('user'))

@app.route('/api/search')
def api_search():
    """API для поиска книг"""
    query = request.args.get('q', '')
    if query:
        results = [book for book in books_data 
                  if query.lower() in book['title'].lower() 
                  or query.lower() in book['author'].lower()]
        return jsonify(results[:5])
    return jsonify([])

@app.route('/delete_account', methods=['POST'])
def delete_account():
    """Удаляет аккаунт пользователя"""
    if 'user' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('login'))
    
    current_users = load_data(USERS_FILE) or {}
    username = session['user']['username']
    
    if username not in current_users:
        flash('Ошибка: пользователь не найден', 'error')
        return redirect(url_for('profile'))
    
    # Получаем подтверждение из формы
    confirmation = request.form.get('confirmation')
    
    if confirmation != 'УДАЛИТЬ АККАУНТ':
        flash('Неправильное подтверждение. Аккаунт не удален.', 'error')
        return redirect(url_for('profile'))
    
    # Удаляем пользователя
    del current_users[username]
    save_data(USERS_FILE, current_users)
    
    # Выходим из системы
    session.pop('user', None)
    
    flash('Ваш аккаунт был успешно удален. Все данные удалены.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("=" * 50)
    print("Библиотека школы 509 запущена!")
    print("Доступна по адресу: http://localhost:5000")
    print("Тестовый аккаунт: admin / admin123")
    print("=" * 50)
    app.run(debug=True, port=5000)