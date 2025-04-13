import streamlit as st
import sqlite3
import pandas as pd
import os
import time
from datetime import datetime
import uuid
import openai
import praw

# Import the app content
from app import app_content

# Set page config
st.set_page_config(
    page_title="Pendo Listen Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Setup database
def setup_database():
    # Create database file if it doesn't exist
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()
    
    # Create raw feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS raw_feedback (
        post_id TEXT PRIMARY KEY,
        title TEXT,
        content TEXT,
        source TEXT,
        date TEXT,
        url TEXT
    )
    ''')
    
    # Create analyzed feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analyzed_feedback (
        feedback_id TEXT PRIMARY KEY,
        theme TEXT,
        sentiment TEXT,
        summary TEXT,
        source_id TEXT,
        FOREIGN KEY (source_id) REFERENCES raw_feedback (post_id)
    )
    ''')
    
    # Create ideas table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ideas (
        idea_id TEXT PRIMARY KEY,
        title TEXT,
        description TEXT,
        votes INTEGER DEFAULT 0,
        status TEXT,
        created_date TEXT,
        last_updated TEXT
    )
    ''')
    
    # Create notifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id TEXT PRIMARY KEY,
        feedback_id TEXT,
        idea_id TEXT,
        message TEXT,
        status TEXT,
        created_date TEXT,
        sent_date TEXT
    )
    ''')
    
    # Create feedback_idea_map table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback_idea_map (
        feedback_id TEXT,
        idea_id TEXT,
        PRIMARY KEY (feedback_id, idea_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Add sample data
def add_sample_data():
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()
    
    # Check if we already have data
    cursor.execute("SELECT COUNT(*) FROM raw_feedback")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Sample data
        sample_data = [
            {
                "id": "sample1",
                "title": "Pendo is great but missing some features",
                "content": "We've been using Pendo for about 6 months now. The analytics are really good, and the in-app guides are easy to set up. But we're struggling with the feedback collection. It's not as intuitive as the rest of the platform. Would love to see improvements in how feedback is categorized and analyzed.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample1"
            },
            {
                "id": "sample2",
                "title": "Comparing Pendo vs Mixpanel vs Amplitude",
                "content": "My team is evaluating different product analytics tools. Pendo seems to have the best combination of analytics and user guidance, but it's more expensive than Mixpanel. Amplitude has better event tracking. Anyone using Pendo who can share their experience with their AI features? Are they worth the premium price?",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample2"
            },
            {
                "id": "sample3",
                "title": "Pendo Listen - first impressions",
                "content": "Just started using Pendo Listen to collect and analyze customer feedback. The AI summarization is pretty impressive - it's saved hours of manual categorization work. However, I wish there was better integration with our support ticketing system. Right now we have to manually export data from Zendesk.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample3"
            },
            {
                "id": "sample4",
                "title": "Need help with Pendo implementation",
                "content": "We're in the process of implementing Pendo across our SaaS platform, but having some issues with the event tracking. Has anyone dealt with custom events not showing up in the dashboard? Also, the Listen feature seems to be collecting feedback but the AI analysis is sometimes missing the point of the customer's comment.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample4"
            },
            {
                "id": "sample5",
                "title": "Pendo Listen vs UserVoice",
                "content": "Our team is currently using UserVoice for feedback collection but considering a switch to Pendo Listen. Has anyone made this transition? I'm particularly interested in the AI-powered analysis in Listen and how accurate it is. Does it actually save time compared to manual categorization? The pricing is quite a bit higher so trying to justify the cost.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample5"
            }
        ]
        
        # Insert sample data
        for post in sample_data:
            cursor.execute(
                "INSERT INTO raw_feedback VALUES (?, ?, ?, ?, ?, ?)",
                (
                    post["id"],
                    post["title"],
                    post["content"],
                    post["source"],
                    post["date"],
                    post["url"]
                )
            )
        
        conn.commit()
        
        # Sample ideas
        sample_ideas = [
            {
                "id": str(uuid.uuid4()),
                "title": "Improve Feedback Categorization",
                "description": "Enhance the AI model to better categorize feedback by product area and feature requests.",
                "votes": 12,
                "status": "Validated",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Zendesk Integration",
                "description": "Create a seamless integration with Zendesk to import support tickets as feedback.",
                "votes": 8,
                "status": "Proposed",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Feedback Analytics Dashboard",
                "description": "Build an analytics dashboard specifically for tracking feedback trends over time.",
                "votes": 15,
                "status": "Planned",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        ]
        
        # Insert sample ideas
        for idea in sample_ideas:
            cursor.execute(
                "INSERT INTO ideas VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    idea["id"],
                    idea["title"],
                    idea["description"],
                    idea["votes"],
                    idea["status"],
                    idea["created_date"],
                    idea["last_updated"]
                )
            )
        
        conn.commit()
    
    # Ensure there's analyzed feedback
    cursor.execute("SELECT COUNT(*) FROM analyzed_feedback")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Get unanalyzed feedback
        cursor.execute("SELECT post_id, title, content FROM raw_feedback")
        unanalyzed_posts = cursor.fetchall()
        
        # Add sample analyzed data
        sentiments = ["positive", "negative", "neutral"]
        themes = ["UI/UX", "Performance", "Integrations", "Analytics", "Pricing"]
        
        for i, post in enumerate(unanalyzed_posts):
            post_id = post[0]
            theme = themes[i % len(themes)]
            sentiment = sentiments[i % len(sentiments)]
            summary = f"This feedback is about {theme.lower()} with a {sentiment} sentiment."
            
            cursor.execute(
                "INSERT INTO analyzed_feedback VALUES (?, ?, ?, ?, ?)",
                (post_id, theme, sentiment, summary, post_id)
            )
        
        conn.commit()
    
    conn.close()
    print("Sample data added!")

# Setup database on first run
setup_database()
add_sample_data()

# Display the demo notice
st.warning("👋 **Welcome to the Pendo Listen Simulator demo!** This app contains sample data and full functionality. Explore all tabs to see how feedback is analyzed, ideas are validated, and product roadmaps are managed.")

# Run the main app content
app_content()
