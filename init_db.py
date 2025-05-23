import pymysql
import os

# Конфигурация базы данных
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def init_database():
    try:
        # Подключаемся к MySQL серверу
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        # Создаем базу данных если она не существует
        cursor.execute("CREATE DATABASE IF NOT EXISTS employees")
        cursor.execute("USE employees")
        
        # Читаем SQL файл
        with open('create_tables.sql', 'r', encoding='utf-8') as file:
            sql_commands = file.read()
        
        # Выполняем команды из файла
        for command in sql_commands.split(';'):
            if command.strip():
                cursor.execute(command)
        
        connection.commit()
        print("База данных успешно инициализирована")
        
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    init_database()