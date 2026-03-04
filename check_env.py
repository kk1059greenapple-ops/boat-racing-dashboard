import os
from dotenv import load_dotenv

print("Before load_dotenv:")
print("GEMINI_API_KEY =", repr(os.getenv("GEMINI_API_KEY")))

load_dotenv(override=True)

print("After load_dotenv(override=True):")
print("GEMINI_API_KEY =", repr(os.getenv("GEMINI_API_KEY")))
