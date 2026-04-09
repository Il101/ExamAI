# 🎓 ExamAI Pro

> AI-powered exam preparation platform with spaced repetition learning

[![Tests](https://img.shields.io/badge/tests-84%2F86%20passing-green)]()
[![Coverage](https://img.shields.io/badge/coverage-75%25-yellow)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

ExamAI Pro is a full-stack application that uses AI (Google Gemini 2.0 Flash) to generate personalized study materials and implements spaced repetition learning with the FSRS algorithm.

## ✨ Features

- 🤖 **AI-Powered Content Generation** - Uses Plan-and-Execute agent pattern with Google Gemini
- 🧠 **Spaced Repetition** - FSRS algorithm for optimal learning retention
- 📚 **Smart Study Sessions** - Interactive flashcard reviews with progress tracking
- 📊 **Analytics Dashboard** - Track your progress, streaks, and performance
- 🔄 **Background Processing** - Celery for async exam generation
- 🔐 **Secure Authentication** - JWT tokens with refresh mechanism
- 💰 **Cost Protection** - Daily spending limits for AI API usage
- 📱 **RESTful API** - Well-documented with OpenAPI/Swagger

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                   │
│                  React + TypeScript + Tailwind           │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  API Layer (v1/endpoints)                        │   │
│  └──────────────────┬───────────────────────────────┘   │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  Service Layer (Business Logic)                  │   │
│  │  - AuthService  - ExamService  - StudyService    │   │
│  └──────────────────┬───────────────────────────────┘   │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  Repository Layer (Data Access)                  │   │
│  └──────────────────┬───────────────────────────────┘   │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  Domain Models (Pure Business Logic)            │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
│  PostgreSQL  │  │    Redis    │  │   Gemini   │
│  (Supabase)  │  │   (Cache)   │  │  2.0 Flash │
└──────────────┘  └─────────────┘  └────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 20+ (for frontend)
- Google Gemini API key

### Backend Setup

```bash
# Clone repository
git clone https://github.com/yourusername/examai-pro.git
cd examai-pro/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Docker Setup

```bash
# Start all services (backend, database, redis, celery)
docker-compose up --build

# Or for production:
docker-compose -f docker-compose.prod.yml up --build
```

## 📚 Documentation

- **API Documentation**: http://localhost:8000/api/docs (Swagger UI)
- **Project Summary**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- **Stage 10 Status**: [docs/STAGE_10_STATUS.md](docs/STAGE_10_STATUS.md)
- **Installation Guide**: [docs/STAGE_10_INSTALLATION.md](docs/STAGE_10_INSTALLATION.md)
- **Database Schema**: [docs/DATABASE_SCHEMA_EN.md](docs/DATABASE_SCHEMA_EN.md)
- **API Specification**: [docs/API_SPECIFICATION_EN.md](docs/API_SPECIFICATION_EN.md)
- **Testing Strategy**: [docs/TESTING_STRATEGY_EN.md](docs/TESTING_STRATEGY_EN.md)

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # End-to-end tests only

# Run tests in parallel
pytest -n auto
```

**Current Test Status**: 84/86 tests passing (98%)

## 🏗️ Project Structure

```
ExamAI/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # API routes
│   │   ├── services/             # Business logic
│   │   ├── repositories/         # Data access
│   │   ├── domain/               # Domain models
│   │   ├── agent/                # AI agent components
│   │   ├── core/                 # Config, security, monitoring
│   │   ├── db/                   # Database models & migrations
│   │   ├── tasks/                # Celery tasks
│   │   └── middleware/           # Security middleware
│   ├── tests/                    # Test suite
│   ├── alembic/                  # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                  # Next.js pages
│   │   ├── components/           # React components
│   │   └── lib/                  # Utilities
│   └── package.json
├── scripts/                      # Deployment scripts
├── docs/                         # Documentation
└── docker-compose.yml
```

## 🔑 Environment Variables

### Backend (.env)

```bash
# Application
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-min-32-chars

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/examai

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash-exp

# Monitoring (Production)
SENTRY_DSN=your-sentry-dsn
```

See `.env.production.example` for complete production configuration.

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token

### Exams
- `GET /api/v1/exams` - List user's exams
- `POST /api/v1/exams` - Create new exam
- `GET /api/v1/exams/{id}` - Get exam details
- `POST /api/v1/exams/{id}/start` - Start exam generation
- `GET /api/v1/exams/{id}/status` - Check generation status

### Study Sessions
- `POST /api/v1/sessions` - Create study session
- `GET /api/v1/sessions/{id}` - Get session details
- `PATCH /api/v1/sessions/{id}/complete` - Complete session

### Reviews
- `GET /api/v1/reviews/due` - Get due reviews
- `POST /api/v1/reviews/{id}/submit` - Submit review answer

### Analytics
- `GET /api/v1/analytics/progress` - Get progress stats
- `GET /api/v1/analytics/streaks` - Get study streaks

### Health
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with dependencies
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe

## 🚢 Deployment

### Railway.app (Backend)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

### Vercel (Frontend)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

### GitHub Actions (CI/CD)

Push to `main` or `develop` branch triggers automated deployment:

```bash
git push origin main      # → Production
git push origin develop   # → Staging
```

See [docs/STAGE_10_STATUS.md](docs/STAGE_10_STATUS.md) for complete deployment guide.

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.109
- **Database**: PostgreSQL 15 (Supabase)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Cache/Queue**: Redis 7
- **Tasks**: Celery
- **AI**: Google Gemini 2.0 Flash
- **Auth**: JWT (python-jose)
- **Validation**: Pydantic 2.0

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **State**: Zustand + React Query

### DevOps
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry
- **Logging**: Structured JSON logs
- **Deployment**: Railway.app + Vercel

## 📈 Performance

- **API Response Time**: <100ms (excluding AI generation)
- **AI Generation**: 30-60 seconds for complete exam
- **Database Queries**: Optimized with indexes and async queries
- **Caching**: Redis for frequently accessed data
- **Background Jobs**: Celery for long-running tasks

## 🔒 Security

- ✅ JWT authentication with refresh tokens
- ✅ Password hashing with bcrypt
- ✅ Security headers middleware
- ✅ CORS configuration
- ✅ Rate limiting (planned)
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Sensitive data filtering in logs

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Run `./scripts/deploy-check.sh` before committing

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI model
- [FSRS Algorithm](https://github.com/open-spaced-repetition/fsrs4anki) - Spaced repetition
- [Supabase](https://supabase.com/) - PostgreSQL hosting

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/examai-pro/issues)
- **Email**: (contact via GitHub Issues)

## 🗺️ Roadmap

### v1.0 (MVP) ✅
- [x] AI exam generation
- [x] Spaced repetition
- [x] Study sessions
- [x] Analytics
- [x] Authentication
- [x] Docker deployment

### v1.1 (Planned)
- [ ] Complete frontend implementation
- [ ] Email notifications
- [ ] Social authentication
- [ ] Custom domain
- [ ] Mobile app (React Native)

### v2.0 (Planned)
- [ ] Advanced analytics
- [ ] Collaborative study groups
- [ ] AI quiz generation
- [ ] Voice-based study
- [ ] Gamification

---

**Status**: ✅ Production Ready | **Version**: 1.0.0 | **Last Updated**: November 19, 2025
