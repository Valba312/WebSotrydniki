import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from datetime import date, datetime
import pymysql
import csv
import os

class EmployeeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управления персоналом")
        self.root.geometry("1200x800")
        
        # Установка стилей
        self.setup_styles()
        
        # Подключение к базе данных
        self.conn = pymysql.connect(
            host='localhost',
            user='root',
            password='root',
            database='employees',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.Cursor
        )

        self.cursor = self.conn.cursor()
        self.create_tables()
        
        # Создание меню
        self.create_menu()
        
        # Создание вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Вкладка "Сотрудники"
        self.employees_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.employees_frame, text="Сотрудники")
        
        # Вкладка "Должности"
        self.positions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.positions_frame, text="Должности")
        
        # Настройка интерфейса
        self.setup_employees_tab()
        self.setup_positions_tab()
        
        # Инициализация данных
        self.init_data()
        
        # Добавление статусбара
        self.create_statusbar()

    def setup_styles(self):
        """Настройка стилей приложения"""
        style = ttk.Style()
        
        # Основной стиль
        style.configure('TLabel', padding=5)
        style.configure('TButton', padding=5)
        style.configure('TEntry', padding=5)
        
        # Стиль заголовков
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        
        # Стиль кнопок действий
        style.configure('Action.TButton', 
                       background='#4CAF50',
                       foreground='white',
                       padding=10)
        
        # Стиль предупреждений
        style.configure('Warning.TLabel',
                       foreground='red',
                       font=('Arial', 10, 'italic'))

    def create_statusbar(self):
        """Создание статусбара"""
        self.statusbar = ttk.Label(self.root, text="Готов к работе", 
                                 relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        """Обновление статуса"""
        self.statusbar.config(text=message)
        self.root.after(3000, lambda: self.statusbar.config(text="Готов к работе"))

    def create_tables(self):
        """Создание таблиц базы данных"""

        table_sql = [
            '''CREATE TABLE IF NOT EXISTS education_types (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',

            '''CREATE TABLE IF NOT EXISTS positions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) NOT NULL UNIQUE,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',

            '''CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                personal_number VARCHAR(50) NOT NULL UNIQUE,
                last_name VARCHAR(100) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                middle_name VARCHAR(100),
                address TEXT NOT NULL,
                phone VARCHAR(50),
                education_type_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (education_type_id) REFERENCES education_types(id)
            )''',

            '''CREATE TABLE IF NOT EXISTS employee_positions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                position_id INT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (position_id) REFERENCES positions(id)
            )''',

            '''CREATE TABLE IF NOT EXISTS employee_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )'''
        ]

        for sql in table_sql:
            self.cursor.execute(sql)

        self.conn.commit()

    def create_menu(self):
        """Создание главного меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Экспорт сотрудников в CSV", command=self.export_employees)
        file_menu.add_command(label="Экспорт должностей в CSV", command=self.export_positions)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню "Отчеты"
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Отчеты", menu=reports_menu)
        reports_menu.add_command(label="Отчет по сотрудникам", command=self.generate_employee_report)
        reports_menu.add_command(label="Отчет по должностям", command=self.generate_position_report)

    def setup_employees_tab(self):
        """Настройка вкладки сотрудников"""
        # Разделение на левую и правую части
        left_frame = ttk.Frame(self.employees_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(self.employees_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Форма добавления сотрудника (слева)
        ttk.Label(left_frame, text="Добавление нового сотрудника", 
                 style='Header.TLabel').pack(pady=10)
        
        form_frame = ttk.LabelFrame(left_frame, text="Данные сотрудника", padding=15)
        form_frame.pack(fill='x', padx=5, pady=5)
        
        # Поля формы с подсказками
        fields = [
            ("Личный номер*:", "personal_number", "Введите уникальный номер сотрудника"),
            ("Фамилия*:", "last_name", "Введите фамилию сотрудника"),
            ("Имя*:", "first_name", "Введите имя сотрудника"),
            ("Отчество:", "middle_name", "Введите отчество сотрудника (если есть)"),
            ("Адрес*:", "address", "Введите полный адрес проживания"),
            ("Телефон:", "phone", "Введите контактный телефон"),
            ("Образование*:", "education", "Выберите уровень образования"),
            ("Должность*:", "position", "Выберите должность")
        ]
        
        for i, (label, name, tooltip) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, padx=5, pady=2, sticky='e')
            if name in ['education', 'position']:
                widget = ttk.Combobox(form_frame, state="readonly")
                widget.grid(row=i, column=1, padx=5, pady=2, sticky='ew')
                self.create_tooltip(widget, tooltip)
                setattr(self, name, widget)
            else:
                widget = ttk.Entry(form_frame)
                widget.grid(row=i, column=1, padx=5, pady=2, sticky='ew')
                self.create_tooltip(widget, tooltip)
                setattr(self, name, widget)
            
            # Добавление метки обязательного поля
            if label.endswith('*:'):
                ttk.Label(form_frame, text="*", 
                         style='Warning.TLabel').grid(row=i, column=2)
        
        # Дата начала работы
        ttk.Label(form_frame, text="Дата начала* (ГГГГ-ММ-ДД):").grid(row=8, column=0, padx=5, pady=2, sticky='e')
        self.start_date = ttk.Entry(form_frame)
        self.start_date.grid(row=8, column=1, padx=5, pady=2, sticky='ew')
        self.start_date.insert(0, date.today().isoformat())
        self.create_tooltip(self.start_date, "Введите дату начала работы в формате ГГГГ-ММ-ДД")
        
        # Кнопки действий
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', padx=5, pady=10)
        
        ttk.Button(btn_frame, text="Добавить сотрудника", 
                  style='Action.TButton', 
                  command=self.add_employee).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Очистить форму", 
                  command=self.clear_form).pack(side='left', padx=5)
        
        # Пояснение к обязательным полям
        ttk.Label(left_frame, text="* - обязательные поля", 
                 style='Warning.TLabel').pack(pady=5)
        
        # Таблица сотрудников (справа)
        ttk.Label(right_frame, text="Список сотрудников", 
                 style='Header.TLabel').pack(pady=5)
        
        # Панель поиска
        search_frame = ttk.LabelFrame(right_frame, text="Поиск", padding=5)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(search_frame, text="Поиск по ФИО или номеру:").pack(side='left', padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_employees)
        self.create_tooltip(self.search_entry, "Введите текст для поиска по ФИО или личному номеру")
        
        # Таблица с улучшенным форматированием
        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill='both', expand=True, padx=5)
        
        columns = ('id', 'personal_number', 'last_name', 'first_name', 
                  'middle_name', 'education', 'current_position')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        headers = {
            'id': '№', 
            'personal_number': 'Личный номер', 
            'last_name': 'Фамилия',
            'first_name': 'Имя', 
            'middle_name': 'Отчество',
            'education': 'Образование',
            'current_position': 'Текущая должность'
        }
        
        for col, header in headers.items():
            self.tree.heading(col, text=header)
            self.tree.column(col, width=100)
        
        # Добавление скроллбаров
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, 
                                  command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, 
                                  command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, 
                          xscrollcommand=x_scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        y_scrollbar.pack(side='right', fill='y')
        x_scrollbar.pack(side='bottom', fill='x')
        
        # Подсказка по двойному клику
        self.create_tooltip(self.tree, 
                          "Дважды щелкните по сотруднику для просмотра подробной информации")
        
        # Привязка двойного клика
        self.tree.bind('<Double-1>', self.show_employee_details)

    def create_tooltip(self, widget, text):
        """Создание всплывающей подсказки для виджета"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, justify='left',
                            background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
            tooltip.bind('<Leave>', lambda e: hide_tooltip())
        
        widget.bind('<Enter>', show_tooltip)

    def init_data(self):
        """Инициализация начальных данных"""
        # Добавление типов образования
        education_types = [
            ('Высшее',),
            ('Среднее',),
            ('Незаконченное высшее',),
            ('Среднее специальное',)
        ]
        
        self.cursor.executemany('''
            INSERT IGNORE INTO education_types (name) 
            VALUES (%s)
        ''', education_types)
        
        # Добавление должностей
        positions = [
            ('Программист', 'Разработка и поддержка программного обеспечения'),
            ('Менеджер', 'Управление проектами и командой'),
            ('Аналитик', 'Анализ данных и подготовка отчетов'),
            ('Тестировщик', 'Тестирование программного обеспечения')
        ]
        
        self.cursor.executemany('''
            INSERT IGNORE INTO positions (title, description) 
            VALUES (%s, %s)
        ''', positions)
        
        self.conn.commit()
        self.update_lists()

    def update_lists(self):
        """Обновление списков"""
        # Обновление списка образования
        self.cursor.execute('SELECT name FROM education_types ORDER BY name')
        self.education['values'] = [row[0] for row in self.cursor.fetchall()]
        
        # Обновление списка должностей
        self.cursor.execute('SELECT title FROM positions ORDER BY title')
        self.position['values'] = [row[0] for row in self.cursor.fetchall()]
        
        # Обновление таблицы сотрудников
        self.update_employees_table()
        
        # Обновление таблицы должностей
        self.update_positions_table()

    def update_employees_table(self):
        """Обновление таблицы сотрудников"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.cursor.execute('''
            SELECT e.id, e.personal_number, e.last_name, e.first_name, 
                   e.middle_name, et.name,
                   (SELECT p.title 
                    FROM employee_positions ep 
                    JOIN positions p ON ep.position_id = p.id 
                    WHERE ep.employee_id = e.id 
                    AND (ep.end_date IS NULL OR ep.end_date >= date('now'))
                    ORDER BY ep.start_date DESC LIMIT 1) as current_position
            FROM employees e
            JOIN education_types et ON e.education_type_id = et.id
            ORDER BY e.last_name, e.first_name
        ''')
        
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def update_positions_table(self, search_term=''):
        """Обновление таблицы должностей"""
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
        
        query = '''
            SELECT p.id, p.title, p.description,
                   COUNT(DISTINCT CASE WHEN ep.end_date IS NULL THEN ep.employee_id END) as employee_count
            FROM positions p
            LEFT JOIN employee_positions ep ON p.id = ep.position_id
            WHERE LOWER(p.title) LIKE %s OR LOWER(p.description) LIKE %s
            GROUP BY p.id
            ORDER BY p.title
        '''
        search_pattern = f'%{search_term}%'
        self.cursor.execute(query, (search_pattern, search_pattern))
        
        for row in self.cursor.fetchall():
            description_preview = row[2][:100] + '...' if len(row[2]) > 100 else row[2]
            self.positions_tree.insert('', 'end', values=(row[0], row[1], description_preview, row[3]))

    def add_employee(self):
        """Добавление сотрудника"""
        try:
            # Проверка обязательных полей
            required_fields = {
                'Личный номер': self.personal_number.get(),
                'Фамилия': self.last_name.get(),
                'Имя': self.first_name.get(),
                'Адрес': self.address.get(),
                'Образование': self.education.get(),
                'Должность': self.position.get()
            }
            
            empty_fields = [field for field, value in required_fields.items() 
                          if not value.strip()]
            
            if empty_fields:
                messagebox.showerror("Ошибка", 
                                   f"Пожалуйста, заполните следующие обязательные поля:\n" +
                                   "\n".join(empty_fields))
                return

            # Проверка даты
            try:
                datetime.strptime(self.start_date.get(), '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Ошибка", 
                                   "Неверный формат даты. Используйте формат ГГГГ-ММ-ДД")
                return

            # Проверка на существование сотрудника с таким личным номером
            self.cursor.execute('SELECT COUNT(*) FROM employees WHERE personal_number = %s',
                              (self.personal_number.get(),))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showerror("Ошибка", 
                                   "Сотрудник с таким личным номером уже существует")
                return

            # Начинаем транзакцию
            self.conn.execute("BEGIN TRANSACTION")
            
            try:
                # Получение ID образования
                self.cursor.execute('SELECT id FROM education_types WHERE name = %s',
                                  (self.education.get(),))
                education_result = self.cursor.fetchone()
                if not education_result:
                    raise Exception("Выбранный тип образования не найден")
                education_id = education_result[0]
                
                # Получение ID должности
                self.cursor.execute('SELECT id FROM positions WHERE title = %s',
                                  (self.position.get(),))
                position_result = self.cursor.fetchone()
                if not position_result:
                    raise Exception("Выбранная должность не найдена")
                position_id = position_result[0]
                
                # Добавление сотрудника
                self.cursor.execute('''
                    INSERT INTO employees (
                        personal_number, last_name, first_name, middle_name,
                        address, phone, education_type_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    self.personal_number.get().strip(),
                    self.last_name.get().strip(),
                    self.first_name.get().strip(),
                    self.middle_name.get().strip(),
                    self.address.get().strip(),
                    self.phone.get().strip(),
                    education_id
                ))
                
                employee_id = self.cursor.lastrowid
                
                # Добавление назначения на должность
                self.cursor.execute('''
                    INSERT INTO employee_positions (
                        employee_id, position_id, start_date
                    ) VALUES (%s, %s, %s)
                ''', (employee_id, position_id, self.start_date.get()))
                
                # Добавление записи в историю
                self.cursor.execute('''
                    INSERT INTO employee_history (
                        employee_id, action_type, description
                    ) VALUES (%s, %s, %s)
                ''', (
                    employee_id,
                    'CREATE',
                    f'Создан новый сотрудник: {self.last_name.get()} {self.first_name.get()}'
                ))
                
                # Подтверждаем транзакцию
                self.conn.commit()
                
                self.clear_form()
                self.update_lists()
                
                self.update_status(f"Сотрудник успешно добавлен: {self.last_name.get()} {self.first_name.get()}")
                messagebox.showinfo("Успех", "Сотрудник успешно добавлен")
                
            except Exception as e:
                # Если произошла ошибка, откатываем транзакцию
                self.conn.rollback()
                raise e
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка", 
                               f"Произошла ошибка при добавлении сотрудника:\n{str(e)}")
            self.update_status("Ошибка при добавлении сотрудника")

    def add_position(self):
        """Добавление должности"""
        try:
            title = self.position_title.get().strip()
            description = self.position_description.get('1.0', tk.END).strip()
            
            if not title or not description:
                messagebox.showerror("Ошибка", "Заполните название и описание должности")
                return
            
            self.cursor.execute('INSERT INTO positions (title, description) VALUES (%s, %s)',
                              (title, description))
            self.conn.commit()
            
            self.position_title.delete(0, tk.END)
            self.position_description.delete('1.0', tk.END)
            
            self.update_lists()
            messagebox.showinfo("Успех", "Должность успешно добавлена")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Должность с таким названием уже существует")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_employee_details(self, event):
        """Показать детали сотрудника"""
        item = self.tree.selection()[0]
        employee_id = self.tree.item(item)['values'][0]
        
        # Получение информации о сотруднике
        self.cursor.execute('''
            SELECT e.personal_number, e.last_name, e.first_name, e.middle_name,
                   e.address, e.phone, et.name as education
            FROM employees e
            LEFT JOIN education_types et ON e.education_type_id = et.id
            WHERE e.id = %s
        ''', (employee_id,))
        
        employee_data = self.cursor.fetchone()
        
        # Создание окна деталей
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Детали сотрудника: {employee_data[1]} {employee_data[2]}")
        details_window.geometry("600x500")
        
        # Основная информация
        info_frame = ttk.LabelFrame(details_window, text="Основная информация", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        labels = [
            ("Личный номер:", employee_data[0]),
            ("ФИО:", f"{employee_data[1]} {employee_data[2]} {employee_data[3] or ''}"),
            ("Адрес:", employee_data[4]),
            ("Телефон:", employee_data[5]),
            ("Образование:", employee_data[6])
        ]
        
        for i, (label, value) in enumerate(labels):
            ttk.Label(info_frame, text=label, font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            ttk.Label(info_frame, text=value).grid(row=i, column=1, sticky='w', padx=5, pady=2)
        
        # История должностей
        history_frame = ttk.LabelFrame(details_window, text="История должностей", padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Таблица истории должностей
        columns = ('position', 'start_date', 'end_date')
        history_tree = ttk.Treeview(history_frame, columns=columns, show='headings')
        
        history_tree.heading('position', text='Должность')
        history_tree.heading('start_date', text='Дата начала')
        history_tree.heading('end_date', text='Дата окончания')
        
        history_tree.column('position', width=200)
        history_tree.column('start_date', width=100)
        history_tree.column('end_date', width=100)
        
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)
        
        history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Заполнение истории должностей
        self.cursor.execute('''
            SELECT p.title, ep.start_date, ep.end_date
            FROM employee_positions ep
            JOIN positions p ON ep.position_id = p.id
            WHERE ep.employee_id = %s
            ORDER BY ep.start_date DESC
        ''', (employee_id,))
        
        for row in self.cursor.fetchall():
            end_date = row[2] if row[2] else 'по настоящее время'
            history_tree.insert('', 'end', values=(row[0], row[1], end_date))

    def clear_form(self):
        """Очистка формы"""
        for widget in [self.personal_number, self.last_name, self.first_name,
                      self.middle_name, self.address, self.phone]:
            widget.delete(0, tk.END)
        
        self.education.set('')
        self.position.set('')
        self.start_date.delete(0, tk.END)
        self.start_date.insert(0, date.today().isoformat())

    def search_employees(self, event):
        """Поиск сотрудников"""
        search_text = self.search_entry.get().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.cursor.execute('''
            SELECT e.id, e.personal_number, e.last_name, e.first_name, 
                   e.middle_name, et.name,
                   (SELECT p.title 
                    FROM employee_positions ep 
                    JOIN positions p ON ep.position_id = p.id 
                    WHERE ep.employee_id = e.id 
                    AND (ep.end_date IS NULL OR ep.end_date >= date('now'))
                    ORDER BY ep.start_date DESC LIMIT 1) as current_position
            FROM employees e
            JOIN education_types et ON e.education_type_id = et.id
            WHERE LOWER(e.last_name) LIKE %s OR 
                  LOWER(e.first_name) LIKE %s OR 
                  LOWER(e.personal_number) LIKE %s
            ORDER BY e.last_name, e.first_name
        ''', (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%'))
        
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def export_employees(self):
        """Экспорт списка сотрудников в CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Сохранить отчет по сотрудникам"
        )
        if filename:
            self.cursor.execute('''
                SELECT e.personal_number, e.last_name, e.first_name, e.middle_name,
                       e.address, e.phone, et.name as education,
                       p.title as position, ep.start_date, ep.end_date
                FROM employees e
                LEFT JOIN education_types et ON e.education_type_id = et.id
                LEFT JOIN employee_positions ep ON e.id = ep.employee_id
                LEFT JOIN positions p ON ep.position_id = p.id
            ''')
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Личный номер', 'Фамилия', 'Имя', 'Отчество', 'Адрес',
                               'Телефон', 'Образование', 'Должность', 'Дата начала', 'Дата окончания'])
                writer.writerows(self.cursor.fetchall())
            messagebox.showinfo("Успех", "Данные успешно экспортированы")

    def export_positions(self):
        """Экспорт списка должностей в CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Сохранить отчет по должностям"
        )
        if filename:
            self.cursor.execute('SELECT title, description FROM positions')
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Название', 'Должностная инструкция'])
                writer.writerows(self.cursor.fetchall())
            messagebox.showinfo("Успех", "Данные успешно экспортированы")

    def generate_employee_report(self):
        """Генерация подробного отчета по сотрудникам"""
        report_window = tk.Toplevel(self.root)
        report_window.title("Отчет по сотрудникам")
        report_window.geometry("800x600")
        
        report_text = scrolledtext.ScrolledText(report_window, wrap=tk.WORD)
        report_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.cursor.execute('''
            SELECT e.personal_number, e.last_name, e.first_name, e.middle_name,
                   e.address, e.phone, et.name as education,
                   GROUP_CONCAT(p.title || ' (' || ep.start_date || 
                   CASE WHEN ep.end_date IS NULL THEN ' - по настоящее время)'
                        ELSE ' - ' || ep.end_date || ')' END) as positions
            FROM employees e
            LEFT JOIN education_types et ON e.education_type_id = et.id
            LEFT JOIN employee_positions ep ON e.id = ep.employee_id
            LEFT JOIN positions p ON ep.position_id = p.id
            GROUP BY e.id
            ORDER BY e.last_name, e.first_name
        ''')
        
        report_text.insert(tk.END, "ОТЧЕТ ПО СОТРУДНИКАМ\n")
        report_text.insert(tk.END, "=" * 50 + "\n\n")
        
        for row in self.cursor.fetchall():
            report_text.insert(tk.END, f"Сотрудник: {row[1]} {row[2]} {row[3]}\n")
            report_text.insert(tk.END, f"Личный номер: {row[0]}\n")
            report_text.insert(tk.END, f"Адрес: {row[4]}\n")
            report_text.insert(tk.END, f"Телефон: {row[5]}\n")
            report_text.insert(tk.END, f"Образование: {row[6]}\n")
            report_text.insert(tk.END, f"История должностей:\n{row[7]}\n")
            report_text.insert(tk.END, "-" * 50 + "\n\n")
        
        report_text.configure(state='disabled')

    def generate_position_report(self):
        """Генерация подробного отчета по должностям"""
        report_window = tk.Toplevel(self.root)
        report_window.title("Отчет по должностям")
        report_window.geometry("800x600")
        
        report_text = scrolledtext.ScrolledText(report_window, wrap=tk.WORD)
        report_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.cursor.execute('''
            SELECT p.title, p.description,
                   COUNT(DISTINCT ep.employee_id) as current_employees
            FROM positions p
            LEFT JOIN employee_positions ep ON p.id = ep.position_id
                AND ep.end_date IS NULL
            GROUP BY p.id
            ORDER BY p.title
        ''')
        
        report_text.insert(tk.END, "ОТЧЕТ ПО ДОЛЖНОСТЯМ\n")
        report_text.insert(tk.END, "=" * 50 + "\n\n")
        
        for row in self.cursor.fetchall():
            report_text.insert(tk.END, f"Должность: {row[0]}\n")
            report_text.insert(tk.END, f"Описание:\n{row[1]}\n")
            report_text.insert(tk.END, f"Текущее количество сотрудников: {row[2]}\n")
            report_text.insert(tk.END, "-" * 50 + "\n\n")
        
        report_text.configure(state='disabled')

    def clear_position_form(self):
        """Очистка формы добавления должности"""
        self.position_title.delete(0, tk.END)
        self.position_description.delete('1.0', tk.END)

    def search_positions(self, event):
        """Поиск должностей"""
        search_term = self.position_search.get().lower()
        self.update_positions_table(search_term)

    def show_position_details(self, event):
        """Показать детали должности"""
        item = self.positions_tree.selection()[0]
        position_id = self.positions_tree.item(item)['values'][0]
        
        # Получение информации о должности
        self.cursor.execute('''
            SELECT p.title, p.description,
                   GROUP_CONCAT(
                       e.last_name || ' ' || e.first_name || 
                       ' (' || ep.start_date || 
                       CASE WHEN ep.end_date IS NULL THEN ' - по настоящее время)'
                            ELSE ' - ' || ep.end_date || ')' END
                   ) as employees
            FROM positions p
            LEFT JOIN employee_positions ep ON p.id = ep.position_id
            LEFT JOIN employees e ON ep.employee_id = e.id
            WHERE p.id = %s
            GROUP BY p.id
        ''', (position_id,))
        
        position_data = self.cursor.fetchone()
        
        # Создание окна деталей
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Детали должности: {position_data[0]}")
        details_window.geometry("600x400")
        
        # Информация о должности
        ttk.Label(details_window, text="Название:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        ttk.Label(details_window, text=position_data[0]).pack(anchor='w', padx=10)
        
        ttk.Label(details_window, text="Должностная инструкция:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        description_text = scrolledtext.ScrolledText(details_window, height=8, wrap=tk.WORD)
        description_text.pack(fill='x', padx=10, pady=5)
        description_text.insert('1.0', position_data[1])
        description_text.configure(state='disabled')
        
        ttk.Label(details_window, text="История занятости:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=10, pady=5)
        history_text = scrolledtext.ScrolledText(details_window, height=8, wrap=tk.WORD)
        history_text.pack(fill='both', expand=True, padx=10, pady=5)
        if position_data[2]:
            history_text.insert('1.0', position_data[2].replace(',', '\n'))
        else:
            history_text.insert('1.0', 'Нет истории занятости')
        history_text.configure(state='disabled')

    def setup_positions_tab(self):
        """Настройка вкладки должностей"""
        # Разделение на левую и правую части
        left_frame = ttk.Frame(self.positions_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(self.positions_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Форма добавления должности
        ttk.Label(left_frame, text="Добавление должности", 
                 style='Header.TLabel').pack(pady=10)
        
        form_frame = ttk.LabelFrame(left_frame, text="Данные должности", padding=15)
        form_frame.pack(fill='x', padx=5, pady=5)
        
        # Название должности
        ttk.Label(form_frame, text="Название*:").grid(row=0, column=0, padx=5, pady=5)
        self.position_title = ttk.Entry(form_frame)
        self.position_title.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.create_tooltip(self.position_title, "Введите название должности")
        
        # Должностная инструкция
        ttk.Label(form_frame, text="Должностная инструкция*:").grid(row=1, column=0, padx=5, pady=5)
        self.position_description = scrolledtext.ScrolledText(form_frame, height=10, width=40)
        self.position_description.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.create_tooltip(self.position_description, "Введите подробное описание должностных обязанностей")
        
        # Кнопки управления
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Добавить должность", 
                  style='Action.TButton',
                  command=self.add_position).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Очистить форму", 
                  command=self.clear_position_form).pack(side='left', padx=5)
        
        # Пояснение к обязательным полям
        ttk.Label(left_frame, text="* - обязательные поля", 
                 style='Warning.TLabel').pack(pady=5)
        
        # Список должностей
        ttk.Label(right_frame, text="Список должностей", 
                 style='Header.TLabel').pack(pady=5)
        
        # Панель поиска
        search_frame = ttk.LabelFrame(right_frame, text="Поиск", padding=5)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(search_frame, text="Поиск по названию:").pack(side='left', padx=5)
        self.position_search = ttk.Entry(search_frame)
        self.position_search.pack(side='left', fill='x', expand=True, padx=5)
        self.position_search.bind('<KeyRelease>', self.search_positions)
        self.create_tooltip(self.position_search, "Введите текст для поиска по названию должности")
        
        # Таблица должностей
        list_frame = ttk.LabelFrame(right_frame, text="Список должностей", padding=10)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('id', 'title', 'description', 'employee_count')
        self.positions_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Настройка заголовков и столбцов
        headers = {
            'id': '№',
            'title': 'Название',
            'description': 'Должностная инструкция',
            'employee_count': 'Кол-во сотрудников'
        }
        
        for col, header in headers.items():
            self.positions_tree.heading(col, text=header)
            width = 150 if col in ['id', 'employee_count'] else 300
            self.positions_tree.column(col, width=width)
        
        # Добавление скроллбаров
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                  command=self.positions_tree.yview)
        x_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, 
                                  command=self.positions_tree.xview)
        
        self.positions_tree.configure(yscrollcommand=y_scrollbar.set,
                                   xscrollcommand=x_scrollbar.set)
        
        self.positions_tree.pack(side='left', fill='both', expand=True)
        y_scrollbar.pack(side='right', fill='y')
        x_scrollbar.pack(side='bottom', fill='x')
        
        # Подсказка по двойному клику
        self.create_tooltip(self.positions_tree, 
                          "Дважды щелкните по должности для просмотра подробной информации")
        
        # Привязка двойного клика
        self.positions_tree.bind('<Double-1>', self.show_position_details)

if __name__ == '__main__':
    root = tk.Tk()
    app = EmployeeApp(root)
    root.mainloop() 