# CS5342 - Network Security Tutor & Quiz Bot

> This project is a privacy-preserving intelligent tutor and quiz bot developed for the CS5342 Network Security course (Fall 2025). It is designed to run entirely on a local machine, ensuring no user data is sent to external servers.

---

## 🚀 Key Features

* **Intelligent Tutoring**: Answers course-related questions with citations from lecture materials.
* **Quiz Generation**: Creates custom quizzes with Multiple Choice, True/False, and Open-ended questions.
* **Automated Grading**: Grades user responses and provides instant, constructive feedback.
* **100% Local**: Ensures all data and interactions remain on the user's local machine for maximum privacy.

---

## ⚙️ Required Environment

| Component | Recommended Version |
|------------|----------------------|
| **OS** | Windows 10 / Ubuntu 20+ / macOS |
| **Python** | 3.9 – 3.11 |
| **RAM** | 8 GB minimum (16 GB recommended) |
| **Storage** | ≥ 5 GB free |
| **Libraries** | See `requirements.txt` |
| **GPU (Optional)** | CUDA-compatible GPU for faster embedding inference |

---

## 🧰 Adopted Libraries

| Library | Purpose |
|----------|----------|
| `streamlit` | User interface for the tutor and quiz system |
| `sentence-transformers` | Generates embeddings from course material |
| `chromadb` | Stores and retrieves embeddings for context search |
| `pypdf` | Extracts text from PDF lecture slides |
| `numpy`, `scikit-learn` | Preprocessing, similarity scoring, and calculations |
| `os`, `json`, `random` | File handling and quiz generation logic |

All dependencies are listed in `requirements.txt`.

---

## 🔄 Flow of Execution

The system must be executed in the following order:

1. **Clone the Repository**  
   Download the complete project source code from GitHub.

2. **Create and Activate a Virtual Environment**  
   This isolates all Python dependencies for the project.

3. **Install Required Dependencies**  
   Install all libraries listed in `requirements.txt` including Streamlit, ChromaDB, Sentence-Transformers, and others.

4. **Run `ingest.py` (Data Ingestion Step)**  
   - Extracts text from the provided Network Security lecture PDFs.  
   - Splits the data into 500-word chunks.  
   - Generates embeddings using Sentence-Transformers.  
   - Stores the embeddings locally in a ChromaDB persistent directory.  
   - This step must be run **once before launching the app** so that the knowledge base is available.

5. **Run `app.py` Using Streamlit (Main Application Step)**  
   - Starts the user interface for both the **Tutor Agent** and the **Quiz Agent**.  
   - Loads the saved embeddings and interacts with them locally for Q&A and quiz generation.

6. **Interact With the App**  
   - Use Tutor Mode to ask any course-related questions.  
   - Use Quiz Mode to generate and answer quizzes.  
   - View feedback, grading, and citations—all executed locally.

---

## 🧪 Commands to Run the Code

```bash
# 1. Clone this repository
git clone https://github.com/<groupname>/<repo>.git
cd <repo>

# 2. Create a virtual environment
python -m venv venv
# Activate environment
# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run data ingestion script
python ingest.py

# 5. Launch the application
streamlit run app.py
```

Once started, open **http://localhost:8501** in your browser to use the Tutor & Quiz Bot interface.

---

## 🧩 Issues Encountered and Solutions

| Issue | Solution |
|--------|-----------|
| **Streamlit crashing when generating long responses** | Used session caching and limited model response length to 500 tokens. |
| **ChromaDB not persisting embeddings** | Initialized persistent directory (`persist_directory='./chroma_db'`). |
| **PDF parsing skipped some encrypted slides** | Added `strict=False` flag in PyPDF text extraction. |
| **Quiz results not updating properly** | Used Streamlit session state to persist scores. |
| **Slow embedding generation** | Batched embeddings and saved them to disk incrementally. |

---

## 💡 Suggestions and Feedback

**Suggestions**
- Integrate **GPU inference** for faster responses.  
- Add **user progress tracking** and analytics dashboard.  
- Extend quiz question types with **fill-in-the-blank** and **scenario-based** problems.  
- Implement **text-to-speech feedback** for accessibility.

**Team Feedback**
- The project strengthened our understanding of **Retrieval-Augmented Generation (RAG)** systems.  
- Learned how to fine-tune open-source embeddings and vector databases for privacy-preserving LLMs.  
- Facing challenges with Streamlit state management helped us improve debugging and modular coding practices.

---

## 📚 References

1. *How to Build a Chatbot Based on Your Own Documents* – Analytics Vidhya (2024)  
2. *Create a Private ChatGPT That Interacts With Your Local Documents* – TechTalks (2025)  
3. *LangChain and ChromaDB for Local RAG Pipelines* – Medium (2025)  
4. *Sentence Transformers Documentation* – UKP Lab (2024)

---

## 👥 Team Members

* Naveen Sai Cremsi Yadlapalli  
* Sameera Shaik  
* Tanmayi Allu  
* Sai Eswar Gude  
* Sai Sanjay Chitteni  
* Rupesh Sai Narendra Kalyanam  
* Yugandhar Narravula  
* Swetha Uma Shankar

---
