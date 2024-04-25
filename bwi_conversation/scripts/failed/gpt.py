import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key="sk-proj-98CEKi821xDabqz4Lmi1T3BlbkFJWLZVBqJ15e7eqBxCwZCR",
)

generated_response = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Greet the person you just met.",
        }
    ],
    model="gpt-3.5-turbo",
)

response = generated_response.choices[0].message.content

print(response)