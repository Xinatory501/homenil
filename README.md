# CartaMe Telegram Bot

Multi-bot support system with AI integration, operator handoff, and full admin panel.

## Features

- **Multi-bot architecture**: Support for 1-3 bots with shared database coordination
- **AI Integration**: OpenAI-compatible API with failover support
- **Support Topics**: Per-bot topics in supergroups with language labels
- **Admin Panel**: Full management of providers, keys, models, users, training
- **Anti-flood**: Configurable rate limiting with auto-ban
- **Localization**: ru/en/uz/kz support
- **No duplicate responses**: Claim-based coordination ensures only one bot responds

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for distributed locking)
- Docker & Docker Compose (recommended)

## Quick Start

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your tokens
```

### 2. Configure environment

```env
# Required
BOT1_TOKEN=your_bot1_token
ADMIN_IDS=123456789,987654321

# Optional additional bots
BOT2_TOKEN=your_bot2_token
BOT3_TOKEN=your_bot3_token

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/cartame
SHARED_DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/cartame_shared
```

### 3. Run with Docker

```bash
docker-compose up -d
```

### 4. Run locally (development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## Architecture

### Databases

- **Bot DB** (`cartame`, `cartame_bot2`, `cartame_bot3`): Per-bot data (users, sessions, history)
- **Shared DB** (`cartame_shared`): AI providers, keys, models, claims, user locks

### Multi-bot Coordination

1. **Request Claims**: Each message gets a unique claim in shared DB
2. **User Locks**: First bot to respond owns the user for 15 minutes
3. **Per-bot Topics**: Each bot creates its own topic for each user

### Topic Naming

Format: `[B1][RU] Username (ID)`
- `B1/B2/B3` - bot identifier
- `RU/EN/UZ/KZ` - user language
- Updated when user changes language

## Commands

### User Commands

- `/start` - Start bot, select language
- Text messages - Chat with AI

### Admin Commands

- `/admin` - Admin panel
- `/id` or `?id` - Show chat/topic info (in groups)
- `/ai` - Re-enable AI for user (in topic)

## Admin Panel Features

1. **AI Providers** - Manage OpenAI-compatible providers
2. **API Keys** - Add/manage API keys with rate limiting
3. **AI Models** - Configure available models
4. **Local AI** - Wizard for adding local models (Ollama, etc.)
5. **Training** - System messages for AI context
6. **Anti-flood** - Configure rate limits
7. **Privacy Policy** - Set privacy policy URL
8. **User Info** - Search and manage users
9. **Reports** - Statistics and top questions
10. **Chats** - Manage support groups
11. **Database** - Export/backup

## AI Failover

1. Try default provider -> available key -> available model
2. On failure, try other models of same provider
3. On failure, try other keys/providers
4. On complete failure, notify support and user

## Support Workflow

1. User sends message
2. AI responds (if enabled)
3. User requests operator (keywords or AI decides)
4. AI disabled, operator notified
5. Operator responds in topic
6. Response forwarded to user
7. AI auto-returns after 10 minutes of silence

## Project Structure

```
cartame/
├── main.py                 # Entry point
├── bot/
│   ├── config.py          # Configuration
│   ├── loader.py          # Bot initialization
│   ├── handlers/          # Message handlers
│   │   ├── user/          # User commands
│   │   ├── admin/         # Admin panel
│   │   └── support/       # Support group
│   ├── middlewares/       # Request processing
│   ├── keyboards/         # Inline keyboards
│   ├── services/          # Business logic
│   ├── states/            # FSM states
│   └── locales/           # Translations
├── database/
│   ├── base.py            # DB connections
│   └── models/            # SQLAlchemy models
└── docker-compose.yml     # Docker configuration
```

## License

MIT
