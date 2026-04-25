# StressMap Backend API

A FastAPI backend for **StressMap** — a Taglish wellness app that lets users log daily stress data, share posts in a community feed, and receive AI-generated motivational reminders powered by Google Gemini.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| Database | MongoDB (via Motor async driver) |
| AI | Google Gemini 2.5 Flash (`google-genai`) |
| Content Moderation | scikit-learn ML model (`.pkl`) |
| Auth | bcrypt + JWT |
| Deployment | Heroku (Procfile) |

---

## Project Structure

```
hackathon-backend-main/
├── main.py                    # App entry point, CORS, startup indexes
├── Procfile                   # Heroku deployment config
├── requirements.txt           # Python dependencies
│
├── db/
│   └── database.py            # MongoDB connection (Motor)
│
├── models/
│   ├── post.py                # Post & comment request models
│   ├── user.py                # User request/response models
│   ├── schemas.py             # DailyLog & LogResponse schemas
│   └── nlp/
│       └── words-filter.pkl   # Trained ML moderation model
│
├── routes/
│   ├── posts.py               # Post & comment CRUD endpoints
│   ├── users.py               # Auth endpoints (register/login)
│   ├── logs.py                # Daily stress log endpoints
│   ├── motivational.py        # AI quote generation endpoint
│   └── insights.py            # (reserved)
│
└── services/
    ├── ai_service.py          # Gemini API integration with retry logic
    ├── post_service.py        # Post/comment business logic
    ├── user_service.py        # Auth business logic
    ├── moderation_service.py  # ML-based content moderation
    └── pattern_engine.py      # (reserved)
```

---

## Features

- **Daily Stress Logging** — Users log stress level, sleep hours, breakfast habits, food quality, physical activity, and notes.
- **Community Posts** — Anonymous feed with full CRUD, likes, comments, and hide/unhide functionality. Posts hidden by a user are filtered from their feed.
- **ML Content Moderation** — Every post is run through a local scikit-learn model before publishing. Posts flagged as `harassment` are rejected; `support_needed` and `safe` are allowed through.
- **AI Motivational Quotes** — Picks a random log from the database and sends it to Gemini 2.5 Flash, which generates a short Taglish wellness reminder without exposing the user's raw data back to them.
- **User Auth** — Register and login with bcrypt-hashed passwords and 7-day JWT tokens.

---

## Getting Started

### Prerequisites

- Python 3.10+
- MongoDB instance (local or Atlas)
- Google Gemini API key

### Installation

```bash
git clone <repo-url>
cd hackathon-backend-main
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<dbname>
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_jwt_secret_here
```

> ⚠️ `JWT_SECRET` falls back to `"fallback_secret_change_this"` if not set. Always override this in production.

### Running Locally

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

- Health check: `GET /`
- Interactive docs: `GET /docs`

---

## API Reference

### Auth — `/users`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/users/register` | Register a new user |
| POST | `/users/login` | Login and receive a JWT token |
| GET | `/users/{user_id}` | Get user profile (no password) |

**Register / Login body:**
```json
{
  "nickname": "Kuya Dev",
  "username": "kuyadev",
  "password": "securepassword"
}
```

---

### Daily Logs — `/logs`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/logs/` | Create a new daily log |
| GET | `/logs/` | Get recent logs (default: last 5) |
| DELETE | `/logs/{log_id}` | Delete a log |

**Log body:**
```json
{
  "stress_level": 7,
  "sleep_hours": 5.5,
  "skipped_breakfast": true,
  "food_quality": "poor",
  "activity": "none",
  "notes": "Mahirap na araw ngayon."
}
```

---

### Posts — `/posts`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/posts/?user_id=` | Create a post (moderated) |
| GET | `/posts/?user_id=` | Get all posts (filtered by hidden) |
| GET | `/posts/{post_id}` | Get a single post |
| PUT | `/posts/{post_id}?user_id=` | Edit your post |
| DELETE | `/posts/{post_id}?user_id=` | Delete your post |
| POST | `/posts/{post_id}/like?user_id=` | Toggle like on a post |
| POST | `/posts/{post_id}/hide?user_id=` | Toggle hide a post from your feed |

**Post body:**
```json
{ "content": "Sobrang pagod ngayon pero kaya pa!" }
```

#### Comments — nested under `/posts`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/posts/{post_id}/comments?user_id=` | Add a comment |
| GET | `/posts/{post_id}/comments` | Get comments on a post |
| PUT | `/posts/comments/{comment_id}?user_id=` | Edit your comment |
| DELETE | `/posts/comments/{comment_id}?user_id=` | Delete your comment |
| POST | `/posts/comments/{comment_id}/like?user_id=` | Toggle like on a comment |

---

### Motivational Quote — `/motivational`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/motivational/` | Get an AI-generated Taglish wellness quote |

The endpoint picks a random log from the database and prompts Gemini to generate a short, caring reminder focused on the user's most concerning metric — without echoing raw numbers back. Falls back to canned Taglish messages if the API quota is exhausted or unavailable.

---

## Content Moderation

Posts are classified by a local ML model (`words-filter.pkl`) before being saved:

| Label | Behavior |
|---|---|
| `safe` | Published normally |
| `support_needed` | Published; may trigger wellness resources in the frontend |
| `harassment` | Rejected with HTTP 422 |

---

## Deployment (Railway)

The `Procfile` tells Railway how to start the server:

```
web: uvicorn main:app --host=0.0.0.0 --port=${PORT:-8000}
```

### Steps

1. Push your code to a GitHub repository.
2. Go to [railway.app](https://railway.app) and create a new project → **Deploy from GitHub repo**.
3. Select your repository. Railway will auto-detect the `Procfile`.
4. Go to your service's **Variables** tab and add:

| Variable | Value |
|---|---|
| `MONGO_URI` | Your MongoDB Atlas connection string |
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `JWT_SECRET` | A strong random secret string |

5. Railway will build and deploy automatically. Your app will be assigned a public URL (e.g. `https://your-app.up.railway.app`).

> 💡 Railway reads `PORT` from the environment automatically — the `${PORT:-8000}` fallback in the Procfile handles both local and Railway deployments.

---

## Dependencies

```
fastapi
uvicorn
motor==3.3.2
pymongo[srv]==4.6.1
python-dotenv
google-genai
bcrypt
pyjwt
scikit-learn==1.7.2
```
