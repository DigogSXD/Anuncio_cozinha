# 🍽️ RestaurantePro — Sistema de Gestão para Restaurantes

Sistema completo com **Digital Signage para Smart TVs** e **Sistema de Comandas (KDS)** construído com Flask + MySQL + Bootstrap.

---

## 📁 Estrutura do Projeto

```
restaurante/
├── app.py                  # Aplicação principal (factory + blueprints)
├── models.py               # Modelos SQLAlchemy
├── init_db.py              # Script de inicialização do banco
├── requirements.txt        # Dependências Python
├── .env.example            # Modelo de variáveis de ambiente
├── database.sql            # Script SQL manual (alternativa ao init_db.py)
│
├── routes/
│   ├── auth.py             # Login / Logout
│   ├── admin.py            # Painel administrativo completo
│   ├── tv.py               # Player das Smart TVs + API JSON
│   ├── garcom.py           # Painel do garçom (mobile-first)
│   └── cozinha.py          # KDS — cozinha em tempo real
│
├── templates/
│   ├── base.html           # Layout base com navbar
│   ├── auth/login.html
│   ├── admin/              # Dashboard, TVs, Playlists, Cardápio, Mesas, Pedidos
│   ├── tv/player.html      # Player de Digital Signage (fullscreen)
│   ├── garcom/             # Seleção de mesa, pedido, confirmação
│   └── cozinha/index.html  # KDS dark-mode com polling
│
└── static/
    ├── css/app.css
    ├── js/app.js
    └── uploads/
        ├── imagens/        # Imagens das playlists (gerado automaticamente)
        └── videos/         # Vídeos das playlists (gerado automaticamente)
```

---

## ⚙️ Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| Python | 3.10+ |
| MySQL | 8.0+ (ou Docker) |
| pip | qualquer |

---

## 🚀 Passo a Passo — Setup Completo

### 1. Subir o MySQL com Docker (recomendado)

Se não tiver MySQL instalado localmente, use Docker:

```bash
docker run --name restaurante-db \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=restaurante_db \
  -p 3306:3306 \
  -d mysql:8.0
```

Aguarde ~10 segundos para o container iniciar.

---

### 2. Criar e ativar a Virtual Environment (venv)

**Windows (PowerShell):**
```powershell
cd "c:\Users\Diogo\Desktop\Anuncio cozinha\restaurante"

# Cria a venv
python -m venv venv

# Ativa a venv
venv\Scripts\Activate.ps1

# Se aparecer erro de política de execução, rode primeiro:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux / macOS:**
```bash
cd ~/restaurante

python3 -m venv venv
source venv/bin/activate
```

Quando ativada, o terminal mostra `(venv)` no início da linha.

---

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

---

### 4. Configurar as variáveis de ambiente

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Abra o arquivo `.env` e preencha:

```env
SECRET_KEY=coloque-uma-chave-aleatoria-longa-aqui
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root123
MYSQL_DATABASE=restaurante_db
```

> **Dica:** Para gerar uma SECRET_KEY segura:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

### 5. Inicializar o banco de dados

```bash
python init_db.py
```

Saída esperada:
```
✔  Tabelas criadas / verificadas.
✔  Usuário admin criado  (admin@restaurante.com / admin123)
✔  TVs padrão verificadas.
✔  Playlist principal verificada.
✔  Categorias do cardápio verificadas.
✔  Mesas 1–20 verificadas.

🚀  Banco inicializado com sucesso!
```

---

### 6. Rodar o servidor

```bash
python app.py
```

O servidor inicia em `http://0.0.0.0:5000` — acessível por qualquer dispositivo na mesma rede.

---

## 🔐 Primeiro Acesso

| Campo | Valor |
|---|---|
| URL | http://localhost:5000 |
| E-mail | admin@restaurante.com |
| Senha | **admin123** |

> ⚠️ **Troque a senha** assim que acessar. No momento a troca é feita diretamente no banco ou adicionando uma rota de perfil.

---

## 📺 URLs do Sistema

| Módulo | URL | Dispositivo |
|---|---|---|
| Admin / Dashboard | `/` ou `/admin/` | PC / notebook |
| Login | `/login` | qualquer |
| **TV 1** | `/tv/1` | Smart TV 1 |
| **TV 2** | `/tv/2` | Smart TV 2 |
| **TV 3** | `/tv/3` | Smart TV 3 |
| **Todas as TVs** | `/tv/todos` | qualquer TV |
| **Garçom** | `/garcom/` | celular do garçom |
| **Cozinha (KDS)** | `/cozinha/` | tela da cozinha |

Para acessar de outro dispositivo na mesma rede Wi-Fi:
```
http://<IP-DO-SERVIDOR>:5000/garcom/
```
Descubra o IP do servidor com `ipconfig` (Windows) ou `ip a` (Linux).

---

## 📋 Fluxo de Uso

### Digital Signage (Smart TVs)

1. Acesse o Admin → **Playlists** → crie uma playlist
2. Dentro da playlist, clique em **Gerenciar Mídias** → faça upload de imagens/vídeos
3. Configure a duração de cada imagem (em segundos)
4. Vá em **TVs** → associe cada TV à playlist desejada
5. Abra `/tv/1` na Smart TV — o player carrega e faz loop automaticamente

**Comportamento do player:**
- Imagens: exibidas pelo tempo configurado, com barra de progresso
- Vídeos: reproduzidos até o final antes de avançar
- Ciclo infinito pela ordem definida
- Duplo clique na TV → entra em fullscreen
- Playlist recarregada automaticamente a cada 5 minutos

---

### Pedidos (Garçom → Cozinha)

1. **Admin** → **Cardápio**: cadastre categorias e itens com preços
2. O garçom acessa `/garcom/` no celular
3. Toca na mesa desejada
4. Seleciona os itens (+ / −) por categoria
5. Adiciona observação opcional e envia
6. A **Cozinha** em `/cozinha/` recebe o pedido em tempo real

**Fluxo de status na cozinha:**
```
Aguardando → Em Preparo → Pronto → Entregue (sai da tela)
```

- Timer visível em cada card (fica vermelho após 10 minutos)
- Som de notificação quando novo pedido chega
- Pedidos sempre ordenados do mais antigo para o mais recente

---

## 🔧 Comandos úteis do dia a dia

```bash
# Ativar venv (sempre antes de rodar)
venv\Scripts\Activate.ps1        # Windows
source venv/bin/activate          # Linux/macOS

# Rodar o servidor
python app.py

# Reinicializar banco (apaga e recria tudo)
python init_db.py

# Atualizar dependências após alterar requirements.txt
pip install -r requirements.txt

# Desativar a venv
deactivate

# Ver dependências instaladas
pip list
```

---

## 🐳 Docker Compose (opcional — MySQL + app juntos)

Crie um `docker-compose.yml` na raiz do projeto:

```yaml
version: '3.8'
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: restaurante_db
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      MYSQL_HOST: db
      MYSQL_USER: root
      MYSQL_PASSWORD: root123
      MYSQL_DATABASE: restaurante_db
      SECRET_KEY: troque-aqui
    depends_on:
      - db

volumes:
  db_data:
```

E um `Dockerfile` simples:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

## 🛠️ Possíveis problemas

| Problema | Solução |
|---|---|
| `ModuleNotFoundError` | Certifique-se que a venv está ativada: `venv\Scripts\Activate.ps1` |
| `Access denied for user 'root'` | Verifique usuário/senha no `.env` |
| `Can't connect to MySQL` | Verifique se o MySQL/Docker está rodando |
| Erro de política no PowerShell | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| TV não mostra conteúdo | Verifique se a TV tem playlist associada no admin |
| Autoplay de vídeo bloqueado | Clique uma vez na tela da TV para desbloquear |

---

## 📦 Dependências principais

| Pacote | Uso |
|---|---|
| Flask 3.0 | Framework web |
| Flask-SQLAlchemy | ORM para o banco |
| Flask-Login | Autenticação de sessão |
| PyMySQL | Driver MySQL para Python |
| Werkzeug | Hash de senhas + upload seguro |
| python-dotenv | Leitura do arquivo `.env` |
| Pillow | Processamento de imagens (futuro) |

---

*RestaurantePro — desenvolvido com Flask + MySQL + Bootstrap 5*
