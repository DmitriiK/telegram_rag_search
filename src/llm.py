from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

def llm(prompt, model='gpt-4o-mini'):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
