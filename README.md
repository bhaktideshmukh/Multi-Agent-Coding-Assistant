# 🤖 Multi-Agent Coding Assistant

An AI-powered software engineering team built with **LangGraph**, **Llama 3.3**, and **Streamlit**. 

This application takes a natural language request (e.g., "Build a calculator app") and uses a multi-agent system to plan the architecture, define the file structure, and write the code file-by-file.

## 🏗️ Architecture
- **Planner Agent:** Analyzes the prompt and creates a software engineering plan.
- **Architect Agent:** Converts the plan into a strict JSON file structure using Pydantic.
- **Coder Agent:** Loops through the architecture and writes the raw code for each file.

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/bhaktideshmukh/Multi-Agent-Coding-Assistant.git
cd Multi-Agent-Coding-Assistant
```

### 2. Set up the Environment
Create a virtual environment and install the dependencies:
```bash
python -m venv venv
# On Windows use: .\venv\Scripts\activate
# On Mac/Linux use: source venv/bin/activate

pip install -r requirements.txt
```

### 3. Add your API Key
Create a `.env` file in the root directory and add your free Groq API key:
```env
GROQ_API_KEY=your_api_key_here
```

### 4. Run the App
Launch the Streamlit interface:
```bash
streamlit run main.py
```