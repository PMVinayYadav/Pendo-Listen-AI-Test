import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import uuid
from datetime import datetime
import time

# Set page config
st.set_page_config(
    page_title="Pendo Listen Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme styling
st.markdown("""
<style>
    /* Force dark mode everywhere */
    .stApp {
        background-color: #121212 !important;
    }
    
    .main {
        background-color: #121212 !important;
    }
    
    /* SIDEBAR SPECIFIC FIXES */
    .css-1d391kg, .css-1iyw2u1, [data-testid="stSidebar"] {
        background-color: #121212 !important;
    }
    
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, 
    [data-testid="stSidebar"] div {
        color: #ffffff !important;
    }
    
    /* Fix for sidebar headers */
    .css-6qob1r, .css-10oheav, .css-ue6h4q {
        color: #ffffff !important;
    }
    
    /* All text should be white on dark backgrounds */
    p, span, h1, h2, h3, h4, h5, h6, div, label {
        color: #ffffff !important;
    }
    
    /* Card styling */
    .card {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #7c4dff;
    }
    
    /* Make Streamlit inputs visible in dark mode */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    
    /* Fix select box text */
    .stSelectbox > div > div > div {
        color: #ffffff !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #7c4dff;
        color: white !important;
        border-radius: 4px;
        border: none;
        padding: 10px 15px;
    }
    
    .stButton > button:hover {
        background-color: #6a40e0;
    }
    
    /* Status badges with high contrast */
    .badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 4px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .badge-positive {
        background-color: #10b981;
        color: white !important;
    }
    
    .badge-neutral {
        background-color: #6b7280;
        color: white !important;
    }
    
    .badge-negative {
        background-color: #ef4444;
        color: white !important;
    }
    
    /* Status colors for roadmap */
    .status-proposed {
        background-color: #f59e0b;
        color: white !important;
        padding: 5px 10px;
        border-radius: 4px;
    }
    
    .status-validated {
        background-color: #3b82f6;
        color: white !important;
        padding: 5px 10px;
        border-radius: 4px;
    }
    
    .status-planned {
        background-color: #8b5cf6;
        color: white !important;
        padding: 5px 10px;
        border-radius: 4px;
    }
    
    .status-completed {
        background-color: #10b981;
        color: white !important;
        padding: 5px 10px;
        border-radius: 4px;
    }
    
    /* Metric card styling */
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        color: #7c4dff !important;
    }
    
    /* Roadmap columns */
    .roadmap-column {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 15px;
        min-height: 200px;
    }
    
    .roadmap-item {
        background-color: #2d2d2d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #7c4dff;
    }
    
    /* Make expander text white */
    .streamlit-expanderHeader {
        color: #ffffff !important;
    }
    
    /* Fix info boxes to be visible */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.1);
        color: white !important;
    }
    
    .stAlert > div > p {
        color: #ffffff !important;
    }
    
    /* Fix textarea color */
    .stTextArea textarea {
        color: white !important;
        background-color: #2d2d2d !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2d2d2d;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #7c4dff !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Setup in-memory database
@st.cache_resource
def init_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
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
    
    return conn

# Initialize database
conn = init_db()

# Helper functions to work with the database
def get_data(query, params=()):
    df = pd.read_sql_query(query, conn, params=params)
    return df

def execute_sql(query, params=()):
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()

# Add sample data
def add_sample_data():
    cursor = conn.cursor()
    
    # Check if we already have data
    cursor.execute("SELECT COUNT(*) FROM raw_feedback")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Sample feedback data
        sample_feedback = [
            {
                "id": "sample1",
                "title": "Pendo is great but missing some features",
                "content": "We've been using Pendo for about 6 months now. The analytics are really good, and the in-app guides are easy to set up. But we're struggling with the feedback collection. It's not as intuitive as the rest of the platform. Would love to see improvements in how feedback is categorized and analyzed.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample1",
                "theme": "User Interface",
                "sentiment": "neutral",
                "summary": "User appreciates Pendo's analytics and guides but finds the feedback collection system unintuitive and difficult to use."
            },
            {
                "id": "sample2",
                "title": "Comparing Pendo vs Mixpanel vs Amplitude",
                "content": "My team is evaluating different product analytics tools. Pendo seems to have the best combination of analytics and user guidance, but it's more expensive than Mixpanel. Amplitude has better event tracking. Anyone using Pendo who can share their experience with their AI features? Are they worth the premium price?",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample2",
                "theme": "Pricing",
                "sentiment": "neutral",
                "summary": "User is comparing analytics platforms and is concerned about Pendo's pricing compared to competitors while evaluating its AI features."
            },
            {
                "id": "sample3",
                "title": "Pendo Listen - first impressions",
                "content": "Just started using Pendo Listen to collect and analyze customer feedback. The AI summarization is pretty impressive - it's saved hours of manual categorization work. However, I wish there was better integration with our support ticketing system. Right now we have to manually export data from Zendesk.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample3",
                "theme": "Integrations",
                "sentiment": "positive",
                "summary": "User is impressed with Pendo Listen's AI summarization but wants better integration with support ticketing systems like Zendesk."
            },
            {
                "id": "sample4",
                "title": "Need help with Pendo implementation",
                "content": "We're in the process of implementing Pendo across our SaaS platform, but having some issues with the event tracking. Has anyone dealt with custom events not showing up in the dashboard? Also, the Listen feature seems to be collecting feedback but the AI analysis is sometimes missing the point of the customer's comment.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample4",
                "theme": "Technical Issues",
                "sentiment": "negative",
                "summary": "User is experiencing problems with event tracking and AI analysis during Pendo implementation, particularly with custom events and accurate feedback understanding."
            },
            {
                "id": "sample5",
                "title": "Pendo Listen vs UserVoice",
                "content": "Our team is currently using UserVoice for feedback collection but considering a switch to Pendo Listen. Has anyone made this transition? I'm particularly interested in the AI-powered analysis in Listen and how accurate it is. Does it actually save time compared to manual categorization? The pricing is quite a bit higher so trying to justify the cost.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample5",
                "theme": "Competitor Comparison",
                "sentiment": "neutral",
                "summary": "User is considering switching from UserVoice to Pendo Listen and wants to know if the AI-powered analysis justifies the higher price."
            },
            {
                "id": "sample6",
                "title": "Pendo Listen's AI is a game changer",
                "content": "We started using Pendo Listen about 3 months ago and the AI capabilities have completely transformed how we handle customer feedback. Before, we had a team manually going through feedback and categorizing it, which took hours. Now the AI does it in seconds and with remarkable accuracy. We can spot trends we'd have missed before. Definitely worth the investment.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample6",
                "theme": "AI Capabilities",
                "sentiment": "positive",
                "summary": "User praises Pendo Listen's AI as transformative for processing customer feedback, saving time and revealing new insights."
            },
            {
                "id": "sample7",
                "title": "Feature request for Pendo Listen",
                "content": "I'd love to see Pendo Listen add a feature that automatically groups similar feedback items into clusters, even beyond the current categorization. It would help us identify common requests that might span different categories but represent the same underlying need. Also, better visualization of feedback trends over time would be really helpful for reporting to executives.",
                "source": "Sample Data",
                "date": datetime.now().isoformat(),
                "url": "https://example.com/sample7",
                "theme": "Feature Requests",
                "sentiment": "neutral",
                "summary": "User requests improved clustering of related feedback across categories and better visualization of feedback trends for executive reporting."
            }
        ]
        
        # Insert raw feedback data
        for item in sample_feedback:
            cursor.execute(
                "INSERT INTO raw_feedback VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["title"],
                    item["content"],
                    item["source"],
                    item["date"],
                    item["url"]
                )
            )
            
            # Insert analyzed feedback data
            cursor.execute(
                "INSERT INTO analyzed_feedback VALUES (?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["theme"],
                    item["sentiment"],
                    item["summary"],
                    item["id"]  # source_id
                )
            )
        
        # Sample ideas data
        sample_ideas = [
            {
                "id": str(uuid.uuid4()),
                "title": "Improve Feedback Categorization",
                "description": "Enhance the AI model to better categorize feedback by product area and feature requests, focusing on accuracy for complex feedback.",
                "votes": 12,
                "status": "Validated",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Zendesk Integration",
                "description": "Create a seamless integration with Zendesk to automatically import support tickets as feedback and sync resolution status.",
                "votes": 8,
                "status": "Proposed",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Feedback Analytics Dashboard",
                "description": "Build an analytics dashboard specifically for tracking feedback trends over time with visualization of sentiment changes and theme distribution.",
                "votes": 15,
                "status": "Planned",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Advanced Feedback Clustering",
                "description": "Implement an AI-powered system to identify and group similar feedback across different categories to reveal deeper patterns.",
                "votes": 7,
                "status": "Proposed",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Executive Summary Reports",
                "description": "Create automated weekly/monthly reports summarizing key feedback insights, trends, and recommended actions for executive teams.",
                "votes": 10,
                "status": "Completed",
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
        
        return True
    return False

# Add the sample data
add_sample_data()

# Display welcome message
st.warning("👋 **Welcome to the Pendo Listen Simulator!** This demo contains sample data showing how Pendo Listen analyzes user feedback, validates ideas, and manages product roadmaps. Created for a Pendo PM application.")

# Main App UI
st.title("Pendo Listen Simulator")
st.write("Transform feedback into actionable insights, validate ideas, and create strategic roadmaps")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Feedback Analysis", "💡 Idea Validation", "🗺️ Product Roadmap", "🔄 Close the Loop"])

# Tab 1: Feedback Analysis
with tab1:
    st.header("Customer Feedback Analysis")
    
    # Get the data
    df_feedback = get_data("""
        SELECT af.*, rf.title, rf.content, rf.source, rf.date, rf.url 
        FROM analyzed_feedback af 
        JOIN raw_feedback rf ON af.source_id = rf.post_id
    """)
    
    # Display metrics and charts
    if not df_feedback.empty:
        # Get sentiment counts
        sentiment_counts = df_feedback['sentiment'].value_counts()
        positive_count = sentiment_counts.get('positive', 0)
        negative_count = sentiment_counts.get('negative', 0)
        neutral_count = sentiment_counts.get('neutral', 0)
        
        # Metrics row
        st.subheader("Key Metrics")
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(df_feedback)}</div>
                <div>Total Feedback</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_cols[1]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #10b981 !important;">{positive_count}</div>
                <div>Positive</div>
            </div>
            """, unsafe_allow_html=True)
            
        with metric_cols[2]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #ef4444 !important;">{negative_count}</div>
                <div>Negative</div>
            </div>
            """, unsafe_allow_html=True)
            
        with metric_cols[3]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df_feedback['theme'].nunique()}</div>
                <div>Themes</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Charts - using dark mode compatible colors
        st.subheader("Feedback Overview")
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            # Theme distribution
            theme_counts = df_feedback['theme'].value_counts()
            theme_counts_df = theme_counts.reset_index()
            theme_counts_df.columns = ['Theme', 'Count']
            
            fig1 = px.pie(
                theme_counts_df, 
                values='Count', 
                names='Theme', 
                title='Feedback by Theme',
                color_discrete_sequence=px.colors.sequential.Plasma_r,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig1, use_container_width=True)
        
        with chart_cols[1]:
            # Sentiment distribution
            sentiment_counts_df = sentiment_counts.reset_index()
            sentiment_counts_df.columns = ['Sentiment', 'Count']
            
            # Use high-contrast colors
            colors = {'positive': '#10b981', 'neutral': '#6b7280', 'negative': '#ef4444'}
            
            fig2 = px.bar(
                sentiment_counts_df, 
                x='Sentiment', 
                y='Count', 
                title='Feedback by Sentiment',
                color='Sentiment',
                color_discrete_map=colors,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Display feedback list
        st.subheader("Recent Feedback")
        
        for i, row in df_feedback.iterrows():
            with st.expander(f"{row['title'][:70]}...", expanded=i==0):
                # Get appropriate badge for sentiment
                sentiment_badge = f"badge-{row['sentiment']}"
                
                st.markdown(f"""
                <div class="card">
                    <div><span class="badge {sentiment_badge}">{row['sentiment'].upper()}</span></div>
                    <h3>{row['title']}</h3>
                    <p><strong>Theme:</strong> {row['theme']}</p>
                    <p><strong>Summary:</strong> {row['summary']}</p>
                    <p><strong>Source:</strong> {row['source']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display full content
                st.markdown("**Original Content:**")
                st.text_area("", value=row['content'], height=100, disabled=True, key=f"content_{i}")
    else:
        st.info("No feedback data available. Add sample data to continue.")

# Tab 2: Idea Validation
with tab2:
    st.header("Idea Validation")
    
    # Create two columns
    idea_cols = st.columns([3, 2])
    
    with idea_cols[0]:
        st.subheader("Current Ideas")
        
        # Display existing ideas
        ideas_df = get_data("SELECT * FROM ideas ORDER BY votes DESC")
        
        if not ideas_df.empty:
            for i, row in ideas_df.iterrows():
                # Get appropriate status class
                status_class = f"status-{row['status'].lower()}"
                
                st.markdown(f"""
                <div class="card">
                    <div><span class="{status_class}">{row['status'].upper()}</span></div>
                    <h3>{row['title']}</h3>
                    <p>{row['description']}</p>
                    <p><strong>Votes:</strong> {row['votes']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add action buttons
                cols = st.columns([1, 1])
                with cols[0]:
                    if st.button("👍 Upvote", key=f"vote_{i}_{row['idea_id']}"):
                        execute_sql(
                            "UPDATE ideas SET votes = votes + 1, last_updated = ? WHERE idea_id = ?",
                            (datetime.now().isoformat(), row['idea_id'])
                        )
                        st.success("Vote recorded!")
                        time.sleep(0.5)
                        st.rerun()
                
                with cols[1]:
                    if st.button("🔗 Link Feedback", key=f"link_{i}_{row['idea_id']}"):
                        st.session_state.selected_idea = row['idea_id']
                        st.success("Go to the 'Close the Loop' tab to link feedback to this idea")
        else:
            st.info("No ideas created yet. Use the form to add your first idea.")
    
    with idea_cols[1]:
        st.subheader("Create New Idea")
        
        # Simple form
        with st.form("new_idea_form", clear_on_submit=True):
            idea_title = st.text_input("Idea Title")
            idea_description = st.text_area("Description")
            idea_status = st.selectbox(
                "Initial Status",
                options=["Proposed", "Validated", "Planned", "Completed"],
                index=0
            )
            
            submitted = st.form_submit_button("Submit Idea")
            
            if submitted and idea_title and idea_description:
                # Generate a unique ID
                idea_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                # Insert the new idea
                execute_sql(
                    "INSERT INTO ideas VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (idea_id, idea_title, idea_description, 0, idea_status, now, now)
                )
                
                st.success("Idea submitted successfully!")
                time.sleep(0.5)
                st.rerun()
        
        # AI recommendations
        st.subheader("AI Recommendations")
        
        # Get data for recommendations
        df_feedback = get_data("""
            SELECT * FROM analyzed_feedback 
            WHERE sentiment = 'negative' 
            ORDER BY theme
        """)
        
        if not df_feedback.empty:
            # Find top negative themes
            neg_themes = df_feedback['theme'].value_counts().head(2)
            
            for theme, count in neg_themes.items():
                st.markdown(f"""
                <div class="card">
                    <h3>Improve {theme}</h3>
                    <p>Address {count} pieces of negative feedback about {theme}.</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Use This Suggestion", key=f"use_{theme}"):
                    st.session_state.prefill_title = f"Improve {theme}"
                    st.session_state.prefill_desc = f"Address user concerns related to {theme} based on collected feedback."
                    st.rerun()
        else:
            st.info("Collect more feedback to get AI-generated recommendations.")

# Tab 3: Roadmap
with tab3:
    st.header("Product Roadmap")
    
    # Get ideas for roadmap
    roadmap_df = get_data("SELECT * FROM ideas ORDER BY votes DESC")
    
    # Create columns for each status
    status_cols = st.columns(4)
    statuses = ["Proposed", "Validated", "Planned", "Completed"]
    
    for i, status in enumerate(statuses):
        with status_cols[i]:
            st.subheader(status)
            
            # Add background styling
            st.markdown('<div class="roadmap-column">', unsafe_allow_html=True)
            
            filtered_df = roadmap_df[roadmap_df['status'] == status] if not roadmap_df.empty else pd.DataFrame()
            
            if not filtered_df.empty:
                for j, row in filtered_df.iterrows():
                    # Get appropriate status class
                    status_class = f"status-{row['status'].lower()}"
                    
                    st.markdown(f"""
                    <div class="roadmap-item">
                        <h4>{row['title']}</h4>
                        <p>{row['description'][:100]}{'...' if len(row['description']) > 100 else ''}</p>
                        <p>👍 {row['votes']} votes</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add status change buttons
                    new_statuses = [s for s in statuses if s != status]
                    
                    if len(new_statuses) > 0:
                        move_cols = st.columns(len(new_statuses))
                        for k, new_status in enumerate(new_statuses):
                            with move_cols[k]:
                                if st.button(f"Move to {new_status}", key=f"move_{j}_{row['idea_id']}_{new_status}"):
                                    # Update idea status
                                    now = datetime.now().isoformat()
                                    execute_sql(
                                        "UPDATE ideas SET status = ?, last_updated = ? WHERE idea_id = ?",
                                        (new_status, now, row['idea_id'])
                                    )
                                    
                                    st.success(f"Moved to {new_status}!")
                                    time.sleep(0.5)
                                    st.rerun()
            else:
                st.info(f"No ideas in {status} status")
            
            # Close the div
            st.markdown('</div>', unsafe_allow_html=True)

# Tab 4: Close the Loop
with tab4:
    st.header("Close the Loop")
    
    # Create two columns
    loop_cols = st.columns([3, 2])
    
    with loop_cols[0]:
        st.subheader("User Feedback")
        
        # Get feedback
        df_feedback = get_data("""
            SELECT af.*, rf.title, rf.content, rf.source, rf.date, rf.url 
            FROM analyzed_feedback af 
            JOIN raw_feedback rf ON af.source_id = rf.post_id
            ORDER BY rf.date DESC
        """)
        
        if not df_feedback.empty:
            for i, row in df_feedback.iterrows():
                # Get appropriate sentiment badge
                sentiment_badge = f"badge-{row['sentiment']}"
                
                st.markdown(f"""
                <div class="card">
                    <div><span class="badge {sentiment_badge}">{row['sentiment'].upper()}</span></div>
                    <h3>{row['title']}</h3>
                    <p><strong>Theme:</strong> {row['theme']}</p>
                    <p><strong>Summary:</strong> {row['summary']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Get ideas to connect with
                ideas_df = get_data("SELECT * FROM ideas ORDER BY votes DESC LIMIT 3")
                
                if not ideas_df.empty:
                    st.markdown("**Link to ideas:**")
                    idea_cols = st.columns(3)


                    for j, idea_row in enumerate(ideas_df.itertuples()):
    with idea_cols[j]:
        if st.button(f"{idea_row.title[:15]}...", key=f"link_loop_{i}_{j}_{idea_row.idea_id}"):
            # Create mapping
            execute_sql(
                "INSERT OR IGNORE INTO feedback_idea_map VALUES (?, ?)",
                (row['feedback_id'], idea_row.idea_id)
            )
            st.success("Feedback linked to idea!")
            time.sleep(0.5)
            st.rerun()

        else:
            st.info("No feedback data available.")
    
    with loop_cols[1]:
        st.subheader("Notification Templates")
        
        # Create template cards
        templates = [
            {
                "title": "Feature Request Acknowledged",
                "message": "Thank you for your feedback! We've added your feature request to our backlog and our product team is currently evaluating it."
            },
            {
                "title": "Feature In Development",
                "message": "Good news! Based on your feedback, we've started development on this feature. We expect to release it in our next major update."
            },
            {
                "title": "Feature Released",
                "message": "We're excited to announce that the feature you requested is now live! Check out our latest release to see it in action."
            }
        ]
        
        for i, template in enumerate(templates):
            st.markdown(f"""
            <div class="card">
                <h3>{template['title']}</h3>
                <p>{template['message']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Use Template", key=f"template_{i}_{template['title']}"):
                st.session_state.template_message = template['message']
                st.success("Template copied! Create a notification with this message.")
        
        # Notification creator
        st.subheader("Create Notification")
        
        with st.form("notification_form"):
            notification_message = st.text_area(
                "Message", 
                value=st.session_state.get('template_message', ''),
                placeholder="Enter your notification message here..."
            )
            
            submitted = st.form_submit_button("Send Notification")
            
            if submitted and notification_message:
                st.success("Notification sent to users!")
                time.sleep(0.5)
                if 'template_message' in st.session_state:
                    del st.session_state.template_message

# Simple sidebar with guaranteed readability
with st.sidebar:
    st.header("Pendo Listen Simulator")
    st.write("This tool simulates Pendo Listen's capabilities to analyze feedback, validate ideas, and create strategic roadmaps.")
    
    st.subheader("Navigation")
    
    if st.button("📊 Feedback Analysis", use_container_width=True):
        st.session_state.active_tab = 0
    
    if st.button("💡 Idea Validation", use_container_width=True):
        st.session_state.active_tab = 1
    
    if st.button("🗺️ Product Roadmap", use_container_width=True):
        st.session_state.active_tab = 2
    
    if st.button("🔄 Close the Loop", use_container_width=True):
        st.session_state.active_tab = 3
    
    st.subheader("Data Controls")
    
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()
    
    if st.button("🧠 Simulate AI Analysis", use_container_width=True):
        progress_bar = st.progress(0)
        for percent_complete in range(100):
            time.sleep(0.01)
            progress_bar.progress(percent_complete + 1)
        st.success("Analysis complete!")
        time.sleep(0.5)
        st.empty()
        st.rerun()
    
    st.markdown("""
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #333333;">
        <p style="text-align: center; color: #a0a0a0 !important; font-size: 12px;">
            Created for Pendo PM Application
        </p>
    </div>
    """, unsafe_allow_html=True)
