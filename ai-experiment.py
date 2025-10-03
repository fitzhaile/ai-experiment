# Standalone sample script to test your OpenAI setup from the CLI.
#
# - Loads environment variables from `.env` (OPENAI_API_KEY)
# - Creates an OpenAI client
# - Sends a simple request and prints the result
#
# This file is NOT used by the Flask server. It's safe to run directly:
#   source .venv/bin/activate
#   python ai-experiment.py
#
# If you want to try a different model, export OPENAI_MODEL first or edit
# the string below. The Flask app uses a fallback strategy separately.

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

response = client.responses.create(
  model="gpt-5-mini",
  input="write a haiku about ai",
  store=True,
)

print(response.output_text)
