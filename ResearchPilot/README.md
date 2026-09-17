# ResearchPilot

**ResearchPilot** is a Multi-Agent AI Research Accelerator designed to automate and streamline the research process.

## Project Overview

ResearchPilot uses an AI-driven multi-agent architecture to accept a research question, break it down into executable tasks, and (in future phases) execute literature search, hypothesis generation, and critique. 

This repository currently implements Phase 1, which includes:
- **Research Input**: A modern UI for inputting research questions and uploading reference files.
- **Supervisor Agent**: An AI agent that analyzes the input and generates a structured plan of tasks to accomplish the research goal.

## Architecture

The project is structured with a React + Vite frontend and a FastAPI (Python 3.12) backend. For detailed architecture documentation, see [architecture.md](./architecture.md).

## Folder Explanation

- `frontend/`: Contains the React + Vite web application.
- `backend/`: Contains the FastAPI backend, core logic, API routes, and Supervisor Agent.
  - `backend/app/agents/`: Where AI agents are implemented (Supervisor agent in Phase 1).
  - `backend/app/api/`: FastAPI route definitions.
  - `backend/app/schemas/`: Pydantic models for data validation.
  - `backend/app/services/`: Reusable services (Gemini API, file handling).
  - `backend/uploads/`: Temporary storage for uploaded research files.

## Installation & Setup

### Environment Setup

1. Copy the frontend `.env.example` to `.env`:
   ```bash
   cp frontend/.env.example frontend/.env
   ```
2. Copy the backend `.env.example` to `.env` and fill in your Gemini API key:
   ```bash
   cp backend/.env.example backend/.env
   ```

### Running the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Mac/Linux
   source .venv/bin/activate
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Running the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## Future Roadmap

Subsequent phases will introduce:
- **Literature Search Agent**: To find external papers and sources.
- **Hypothesis Generator**: To propose novel research directions based on input data.
- **Critic Agent**: To review findings and enforce scientific rigor.
- **Memory System**: A database (PostgreSQL/Vector DB) to store past knowledge.
