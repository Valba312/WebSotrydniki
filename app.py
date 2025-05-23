from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
import pymysql
from datetime import datetime
import json
import csv

from io import StringIO

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'employees',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db():
    try:
        if not hasattr(Flask, 'db'):
            Flask.db = pymysql.connect(**db_config)
        return Flask.db
    except pymysql.Error as e:
        print(f"Error connecting to database: {e}")
        return None

@app.before_request
def before_request():
    db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection error'}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/management')
def management():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM employees ORDER BY last_name, first_name')
        employees = cursor.fetchall()
        return render_template('management.html', employees=employees)
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/employees')
def employees():
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Получаем список сотрудников
        cursor.execute('''
            SELECT e.*, et.name as education_name,
            (SELECT p.title 
             FROM employee_positions ep 
             JOIN positions p ON ep.position_id = p.id 
             WHERE ep.employee_id = e.id 
             AND (ep.end_date IS NULL OR ep.end_date >= CURDATE())
             ORDER BY ep.start_date DESC LIMIT 1) as current_position
            FROM employees e
            LEFT JOIN education_types et ON e.education_type_id = et.id
            ORDER BY e.last_name, e.first_name
        ''')
        employees = cursor.fetchall()
        
        # Получаем список всех должностей
        cursor.execute('SELECT id, title FROM positions ORDER BY title')
        positions = cursor.fetchall()
        
        # Получаем список типов образования
        cursor.execute('SELECT id, name FROM education_types ORDER BY name')
        education_types = cursor.fetchall()
        
        return render_template('employees.html', 
            employees=employees, 
            positions=positions,
            education_types=education_types)
    except Exception as e:
        print(f"Error in employees route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/positions')
def positions():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT p.*, 
            COUNT(DISTINCT CASE WHEN ep.end_date IS NULL THEN ep.employee_id END) as current_employees
            FROM positions p
            LEFT JOIN employee_positions ep ON p.id = ep.position_id
            GROUP BY p.id, p.title
            ORDER BY p.title
        ''')
        positions = cursor.fetchall()
        return render_template('positions.html', positions=positions)
    except Exception as e:
        print(f"Error in positions route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/reports')
def reports():
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT p.title, COUNT(DISTINCT ep.employee_id) as employee_count
            FROM positions p
            LEFT JOIN employee_positions ep ON p.id = ep.position_id
            WHERE ep.end_date IS NULL OR ep.end_date >= CURDATE()
            GROUP BY p.id, p.title
            ORDER BY employee_count DESC
        ''')
        positions_stats = cursor.fetchall()
        
        cursor.execute('''
            SELECT et.name, COUNT(e.id) as count
            FROM education_types et
            LEFT JOIN employees e ON et.id = e.education_type_id
            GROUP BY et.id, et.name
            ORDER BY count DESC
        ''')
        education_stats = cursor.fetchall()
        
        return render_template('reports.html', 
                             positions_stats=positions_stats,
                             education_stats=education_stats)
    except Exception as e:
        print(f"Error in reports route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analytics')
def analytics():
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Статистика по должностям
        cursor.execute('''
            SELECT p.title, COUNT(ep.employee_id) as count
            FROM positions p
            LEFT JOIN employee_positions ep ON p.id = ep.position_id
            WHERE ep.end_date IS NULL OR ep.end_date >= CURDATE()
            GROUP BY p.id, p.title
            ORDER BY count DESC
        ''')
        position_stats = cursor.fetchall()
        
        # Статистика по образованию
        cursor.execute('''
            SELECT et.name, COUNT(e.id) as count
            FROM education_types et
            LEFT JOIN employees e ON et.id = e.education_type_id
            GROUP BY et.id, et.name
            ORDER BY count DESC
        ''')
        education_stats = cursor.fetchall()
        
        return render_template('analytics.html', 
                             position_stats=position_stats,
                             education_stats=education_stats)
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/employees', methods=['POST'])
def create_employee():
    try:
        data = request.get_json()
        db = get_db()
        cursor = db.cursor()
        
        # Добавляем сотрудника
        cursor.execute('''
            INSERT INTO employees (first_name, last_name, education_type_id)
            VALUES (%s, %s, %s)
        ''', (data['first_name'], data['last_name'], data.get('education_type_id')))
        
        employee_id = cursor.lastrowid
        
        # Если указана должность, добавляем запись в employee_positions
        if data.get('position_id'):
            cursor.execute('''
                INSERT INTO employee_positions (employee_id, position_id, start_date)
                VALUES (%s, %s, CURDATE())
            ''', (employee_id, data['position_id']))
        
        db.commit()
        return jsonify({'success': True, 'id': employee_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/employees/<int:id>', methods=['GET'])
def get_employee(id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Получаем информацию о сотруднике
        cursor.execute('''
            SELECT e.*, et.name as education_name,
            (SELECT p.title 
             FROM employee_positions ep 
             JOIN positions p ON ep.position_id = p.id 
             WHERE ep.employee_id = e.id 
             AND (ep.end_date IS NULL OR ep.end_date >= CURDATE())
             ORDER BY ep.start_date DESC LIMIT 1) as current_position,
            (SELECT ep.position_id
             FROM employee_positions ep
             WHERE ep.employee_id = e.id 
             AND (ep.end_date IS NULL OR ep.end_date >= CURDATE())
             ORDER BY ep.start_date DESC LIMIT 1) as position_id
            FROM employees e
            LEFT JOIN education_types et ON e.education_type_id = et.id
            WHERE e.id = %s
        ''', (id,))
        
        employee = cursor.fetchone()
        
        if not employee:
            return jsonify({'success': False, 'error': 'Сотрудник не найден'})
        
        # Получаем историю должностей
        cursor.execute('''
            SELECT p.title, ep.start_date, ep.end_date
            FROM employee_positions ep
            JOIN positions p ON ep.position_id = p.id
            WHERE ep.employee_id = %s
            ORDER BY ep.start_date DESC
        ''', (id,))
        
        position_history = cursor.fetchall()
        
        return jsonify({
            'id': employee['id'],
            'first_name': employee['first_name'],
            'last_name': employee['last_name'],
            'education_type_id': employee['education_type_id'],
            'education_name': employee['education_name'],
            'position_id': employee['position_id'],
            'current_position': employee['current_position'],
            'position_history': position_history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/employees/<int:id>', methods=['PUT'])
def update_employee(id):
    try:
        data = request.get_json()
        db = get_db()
        cursor = db.cursor()
        
        # Обновляем основную информацию о сотруднике
        cursor.execute('''
            UPDATE employees
            SET first_name = %s, last_name = %s, education_type_id = %s
            WHERE id = %s
        ''', (data['first_name'], data['last_name'], data.get('education_type_id'), id))
        
        # Если указана новая должность
        if data.get('position_id'):
            # Закрываем текущую должность
            cursor.execute('''
                UPDATE employee_positions
                SET end_date = CURDATE()
                WHERE employee_id = %s AND end_date IS NULL
            ''', (id,))
            
            # Добавляем новую должность
            cursor.execute('''
                INSERT INTO employee_positions (employee_id, position_id, start_date)
                VALUES (%s, %s, CURDATE())
            ''', (id, data['position_id']))
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/positions', methods=['POST'])
def create_position():
    try:
        data = request.get_json()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO positions (title, description)
            VALUES (%s, %s)
        ''', (data['title'], data.get('description', '')))
        
        db.commit()
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/positions/<int:id>', methods=['GET'])
def get_position(id):
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Получаем информацию о должности
        cursor.execute('''
            SELECT p.*, 
                   GROUP_CONCAT(CONCAT(e.last_name, ' ', e.first_name)) as employee_names
            FROM positions p
            LEFT JOIN employee_positions ep ON p.id = ep.position_id
            LEFT JOIN employees e ON ep.employee_id = e.id
            WHERE p.id = %s
            GROUP BY p.id
        ''', (id,))
        
        position = cursor.fetchone()
        
        if not position:
            return jsonify({'success': False, 'error': 'Должность не найдена'})
        
        # Получаем список сотрудников на этой должности
        cursor.execute('''
            SELECT e.id, e.first_name, e.last_name
            FROM employees e
            JOIN employee_positions ep ON e.id = ep.employee_id
            WHERE ep.position_id = %s AND (ep.end_date IS NULL OR ep.end_date >= CURDATE())
        ''', (id,))
        
        employees = cursor.fetchall()
        
        return jsonify({
            'id': position['id'],
            'title': position['title'],
            'description': position['description'],
            'employees': employees
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/positions/<int:id>', methods=['PUT'])
def update_position(id):
    try:
        data = request.get_json()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            UPDATE positions
            SET title = %s, description = %s
            WHERE id = %s
        ''', (data['title'], data.get('description', ''), id))
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(500)
def handle_500_error(error):
    return jsonify({'error': 'Internal Server Error. Please try again later.'}), 500

@app.errorhandler(404)
def handle_404_error(error):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)