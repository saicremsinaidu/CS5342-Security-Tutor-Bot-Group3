# for building the web application interface
import gradio as gr
from sentence_transformers import SentenceTransformer, util
from qdrant_client import QdrantClient
from gpt4all import GPT4All
import requests, logging, random, re
from functools import lru_cache
from fuzzywuzzy import fuzz

logging.basicConfig(filename='query_logs.txt', level=logging.INFO)

#converts the text into numerical vectors for search
embedder = SentenceTransformer("all-MiniLM-L12-v2")

# connects to the local Qdrant database to store and retrieve document vectors
qdrant_client = QdrantClient(host="localhost", port=6333)

# Loads the GPT4All model locally for generating responses
gpt4all_model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# SerpAPI key for web searches
SERPAPI_API_KEY = "7fa7214ef761e09c624ba83150a6881f0238327672d3fe4023bc65610c566cc8"

# Qdrant collection name
collection_name = "network_security_knowledge"

@lru_cache(maxsize=100)
def cached_generate_response(prompt, mode):
    # Implements Least Recently Used (LRU) caching for the last 100 queries to improve speed and reduce LLM load.
    return generate_response(prompt, mode)


# This function takes the user's Prompt and converts into an embedding and queries the Qdrant database for similar documents
# This uses fuzz.partial_ratio to filter results based on text similarity to ensure relevance

def find_relevant_document(prompt):
    emb = embedder.encode([prompt])[0]
    results = qdrant_client.query_points(
        collection_name=collection_name,
        query=emb.tolist(),
        limit=10
    ).points
    matches = []
    for hit in results:
        payload = hit.payload
        score = fuzz.partial_ratio(prompt.lower(), payload["text"].lower())
        if score > 60:
            matches.append(payload)
    return matches


# web_search function uses SerpAPI to perform online searches when no relevant documents are found in the local database.
def web_search(query):
    # --------------------------
    # Validate API Key
    # --------------------------
    if not SERPAPI_API_KEY or SERPAPI_API_KEY == "YOUR_KEY":
        return (
            "⚠️ ERROR: SERPAPI_API_KEY is missing or invalid.\n"
            "Please set a valid API key.\n"
            
            ""
        )

    try:
        # --------------------------
        # Perform SerpAPI Search
        # --------------------------
        r = requests.get(
            "https://serpapi.com/search",
            params={"q": query, "api_key": SERPAPI_API_KEY," engine": "google" ,"num": 3}
        )

        # --------------------------
        # HTTP-Level Errors
        # --------------------------
        if r.status_code == 401:
            return ("⚠️ ERROR: Unauthorized (401). API key is wrong or expired.", "")
        if r.status_code == 403:
            return ("⚠️ ERROR: Forbidden (403). API key may be invalid or blocked.", "")
        if r.status_code == 429:
            return ("⚠️ ERROR: Rate limit exceeded (429). Free quota is used up.", "")
        if r.status_code != 200:
            return (f"⚠️ ERROR: HTTP {r.status_code}. Unable to fetch online results.", "")

        # --------------------------
        # Parse JSON Results
        # --------------------------
        data = r.json().get("organic_results", [])

        if not data:
            return ("⚠️ No results found for this query online.", "")

        # --------------------------
        # Extract snippets
        # --------------------------
        snippet = data[0].get("snippet", "⚠️ No snippet available.")
        urls = "\n".join([
            f"{d.get('title', 'No title')} – {d.get('link', '')}"
            for d in data
        ])

        return snippet, urls

    except Exception as e:
        # --------------------------
        # Catch Network / Parsing Errors
        # --------------------------
        return (f"⚠️ ERROR: Online search failed.\nDetails: {str(e)}", "")
    

# if the find_relevant_document function returns results, this function constructs a prompt with the relevant document texts and generates a response using the GPT4All model.
# If no relevant documents are found, it falls back to performing a web search and uses the snippet from that search to generate a response.
def generate_response(prompt, mode):
    docs = find_relevant_document(prompt)
    
    if docs:
        ctx = f"Answer the following question '{prompt}'\n\n from the below Context:\n"
        
        for d in docs:
            ctx += d["text"] + "\n\n"
        out = gpt4all_model.generate(ctx, max_tokens=500).strip()
        if mode == "Concise":
            out = out.split("\n")[0]
        src = "\n".join([f"{d['document']}, Page {d['page_number']}" for d in docs])
        return out, src
    snippet, src = web_search(prompt)
    return snippet, src


# Parses the raw output from GPT4All to extract different question types
def parse_mcq(block, source):
    q = re.search(r"QUESTION:\s*(.+)", block)
    A = re.search(r"A\)\s*(.+)", block)
    B = re.search(r"B\)\s*(.+)", block)
    C = re.search(r"C\)\s*(.+)", block)
    D = re.search(r"D\)\s*(.+)", block)
    correct = re.search(r"CORRECT:\s*([A-D])", block)

    if not (q and A and B and C and D and correct):
        return None

    opts = [A.group(1).strip(), B.group(1).strip(),
            C.group(1).strip(), D.group(1).strip()]
    correct_opt = opts["ABCD".index(correct.group(1).strip())]

    return {
        "type": "MCQ",
        "question": q.group(1).strip(),
        "options": opts,
        "answer": correct_opt,
        "source": source
    }

# Parses True/False questions from the GPT4All output
def parse_tf(block, source):
    q = re.search(r"QUESTION:\s*(.+)", block)
    correct = re.search(r"CORRECT:\s*(True|False)", block, re.I)

    if not (q and correct):
        return None

    return {
        "type": "TF",
        "question": q.group(1).strip(),
        "options": ["True", "False"],
        "answer": correct.group(1).capitalize(),
        "source": source
    }

# Parses Open-ended questions from the GPT4All output
def parse_open(block, source):
    q = re.search(r"QUESTION:\s*(.+)", block)
    ans = re.search(r"EXPECTED_ANSWER:\s*(.+)", block)

    if not (q and ans):
        return None

    return {
        "type": "OPEN",
        "question": q.group(1).strip(),
        "answer": ans.group(1).strip(),
        "source": source
    }

# List of topics for quiz generation
SLIDE_TOPICS = [
    "CIA Triad", "Security Attacks", "Symmetric Encryption",
    "Public Key Cryptography", "Hashing", "MAC", "AES", "DES",
    "Kerberos", "Diffie-Hellman", "Digital Signatures", "PKI"
]



# if mode is "Random Quiz", a random topic from SLIDE_TOPICS is selected.
# if mode is "Topic-Specific Quiz", the provided topic is used.
def generate_quiz(topic, mode):
    if mode == "Random Quiz":
        topic = random.choice(SLIDE_TOPICS)
    
    if mode == "Topic-Specific Quiz" and not topic.strip():
        topic = random.choice(SLIDE_TOPICS)
    

    docs = find_relevant_document(topic)

    if docs:
        context = "\n\n".join([d["text"] for d in docs[:3]])
        source = f"{docs[0]['document']}, Page {docs[0]['page_number']}"
    else:
        snippet, _ = web_search(topic)
        context = snippet
        source = "Internet Search"

    # STRICT MCQ generation prompt
    prompt = f"""
Generate EXACTLY 5 quiz questions about {topic}.
DO NOT SKIP ANY QUESTION
FORMAT:
MCQ1:
QUESTION: <text>
A) <text>
B) <text>
C) <text>
D) <text>
CORRECT: <A/B/C/D>

MCQ2:
QUESTION: <text>
A) <text>
B) <text>
C) <text>
D) <text>
CORRECT: <A/B/C/D>

TF1:
QUESTION: <text>
CORRECT: True/False

TF2:
QUESTION: <text>
CORRECT: True/False

OPEN:
QUESTION: <text>
EXPECTED_ANSWER: <short>

RULES:
- No repeated options
- No extra explanations
- Each option must be on a new line
- Follow format exactly
CONTENT:
{context}
"""

    raw = gpt4all_model.generate(prompt, max_tokens=800)

    mcq_blocks = re.findall(r"MCQ\d+:(.+?)(?=MCQ|TF|OPEN|$)", raw, re.DOTALL)
    tf_blocks = re.findall(r"TF\d+:(.+?)(?=MCQ|TF|OPEN|$)", raw, re.DOTALL)
    open_block = re.search(r"OPEN:(.+)$", raw, re.DOTALL)

    quiz = []

    for blk in mcq_blocks[:2]:
        q = parse_mcq(blk, source)
        if q: quiz.append(q)

    for blk in tf_blocks[:2]:
        q = parse_tf(blk, source)
        if q: quiz.append(q)

    if open_block:
        q = parse_open(open_block.group(1), source)
        if q: quiz.append(q)

    # FORCE OPEN QUESTION LAST
    quiz = sorted(quiz, key=lambda x: x["type"] == "OPEN")

    return quiz[:5]


"""
 Grades the quiz based on user answers and the generated quiz
 Provides feedback and a grade
 for MCQ and TF questions, it checks for exact matches
 for OPEN questions, it uses semantic similarity to grade
 Similarity > 0.65 = Full point (Correct)
 Similarity > 0.40 = Half point (Partial) 
 Similarity <=0.40 = Zero points (Wrong)
"""
def grade_quiz(user_answers, quiz):
    score = 0
    details = ""

    for i, (ua, q) in enumerate(zip(user_answers, quiz)):
        if ua in [None, "", []]:
            details += f"Q{i+1}: ✗ Not answered -Correct: {q['answer']}\n"
            continue
        if q["type"] in ["MCQ", "TF"]:
            if ua == q["answer"]:
                score += 1
                details += f"Q{i+1}: ✓ Correct\n"
            else:
                details += f"Q{i+1}: ✗ Wrong — Correct: {q['answer']}\n"
        else:
            emb1 = embedder.encode([ua], convert_to_tensor=True)
            emb2 = embedder.encode([q["answer"]], convert_to_tensor=True)
            sim = float(util.pytorch_cos_sim(emb1, emb2))

            if sim > 0.65:
                score += 1
                details += f"Q{i+1}: ✓ Correct (Sim={sim:.2f})\n"
            elif sim > 0.40:
                score += 0.5
                details += f"Q{i+1}: ◐ Partial (Sim={sim:.2f})\n"
            else:
                details += f"Q{i+1}: ✗ Wrong (Sim={sim:.2f})\n"

    return score, details


# Renders the quiz UI dynamically based on the generated quiz
def render_quiz(mode, topic):
    quiz = generate_quiz(topic, mode)

    # FIXED LAYOUT - Always handle all 5 slots
    q_updates, a_updates, s_updates = [], [], []

    for i in range(5):  # Always loop 5 times
        if i < len(quiz):  # If we have a question for this slot
            q = quiz[i]
            q_updates.append(gr.update(value=f"**Q{i+1} ({q['type']})**\n{q['question']}", visible=True))

            if q["type"] == "OPEN":
                a_updates.append(gr.update(value="", visible=True))
            else:
                a_updates.append(gr.update(value=None, choices=q["options"], visible=True))

            s_updates.append(gr.update(value=f"_Source: {q['source']}_", visible=True))
        else:  # No question for this slot - hide it
            q_updates.append(gr.update(value="", visible=False))
            a_updates.append(gr.update(visible=False))
            s_updates.append(gr.update(value="", visible=False))

    return (
        quiz,
        gr.update(value="✅ Quiz generated successfully!", visible=True),
        *q_updates, *a_updates, *s_updates
    )




#############################################
###############  UI SETUP  ##################
#############################################

with gr.Blocks(title="NS Tutor & Quiz Agent") as app:

    with gr.Tabs():

        with gr.Tab("Tutor"):
            gr.Markdown("## 📘 Tutor Agent")
            t_in = gr.Textbox(lines=4, label="Your Question")
            t_mode = gr.Dropdown(["Concise", "Detailed"], value="Detailed")
            t_out = gr.Textbox(lines=10)
            t_src = gr.Textbox(lines=5)
            gr.Button("Ask").click(
                lambda p, m: cached_generate_response(p, m),
                [t_in, t_mode],
                [t_out, t_src]
            )

        with gr.Tab("Quiz"):
            gr.Markdown("## 📝 Dynamic Quiz")

            quiz_mode = gr.Radio(["Random Quiz", "Topic-Specific Quiz"], value="Random Quiz")
            topic_input = gr.Textbox(label="Topic (optional)")
            loading_msg = gr.Markdown("Click Generate to begin")
            generate_btn = gr.Button("Generate Quiz")

            quiz_state = gr.State()

            q1 = gr.Markdown(visible=False); a1 = gr.Radio([], visible=False); s1 = gr.Markdown(visible=False)
            q2 = gr.Markdown(visible=False); a2 = gr.Radio([], visible=False); s2 = gr.Markdown(visible=False)
            q3 = gr.Markdown(visible=False); a3 = gr.Radio([], visible=False); s3 = gr.Markdown(visible=False)
            q4 = gr.Markdown(visible=False); a4 = gr.Radio([], visible=False); s4 = gr.Markdown(visible=False)
            q5 = gr.Markdown(visible=False); a5 = gr.Textbox(lines=3, visible=False); s5 = gr.Markdown(visible=False)

            generate_btn.click(
                lambda: gr.update(value="Generating...", visible=True),
                None,
                loading_msg
            ).then(
                render_quiz,
                [quiz_mode, topic_input],
                [quiz_state, loading_msg,
                 q1, q2, q3, q4, q5,
                 a1, a2, a3, a4, a5,
                 s1, s2, s3, s4, s5]
            )

            score_out = gr.Textbox(label="Score")
            details_out = gr.Textbox(lines=10, label="Details")
            grade_btn = gr.Button("Grade Quiz")

            def grade_ui(quiz, a1, a2, a3, a4, a5):
                answers = [a1, a2, a3, a4, a5]
                score, detail = grade_quiz(answers, quiz)
                return f"{score}/5", detail

            grade_btn.click(
                grade_ui,
                [quiz_state, a1, a2, a3, a4, a5],
                [score_out, details_out]
            )

app.launch()


