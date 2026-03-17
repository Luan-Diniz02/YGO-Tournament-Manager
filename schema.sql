CREATE DATABASE IF NOT EXISTS torneio CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE torneio;

CREATE TABLE IF NOT EXISTS duelistas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL UNIQUE,
    vitorias INT NOT NULL DEFAULT 0,
    derrotas INT NOT NULL DEFAULT 0,
    empates INT NOT NULL DEFAULT 0,
    participacao INT NOT NULL DEFAULT 0,
    pontos INT NOT NULL DEFAULT 0,
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_duelistas_ativo (ativo),
    INDEX idx_duelistas_pontos (pontos)
);

CREATE TABLE IF NOT EXISTS torneios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    rodadas INT NOT NULL,
    quant_duelistas INT NOT NULL,
    data DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_torneios_data (data)
);

CREATE TABLE IF NOT EXISTS torneio_participantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    torneio_id INT NOT NULL,
    duelista_id INT NOT NULL,
    vitorias INT NOT NULL DEFAULT 0,
    derrotas INT NOT NULL DEFAULT 0,
    empates INT NOT NULL DEFAULT 0,
    pontos_obtidos INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tp_torneio FOREIGN KEY (torneio_id)
        REFERENCES torneios(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_tp_duelista FOREIGN KEY (duelista_id)
        REFERENCES duelistas(id)
        ON DELETE RESTRICT,
    UNIQUE KEY uk_tp_torneio_duelista (torneio_id, duelista_id),
    INDEX idx_tp_torneio (torneio_id),
    INDEX idx_tp_duelista (duelista_id)
);
