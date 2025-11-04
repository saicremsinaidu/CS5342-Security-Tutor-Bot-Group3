import os
import streamlit as st
from rag import make_answer, generate_quiz, grade_quiz
import subprocess

st.set_page_config(page_title="CS5342 Local Tutor", page_icon="🛡️", layout="wide")

st.title("🛡️ CS5342 Local Network-Security Tutor & Quiz (Offline)")

# -------- Sidebar controls --------
with st.sidebar:
    st.header("📂 Index Builder")
    st.write("Add your notes in `data/seeds/` (Markdown) or PDFs under `data/`.")
    if st.button("🔄 Build / Rebuild Index"):
        with st.spinner("Indexing your materials..."):
            result = subprocess.run(["python", "ingest.py"], capture_output=True, text=True)
            st.code(result.stdout + "\n" + result.stderr)
    st.divider()
    st.caption("All processing stays 100% on your machine (privacy-preserving).")

# -------- Tabs --------
tab1, tab2 = st.tabs(["💬 Tutor Agent", "📝 Quiz Agent"])

# ================= TUTOR AGENT =================
with tab1:
    st.subheader("Ask a Question (Tutor Agent)")
    query = st.text_input("Enter your network-security question:", 
                          placeholder="e.g., What is the purpose of a firewall?")
    k = st.slider("Number of reference sources to consider", 2, 8, 4)

    if st.button("Get Answer", type="primary"):
        if not query.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Searching your local knowledge base..."):
                answer, sources = make_answer(query, k=k)
            st.markdown("### 🧠 Answer")
            st.write(answer)
            if sources:
                with st.expander("📎 Sources used"):
                    for i, s in enumerate(sources, start=1):
                        st.write(f"[{i}] {s['source']}")

# ================= QUIZ AGENT =================
with tab2:
    st.subheader("Generate and Take a Quiz")
    c1, c2 = st.columns(2)
    with c1:
        topic = st.text_input("Topic (optional):",
                              placeholder="e.g., TLS, firewalls, IDS, VPN")
    with c2:
        n = st.slider("Number of questions", 3, 10, 5)

    if st.button("🎲 Generate Quiz"):
        with st.spinner("Generating quiz questions..."):
            st.session_state.quiz = generate_quiz(topic, n)
        st.success("Quiz generated successfully!")

    if "quiz" in st.session_state:
        quiz = st.session_state.quiz
        if not quiz["items"]:
            st.warning("No quiz questions available. Try rebuilding your index.")
        else:
            st.markdown(f"**Topic:** {quiz['topic'].title()}  | **Total Questions:** {len(quiz['items'])}")
            st.divider()

        answers = []
        all_answered = True

        for i, item in enumerate(quiz["items"], start=1):
            st.markdown(f"**Q{i}.** {item['q']}")

            if item["type"] == "tf":
                # radio with NO default (index=None) → user must choose
                resp = st.radio(
                    f"Answer {i}",
                    options=[True, False],
                    key=f"tf_{i}",
                    index=None
                )

            elif item["type"] == "mcq":
                # radio with NO default (index=None)
                resp = st.radio(
                    f"Select option {i}",
                    options=item["options"],
                    key=f"mcq_{i}",
                    index=None
                )

            else:  # open-ended
                text = st.text_area(f"Your response {i}", key=f"open_{i}", height=80)
                resp = text.strip() if text.strip() else None

            if resp is None:
                all_answered = False
            answers.append(resp)
            st.divider()

        # Disable Grade until every question has a response
        if st.button("✅ Grade Quiz", disabled=not all_answered):
            with st.spinner("Evaluating your responses..."):
                result = grade_quiz(quiz["items"], answers)
            st.success(f"**Your Score:** {result['score']} / {result['total']}")
            for d in result["details"]:
                icon = "✅" if d["correct"] else "❌"
                st.markdown(f"{icon} **Question:** {d['question']}")
                st.write(f"- **Your Answer:** {d['your_answer']}")
                st.write(f"- **Expected:** {d['expected']}")
                st.write(f"- **Reasoning:** {d['rationale']}")
                if d.get("sources"):
                    st.caption("Sources: " + ", ".join(d["sources"]))
                st.divider()

        if not all_answered:
            st.info("Please answer all questions before grading.")
