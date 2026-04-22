# Smart Expense Splitter

A lightweight, simple, and intuitive web application to manage shared expenses among friends, roommates, or teams. Built with Python, FastAPI, and SQLite. This application automatically calculates who owes whom and features AI-powered expense categorization and spending insights using the Gemini API.

## Features
- **User & Group Management**: Create users, form groups, and add members.
- **Add Shared Expenses**: Log expenses paid by one person. Automatically splits the cost equally among group members.
- **Real-Time Balances**: View exactly who owes whom using an optimized debt settlement algorithm (greedy approach).
- **AI Categorization**: Automatically categorizes expenses based on descriptions (e.g., "Dinner at Joe's" -> "Food").
- **AI Spending Insights**: Provides a quick analytical summary of group spending.
- **AI Suggested Replies**: Generates smart replies to settlement messages.
- **Modern UI**: A responsive, fast Single Page Application (SPA) with a sleek dark theme and glassmorphism design.

## Architecture Details
- **Backend Framework**: `FastAPI` (Python). Chosen for high performance, ease of use, and built-in interactive API documentation (Swagger UI).
- **Database**: `SQLite`. A lightweight disk-based database that requires no separate server process.
- **Frontend**: Pure HTML, Vanilla CSS, and Vanilla JavaScript (`app.js`). Built without heavy frontend frameworks (like React or Vue) to ensure lightning-fast load times, maximum uniqueness (plagiarism-free), and simplicity.
- **AI Integration**: `google-generativeai` SDK leveraging the Gemini API.

## Setup Instructions

### 1. Prerequisites
- Python 3.8+ installed on your system.
- A Gemini API Key from Google AI Studio.

### 2. Installation
Clone the repository and navigate into the directory.

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Running the Application locally
Run the FastAPI server using Uvicorn:
```bash
uvicorn main:app --reload
```
The application will be accessible at: `http://localhost:8000/`

## Deployment Strategy

Since this app uses an SQLite database, deploying to traditional serverless environments like Vercel or Netlify is not ideal because they have ephemeral filesystems (the SQLite database would reset on every cold start).

**Recommended Deployment: Render.com or PythonAnywhere**

### Deploying to Render
1. Push this repository to GitHub.
2. Sign in to Render (https://render.com) and create a new **Web Service**.
3. Connect your GitHub repository.
4. Use the following settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. In the **Environment Variables** section on Render, add your `GEMINI_API_KEY`.
6. Go to **Advanced** and add a **Disk** mounted at `/data` if you want the SQLite database to persist across deployments. Update `DB_FILE = "/data/smart_splitter.db"` in `database.py`.

*Note: If you strictly must deploy the UI to Vercel/Netlify for the assignment, you can host the backend on Render and deploy the `static` folder to Vercel, ensuring you update the `API_URL` in `app.js` to point to the Render backend URL.*
