"""
Summarizer module using Groq API for email summarization.
"""

# import requests

from groq import Groq


def summarize_with_groq(text, groq_api_key, max_bullets=3):
    """
    Summarize text using Groq API (OpenAI-compatible chat completion).
    
    Args:
        text: Text content to summarize
        groq_api_key: Groq API key
        max_bullets: Maximum number of bullet points in summary
    
    Returns:
        Summary string from Groq API
    """
    # Build prompt
    system = "You are a concise summarizer. Extract the most important points from the email and present them as numbered bullets (max {}), and one-line action items if present.".format(max_bullets)
    user = text[:30000]  # truncate if too long
    client = Groq(api_key=groq_api_key)
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.2,
        max_completion_tokens=512,
        top_p=1,
        reasoning_effort="low",
    )

    summary = completion.choices[0].message.content
    return summary
    # payload = {
    #     "model": "compound-beta",  # change model if you want; compound-beta or mixtral variants are common
    #     "messages": [
    #         {"role": "system", "content": system},
    #         {"role": "user", "content": user}
    #     ],
    #     "max_tokens": 512,
    #     "temperature": 0.2
    #     reasoning_effort="low",
    # }

    # headers = {
    #     "Authorization": f"Bearer {groq_api_key}",
    #     "Content-Type": "application/json"
    # }
    # # Groq exposes an OpenAI-compatible endpoint
    # url = "https://api.groq.com/openai/v1/chat/completions"

    # r = requests.post(url, json=payload, headers=headers, timeout=60)
    # r.raise_for_status()
    # resp = r.json()

    # # Compatibility: take the first choice's message
    # try:
    #     return resp['choices'][0]['message']['content'].strip()
    # except Exception:
    #     # fallback to full text
    #     return str(resp)

# summary = summarize_with_groq("Finding Your Personal Chat ID\nOpen the Telegram app on your Android device.",
#                                "grroq_api_key_here", 
#                                 3) 
# print(summary)