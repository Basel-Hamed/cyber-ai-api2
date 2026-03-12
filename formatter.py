def format_answer(text, mode="short"):

    if not text:
        return "No information found."

    if mode == "short":
        text = text[:500]

    else:
        text = text[:1500]

    answer = f"""
Topic Explanation:

{text}

Security Tips:
• Always validate input
• Use prepared statements
• Keep software updated
"""

    return answer
