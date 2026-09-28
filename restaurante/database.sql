-- =============================================================
--  SISTEMA DE GESTÃO DE RESTAURANTE
--  Script de criação do banco de dados MySQL
-- =============================================================

CREATE DATABASE IF NOT EXISTS restaurante_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE restaurante_db;

-- -------------------------------------------------------------
-- Tabela de Usuários (Admin)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL,
    criado_em   DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de TVs cadastradas
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tvs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,          -- Ex: "TV Entrada", "TV Bar"
    slug        VARCHAR(50)  NOT NULL UNIQUE,   -- Ex: "1", "2", "todos"
    ativa       TINYINT(1)   DEFAULT 1,
    criado_em   DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de Playlists
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS playlists (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    descricao   VARCHAR(255),
    criado_em   DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Associação TV <-> Playlist (muitos-para-um: cada TV tem 1 playlist ativa)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tv_playlist (
    tv_id           INT NOT NULL,
    playlist_id     INT NOT NULL,
    PRIMARY KEY (tv_id),
    FOREIGN KEY (tv_id)       REFERENCES tvs(id)       ON DELETE CASCADE,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de Mídias (imagens e vídeos)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS midias (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    playlist_id     INT NOT NULL,
    nome            VARCHAR(150) NOT NULL,
    tipo            ENUM('imagem', 'video') NOT NULL,
    arquivo         VARCHAR(255) NOT NULL,          -- caminho relativo em static/uploads/
    duracao_seg     INT DEFAULT 10,                 -- segundos (só para imagens)
    ordem           INT DEFAULT 0,                  -- posição na playlist
    ativa           TINYINT(1) DEFAULT 1,
    criado_em       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de Categorias do Cardápio
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    ordem       INT DEFAULT 0,
    ativa       TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de Itens do Cardápio
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cardapio (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    categoria_id    INT,
    nome            VARCHAR(150) NOT NULL,
    descricao       VARCHAR(255),
    preco           DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    disponivel      TINYINT(1) DEFAULT 1,
    criado_em       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de Mesas
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mesas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    numero      INT NOT NULL UNIQUE,
    descricao   VARCHAR(100),
    ativa       TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de Comandas (pedidos por mesa)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comandas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    mesa_id     INT NOT NULL,
    status      ENUM('aberta', 'fechada') DEFAULT 'aberta',
    aberta_em   DATETIME DEFAULT CURRENT_TIMESTAMP,
    fechada_em  DATETIME,
    FOREIGN KEY (mesa_id) REFERENCES mesas(id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de Pedidos (cada pedido vai para a cozinha)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pedidos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    comanda_id      INT NOT NULL,
    mesa_numero     INT NOT NULL,               -- desnormalizado para facilitar exibição no KDS
    status          ENUM('aguardando', 'em_preparo', 'pronto', 'entregue') DEFAULT 'aguardando',
    observacao      VARCHAR(255),
    criado_em       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comanda_id) REFERENCES comandas(id)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Tabela de Itens do Pedido
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pedido_itens (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id       INT NOT NULL,
    cardapio_id     INT NOT NULL,
    nome_item       VARCHAR(150) NOT NULL,       -- snapshot do nome no momento do pedido
    preco_unit      DECIMAL(10,2) NOT NULL,      -- snapshot do preço
    quantidade      INT NOT NULL DEFAULT 1,
    FOREIGN KEY (pedido_id)   REFERENCES pedidos(id)  ON DELETE CASCADE,
    FOREIGN KEY (cardapio_id) REFERENCES cardapio(id)
) ENGINE=InnoDB;

-- =============================================================
-- DADOS INICIAIS
-- =============================================================

-- TV padrões
INSERT INTO tvs (nome, slug) VALUES
    ('TV 1', '1'),
    ('TV 2', '2'),
    ('TV 3', '3'),
    ('Todas as TVs', 'todos');

-- Playlist padrão
INSERT INTO playlists (nome, descricao) VALUES
    ('Principal', 'Playlist padrão do estabelecimento');

-- Associar todas as TVs à playlist principal
INSERT INTO tv_playlist (tv_id, playlist_id) VALUES (1,1),(2,1),(3,1),(4,1);

-- Categorias do cardápio
INSERT INTO categorias (nome, ordem) VALUES
    ('Entradas', 1),
    ('Pratos Principais', 2),
    ('Bebidas', 3),
    ('Sobremesas', 4);

-- Mesas de 1 a 20
INSERT INTO mesas (numero) VALUES
    (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),
    (11),(12),(13),(14),(15),(16),(17),(18),(19),(20);

-- Usuário admin padrão (senha: admin123 — troque após o primeiro login!)
-- Hash gerado com werkzeug.security.generate_password_hash
INSERT INTO usuarios (nome, email, senha_hash) VALUES (
    'Administrador',
    'admin@restaurante.com',
    'scrypt:32768:8:1$placeholder$hash_gerado_pelo_flask'
);
-- ATENÇÃO: O hash acima é um placeholder. O Flask irá gerar o hash real
-- na primeira execução via python init_db.py

