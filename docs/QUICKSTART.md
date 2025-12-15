# 🚀 Quick Start Guide - Docker Deployment

## Prerequisites Checklist

- [ ] Docker & Docker Compose installed
- [ ] Firebase credentials JSON file ready
- [ ] Firebase Project ID

## 🎯 Fastest Way to Start

### Windows:

```cmd
docker-start.bat
```

### Linux/Mac:

```bash
chmod +x docker-start.sh
./docker-start.sh
```

### Or manually:

```bash
# 1. Copy Firebase credentials
cp /path/to/firebase-credentials.json ./firebase-credentials.json

# 2. Start everything
docker-compose up -d --build

# 3. Check status
docker-compose ps
```

## 📦 What Gets Started

| Service           | Port | Access                       |
| ----------------- | ---- | ---------------------------- |
| FastAPI Backend   | 8000 | http://localhost:8000        |
| API Documentation | 8000 | http://localhost:8000/docs   |
| MySQL Database    | 3306 | Internal (or via phpMyAdmin) |
| phpMyAdmin        | 8081 | http://localhost:8081        |

## 🔐 Default Credentials

**MySQL Database:**

- Username: `inkubator`
- Password: `inkubator`
- Database: `inkubator_db`

**phpMyAdmin:**

- Same as MySQL credentials above

## ✅ Verify Everything Works

```bash
# 1. Check all services are running
docker-compose ps

# 2. Test backend health
curl http://localhost:8000/health

# 3. View API docs
# Open browser: http://localhost:8000/docs

# 4. Test ping endpoint
curl http://localhost:8000/api/v1/ping
```

## 📝 Common Commands

```bash
# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Restart backend only
docker-compose restart backend

# Access database
docker-compose exec db mysql -u inkubator -pinkubator inkubator_db

# Backup database
docker-compose exec db mysqldump -u inkubator -pinkubator inkubator_db > backup.sql
```

## 🎨 Using Makefile (Easier)

```bash
make help           # Show all commands
make up-build       # Start everything
make logs-backend   # View backend logs
make status         # Show status + URLs
make down           # Stop everything
make clean          # Remove everything
```

## 🧪 Testing Authentication

1. **Open test page**: http://localhost:8080 (if using `serve_static.py`)
2. **Or use the token generator**: `public/index.html`
3. **Sign in with Google** and get token
4. **Test login endpoint**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"firebase_token": "YOUR_TOKEN_HERE"}'
   ```

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for complete testing instructions.

## 🐛 Troubleshooting

### Backend won't start?

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Firebase credentials missing
# 2. Database not ready (wait 10s and restart)
docker-compose restart backend
```

### Port already in use?

Edit `docker-compose.yaml` and change host ports:

```yaml
ports:
  - "8001:8000" # Change 8000 to 8001
```

### Database issues?

```bash
# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

## 📚 Full Documentation

- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Complete Docker documentation
- [SETUP_AUTH.md](docs/SETUP_AUTH.md) - Firebase & MySQL setup
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - API testing guide
- [README.md](README.md) - Main project documentation

## 🎯 Next Steps

1. ✅ Services running? Go to http://localhost:8000/docs
2. ✅ Test health endpoint
3. ✅ Set up Firebase authentication
4. ✅ Test login with your frontend/client
5. ✅ Build something awesome! 🚀

---

**Need Help?** Check the full guides or open an issue!
