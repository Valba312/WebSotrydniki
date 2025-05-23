-- Создание базы данных
CREATE DATABASE IF NOT EXISTS employees DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE employees;

-- Создание таблицы типов образования
CREATE TABLE IF NOT EXISTS education_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы должностей
CREATE TABLE IF NOT EXISTS positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы сотрудников
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    education_type_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (education_type_id) REFERENCES education_types(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание таблицы назначений на должности
CREATE TABLE IF NOT EXISTS employee_positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    position_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (position_id) REFERENCES positions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Вставка начальных данных для типов образования
INSERT INTO education_types (name) VALUES
('Высшее'),
('Среднее'),
('Незаконченное высшее'),
('Среднее специальное');

-- Вставка начальных данных для должностей
INSERT INTO positions (title, description) VALUES
('Программист', 'Разработка и поддержка программного обеспечения'),
('Менеджер', 'Управление проектами и командой'),
('Аналитик', 'Анализ данных и подготовка отчетов'),
('Тестировщик', 'Тестирование программного обеспечения'); 