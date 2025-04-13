import sqlite3
import openai
import json
import time
import re

# Set your OpenAI API key
openai.api_key = "OPENAI_API_KEY"  # Replace with your actual OpenAI API key


def extract_json_from_text(text):
    """Attempt to extract JSON from text even if it's malformed or has extra content"""
    # Try to find JSON-like content between curly braces
    json_match = re.search(r'\{.+\}', text, re.DOTALL)
    if json_match:
        try:
            # Clean up common issues with JSON from LLMs
            potential_json = json_match.group(0)
            # Fix trailing commas before closing braces
            potential_json = re.sub(r',\s*}', '}', potential_json)
            # Fix unquoted property names
            potential_json = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', potential_json)
            return json.loads(potential_json)
        except:
            pass
    return None


def analyze_feedback(max_retries=2):
    """Analyze feedback with improved prompting and error handling"""
    # Connect to database
    conn = sqlite3.connect('feedback.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get unanalyzed feedback
    cursor.execute("""
        SELECT rf.post_id, rf.title, rf.content 
        FROM raw_feedback rf
        LEFT JOIN analyzed_feedback af ON rf.post_id = af.source_id
        WHERE af.source_id IS NULL
    """)

    unanalyzed_posts = cursor.fetchall()
    print(f"Found {len(unanalyzed_posts)} posts to analyze")

    for post in unanalyzed_posts:
        print(f"Analyzing post: {post['title'][:40]}...")

        # Prepare the content to analyze
        content_to_analyze = f"Title: {post['title']}\n\nContent: {post['content']}"

        # Enhanced prompt with examples and precise instructions
        system_prompt = """
You are an expert product feedback analyzer. Your task is to analyze the product feedback and return ONLY valid JSON in the exact format shown below:

{
  "theme": "string representing the primary category/theme of feedback (e.g., 'UI/UX', 'Performance', 'Feature Request', 'Pricing', 'Integration')",
  "sentiment": "one of exactly these three values: positive, negative, or neutral",
  "summary": "a concise 1-2 sentence summary of the key points"
}

Rules:
1. Return ONLY the JSON. No other text, explanations, or markdown formatting.
2. Ensure valid JSON with proper quotes around all keys and values.
3. Always include all three fields (theme, sentiment, summary).
4. For sentiment, use ONLY: positive, negative, or neutral.
5. Keep summaries concise but informative.
"""

        success = False
        retries = 0

        while not success and retries <= max_retries:
            try:
                # Call OpenAI API with enhanced system prompt
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content_to_analyze}
                    ],
                    temperature=0.3  # Lower temperature for more consistent, structured output
                )

                # Extract the response content
                result_text = response.choices[0].message.content

                # Try to parse JSON directly
                try:
                    result = json.loads(result_text)
                    success = True
                except json.JSONDecodeError:
                    # If direct parsing fails, try to extract JSON from text
                    result = extract_json_from_text(result_text)
                    if result:
                        success = True
                    else:
                        print(f"  Retry {retries + 1}: JSON parsing failed")
                        retries += 1
                        time.sleep(1)  # Wait before retry

                # If we have results, save them
                if success:
                    # Validate required fields are present
                    if all(k in result for k in ["theme", "sentiment", "summary"]):
                        # Normalize sentiment value
                        sentiment = result["sentiment"].lower()
                        if sentiment not in ["positive", "negative", "neutral"]:
                            sentiment = "neutral"  # Default if invalid

                        # Insert into analyzed_feedback table
                        cursor.execute(
                            "INSERT INTO analyzed_feedback VALUES (?, ?, ?, ?, ?)",
                            (
                                post['post_id'],
                                result.get('theme', 'Other'),
                                sentiment,
                                result.get('summary', 'No summary provided'),
                                post['post_id']
                            )
                        )
                        conn.commit()
                        print("  Analysis saved!")
                    else:
                        print("  Error: Missing required fields in JSON")
                        if retries < max_retries:
                            retries += 1
                        else:
                            # Use defaults if all retries failed
                            cursor.execute(
                                "INSERT INTO analyzed_feedback VALUES (?, ?, ?, ?, ?)",
                                (
                                    post['post_id'],
                                    "Other",
                                    "neutral",
                                    "Unable to analyze this feedback automatically.",
                                    post['post_id']
                                )
                            )
                            conn.commit()
                            print("  Saved with default values after failed retries")

            except Exception as e:
                print(f"  Error calling OpenAI API: {str(e)}")
                retries += 1
                if retries > max_retries:
                    # Use defaults if all retries failed
                    try:
                        cursor.execute(
                            "INSERT INTO analyzed_feedback VALUES (?, ?, ?, ?, ?)",
                            (
                                post['post_id'],
                                "Other",
                                "neutral",
                                "Unable to analyze this feedback due to API error.",
                                post['post_id']
                            )
                        )
                        conn.commit()
                        print("  Saved with default values after API error")
                    except Exception as db_error:
                        print(f"  Database error: {str(db_error)}")

            # Be nice to the API rate limits
            time.sleep(1)

    conn.close()
    print("Analysis complete!")


if __name__ == "__main__":
    analyze_feedback()
