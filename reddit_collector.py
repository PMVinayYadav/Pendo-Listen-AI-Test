import praw
import sqlite3
import datetime
import uuid


def collect_reddit_feedback(subreddit_name, keywords=None, post_limit=20):
    # Reddit API credentials
    reddit = praw.Reddit(
        client_id="B1SmsevnZdQBDzsHNjrGpA",  # Replace with your actual client ID
        client_secret="YVkmdnYroCgJ8rhZsP1kzrBFuejwnA",  # Replace with your actual client secret
        user_agent="PendoListenSimulator/1.0 by YourUsername"  # You can customize this
    )

    # Connect to database
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()

    # Collect posts from the subreddit
    subreddit = reddit.subreddit(subreddit_name)
    collected_count = 0

    print(f"Collecting posts from r/{subreddit_name}...")

    # If keywords provided, use search instead of hot
    if keywords:
        keyword_string = ' OR '.join(keywords)
        print(f"Filtering for keywords: {keyword_string}")
        posts = subreddit.search(keyword_string, limit=post_limit)
    else:
        posts = subreddit.hot(limit=post_limit)

    for post in posts:
        # Only process text posts with sufficient content
        if post.is_self and len(post.selftext) > 100:
            # If keywords provided, double-check content actually contains at least one
            if keywords:
                contains_keyword = any(keyword.lower() in post.title.lower() or
                                       keyword.lower() in post.selftext.lower()
                                       for keyword in keywords)
                if not contains_keyword:
                    continue

            # Check if post already exists
            cursor.execute("SELECT post_id FROM raw_feedback WHERE post_id = ?", (post.id,))
            if cursor.fetchone() is None:
                # Insert new post
                cursor.execute(
                    "INSERT INTO raw_feedback VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        post.id,
                        post.title,
                        post.selftext,
                        f"Reddit - r/{subreddit_name}",
                        datetime.datetime.fromtimestamp(post.created_utc).isoformat(),
                        f"https://www.reddit.com{post.permalink}"
                    )
                )
                collected_count += 1

    conn.commit()
    conn.close()

    print(f"Collected {collected_count} new posts from r/{subreddit_name}")
    return collected_count


def clear_previous_data():
    """Clear previous data from the database when starting a new search"""
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()

    # Clear previous feedback and analysis
    cursor.execute("DELETE FROM raw_feedback")
    cursor.execute("DELETE FROM analyzed_feedback")

    # Also clear related tables that depend on feedback
    try:
        cursor.execute("DELETE FROM notifications")
        cursor.execute("DELETE FROM feedback_idea_map")
    except sqlite3.OperationalError:
        # Tables might not exist in older database versions
        pass

    # Don't delete ideas as users might want to keep them

    conn.commit()
    conn.close()
    print("Previous data cleared!")


def add_sample_data():
    """Adds sample data if no data could be collected from Reddit"""
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()

    # Create sample data based on the search term
    sample_data = [
        {
            "id": "sample1",
            "title": "Pendo is great but missing some features",
            "content": "We've been using Pendo for about 6 months now. The analytics are really good, and the in-app guides are easy to set up. But we're struggling with the feedback collection. It's not as intuitive as the rest of the platform. Would love to see improvements in how feedback is categorized and analyzed.",
            "source": "Sample Data",
            "date": datetime.datetime.now().isoformat(),
            "url": "https://example.com/sample1"
        },
        {
            "id": "sample2",
            "title": "Comparing Pendo vs Mixpanel vs Amplitude",
            "content": "My team is evaluating different product analytics tools. Pendo seems to have the best combination of analytics and user guidance, but it's more expensive than Mixpanel. Amplitude has better event tracking. Anyone using Pendo who can share their experience with their AI features? Are they worth the premium price?",
            "source": "Sample Data",
            "date": datetime.datetime.now().isoformat(),
            "url": "https://example.com/sample2"
        },
        {
            "id": "sample3",
            "title": "Pendo Listen - first impressions",
            "content": "Just started using Pendo Listen to collect and analyze customer feedback. The AI summarization is pretty impressive - it's saved hours of manual categorization work. However, I wish there was better integration with our support ticketing system. Right now we have to manually export data from Zendesk.",
            "source": "Sample Data",
            "date": datetime.datetime.now().isoformat(),
            "url": "https://example.com/sample3"
        },
        {
            "id": "sample4",
            "title": "Need help with Pendo implementation",
            "content": "We're in the process of implementing Pendo across our SaaS platform, but having some issues with the event tracking. Has anyone dealt with custom events not showing up in the dashboard? Also, the Listen feature seems to be collecting feedback but the AI analysis is sometimes missing the point of the customer's comment.",
            "source": "Sample Data",
            "date": datetime.datetime.now().isoformat(),
            "url": "https://example.com/sample4"
        },
        {
            "id": "sample5",
            "title": "Pendo Listen vs UserVoice",
            "content": "Our team is currently using UserVoice for feedback collection but considering a switch to Pendo Listen. Has anyone made this transition? I'm particularly interested in the AI-powered analysis in Listen and how accurate it is. Does it actually save time compared to manual categorization? The pricing is quite a bit higher so trying to justify the cost.",
            "source": "Sample Data",
            "date": datetime.datetime.now().isoformat(),
            "url": "https://example.com/sample5"
        }
    ]

    # Insert sample data
    for post in sample_data:
        cursor.execute("SELECT post_id FROM raw_feedback WHERE post_id = ?", (post["id"],))
        if cursor.fetchone() is None:
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
    conn.close()
    return len(sample_data)


def run_collector():
    # Get user input for product search
    product = input("For which product do you want to collect and summarize data from Reddit? ")

    # Clear previous data when starting a new search
    clear_previous_data()

    print(f"Looking for feedback about '{product}'...")

    # Create keywords list based on the input
    keywords = [product]

    # Add some related terms to improve search results
    keywords.extend([f"{product} review", f"{product} feedback", f"{product} feature"])

    # Relevant subreddits for product feedback
    subreddits = ["ProductManagement", "SaaS", "UserExperience", "webdev"]

    total_collected = 0
    for subreddit in subreddits:
        total_collected += collect_reddit_feedback(subreddit, keywords=keywords, post_limit=20)

    # If no data found, add sample data
    if total_collected == 0:
        print("No data found on Reddit. Adding sample data for demonstration...")
        total_collected = add_sample_data()

    print(f"Total new posts collected: {total_collected}")
    return total_collected


if __name__ == "__main__":
    run_collector()