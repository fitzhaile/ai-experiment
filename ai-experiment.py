from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

response = client.responses.create(
    model="gpt-4o-mini",
    input="What’s the latest news on Savannah port container volumes? Cite sources.",
    tools=[{"type": "web_search"}],
    tool_choice="auto",
)
print(response.output_text)
