# BizAI - Intelligent Business Management Platform

BizAI is a comprehensive business intelligence platform designed to empower merchants with AI-driven insights, automated inventory management, and multimodal marketing generation. It bridges the gap between raw data and actionable business strategies using a modern tech stack.

## 6.1 Key Features

### 6.1.1 The Onboarding Experience

The first interaction is designed to be seamless. We use **Supabase Auth** for secure and quick authentication, supporting both email/password and social logins.

- **Data Ingestion**: To solve the "Cold Start" problem, merchants can bulk upload their inventory via CSV.
- **Validation**: The system validates the uploaded file in real-time, ensuring data integrity before it enters the database.

### 6.1.2 The Dashboard Overview

The "Command Center" aggregates critical business data into a unified view.

- **Top Cards**: Real-time scalar values for "Total Revenue," "Low Stock Items," and "Active Alerts," fetched efficiently via GraphQL.
- **Weather Widget**: Integrated via **Open-Meteo API**, this widget provides local weather forecasts to help retailers plan for weather-dependent demand (e.g., stocking umbrellas for rain).
- **Sales Graph**: Visualizes historical sales data alongside AI-generated forecasts powered by the **PatchTST** transformer model.

### 6.1.3 The Natural Language Interface (AI Agent)

The core innovation is the "Ask AI" agentic interface.

- **Agentic Workflow**: Unlike simple chatbots, BizAI uses a **Llama 3.1 8B** model equipped with specific tools (`graphql_query`, `sales_query`, `predict_sales`).
- **Structured Responses**: The AI doesn't just chat; it returns structured data that the frontend renders as interactive **Tables**, **Charts**, or **Metric Cards**.
- **Context Aware**: The agent understands business context and can execute complex multi-step reasoning to answer questions like "How did we do last week compared to the weather?"
- **Generative AI**: Integrated with **Google Gemini 2.0 Flash** (for images) and **Veo** (for video).
- **One-Click Campaigns**: Merchants can generate high-quality promotional assets for specific products directly from the inventory view.
- **Customizable**: The AI adapts the content based on the product details and desired campaign tone.

## 6.2 Discussion of Implementation

### 6.2.1 Architecture & Technologies

The system is built as a set of Dockerized microservices:

- **Backend**: Django REST Framework + Graphene (GraphQL).
- **Frontend**: React + Vite + TailwindCSS.
- **AI/ML**:
  - **Ollama**: Hosting Llama 3.1 for the chat agent.
  - **Flask**: Serving the PatchTST prediction model.
  - **Google GenAI**: For external media generation.

### 6.2.2 What Worked Well?

- **GraphQL Efficiency**: Using GraphQL allowed us to fetch complex, nested data structures (like sales with related product info) in a single request, significantly reducing frontend complexity.
- **Agentic Approach**: Giving the LLM access to "Tools" proved more reliable than asking it to write SQL. It allows the AI to interact with our API safely and accurately.
- **PatchTST Reliability**: The transformer-based forecasting model showed resilience to noisy data, providing smooth trend lines even with imperfect inputs.

### 6.2.3 Challenges Faced

- **Docker Networking**: Connecting multiple containers (Django, Flask, Ollama) required a custom **Docker Bridge Network** (`app_network`) to allow internal DNS resolution while maintaining isolation.
- **GPU Resource Management**: Running local LLMs (Llama 3.1) alongside training jobs is resource-intensive. We configured Docker resource reservations to ensure the GPU is utilized efficiently without crashing the system.

## 6.3 Setup & Installation

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU (Recommended for local LLM inference)

### Running the Project

1. **Clone the repository**
2. **Create .env files** in `backend/bizai/` and `llm/project/` with necessary API keys (Supabase, Google Gemini).
3. **Build and Start**:
   ```bash
   docker-compose up --build
   ```
4. **Access the App**:
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`

## 6.4 Summary

BizAI successfully demonstrates how modern AI agents can be integrated into traditional business software. By combining deterministic logic (SQL/GraphQL) with probabilistic reasoning (LLMs/Transformers), the platform offers a robust solution for data-driven decision-making.
