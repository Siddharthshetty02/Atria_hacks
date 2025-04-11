import streamlit as st
import requests
import time
from streamlit_extras.stylable_container import stylable_container

# ===== APP CONFIGURATION =====
st.set_page_config(
    page_title="AI Learning Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== DARK THEME CSS =====
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #000000;
        color: #ffffff;
    }
    .st-emotion-cache-1y4p8pa {
        background-color: #111111;
    }
    .learning-card {
        background: #222222;
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 4px solid #6366f1;
        margin-bottom: 1rem;
        color: white;
    }
    h1, h2, h3, h4, h5, h6, p, div {
        color: white !important;
    }
    .stTextInput>div>div>input {
        color: white;
        background-color: #333333;
    }
    .stButton>button {
        background-color: #6366f1;
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# ===== CONSTANTS =====
BACKEND_URL = "http://localhost:5000"

# ===== SESSION STATE =====
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'learning_style' not in st.session_state:
    st.session_state.learning_style = None
if 'name' not in st.session_state:
    st.session_state.name = ""
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = []

# ===== QUIZ QUESTIONS =====
QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "When learning something new, you prefer to:",
        "options": [
            {"id": 1, "text": "👀 Watch videos", "style": "visual"},
            {"id": 2, "text": "🎧 Listen to explanations", "style": "auditory"},
            {"id": 3, "text": "📖 Read materials", "style": "reading"},
            {"id": 4, "text": "✋ Try hands-on", "style": "kinesthetic"}
        ]
    },
    {
        "id": 2,
        "question": "When trying to remember something, you:",
        "options": [
            {"id": 5, "text": "🖼️ Visualize it", "style": "visual"},
            {"id": 6, "text": "🗣️ Repeat it aloud", "style": "auditory"},
            {"id": 7, "text": "📝 Write it down", "style": "reading"},
            {"id": 8, "text": "👐 Act it out", "style": "kinesthetic"}
        ]
    }
]

# ===== API FUNCTIONS =====
def register_user(name, answers):
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/register",
            json={"name": name, "answers": answers},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def get_recommendations(user_id):
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/recommendations/{user_id}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("recommendations", [])
        return []
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return []

# ===== MAIN APP =====
def main():
    st.title("🧠 Personalized AI Learning Assistant")
    
    # Registration Flow
    if not st.session_state.user_id:
        st.header("Get Started")
        st.session_state.name = st.text_input("Your Name", key="name_input")
        
        st.subheader("Learning Style Assessment")
        st.write("Answer these questions to help us personalize your experience:")
        
        # Store answers in session state
        if len(st.session_state.quiz_answers) != len(QUIZ_QUESTIONS):
            st.session_state.quiz_answers = [None] * len(QUIZ_QUESTIONS)
        
        for i, question in enumerate(QUIZ_QUESTIONS):
            st.markdown(f"**{i+1}. {question['question']}**")
            option_texts = [opt["text"] for opt in question["options"]]
            selected = st.radio(
                "",
                option_texts,
                key=f"question_{i}",
                label_visibility="collapsed"
            )
            # Store selected option details
            selected_option = next(opt for opt in question["options"] if opt["text"] == selected)
            st.session_state.quiz_answers[i] = {
                "question_id": question["id"],
                "option_id": selected_option["id"],
                "style": selected_option["style"]
            }
        
        if st.button("Start Learning", type="primary"):
            if st.session_state.name:
                # Prepare answers for API
                api_answers = [
                    {"question_id": a["question_id"], "option_id": a["option_id"]}
                    for a in st.session_state.quiz_answers if a is not None
                ]
                
                result = register_user(st.session_state.name, api_answers)
                if result:
                    st.session_state.user_id = result.get("user_id")
                    st.session_state.learning_style = result.get("learning_style")
                    st.success(f"Welcome {st.session_state.name}!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Please enter your name")
    
    # Main Dashboard
    else:
        with st.sidebar:
            st.header("Your Profile")
            st.markdown(f"""
                👤 **Name:** {st.session_state.name}  
                🎯 **Learning Style:** {st.session_state.learning_style.capitalize()}
            """)
            
            if st.button("Reset Profile"):
                st.session_state.clear()
                st.rerun()
        
        # Recommendations Section
        st.header("📚 Recommended For You")
        recommendations = get_recommendations(st.session_state.user_id)
        
        if recommendations:
            for i, rec in enumerate(recommendations):
                with stylable_container(
                    key=f"card_{i}_{rec['id']}",
                    css_styles="""
                        {
                            background: #222222;
                            border-radius: 12px;
                            padding: 1.5rem;
                            margin: 1rem 0;
                        }
                    """
                ):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.subheader(rec["title"])
                        st.caption(f"Type: {rec['type'].capitalize()}")
                        st.markdown(f"[🔗 Open Resource]({rec['url']})")
                    with col2:
                        if st.button(
                            "✓ Completed", 
                            key=f"complete_{i}_{rec['id']}"
                        ):
                            # Add your completion logic here
                            st.success("Progress updated!")
                            time.sleep(1)
                            st.rerun()
        else:
            st.warning("No recommendations found")
        
        # AI Tutor Section
        st.header("🤖 AI Tutor")
        with st.expander("💡 Provide context (optional)"):
            context = st.text_area("Context (optional)", key="context_input", label_visibility="collapsed")

        
        question = st.text_input("Ask your question", key="question_input")
        
        if question:
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/ask_ai",
                        json={"question": question, "context": context},
                        timeout=10
                    )
                    if response.status_code == 200:
                        answer = response.json().get("answer", "No response")
                        st.markdown(f"""
                        <div style='background-color:#333333; padding:1rem; border-radius:10px;'>
                            <b>AI Response:</b><br>
                            {answer}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Something went wrong. Could not fetch AI response.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

                

# Run the app
if __name__ == "__main__":
    main()