# TempMail Pro 📧

A production-ready **Temporary Email (Temp Mail)** web application with a premium modern UI. Generate disposable email addresses, receive emails in real-time, and automatically extract OTP codes and verification links.

Built with **React 19 + FastAPI** following Clean Architecture principles.

---

## ✨ Features

### Core Features
- 🎲 **One-click Email Generation** - Random or custom usernames
- 🌐 **Multiple Domain Support** - Choose from various domains
- 📥 **Real-time Inbox** - WebSocket-powered live updates (auto-refresh every 2s)
- 🤖 **Automatic OTP Detection** - Detects 4, 5, 6, and 8 digit codes
- 🔗 **Verification Link Extraction** - Auto-detects and displays verification URLs
- 📎 **Attachments & Images** - View and download email attachments
- ⏰ **Email Expiration Timer** - Visual countdown with renew option
- 🗑️ **Email Management** - Delete individual, delete all, search, paginate
- 📋 **Copy Email & OTP** - One-click copy buttons

### UI/UX
- 🌙 **Dark/Light/System Theme** - Smooth transitions
- 🎨 **Premium SaaS Design** - Glassmorphism, gradients, rounded corners
- 💫 **Framer Motion Animations** - Smooth page transitions
- 📱 **Fully Responsive** - Desktop, tablet, and mobile
- 🔔 **Beautiful Toast Notifications**
- 💀 **Loading Skeletons**
- 🎯 **Empty States**

### Admin Panel
- 📊 **Dashboard** - Total emails, today's emails, active addresses, users
- 🗑️ **Email Management** - View and delete all email addresses
- 📝 **System Logs** - View and export system activity
- 🌐 **Domain Management**
- ⚡ **System Status** - Database, Redis, SMTP health

### Security
- 🛡️ **Rate Limiting** - Per-IP and per-endpoint limits
- ✅ **Input Validation** - Pydantic schemas
- 🔒 **XSS Protection** - HTML sanitization
- 🚫 **CSRF Protection**
- 🌐 **CORS** - Configurable origins
- 🔐 **Secure Headers** - CSP, HSTS, X-Frame-Options
- 📝 **Error Handling** - Structured error responses
- 📊 **Logging** - JSON structured logs

---

## 🏗️ Architecture

```
tempmail-pro/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/   # Route handlers
│   │   │       ├── dependencies.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py       # Settings
│   │   │   ├── security/       # JWT, hashing
│   │   │   └── exceptions/     # Custom exceptions
│   │   ├── db/
│   │   │   └── database.py     # SQLAlchemy setup
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   ├── tasks/              # Background tasks
│   │   ├── websockets/         # WebSocket manager
│   │   └── main.py             # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                # React 19 Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/          # Reusable UI components
│   │   │   ├── layout/      # Layout components
│   │   │   ├── email/       # Email-specific components
│   │   │   ├── admin/       # Admin components
│   │   │   └── common/      # Common components
│   │   ├── pages/           # Route pages
│   │   ├── hooks/           # Custom hooks
│   │   ├── context/         # React context
│   │   ├── services/        # API client
│   │   ├── types/           # TypeScript types
│   │   ├── utils/           # Utilities
│   │   └── styles/          # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── docker-compose.yml      # Full stack deployment
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- (Optional) Docker & Docker Compose

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/tempmail-pro.git
cd tempmail-pro

# Create .env file
cp backend/.env.example backend/.env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run database migrations (if using Alembic)
# alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env
echo "VITE_WS_URL=ws://localhost:8000/api/v1/ws" >> .env

# Start dev server
npm run dev
```

---

## 📡 API Documentation

### REST Endpoints

| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET | `/health/detailed` | Health check with system stats |
| POST | `/api/v1/addresses/generate` | Generate random email address |
| POST | `/api/v1/addresses` | Create custom email address |
| GET | `/api/v1/addresses` | List email addresses |
| GET | `/api/v1/addresses/{id}` | Get email address details |
| POST | `/api/v1/addresses/{id}/extend` | Extend email expiration |
| DELETE | `/api/v1/addresses/{id}` | Delete email address |
| POST | `/api/v1/auth/login` | Login with email |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/emails/{id}/inbox` | Get inbox emails |
| GET | `/api/v1/emails/{id}/emails/{message_id}` | Get specific email |
| DELETE | `/api/v1/emails/{id}/emails/{message_id}` | Delete email |
| DELETE | `/api/v1/emails/{id}/emails` | Delete all emails |
| GET | `/api/v1/emails/{id}/emails/{message_id}/otp` | Extract OTP codes |
| WS | `/api/v1/ws/ws/{email_id}` | WebSocket for real-time updates |
| GET | `/api/v1/admin/stats` | Admin statistics |
| GET | `/api/v1/admin/emails` | List all emails (admin) |
| GET | `/api/v1/admin/logs` | View system logs (admin) |

### WebSocket Events

```json
{
  "type": "new_email",
  "email_id": "uuid",
  "data": {
    "id": "uuid",
    "subject": "Welcome!",
    "from_address": "sender@example.com",
    "from_name": "Sender Name",
    "received_at": "2024-01-01T12:00:00Z",
    "has_attachments": false
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

---

## 🗄️ Database Schema

### Tables
- **email_addresses** - Generated email addresses
- **emails** - Received emails
- **sessions** - User sessions
- **domains** - Supported domains
- **rate_limits** - Rate limiting records
- **audit_logs** - System audit logs

---

## 🔧 Configuration

All configuration is done via environment variables. See `backend/.env.example` for the full list.

### Key Variables
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key (change in production!)
- `ADMIN_PASSWORD` - Admin panel password
- `DEFAULT_DOMAINS` - Comma-separated list of domains
- `CORS_ORIGINS` - Comma-separated allowed origins

---

## 🧪 Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm run test
```

---

## 📦 Production Deployment

### Using Docker Compose
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
1. Build frontend: `cd frontend && npm run build`
2. Serve with nginx or similar
3. Run backend with gunicorn: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [React](https://react.dev/) - UI library
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [Framer Motion](https://www.framer.com/motion/) - Animation library
- [TanStack Query](https://tanstack.com/query) - Data fetching

---

## 📞 Support

For support, email support@tempmail.pro or open an issue on GitHub.

---

<div align="center">
  <p>Built with ❤️ by the TempMail Pro Team</p>
</div>