# Pendo Listen Simulator

A functional prototype simulating Pendo Listen's AI-powered feedback analysis capabilities. This project was created as part of my application for a Product Manager role at Pendo.

## Project Overview

This application demonstrates the core functionality of Pendo Listen:

- **Feedback Collection**: Gathers user feedback from Reddit (or uses sample data)
- **AI-Powered Analysis**: Uses OpenAI/Claude to categorize and extract insights from feedback
- **Idea Validation**: Creates and prioritizes product ideas based on feedback
- **Product Roadmap**: Visualizes the development pipeline from proposal to completion
- **Closing the Loop**: Notifies users when their feedback leads to product changes

## Technologies Used

- **Python**: Core application logic
- **Streamlit**: Interactive dashboard interface
- **OpenAI/Claude API**: AI-powered feedback analysis
- **SQLite**: Local database for storing feedback and ideas
- **PRAW**: Reddit API wrapper for data collection
- **Plotly**: Data visualization

## Screenshots

[Add screenshots here]

## Setup Instructions

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Add your OpenAI API key to `ai_analyzer.py`
4. Add your Reddit API credentials to `reddit_collector.py`
5. Run the application: `python main.py`

## Features

### 1. Feedback Analysis
- Collects user feedback from various sources
- Uses AI to categorize by theme and sentiment
- Generates summaries and identifies key trends

### 2. Idea Validation
- Creates product ideas based on feedback
- Allows voting and prioritization
- AI recommendations for addressing common themes

### 3. Product Roadmap
- Visual kanban-style board for development stages
- Tracks progress from proposal to completion
- Helps communicate priorities to stakeholders

### 4. Close the Loop
- Links user feedback to specific ideas
- Creates notifications when feedback leads to changes
- Improves user satisfaction and engagement

## Future Enhancements

With more time, I would add:
- Integration with additional data sources
- More advanced sentiment trend analysis over time
- Enhanced AI categorization and theme detection
- Better visualization of the feedback-to-feature journey