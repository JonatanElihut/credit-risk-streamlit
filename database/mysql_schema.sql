-- 1. Crear base de datos (ejecutar primero)
CREATE DATABASE IF NOT EXISTS CreditRiskDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE CreditRiskDB;

-- 2. Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    hashed_password VARCHAR(200) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT DEFAULT 1,

    INDEX idx_users_email (email),
    INDEX idx_users_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabla de predicciones
CREATE TABLE IF NOT EXISTS predictions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,

    -- Datos de entrada
    out_prncp DOUBLE,
    out_prncp_inv DOUBLE,
    last_pymnt_amnt DOUBLE,
    total_rec_prncp DOUBLE,
    recoveries DOUBLE,
    collection_recovery_fee DOUBLE,
    total_pymnt DOUBLE,
    installment DOUBLE,
    funded_amnt_inv DOUBLE,
    total_pymnt_inv DOUBLE,
    total_rec_int DOUBLE,
    hardship_payoff_balance_amount DOUBLE,
    orig_projected_additional_accrued_interest DOUBLE,
    int_rate DOUBLE,
    hardship_amount DOUBLE,
    total_rec_late_fee DOUBLE,
    hardship_last_payment_amount DOUBLE,
    dti DOUBLE,
    annual_inc DOUBLE,
    bc_util DOUBLE,

    -- Resultados
    risk_probability DOUBLE NOT NULL,
    decision VARCHAR(20) NOT NULL,
    risk_level VARCHAR(20),
    threshold_used DOUBLE DEFAULT 0.6,
    model_used VARCHAR(50),
    profile_score DOUBLE,
    details_json TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Claves foráneas e índices
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_predictions_user_id (user_id),
    INDEX idx_predictions_created_at (created_at),
    INDEX idx_predictions_decision (decision),
    INDEX idx_predictions_risk_level (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Tabla para logs del sistema (opcional pero recomendado)
CREATE TABLE IF NOT EXISTS system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    user_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_logs_level (log_level),
    INDEX idx_logs_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Tabla de configuración del sistema
CREATE TABLE IF NOT EXISTS system_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value TEXT,
    description VARCHAR(255),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Insertar configuración inicial
INSERT INTO system_config (config_key, config_value, description) VALUES
('default_threshold', '0.4', 'Umbral por defecto para decisiones'),
('model_version', '1.0', 'Versión del modelo actual'),
('max_predictions_per_user', '1000', 'Límite de predicciones por usuario')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- 7. Crear usuario para la aplicación (ejecutar en MySQL como root)
-- CREATE USER 'creditrisk_user'@'localhost' IDENTIFIED BY 'Password123!';
-- GRANT ALL PRIVILEGES ON CreditRiskDB.* TO 'creditrisk_user'@'localhost';
-- FLUSH PRIVILEGES;

-- 8. Verificar las tablas creadas
SHOW TABLES;

-- 9. Ver estructura de tablas
DESCRIBE users;
DESCRIBE predictions;