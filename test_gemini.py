import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found."
    )

print("API key found.")
print("Key prefix:", api_key[:8])
print("Key length:", len(api_key))


client = genai.Client(
    api_key=api_key
)


response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Reply with exactly: Gemini connection successful"
)


print("\nGemini response:")
print(response.text)