import os
from dotenv import load_dotenv
from llamaapi import LlamaAPI

load_dotenv()

llama_api_key = os.getenv('LLAMA_API_KEY')
gpt_api_key = os.getenv('GPT_API_KEY')

llama = LlamaAPI(llama_api_key)

if not llama_api_key or not gpt_api_key:
    raise ValueError("API keys are not set in the environment variables")

from openai import OpenAI

client = OpenAI(api_key=gpt_api_key)

def get_current_llm():
    return current_llm

def set_llm(model_name):
    global current_llm
    if model_name in ["gpt-4o-mini", "llama3"]:
        current_llm = model_name
    else:
        raise ValueError("Invalid model name. Choose 'gpt-4o-mini' or 'llama3'.")

current_llm = "gpt-4o-mini" 

def call_llm(messages):
    if get_current_llm() == "gpt-4o-mini":
        print("using gpt")
        response = ""
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="")
                response += chunk.choices[0].delta.content
    elif get_current_llm() == "llama3":
        print("using llama3")
        api_request_json = {
            "model": "llama3-70b",
            "messages": messages
        }
        response = llama.run(api_request_json)
        response = response.json()['choices'][0]['message']['content']
    else:
        raise ValueError("Invalid LLM configuration.")
    
    return response.strip().strip('```').strip('sql').strip('```').strip().replace('\n', ' ')