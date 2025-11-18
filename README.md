# 📘 CS5342 — Network Security Project  
## **Round-2 Prototype Submission — README**

### **Local Network-Security Tutor & Quiz Agent (Privacy-Preserving)**

This project implements a **local, privacy-preserving intelligent tutor & quiz generator** that interacts with CS5342 network-security documents stored entirely on your local machine. The system uses:

- **Qdrant Vector Database (Docker)**
- **Sentence Transformers**
- **GPT4All (offline LLM)**
- **Gradio UI**
- **Local knowledge base (PDF slides, textbook pages, quizzes)**

This README is written according to **Round-2 requirements**.

---

# 🖥️ 1. System Environment

### **OS Support**
- macOS  
- Windows  
- Linux  

### **Python Version**
Python 3.9+ recommended

### **Hardware Requirements**
- Minimum 8GB RAM  
- CPU-only supported  

---

# 📦 2. Adopted Libraries

| Library | Purpose |
|--------|---------|
| sentence-transformers | Embedding model |
| qdrant-client | Vector DB connection |
| gradio | Web UI |
| gpt4all | Offline LLM |
| pymupdf | PDF → text |
| fuzzywuzzy | Similarity scoring |
| python-Levenshtein | Fast fuzzy matching |

Install:
```
pip install fuzzywuzzy python-Levenshtein sentence-transformers qdrant-client gradio gpt4all pymupdf
```

---

# 🐳 3. Qdrant Setup

```
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

---

# 🔧 4. Virtual Environment

### macOS/Linux
```
python3 -m venv venv
source venv/bin/activate
```

### Windows
```
python -m venv venv
venv\Scripts\activate
```

If PowerShell error:
```
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

# 📂 5. Project Structure

```
project/
│── Scripts/
│   ├── initialise_qdrant.py
│   ├── Data_insertion_qdrant.py
│   ├── chatbot_application.py
│── knowledge_base/
│── README.md
│── venv/
```

---

# 🔄 6. Execution Flow

### **1. Initialize DB**
```
python Scripts/initialise_qdrant.py
```

### **2. Add PDFs**
Place into:
```
knowledge_base/
```

### **3. Insert Into Vector DB**
```
python Scripts/Data_insertion_qdrant.py
```

### **4. Start Chatbot**
```
python Scripts/chatbot_application.py
```

Access:
```
http://127.0.0.1:7860
```

---

# 🤖 7. Features

### Tutor Agent
- Answers questions  
- Includes citations  
- Uses local data first  

### Quiz Agent
- MCQ  
- True/False  
- Open-ended  
- Random OR topic-based  
- Auto-grading with feedback  

---

# 🛑 8. Issues & Solutions

### Issue: Qdrant not running  
Fix: restart Docker container.  

### Issue: PDF extraction fails  
Fix:
```
pip install pymupdf
```

### Issue: Windows venv error  
Fix:
```
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

# 💡 9. Suggestions & Feedback

- Add API/Wireshark trace capture for bonus  
- Add system security filters  
- UI improvements  
- Add GPU model for faster LLM  

---

# 🧱 10. Architecture Diagram

User → Gradio UI → Embedding Model → Qdrant → GPT4All → Response

---

# 📜 11. Commands Summary

```
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant

python -m venv venv
source venv/bin/activate
venv\Scripts\activate

pip install fuzzywuzzy python-Levenshtein sentence-transformers qdrant-client gradio gpt4all pymupdf

python Scripts/initialise_qdrant.py
python Scripts/Data_insertion_qdrant.py
python Scripts/chatbot_application.py
```

---

# 🧾 12. References
- TechTalks — How to create a private ChatGPT  
- CommandBar Blog — LangChain  
- Microsoft Azure + ChromaDB guide  

---

