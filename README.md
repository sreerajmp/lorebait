# Lorebait

Lorebait is a local RAG (Retrieval-Augmented Generation) tool designed to transform your personal notes, research papers, and documents into an interactive learning experience. It empowers learners to dive deep into their material, ask complex questions, and verify their understanding through a conversational interface.

Instead of passively reading, you can actively engage with your knowledge base. Use Lorebait to get clear explanations, synthesize information from multiple sources, or even have the AI quiz you on the content. It's like having a personal tutor, researcher, and study partner who has read all your files.

## Features

*   **Index Local Folders:** Point Lorebait to a directory on your machine, and it will create a searchable knowledge base from your `.pdf`, `.md`, and `.txt` files.
*   **Persona-Driven Chat:** Interact with your documents through different AI personas:
    *   **Tutor:** Get patient explanations and a quiz question to test your comprehension.
    *   **Researcher:** Receive concise summaries with inline citations from your files.
    *   **Learner:** Engage in an active learning dialogue with probing questions.
*   **100% Local:** Your data and the AI models run entirely on your machine via Ollama, ensuring privacy and offline access.
*   **Simple Web UI:** A clean, straightforward interface for managing your indexed folder and chatting with the AI.

## Prerequisites

Before you begin, ensure you have the following installed:

*   Python (3.10+ recommended)
*   Node.js (includes npm)
*   Ollama

After installing Ollama, you need to pull the models used by the application. By default, these are `llama3:8b` and `nomic-embed-text`.

```bash
ollama pull llama3:8b
ollama pull nomic-embed-text
```

> **Note:** The exact model names are configured in your `.env` file (you can copy `.env.example` to create it). Check the `OLLAMA_MODEL` and `OLLAMA_EMBEDDING_MODEL` variables if you wish to use different ones.

## Running the Application

Lorebait requires two separate processes: the Python backend and the React frontend. You will need two terminal windows open in the root `lorebait` directory.

### 1. Start the AI "Brain" (Ollama)

First, make sure the Ollama application is running in the background.

*   On Windows, look for the Ollama icon in your System Tray.
*   On macOS, look for it in the menu bar.
*   If it's not running, start it from your applications.
*   **Verify:** Open a terminal and run `ollama list`. You should see the models you pulled earlier (e.g., `llama3:8b` and `nomic-embed-text`).

### 2. Launch the Backend (FastAPI)

In your **first** terminal, set up and run the backend server.

1.  **Create and activate a virtual environment:**
    ```bash
    # Create the environment (only needs to be done once)
    python -m venv venv

    # Activate it (do this every time you open a new terminal)
    # On Windows (PowerShell):
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the server:**
    ```bash
    uvicorn main:app --reload --port 8000
    ```
    *You should see a message like "Uvicorn running on http://127.0.0.1:8000". Leave this terminal window open.*

### 3. Launch the Frontend (React/Vite)

In your **second** terminal, run the frontend development server.

1.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

2.  **Start the Vite dev server:**
    ```bash
    npm run dev
    ```
    *This will start the frontend and provide a local URL, usually `http://localhost:5173`. Open this URL in your web browser to use Lorebait.*

## How to Use Lorebait

1.  **Enter a Folder Path:** In the "Active Folder" input on the left sidebar, enter the full path to the directory containing the documents you want to study.
2.  **Index the Folder:** Click the "Index Folder" button. Lorebait will scan, chunk, and embed your documents. You can monitor the progress in the "Indexing Status" card.
3.  **Choose a Persona:** Select a persona (Tutor, Researcher, or Learner) that best fits your learning goal.
4.  **Start Chatting:** Once indexing is complete, start asking questions! Your conversation will be grounded in the content of your indexed files.