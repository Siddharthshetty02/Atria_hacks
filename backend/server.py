from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# DeepSeek API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
print("DeepSeek API Key:", DEEPSEEK_API_KEY)


# Initialize database
def init_db():
    conn = sqlite3.connect('learning.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  learning_style TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS progress
                 (user_id INTEGER,
                  topic TEXT,
                  score REAL)''')
    
    conn.commit()
    conn.close()

init_db()

# Quiz Questions Database
QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "When learning something new, you prefer to:",
        "options": [
            {"id": 1, "text": "Watch videos or diagrams", "style": "visual"},
            {"id": 2, "text": "Listen to explanations", "style": "auditory"},
            {"id": 3, "text": "Read textbooks/articles", "style": "reading"},
            {"id": 4, "text": "Try hands-on activities", "style": "kinesthetic"}
        ]
    },
    {
        "id": 2,
        "question": "When trying to remember something, you:",
        "options": [
            {"id": 5, "text": "Visualize it in your mind", "style": "visual"},
            {"id": 6, "text": "Repeat it out loud", "style": "auditory"},
            {"id": 7, "text": "Write it down", "style": "reading"},
            {"id": 8, "text": "Act it out physically", "style": "kinesthetic"}
        ]
    }
]

# Learning Resources Database
LEARNING_RESOURCES = {
    "visual": [
        {"id": 1, "type": "video", "title": "Python Visualization", "url": "https://example.com/python-visual"},
        {"id": 2, "type": "infographic", "title": "Data Structures", "url": "https://example.com/ds-infographic"}
    ],
    "auditory": [
        {"id": 3, "type": "podcast", "title": "Code Podcast", "url": "https://example.com/code-podcast"},
        {"id": 4, "type": "audiobook", "title": "Clean Code", "url": "https://example.com/clean-code-audio"}
    ],
    "reading": [
        {"id": 5, "type": "article", "title": "Python Basics", "url": "https://example.com/python-article"},
        {"id": 6, "type": "ebook", "title": "Learning Python", "url": "https://example.com/python-ebook"}
    ],
    "kinesthetic": [
        {"id": 7, "type": "interactive", "title": "Python Playground", "url": "https://example.com/python-play"},
        {"id": 8, "type": "exercise", "title": "Coding Challenges", "url": "https://example.com/python-challenges"}
    ]
}

# DeepSeek API Helper
def ask_deepseek(question, context=""):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": "You are a helpful AI tutor. Explain concepts clearly and simply."}
    ]
    
    if context:
        messages.append({"role": "user", "content": context})
    
    messages.append({"role": "user", "content": question})
    
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"DeepSeek API Error: {str(e)}")
        return None

# API Endpoints
@app.route('/api/quiz', methods=['GET'])
def get_quiz():
    return jsonify({"questions": QUIZ_QUESTIONS})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    answers = data.get('answers', [])
    
    # Calculate learning style
    style_counts = {}
    for answer in answers:
        q_id = answer['question_id']
        option_id = answer['option_id']
        question = next(q for q in QUIZ_QUESTIONS if q['id'] == q_id)
        option = next(o for o in question['options'] if o['id'] == option_id)
        style = option['style']
        style_counts[style] = style_counts.get(style, 0) + 1
    
    learning_style = max(style_counts, key=style_counts.get)
    
    # Save to database
    conn = sqlite3.connect('learning.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (name, learning_style) VALUES (?, ?)", 
              (name, learning_style))
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        "user_id": user_id,
        "learning_style": learning_style
    })

@app.route('/api/recommendations/<int:user_id>', methods=['GET'])
def recommendations(user_id):
    conn = sqlite3.connect('learning.db')
    c = conn.cursor()
    c.execute("SELECT learning_style FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"error": "User not found"}), 404
    
    learning_style = result[0]
    return jsonify({
        "recommendations": LEARNING_RESOURCES.get(learning_style, [])
    })

@app.route('/api/ask_ai', methods=['POST'])
def ask_ai():
    data = request.json
    question = data.get('question')
    context = data.get('context', '')
    
    answer = ask_deepseek(question, context)
    if answer:
        return jsonify({"answer": answer})
    else:
        return jsonify({"error": "Failed to get AI response"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)