# Setup Guide: Firebase Auth + MySQL

## Prerequisites

1. **Python 3.12+** and **uv** installed
2. **MySQL Server** running (local or cloud)
3. **Firebase Project** created at [Firebase Console](https://console.firebase.google.com/)

## Step 1: Firebase Setup

### 1.1 Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Follow the wizard to create your project
4. Enable Google Analytics (optional)

### 1.2 Enable Authentication Methods

1. In Firebase Console, go to **Build > Authentication**
2. Click "Get started"
3. Enable sign-in methods you want to use:
   - **Email/Password**
   - **Google**
   - Other providers as needed

### 1.3 Generate Service Account Credentials

1. Go to **Project Settings** (gear icon) > **Service accounts**
2. Click **"Generate new private key"**
3. Download the JSON file
4. Save it in your project (e.g., `firebase-credentials.json`)
5. **IMPORTANT:** Add this file to `.gitignore` - never commit it!

### 1.4 Get Project ID

- Find your Project ID in **Project Settings > General**
- You'll need this for the `.env` file

## Step 2: MySQL Database Setup

### 2.1 Create Database

```sql
CREATE DATABASE ai_service_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.2 Create Database User (Optional but recommended)

```sql
CREATE USER 'ai_service_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON ai_service_db.* TO 'ai_service_user'@'localhost';
FLUSH PRIVILEGES;
```

## Step 3: Project Configuration

### 3.1 Install Dependencies

```bash
# Install all dependencies including Firebase Admin SDK and SQLAlchemy
uv sync
```

### 3.2 Configure Environment Variables

Create `.env` file in project root:

```env
# Application Settings
APP_NAME="AI Service"
ENVIRONMENT=development
DEBUG=true
VERSION=1.0.0

# Server Settings
HOST=0.0.0.0
PORT=8000

# CORS Origins (comma separated)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Security (Production)
ALLOWED_HOSTS=localhost,127.0.0.1
SECRET_KEY=change-this-in-production

# ML Models
ML_MODELS_PATH=ml/models

# Database Settings
DATABASE_URL=mysql+pymysql://ai_service_user:your_secure_password@localhost:3306/ai_service_db

# Firebase Settings
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# Logging
LOG_LEVEL=INFO
```

**Important:** Replace these values:

- `your_secure_password` - Your MySQL password
- `ai_service_db` - Your database name
- `firebase-credentials.json` - Path to your Firebase credentials file
- `your-firebase-project-id` - Your Firebase Project ID

### 3.3 Add Firebase Credentials to .gitignore

```bash
echo "firebase-credentials.json" >> .gitignore
echo ".env" >> .gitignore
```

## Step 4: Run the Application

### 4.1 Start Development Server

```bash
uv run fastapi dev
```

The server will start at `http://localhost:8000`

### 4.2 Verify Setup

1. Open browser: `http://localhost:8000/docs`
2. You should see the API documentation
3. Check that `/health` endpoint returns success
4. Try the `/api/v1/ping` endpoint

## Step 5: Test Authentication

### 5.1 Frontend/Client Side (JavaScript Example)

```javascript
// 1. Sign in with Firebase
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";

const auth = getAuth();
const provider = new GoogleAuthProvider();

try {
  // Sign in with Google
  const result = await signInWithPopup(auth, provider);

  // Get Firebase ID token
  const idToken = await result.user.getIdToken();

  // 2. Send token to your backend
  const response = await fetch("http://localhost:8000/api/v1/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      firebase_token: idToken,
    }),
  });

  const data = await response.json();
  console.log("User:", data.data.user);

  // 3. Use token for protected endpoints
  const profileResponse = await fetch("http://localhost:8000/api/v1/auth/me", {
    headers: {
      Authorization: `Bearer ${idToken}`,
    },
  });

  const profile = await profileResponse.json();
  console.log("Profile:", profile.data);
} catch (error) {
  console.error("Authentication error:", error);
}
```

### 5.2 Test with cURL

**📌 How to Get Firebase Token for Testing:**

See detailed guide below in "How to Get Firebase Token for cURL Testing" section.

Quick test:

```bash
# 1. Get Firebase ID token (see methods below)
# 2. Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"firebase_token": "YOUR_FIREBASE_TOKEN_HERE"}'

# 3. Test protected endpoint
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN_HERE"
```

## How to Get Firebase Token for cURL Testing

### Method 1: Web Page Token Generator (Easiest)

1. **Open `test-firebase-token.html` in your browser**
   - File location: `test-firebase-token.html` in project root
2. **Update Firebase Config** in the HTML file:

   ```javascript
   const firebaseConfig = {
     apiKey: "YOUR_API_KEY",
     authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
     projectId: "YOUR_PROJECT_ID",
     // ... other config
   };
   ```

   Get these values from: **Firebase Console > Project Settings > Your apps**

3. **Open the file in browser** and click "Sign in with Google"

4. **Copy the token** - Click "Copy Token" or "Copy cURL Command" button

### Method 2: Python Script

1. **Install requests**:

   ```bash
   pip install requests
   ```

2. **Run the script**:

   ```bash
   python get_firebase_token.py
   ```

3. **Enter your Firebase Web API Key** (from Firebase Console > Project Settings)

4. **Choose authentication method**:

   - Email/Password: Enter your test user credentials
   - Refresh token: Use previously saved refresh token

5. **Copy the generated token** from the output

### Method 3: Manual REST API Call

```bash
# Get token using email/password
curl -X POST 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "returnSecureToken": true
  }'

# Extract idToken from response
```

### Method 4: Firebase Console (For Quick Testing)

1. Go to Firebase Console > Authentication
2. Create a test user with Email/Password
3. Use Method 2 or 3 above with these credentials

## Available Endpoints

### Public Endpoints

- `POST /api/v1/auth/login` - Login or register with Firebase token

### Protected Endpoints (Require Bearer Token)

- `GET /api/v1/auth/me` - Get current user profile
- `PUT /api/v1/auth/me` - Update user profile
- `DELETE /api/v1/auth/me` - Deactivate account

## Troubleshooting

### Database Connection Issues

```bash
# Test MySQL connection
mysql -u ai_service_user -p -h localhost ai_service_db
```

### Firebase Initialization Errors

- Check that `FIREBASE_CREDENTIALS_PATH` points to valid JSON file
- Verify `FIREBASE_PROJECT_ID` matches your Firebase project
- Ensure Firebase credentials file has correct permissions

### Token Verification Fails

- Check that client is sending valid Firebase ID token
- Verify token format: `Authorization: Bearer <token>`
- Ensure Firebase project IDs match between client and server

## Production Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Update `ALLOWED_ORIGINS` with your frontend domain
- [ ] Update `ALLOWED_HOSTS` with your production domain
- [ ] Use environment-specific Firebase credentials
- [ ] Use secure MySQL connection (SSL/TLS)
- [ ] Store `.env` file securely (use secrets manager in cloud)
- [ ] Never commit Firebase credentials to git
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Use connection pooling for database
- [ ] Consider using Alembic for database migrations

## Next Steps

1. **Add more user fields** - Extend `User` model in `app/models/user.py`
2. **Implement role-based access** - Add roles/permissions to User model
3. **Add email verification** - Use Firebase email verification
4. **Implement refresh tokens** - Handle token refresh logic
5. **Add rate limiting** - Protect endpoints from abuse
6. **Set up monitoring** - Use logging and error tracking
7. **Database migrations** - Consider adding Alembic for schema changes
