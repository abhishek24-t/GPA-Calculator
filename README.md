# 🎓 GPA Calculator AI Agent (SPPU Engineering Edition)

> 🚀 **Live Demo on GitHub Pages**:  
> • **[Academic Dashboard App](https://abhishek24-t.github.io/GPA-Calculator/)**  
> • **[Marketing Landing Page](https://abhishek24-t.github.io/GPA-Calculator/landing.html)**

A modern, full-stack, deterministic academic GPA calculation engine and conversational AI advisor designed for college engineering students, with specialized support for the **Savitribai Phule Pune University (SPPU) Choice Based Credit System (CBCS)**.

Built with **FastAPI**, **SQLite**, **Vanilla HTML5/CSS3/JavaScript**, and **OpenAI API** with a deterministic fallback engine.

---

## 🌟 Key Features

1. **Deterministic SGPA Calculator**:
   - Computes Semester Grade Point Average using the true weighted credit formula:  
     $$\text{SGPA} = \frac{\sum (\text{Credit}_i \times \text{Grade Point}_i)}{\sum \text{Credit}_i}$$
   - Supports SPPU letter grades ($O, A+, A, B+, B, C, P, F, Ab$) and numerical grade points.
   - Enforces strict input validation: credits must be strictly positive ($> 0$), grade points within bounds, and missing values are never guessed.
   - Automatically detects backlogs ($< 4.0\text{ GP}$).

2. **Credit-Weighted CGPA Calculator**:
   - Computes cumulative GPA across semesters:  
     $$\text{CGPA} = \frac{\sum (\text{Semester SGPA}_j \times \text{Semester Credits}_j)}{\sum \text{Semester Credits}_j}$$
   - Clearly contrasts credit-weighted CGPA with a simple unweighted average of SGPAs.

3. **Target GPA Predictor**:
   - Calculates the exact average SGPA required in remaining semesters to achieve a target graduation CGPA.
   - Identifies if the target is **Mathematically Achievable**, **Comfortably Achieved**, **High Effort Required**, or **Mathematically Impossible** ($> 10.0\text{ SGPA}$).
   - Displays maximum achievable CGPA (assuming 10.0 in all remaining credits) and benchmark scenarios.

4. **"GPA Assistant AI" Chatbot**:
   - Dual-engine architecture:
     - **OpenAI Function/Tool Calling** (via GPT-4o-mini) when `OPENAI_API_KEY` is provided.
     - **Deterministic Engine Fallback** when API key is not configured, ensuring 100% reliability out-of-the-box.
   - Never hallucinates arithmetic: All numerical results are computed exclusively by the deterministic Python calculation module.
   - Answers questions like:
     - *"What is my SGPA with 4 credits A+, 4 credits A, and 3 credits O?"*
     - *"How can I reach an 8.5 CGPA?"*
     - *"What happens if I score 8.8 SGPA next semester?"*
     - *"How will a backlog affect my CGPA?"*
     - Supports English and conversational Hinglish naturally.

5. **Performance Dashboard**:
   - Displays Current CGPA, Latest SGPA, Total Completed Credits, and Target Gap.
   - Interactive **Chart.js** line chart of semester progression and doughnut chart of grade distribution.

6. **What-If Analysis Simulator**:
   - **Subject Grade Mode**: Adjust hypothetical grades to see immediate impact on semester SGPA.
   - **Semester CGPA Mode**: Add hypothetical future semesters with delta indicators ($+0.25\text{ CGPA}$).

7. **Backlog & Grade Improvement Manager**:
   - Configurable university ordinances: SPPU CBCS Grade Replacement, Capped Penalty, or Separate Clearance.
   - Simulates points gained and cumulative CGPA recovery when clearing backlogs.

8. **Academic History (SQLite Persistence)**:
   - Full CRUD support: view, edit, and delete saved semester records.
   - Pre-seeded with sample SPPU engineering semester records clearly labeled as sample data.

9. **Grading Scheme Settings**:
   - Configurable letter-grade to grade-point mappings.
   - Default SPPU 10-point scale: $O(10), A+(9), A(8), B+(7), B(6), C(5), P(4), F(0), Ab(0)$.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3 (Modern Glassmorphic Design, Dark & Light Mode, Responsive), Vanilla JavaScript, Chart.js CDN.
- **Backend**: Python 3.14+, FastAPI, Uvicorn, Pydantic v2.
- **Database**: SQLite (persisted in `backend/app/gpa_academic.db`).
- **AI**: OpenAI API with deterministic local intent parser fallback.
- **Testing**: Pytest automated test suite (27 passing tests).

---

## 📁 Project Structure

```
gpa-calculator-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point & static server
│   │   ├── calculator.py        # Deterministic Python GPA calculation engine
│   │   ├── schemas.py           # Pydantic request & response models
│   │   ├── database.py          # SQLite database layer & sample data seeding
│   │   ├── ai_agent.py          # GPA Assistant AI with tool calling & fallback
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── calculator_routes.py
│   │       ├── history_routes.py
│   │       └── chat_routes.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_calculator.py  # Comprehensive calculation unit tests
│   │   └── test_api.py         # FastAPI endpoint integration tests
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   └── .env                     # Local environment settings
├── frontend/
│   ├── index.html               # Academic Dashboard with SaaS analytics UI
│   ├── landing.html             # Marketing Landing Page with dark monochrome aesthetic
│   ├── landing.css              # Marketing landing page stylesheet
│   ├── landing.js               # Landing page animations, counter & FAQ accordion
│   ├── css/
│   │   └── style.css            # Dark/light theme, glassmorphic design system
│   └── js/
│       └── app.js               # Frontend controller, Chart.js, SPPU converter & API client
├── README.md                    # Project documentation
└── .gitignore                   # Git ignore rules
```

---

## 🚀 Windows Installation & Setup Guide

### 1. Prerequisites
- Windows 10 or 11
- Python 3.10 or higher installed (Python 3.14 recommended)
- Visual Studio Code or any code editor

### 2. Open Terminal in the Project Directory
Open PowerShell or Command Prompt and navigate to the project directory:
```powershell
cd "c:\Users\userm\OneDrive\Desktop\AI chatbot\gpa-calculator-ai\backend"
```

### 3. Create & Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# (If using Command Prompt)
.\venv\Scripts\activate.bat
```

> **Note on PowerShell Script Execution:**  
> If PowerShell displays a script execution policy error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 4. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables (Optional for OpenAI)
A template file `.env.example` is provided. Copy or edit `.env`:
```powershell
cp .env.example .env
```
Inside `backend/.env`:
```env
OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
HOST=127.0.0.1
PORT=8000
```
> *If no OpenAI API key is supplied, all GPA calculations and the AI Assistant continue to work using the built-in deterministic academic engine.*

---

## 🏃 Running the Application

### Start the Unified FastAPI + Frontend Server
From `gpa-calculator-ai/backend` with the virtual environment activated:
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once started:
- **Web Application**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in any browser.
- **Interactive Swagger API Docs**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- **Alternative Static Frontend**: You can also double-click `frontend/index.html` to open directly.

---

## 🧪 Running Automated Tests

Run the test suite from the `backend` folder:
```powershell
pytest tests/
```
Output:
```
============================= 27 passed in 0.65s ==============================
```

---

## 🔬 Testing Major Features

1. **SGPA Calculator**:
   - Go to the **SGPA Calculator** tab.
   - Click **Load Sample Semester** or add subjects manually with credits and grades.
   - Click **Calculate SGPA** to view the weighted grade point average and breakdown.
   - Click **Save to Academic History** to persist to SQLite.

2. **CGPA Calculator**:
   - Go to **CGPA Calculator**.
   - Click **Load From Saved History** or add semesters with SGPAs and credit loads.
   - Click **Calculate Cumulative CGPA** to see the credit-weighted CGPA vs simple average.

3. **Target GPA Predictor**:
   - Go to **Target GPA Predictor**.
   - Enter your current CGPA (e.g., `8.20`), completed credits (`64`), remaining credits (`44`), and target CGPA (`8.60`).
   - Click **Run Target Feasibility Analysis** to see the exact required remaining SGPA and benchmark scenario outcomes.

4. **GPA Assistant AI**:
   - Go to **GPA Assistant AI**.
   - Click any quick prompt chip (e.g., *"How can I reach an 8.5 CGPA?"* or *"How will a backlog affect my CGPA?"*).
   - Observe the response verified by the calculation engine.

5. **Theme Toggle**:
   - Click the Moon/Sun icon in the top header to seamlessly switch between Dark Mode and Light Mode.

---

## 🛡️ Security & Reliability

- Sensitive API keys are stored exclusively in `.env` and never exposed to the frontend.
- `.env` and database files are excluded in `.gitignore`.
- All arithmetic operations are protected against division-by-zero, negative credits, and invalid grade bounds.
