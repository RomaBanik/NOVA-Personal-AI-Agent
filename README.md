# 🤖 NOVA – Personal AI Agent

NOVA is an AI-powered personal assistant built with Python and Google's Gemini API. It helps users generate Python projects, execute them in a Docker environment, interact with running programs, and detect programming errors.

## ✨ Features

- **AI Chat Assistant:** Interact with NOVA using Gemini AI.
- **Project Generation:** Generate Python projects using natural language prompts.
- **Project Execution:** Run generated projects inside Docker containers.
- **Interactive Terminal:** Send input to running projects and view their output.
- **Error Detection:** Detect and display Python errors.
- **Error Explanation:** Get AI-powered explanations of detected errors.

## 🛠️ Technologies Used

- Python
- Streamlit
- Google Gemini API
- Docker
- Python Subprocess
- HTML and CSS (Streamlit UI styling)

## 📁 Project Structure

```text
NOVA-Personal-AI-Agent/
│
├── main.py
├── project_builder.py
├── project_runner.py
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/RomaBanik/NOVA-Personal-AI-Agent.git
```

### 2. Open the project folder

```bash
cd NOVA-Personal-AI-Agent
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment

Windows PowerShell:

```bash
.\venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure your Gemini API key

Create a `.env` file in the project directory:

```env
GEMINI_API_KEY=your_api_key_here
```

Never share your API key publicly.

### 7. Start Docker Desktop

Make sure Docker Desktop is installed and running.

### 8. Run NOVA

```bash
streamlit run main.py
```

## 🚀 Project Status

NOVA is an ongoing personal AI agent project and currently a working prototype. Some interactive execution features may require further improvements.

## 👩‍💻 Developer

**Roma Banik**

BCA Student | Python | AI | Project Development

