import os
import time
from reddit_collector import run_collector
from ai_analyzer import analyze_feedback


def main():
    print("=" * 50)
    print("Welcome to Pendo Listen Simulator!")
    print("=" * 50)
    print("\nThis tool collects product feedback from Reddit, analyzes it with AI,")
    print("and provides insights similar to Pendo Listen.\n")

    # Run the collector to get user input and collect data
    posts_collected = run_collector()

    # If we collected new posts, analyze them
    if posts_collected > 0:
        print("\nAnalyzing the collected feedback with AI...")
        analyze_feedback()

        print("\nAnalysis complete! Starting dashboard...")
        time.sleep(2)

        # Start the Streamlit dashboard
        os.system("streamlit run app.py")
    else:
        print("\nNo new posts were collected. Try different keywords or subreddits.")
        choice = input("Would you like to try again? (y/n): ")
        if choice.lower() == 'y':
            main()
        else:
            print("Thank you for using Pendo Listen Simulator!")


if __name__ == "__main__":
    main()