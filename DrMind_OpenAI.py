import os
import json
import random
from datetime import datetime
from flask import Flask, request, render_template_string, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from textblob import TextBlob
import google.generativeai as genai
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dr_mind_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drmind.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configure Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDytxYnj_oBOLJrrRJ__-By6gYYfRhYj8o")
genai.configure(api_key=GOOGLE_API_KEY)

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood = db.Column(db.String(50), nullable=False)
    journal = db.Column(db.String(1000))
    sentiment = db.Column(db.Float)
    comfort_message = db.Column(db.String(500))
    suggestions = db.Column(db.String(1000))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Comprehensive mood options
MOODS = [
    {"emoji": "😃", "label": "Joyful", "value": 0.9},
    {"emoji": "😊", "label": "Content", "value": 0.7},
    {"emoji": "😌", "label": "Peaceful", "value": 0.6},
    {"emoji": "😇", "label": "Grateful", "value": 0.8},
    {"emoji": "🤗", "label": "Loved", "value": 0.8},
    {"emoji": "🥳", "label": "Excited", "value": 0.9},
    {"emoji": "😎", "label": "Confident", "value": 0.7},
    {"emoji": "😋", "label": "Satisfied", "value": 0.6},
    {"emoji": "😤", "label": "Determined", "value": 0.5},
    {"emoji": "😐", "label": "Neutral", "value": 0.0},
    {"emoji": "😕", "label": "Confused", "value": -0.2},
    {"emoji": "😟", "label": "Worried", "value": -0.4},
    {"emoji": "😢", "label": "Sad", "value": -0.6},
    {"emoji": "😞", "label": "Down", "value": -0.7},
    {"emoji": "😩", "label": "Exhausted", "value": -0.5},
    {"emoji": "😡", "label": "Angry", "value": -0.8},
    {"emoji": "😱", "label": "Anxious", "value": -0.6},
    {"emoji": "😖", "label": "Stressed", "value": -0.5},
    {"emoji": "😰", "label": "Overwhelmed", "value": -0.7},
    {"emoji": "😭", "label": "Devastated", "value": -0.9}
]

# Motivational quotes
QUOTES = [
    "Every day may not be good, but there is something good in every day.",
    "You are stronger than you think.",
    "Progress, not perfection.",
    "Small steps every day lead to big changes.",
    "You have overcome challenges before, you can do it again.",
    "Your feelings are valid. Take it one day at a time.",
    "Celebrate your wins, no matter how small.",
    "You are not alone. Reach out if you need support.",
    "Rest is productive, too.",
    "Be gentle with yourself.",
    "The only way to do great work is to love what you do.",
    "Believe you can and you're halfway there.",
    "It's okay to not be okay.",
    "Your mental health is a priority.",
    "You are worthy of love and respect."
]

def get_cohere_ai_response(mood, journal, sentiment):
    """Get AI response using Cohere API (FREE tier - 5 requests/minute)"""
    try:
        # Cohere API - free tier with 5 requests per minute
        API_URL = "https://api.cohere.ai/v1/generate"
        
        # Create a context-aware prompt
        context = f"User is feeling {mood.lower()} and wrote: '{journal}'. Sentiment score: {sentiment:.2f}. "
        
        if sentiment < -0.3:
            context += "User seems to be struggling. Provide comfort and practical suggestions."
        elif sentiment > 0.3:
            context += "User is in a positive mood. Provide encouragement and suggestions to maintain this energy."
        else:
            context += "User is in a neutral state. Provide gentle support and suggestions."
        
        # Add specific context detection
        journal_lower = journal.lower()
        if any(word in journal_lower for word in ['study', 'exam', 'test', 'homework', 'assignment', 'class', 'school', 'college', 'university', 'learn', 'education']):
            context += " User is dealing with academic stress. Provide study-specific advice."
        elif any(word in journal_lower for word in ['work', 'job', 'project', 'deadline', 'meeting', 'boss', 'colleague', 'career', 'business', 'build', 'app', 'code', 'programming', 'development']):
            context += " User is dealing with work/project stress. Provide work-specific advice."
        elif any(word in journal_lower for word in ['friend', 'family', 'partner', 'relationship', 'love', 'breakup', 'argument', 'people', 'social']):
            context += " User is dealing with relationship issues. Provide relationship-specific advice."
        
        prompt = f"Dr. Mind: I'm here to help. {context} Please provide a warm, empathetic response with practical suggestions."
        
        headers = {
            "Authorization": "Bearer COHERE_API_KEY",  # You can get a free API key from cohere.ai
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "command",
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": 0.7,
            "k": 0,
            "stop_sequences": [],
            "return_likelihoods": "NONE"
        }
        
        response = requests.post(API_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('generations', [{}])[0].get('text', '')
            
            # Parse the response
            lines = ai_response.split('\n')
            comfort = ""
            suggestions = []
            
            for line in lines:
                if 'comfort' in line.lower() or 'feel' in line.lower():
                    comfort = line.strip()
                elif line.strip().startswith('-') or line.strip().startswith('•'):
                    suggestions.append(line.strip().lstrip('- ').lstrip('• '))
            
            # If parsing fails, create a structured response
            if not comfort:
                comfort = f"I understand you're feeling {mood.lower()}. Your feelings are valid and important."
            
            if not suggestions:
                suggestions = [
                    "Take a moment to breathe deeply and center yourself",
                    "Write down your thoughts to help process them",
                    "Reach out to someone you trust for support"
                ]
            
            return {
                'comfort': comfort,
                'suggestions': suggestions[:3]
            }
        
        # Fallback if API fails
        print("🤖 Cohere API failed, using fallback system...")
        return get_fallback_response(mood, journal, sentiment)
        
    except Exception as e:
        print(f"🤖 Cohere API error: {e}")
        return get_fallback_response(mood, journal, sentiment)

def get_huggingface_ai_response(mood, journal, sentiment):
    """Get AI response using Hugging Face Inference API (FREE)"""
    try:
        # Hugging Face Inference API - completely free for personal use
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        # Create a context-aware prompt
        context = f"User is feeling {mood.lower()} and wrote: '{journal}'. Sentiment score: {sentiment:.2f}. "
        
        if sentiment < -0.3:
            context += "User seems to be struggling. Provide comfort and practical suggestions."
        elif sentiment > 0.3:
            context += "User is in a positive mood. Provide encouragement and suggestions to maintain this energy."
        else:
            context += "User is in a neutral state. Provide gentle support and suggestions."
        
        # Add specific context detection
        journal_lower = journal.lower()
        if any(word in journal_lower for word in ['study', 'exam', 'test', 'homework', 'assignment', 'class', 'school', 'college', 'university', 'learn', 'education']):
            context += " User is dealing with academic stress. Provide study-specific advice."
        elif any(word in journal_lower for word in ['work', 'job', 'project', 'deadline', 'meeting', 'boss', 'colleague', 'career', 'business', 'build', 'app', 'code', 'programming', 'development']):
            context += " User is dealing with work/project stress. Provide work-specific advice."
        elif any(word in journal_lower for word in ['friend', 'family', 'partner', 'relationship', 'love', 'breakup', 'argument', 'people', 'social']):
            context += " User is dealing with relationship issues. Provide relationship-specific advice."
        
        # Prepare the prompt for the model
        prompt = f"Dr. Mind: I'm here to help. {context} Please provide a warm, empathetic response with practical suggestions."
        
        headers = {"Authorization": "Bearer hf_demo"}  # Free demo token
        
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                ai_response = result[0].get('generated_text', '')
                
                # Parse the response to extract comfort and suggestions
                lines = ai_response.split('\n')
                comfort = ""
                suggestions = []
                
                for line in lines:
                    if 'comfort' in line.lower() or 'feel' in line.lower():
                        comfort = line.strip()
                    elif line.strip().startswith('-') or line.strip().startswith('•'):
                        suggestions.append(line.strip().lstrip('- ').lstrip('• '))
                
                # If parsing fails, create a structured response
                if not comfort:
                    comfort = f"I understand you're feeling {mood.lower()}. Your feelings are valid and important."
                
                if not suggestions:
                    suggestions = [
                        "Take a moment to breathe deeply and center yourself",
                        "Write down your thoughts to help process them",
                        "Reach out to someone you trust for support"
                    ]
                
                return {
                    'comfort': comfort,
                    'suggestions': suggestions[:3]
                }
        
        # Fallback if API fails
        print("🤖 Hugging Face API failed, using fallback system...")
        return get_fallback_response(mood, journal, sentiment)
        
    except Exception as e:
        print(f"🤖 Hugging Face API error: {e}")
        return get_fallback_response(mood, journal, sentiment)

def get_ai_response(mood, journal, sentiment):
    """Get real AI-generated comfort message and suggestions using multiple free AI services"""
    
    # Try Hugging Face first (completely free)
    print("🤖 Trying Hugging Face AI (FREE)...")
    huggingface_response = get_huggingface_ai_response(mood, journal, sentiment)
    
    # If Hugging Face worked well, use it
    if huggingface_response and huggingface_response.get('comfort') and len(huggingface_response.get('suggestions', [])) > 0:
        return huggingface_response
    
    # Try Cohere as second option (free tier - 5 requests/minute)
    print("🤖 Trying Cohere AI (FREE tier)...")
    cohere_response = get_cohere_ai_response(mood, journal, sentiment)
    
    # If Cohere worked well, use it
    if cohere_response and cohere_response.get('comfort') and len(cohere_response.get('suggestions', [])) > 0:
        return cohere_response
    
    # Fallback to Google AI if available
    if GOOGLE_API_KEY:
        print("🤖 Trying Google AI...")
        try:
            prompt = f"""
            You are Dr. Mind, a compassionate AI mental health companion. The user wrote: "{journal}" and selected the mood: "{mood}" with a sentiment score of {sentiment:.2f}.

            Please provide:
            1. A warm, empathetic comfort message (2-3 sentences)
            2. Three actionable, practical suggestions for what to do next

            IMPORTANT: If the user mentions studying, exams, work, or academic stress, provide specific study/work advice. If they mention relationship issues, provide relationship advice. If they mention health concerns, provide health advice. Be specific and contextual to their situation.

            Format your response exactly like this:
            COMFORT: [your comfort message here]
            SUGGESTIONS:
            - [suggestion 1]
            - [suggestion 2]
            - [suggestion 3]

            Keep the tone warm, supportive, and actionable. Focus on practical steps they can take.
            """

            # Use Google AI Gemini Pro model
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            ai_response = response.text

            # Parse the AI response
            lines = ai_response.split('\n')
            comfort = ""
            suggestions = []

            for line in lines:
                if line.startswith('COMFORT:'):
                    comfort = line.replace('COMFORT:', '').strip()
                elif line.startswith('-'):
                    suggestions.append(line.replace('-', '').strip())

            # Fallback if parsing fails
            if not comfort or not suggestions:
                return get_fallback_response(mood, journal, sentiment)

            return {
                'comfort': comfort,
                'suggestions': suggestions[:3]  # Limit to 3 suggestions
            }

        except Exception as e:
            print(f"Google AI API error: {e}")
            print("🤖 Using fallback rule-based system for better reliability...")
            return get_fallback_response(mood, journal, sentiment)
    else:
        print("🤖 Using fallback rule-based system (no API key configured)...")
        return get_fallback_response(mood, journal, sentiment)
    
    try:
        prompt = f"""
        You are Dr. Mind, a compassionate AI mental health companion. The user wrote: "{journal}" and selected the mood: "{mood}" with a sentiment score of {sentiment:.2f}.

        Please provide:
        1. A warm, empathetic comfort message (2-3 sentences)
        2. Three actionable, practical suggestions for what to do next

        IMPORTANT: If the user mentions studying, exams, work, or academic stress, provide specific study/work advice. If they mention relationship issues, provide relationship advice. If they mention health concerns, provide health advice. Be specific and contextual to their situation.

        Format your response exactly like this:
        COMFORT: [your comfort message here]
        SUGGESTIONS:
        - [suggestion 1]
        - [suggestion 2]
        - [suggestion 3]

        Keep the tone warm, supportive, and actionable. Focus on practical steps they can take.
        """

        # Use Google AI Gemini Pro model
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        ai_response = response.text

        # Parse the AI response
        lines = ai_response.split('\n')
        comfort = ""
        suggestions = []

        for line in lines:
            if line.startswith('COMFORT:'):
                comfort = line.replace('COMFORT:', '').strip()
            elif line.startswith('-'):
                suggestions.append(line.replace('-', '').strip())

        # Fallback if parsing fails
        if not comfort or not suggestions:
            return get_fallback_response(mood, journal, sentiment)

        return {
            'comfort': comfort,
            'suggestions': suggestions[:3]  # Limit to 3 suggestions
        }

    except Exception as e:
        print(f"Google AI API error: {e}")
        print("🤖 Using fallback rule-based system for better reliability...")
        return get_fallback_response(mood, journal, sentiment)

def get_fallback_response(mood, journal, sentiment):
    """Fallback response when OpenAI is not available"""
    
    # Check for specific contexts in the journal
    journal_lower = journal.lower()
    is_study_context = any(word in journal_lower for word in ['study', 'exam', 'test', 'homework', 'assignment', 'class', 'school', 'college', 'university', 'learn', 'education'])
    is_work_context = any(word in journal_lower for word in ['work', 'job', 'project', 'deadline', 'meeting', 'boss', 'colleague', 'career', 'business', 'build', 'app', 'code', 'programming', 'development'])
    is_relationship_context = any(word in journal_lower for word in ['friend', 'family', 'partner', 'relationship', 'love', 'breakup', 'argument', 'people', 'social'])
    is_creative_context = any(word in journal_lower for word in ['create', 'build', 'make', 'design', 'art', 'music', 'write', 'draw', 'paint', 'craft'])
    
    # Comprehensive comfort messages for different scenarios
    comfort_messages = {
        'positive': [
            "It's wonderful to see you in such a positive space! Your energy is contagious and inspiring.",
            "Your positive outlook is truly beautiful. This kind of energy can create amazing ripples in your life.",
            "What a joy to witness your happiness! These moments of positivity are precious and worth celebrating.",
            "Your enthusiasm and joy are absolutely radiant. Keep shining this beautiful light!",
            "This positive energy you're experiencing is a testament to your inner strength and resilience."
        ],
        'neutral': [
            "It's perfectly okay to feel neutral. Every emotion has its place in our journey.",
            "Neutral moments are often when we can best observe and understand ourselves.",
            "There's wisdom in accepting all our emotional states, including the calm neutral ones.",
            "Sometimes neutrality is exactly what we need to process and reflect.",
            "Your neutral state might be your mind's way of finding balance and equilibrium."
        ],
        'negative': [
            "I hear you, and your feelings are completely valid. It's okay to not be okay.",
            "Your emotions are real and important. You don't have to rush through this difficult time.",
            "It takes courage to acknowledge when we're struggling. You're showing strength by being honest.",
            "Your feelings matter, and it's completely normal to have difficult days.",
            "Remember that this moment is temporary, and you have the strength to get through it."
        ]
    }
    
    # Comprehensive suggestions for different scenarios
    suggestions_database = {
        'positive': [
            "Share this positive energy with someone who might need it",
            "Document this feeling to remember it during tougher times",
            "Use this momentum to tackle something you've been putting off",
            "Express gratitude for this moment of joy",
            "Channel this energy into creative expression",
            "Plan something fun to look forward to",
            "Reach out to someone you care about",
            "Take a moment to appreciate how far you've come"
        ],
        'neutral': [
            "Take a moment to practice mindfulness or meditation",
            "Try a new activity to add some variety to your day",
            "Connect with a friend or family member",
            "Go for a gentle walk and observe your surroundings",
            "Try something creative like drawing or writing",
            "Listen to music that matches your current mood",
            "Take some time for self-reflection",
            "Do something kind for someone else"
        ],
        'negative': [
            "Practice self-compassion - be as kind to yourself as you would be to a friend",
            "Try some gentle physical activity like walking or stretching",
            "Consider talking to someone you trust about how you're feeling",
            "Allow yourself to feel this emotion without judgment",
            "Try listening to uplifting music or watching something funny",
            "Write down your feelings to help process them",
            "Take a warm bath or shower to help relax",
            "Remember that this feeling will pass"
        ]
    }
    
    # Context-specific suggestions
    study_suggestions = [
        "Create a focused study schedule with 25-minute Pomodoro sessions",
        "Break down your exam material into smaller, manageable chunks",
        "Use active recall techniques like flashcards or practice questions",
        "Find a quiet study space and eliminate distractions",
        "Take regular breaks every 45 minutes to maintain focus",
        "Review your notes and create summary sheets for key topics",
        "Practice past exam questions to understand the format",
        "Get adequate sleep tonight - it's crucial for memory retention"
    ]
    
    work_suggestions = [
        "Prioritize your tasks using the Eisenhower Matrix (urgent vs important)",
        "Break down large projects into smaller, actionable steps",
        "Set specific time blocks for focused work sessions",
        "Communicate clearly with your team about deadlines and expectations",
        "Take short breaks to maintain productivity and reduce stress",
        "Document your progress to track your achievements",
        "Seek feedback early to avoid last-minute revisions",
        "Practice time management techniques like time blocking"
    ]
    
    relationship_suggestions = [
        "Practice active listening when talking with others",
        "Express your feelings openly and honestly",
        "Set healthy boundaries in your relationships",
        "Spend quality time with people who support you",
        "Consider couples therapy if you're in a romantic relationship",
        "Reach out to friends or family for support",
        "Practice empathy and try to see others' perspectives",
        "Take time for self-care to maintain healthy relationships"
    ]
    
    creative_project_suggestions = [
        "Start with a simple project to build your confidence",
        "Break down your app idea into smaller, manageable features",
        "Use online tutorials and courses to learn step by step",
        "Join a coding community or forum for support and guidance",
        "Set realistic goals and celebrate small wins along the way",
        "Don't be afraid to start with basic tools and improve over time",
        "Find a mentor or friend who can help guide your learning",
        "Remember that every expert was once a beginner"
    ]
    
    # Mood-specific additional suggestions
    mood_specific = {
        'Joyful': [
            "Channel this joy into creative expression",
            "Plan something fun to look forward to"
        ],
        'Sad': [
            "Allow yourself to feel this emotion without judgment",
            "Try listening to uplifting music or watching something funny"
        ],
        'Anxious': [
            "Practice deep breathing exercises",
            "Write down your worries to help organize your thoughts"
        ],
        'Stressed': [
            "Take a short break to do something you enjoy",
            "Break down overwhelming tasks into smaller steps"
        ],
        'Angry': [
            "Try physical exercise to release tension",
            "Write down your feelings before responding to situations"
        ],
        'Exhausted': [
            "Prioritize rest and self-care today",
            "Be gentle with yourself and don't push too hard"
        ],
        'Confused': [
            "Take time to reflect on what's causing uncertainty",
            "Talk through your thoughts with someone you trust"
        ],
        'Worried': [
            "Practice grounding techniques to stay present",
            "Focus on what you can control right now"
        ],
        'Grateful': [
            "Express your gratitude to someone who has helped you",
            "Write down three things you're thankful for today"
        ],
        'Loved': [
            "Share this feeling of love with others",
            "Take time to appreciate the relationships in your life"
        ]
    }
    
    # Determine response category based on sentiment and mood
    if sentiment > 0.3 or mood in ['Joyful', 'Content', 'Peaceful', 'Grateful', 'Loved', 'Excited', 'Confident', 'Satisfied']:
        category = 'positive'
    elif sentiment < -0.3 or mood in ['Sad', 'Angry', 'Anxious', 'Stressed', 'Overwhelmed', 'Devastated']:
        category = 'negative'
    else:
        category = 'neutral'
    
    # Select random comfort message and suggestions
    comfort = random.choice(comfort_messages[category])
    
    # Prioritize context-specific suggestions
    if is_study_context:
        final_suggestions = random.sample(study_suggestions, 3)
    elif is_work_context or is_creative_context:
        if is_creative_context:
            final_suggestions = random.sample(creative_project_suggestions, 3)
        else:
            final_suggestions = random.sample(work_suggestions, 3)
    elif is_relationship_context:
        final_suggestions = random.sample(relationship_suggestions, 3)
    else:
        base_suggestions = random.sample(suggestions_database[category], 3)
        
        # Add mood-specific suggestions if available
        mood_suggestions = mood_specific.get(mood, [])
        if mood_suggestions:
            # Add 1-2 mood-specific suggestions
            additional_suggestions = random.sample(mood_suggestions, min(2, len(mood_suggestions)))
            all_suggestions = base_suggestions + additional_suggestions
            # Shuffle and take first 3
            random.shuffle(all_suggestions)
            final_suggestions = all_suggestions[:3]
        else:
            final_suggestions = base_suggestions
    
    # Add context-specific comfort message
    if is_study_context:
        comfort += " Academic challenges can be overwhelming, but you're building important skills."
    elif is_work_context:
        comfort += " Work stress is real, and it's okay to feel this way."
    elif is_creative_context:
        comfort += " Starting something new can feel overwhelming, but every journey begins with a single step."
    elif is_relationship_context:
        comfort += " Relationships can be complex, and your feelings matter."
    
    return {
        'comfort': comfort,
        'suggestions': final_suggestions
    }



def analyze_sentiment(text):
    """Analyze sentiment using TextBlob"""
    try:
        analysis = TextBlob(text)
        sentiment = analysis.sentiment.polarity
        return max(-1, min(1, sentiment))  # Normalize to -1 to 1
    except Exception:
        return 0.0

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        mood = request.form.get('mood')
        journal = request.form.get('journal')
        
        if not mood or not journal:
            flash('⚠️ Please select a mood and write a journal entry!', 'error')
        else:
            try:
                # Analyze sentiment
                sentiment = analyze_sentiment(journal)
                
                # Get AI response
                ai_response = get_ai_response(mood, journal, sentiment)
                
                # Save entry
                new_entry = MoodEntry(
                    mood=mood,
                    journal=journal,
                    sentiment=sentiment,
                    comfort_message=ai_response['comfort'],
                    suggestions=json.dumps(ai_response['suggestions'])
                )
                
                db.session.add(new_entry)
                db.session.commit()
                
                flash('📝 Entry saved successfully!', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                flash(f'⚠️ Error saving entry: {str(e)}', 'error')
    
    # Get entries for display
    entries = MoodEntry.query.order_by(MoodEntry.date.desc()).all()
    
    # Prepare chart data
    chart_data = []
    for entry in entries[-10:]:  # Last 10 entries
        chart_data.append({
            'date': entry.date.strftime('%Y-%m-%d'),
            'sentiment': entry.sentiment
        })
    
    # Calculate statistics
    total_entries = len(entries)
    if total_entries > 0:
        avg_sentiment = sum(entry.sentiment for entry in entries) / total_entries
        positive_days = len([e for e in entries if e.sentiment > 0.3])
    else:
        avg_sentiment = 0
        positive_days = 0
    
    # Get random quote
    import random
    current_quote = random.choice(QUOTES)
    
    return render_template_string(HTML_TEMPLATE, 
                                moods=MOODS, 
                                entries=entries, 
                                chart_data=json.dumps(chart_data),
                                total_entries=total_entries,
                                avg_sentiment=avg_sentiment,
                                positive_days=positive_days,
                                current_quote=current_quote)

@app.route('/export')
def export_data():
    """Export all entries as JSON"""
    entries = MoodEntry.query.order_by(MoodEntry.date.desc()).all()
    data = []
    
    for entry in entries:
        data.append({
            'date': entry.date.isoformat(),
            'mood': entry.mood,
            'journal': entry.journal,
            'sentiment': entry.sentiment,
            'comfort_message': entry.comfort_message,
            'suggestions': json.loads(entry.suggestions) if entry.suggestions else []
        })
    
    return json.dumps(data, indent=2)

@app.route('/export/csv')
def export_csv():
    """Export all entries as CSV"""
    entries = MoodEntry.query.order_by(MoodEntry.date.desc()).all()
    
    csv_data = "Date,Time,Mood,Journal,Sentiment,Comfort Message,Suggestions\n"
    
    for entry in entries:
        # Format date and time
        date_str = entry.date.strftime('%Y-%m-%d')
        time_str = entry.date.strftime('%H:%M')
        
        # Clean text for CSV (remove quotes and newlines)
        journal_clean = entry.journal.replace('"', '""').replace('\n', ' ')
        comfort_clean = entry.comfort_message.replace('"', '""').replace('\n', ' ')
        
        # Format suggestions
        suggestions = json.loads(entry.suggestions) if entry.suggestions else []
        suggestions_str = '; '.join(suggestions).replace('"', '""').replace('\n', ' ')
        
        csv_data += f'"{date_str}","{time_str}","{entry.mood}","{journal_clean}","{entry.sentiment:.2f}","{comfort_clean}","{suggestions_str}"\n'
    
    from flask import Response
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=drmind_entries_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

@app.route('/export/txt')
def export_txt():
    """Export all entries as readable text"""
    entries = MoodEntry.query.order_by(MoodEntry.date.desc()).all()
    
    txt_data = "🧠 Dr. Mind - Mood Journal Entries\n"
    txt_data += "=" * 50 + "\n\n"
    
    for i, entry in enumerate(entries, 1):
        txt_data += f"Entry #{i}\n"
        txt_data += f"Date: {entry.date.strftime('%Y-%m-%d %H:%M')}\n"
        txt_data += f"Mood: {entry.mood}\n"
        txt_data += f"Sentiment Score: {entry.sentiment:.2f}\n"
        txt_data += f"Journal: {entry.journal}\n"
        txt_data += f"AI Comfort: {entry.comfort_message}\n"
        
        suggestions = json.loads(entry.suggestions) if entry.suggestions else []
        txt_data += "AI Suggestions:\n"
        for j, suggestion in enumerate(suggestions, 1):
            txt_data += f"  {j}. {suggestion}\n"
        
        txt_data += "\n" + "-" * 40 + "\n\n"
    
    from flask import Response
    return Response(
        txt_data,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename=drmind_entries_{datetime.now().strftime("%Y%m%d")}.txt'}
    )

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dr. Mind - AI-Powered Mood Tracker</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: background 3s ease-in-out;
            overflow-x: hidden;
        }

        .animated-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: background 3s ease-in-out;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            animation: fadeInDown 1s ease-out;
        }

        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
            animation: fadeInUp 1s ease-out 0.3s both;
        }

        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .main-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            animation: slideInUp 0.8s ease-out;
        }

        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .mood-section {
            margin-bottom: 30px;
        }

        .mood-section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8rem;
            text-align: center;
        }

        .mood-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .mood-option {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px;
            border: 2px solid transparent;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.8);
            animation: float 3s ease-in-out infinite;
        }

        .mood-option:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }

        .mood-option.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            transform: scale(1.05);
        }

        .mood-emoji {
            font-size: 2.5rem;
            margin-bottom: 8px;
        }

        .mood-label {
            font-size: 0.9rem;
            font-weight: 500;
            text-align: center;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }

        .journal-section {
            margin-bottom: 30px;
        }

        .journal-section h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.8rem;
            text-align: center;
        }

        .journal-input {
            width: 100%;
            min-height: 120px;
            padding: 20px;
            border: 2px solid #e1e5e9;
            border-radius: 15px;
            font-size: 1rem;
            font-family: inherit;
            resize: vertical;
            transition: border-color 0.3s ease;
            background: rgba(255,255,255,0.9);
        }

        .journal-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .submit-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: block;
            margin: 20px auto;
            min-width: 200px;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .flash-message {
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            font-weight: 500;
            animation: slideInDown 0.5s ease-out;
        }

        .flash-success {
            background: linear-gradient(135deg, #43e97b, #38f9d7);
            color: white;
        }

        .flash-error {
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
        }

        @keyframes slideInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .ai-response {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            animation: fadeIn 0.8s ease-out;
        }

        .ai-response h3 {
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        .ai-suggestions {
            list-style: none;
            padding: 0;
        }

        .ai-suggestions li {
            background: rgba(255,255,255,0.2);
            margin: 10px 0;
            padding: 12px 15px;
            border-radius: 10px;
            backdrop-filter: blur(5px);
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .entries-section {
            margin-top: 40px;
        }

        .entries-section h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8rem;
            text-align: center;
        }

        .entry-card {
            background: rgba(255,255,255,0.9);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            animation: slideInRight 0.6s ease-out;
        }

        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .entry-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .entry-mood {
            font-size: 2rem;
        }

        .entry-date {
            color: #666;
            font-size: 0.9rem;
        }

        .entry-sentiment {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 10px;
            display: inline-block;
        }

        .entry-text {
            color: #333;
            line-height: 1.6;
            margin-bottom: 15px;
        }

        .entry-suggestions {
            background: rgba(102, 126, 234, 0.1);
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }

        .entry-suggestions h4 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1rem;
        }

        .entry-suggestions ul {
            list-style: none;
            padding: 0;
        }

        .entry-suggestions li {
            margin: 5px 0;
            padding-left: 20px;
            position: relative;
        }

        .entry-suggestions li:before {
            content: "•";
            color: #667eea;
            position: absolute;
            left: 0;
        }

        .chart-container {
            background: rgba(255,255,255,0.9);
            border-radius: 15px;
            padding: 20px;
            margin: 30px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            height: 300px;
        }

        .chart-container h2 {
            color: #333;
            margin-bottom: 20px;
            text-align: center;
            font-size: 1.8rem;
        }

        .motivational-quote {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            margin: 30px 0;
            font-style: italic;
            font-size: 1.2rem;
            animation: pulse 3s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }

        .crisis-button {
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: block;
            margin: 20px auto;
            animation: pulse 2s ease-in-out infinite;
        }

        .crisis-button:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(255, 107, 107, 0.3);
        }

        .stats-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .stat-card {
            background: rgba(255,255,255,0.9);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 0.9rem;
        }

        .export-section {
            background: rgba(255,255,255,0.9);
            border-radius: 15px;
            padding: 20px;
            margin: 30px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .export-buttons {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
        }

        .export-btn {
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            text-align: center;
            min-width: 120px;
        }

        .export-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .mood-grid {
                grid-template-columns: repeat(auto-fit, minmax(70px, 1fr));
                gap: 10px;
            }
            
            .mood-emoji {
                font-size: 2rem;
            }
            
            .main-card {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="animated-bg"></div>
    
    <div class="container">
        <div class="header">
            <h1>🧠 Dr. Mind</h1>
            <p>AI-Powered Mood Tracking & Wellness Companion</p>
        </div>

        <div class="main-card">
            <div class="mood-section">
                <h2>How are you feeling today?</h2>
                <form method="POST">
                    <div class="mood-grid">
                        {% for mood in moods %}
                        <label class="mood-option" onclick="selectMood(this, '{{ mood.label }}')">
                            <div class="mood-emoji">{{ mood.emoji }}</div>
                            <div class="mood-label">{{ mood.label }}</div>
                            <input type="radio" name="mood" value="{{ mood.label }}" style="display: none;">
                        </label>
                        {% endfor %}
                    </div>
                    
                    <div class="journal-section">
                        <h2>Share your thoughts...</h2>
                        <textarea 
                            class="journal-input" 
                            name="journal" 
                            placeholder="Write about your day, your feelings, or anything on your mind. Be as detailed as you'd like..."
                            required
                        ></textarea>
                    </div>

                    <button type="submit" class="submit-btn">
                        📝 Save Entry & Get AI Insights
                    </button>
                </form>
            </div>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ 'success' if category == 'success' else 'error' }}">
                            {{ message }}
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>

        <div class="chart-container">
            <h2>Your Mood Journey</h2>
            <canvas id="moodChart"></canvas>
        </div>

        <div class="stats-section">
            <div class="stat-card">
                <div class="stat-number">{{ total_entries }}</div>
                <div class="stat-label">Total Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ "%.2f"|format(avg_sentiment) }}</div>
                <div class="stat-label">Average Sentiment</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ positive_days }}</div>
                <div class="stat-label">Positive Days</div>
            </div>
        </div>

        <div class="motivational-quote">
            "{{ current_quote }}"
        </div>

        <button class="crisis-button" onclick="showCrisisHelp()">
            🆘 Need Immediate Help?
        </button>

        <div class="export-section">
            <h3 style="text-align: center; color: #333; margin-bottom: 15px;">📊 Export Your Data</h3>
            <div class="export-buttons">
                <a href="/export/txt" class="export-btn" style="background: linear-gradient(135deg, #43e97b, #38f9d7); margin: 5px;">
                    📝 Readable Text
                </a>
                <a href="/export/csv" class="export-btn" style="background: linear-gradient(135deg, #667eea, #764ba2); margin: 5px;">
                    📊 Excel/CSV
                </a>
                <a href="/export" class="export-btn" style="background: linear-gradient(135deg, #fa709a, #fee140); margin: 5px;">
                    🔧 JSON (Advanced)
                </a>
            </div>
        </div>

        <div class="entries-section">
            <h2>Your Journal Entries</h2>
            {% if entries %}
                {% for entry in entries %}
                <div class="entry-card">
                    <div class="entry-header">
                        <div class="entry-mood">
                            {% for mood in moods %}
                                {% if mood.label == entry.mood %}
                                    {{ mood.emoji }}
                                {% endif %}
                            {% endfor %}
                        </div>
                        <div class="entry-date">{{ entry.date.strftime('%Y-%m-%d %H:%M') }}</div>
                    </div>
                    <div class="entry-sentiment">
                        Sentiment: {{ "%.2f"|format(entry.sentiment) }}
                    </div>
                    <div class="entry-text">{{ entry.journal }}</div>
                    <div class="entry-suggestions">
                        <h4>🤖 AI Response:</h4>
                        <p><strong>Comfort:</strong> {{ entry.comfort_message }}</p>
                        <h4>Suggestions:</h4>
                        <ul>
                            {% for suggestion in entry.suggestions|from_json %}
                                <li>{{ suggestion }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; color: #666; font-style: italic;">No entries yet. Start your journey by adding your first entry!</p>
            {% endif %}
        </div>
    </div>

    <script>
        // Mood selection
        function selectMood(element, mood) {
            // Remove selection from all options
            document.querySelectorAll('.mood-option').forEach(option => {
                option.classList.remove('selected');
            });
            
            // Add selection to clicked option
            element.classList.add('selected');
            
            // Set the radio button value
            const radio = element.querySelector('input[type="radio"]');
            radio.checked = true;
        }

        // Chart initialization
        const chartData = {{ chart_data|safe }};
        
        if (chartData.length > 0) {
            const ctx = document.getElementById('moodChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.map(item => item.date),
                    datasets: [{
                        label: 'Mood Sentiment',
                        data: chartData.map(item => item.sentiment),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: -1,
                            max: 1,
                            ticks: {
                                stepSize: 0.25,
                                callback: function(value) {
                                    if (value === 1) return 'Very Positive';
                                    if (value === 0.75) return 'Positive';
                                    if (value === 0.5) return 'Somewhat Positive';
                                    if (value === 0.25) return 'Slightly Positive';
                                    if (value === 0) return 'Neutral';
                                    if (value === -0.25) return 'Slightly Negative';
                                    if (value === -0.5) return 'Somewhat Negative';
                                    if (value === -0.75) return 'Negative';
                                    if (value === -1) return 'Very Negative';
                                    return '';
                                }
                            }
                        },
                        x: {
                            ticks: {
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // Gradient animation
        let gradientIndex = 0;
        const gradients = [
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
        ];
        
        setInterval(() => {
            gradientIndex = (gradientIndex + 1) % gradients.length;
            document.querySelector('.animated-bg').style.background = gradients[gradientIndex];
        }, 5000);

        // Crisis help
        function showCrisisHelp() {
            // Redirect to crisis help website
            window.open('https://988lifeline.org/', '_blank');
        }
    </script>
</body>
</html>
'''

# Custom Jinja filter
@app.template_filter('from_json')
def from_json(value):
    try:
        return json.loads(value)
    except:
        return []

# Initialize database tables (this runs when the app starts, regardless of how it's started)
with app.app_context():
    db.create_all()
    print("🗄️  Database initialized successfully!")

if __name__ == '__main__':
    print("🧠 Dr. Mind is starting up...")
    if GOOGLE_API_KEY:
        print("🤖 Real AI system ready with Google AI (Gemini 1.5 Pro)!")
        print("🎉 You have 1,000 free requests per month!")
    else:
        print("⚠️  No Google AI API key found - using fallback system")
        print("💡 To enable real AI, set GOOGLE_API_KEY environment variable")
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("🔄 Press Ctrl+C to stop the server")
    
    # Check if running in production (Render sets PORT environment variable)
    import os
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 
