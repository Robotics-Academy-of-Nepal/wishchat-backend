import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import tiktoken

load_dotenv()

def initialize_client():
    """Initializes the Azure OpenAI client."""
    endpoint = os.getenv("ENDPOINT_URL")
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY")

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=subscription_key,
        api_version="2024-05-01-preview",
    )

client = initialize_client()
last_response = None

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens for a given text using the specified model's tokenizer."""
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))

def count_message_tokens(messages: list, model: str = "gpt-4") -> int:
    """Count tokens in a list of messages."""
    encoder = tiktoken.encoding_for_model(model)
    total_tokens = 0
    
    for message in messages:
        total_tokens += len(encoder.encode(message["content"]))
        total_tokens += len(encoder.encode(message["role"]))
        total_tokens += 3  # message overhead
    
    total_tokens += 3  # conversation overhead
    return total_tokens

def query_assistant(user_input,index_name,temperature=0.7,prompt = ''):
    """
    Sends a query to the Azure OpenAI service and receives a response,
    while preserving conversation context.
    """
    global last_response
    deployment = os.getenv("DEPLOYMENT_NAME")
    search_endpoint = os.getenv("SEARCH_ENDPOINT")
    search_key = os.getenv("SEARCH_KEY")
    search_index = index_name
    print("search_index: ",search_index)

    if prompt == '':
        system_prompt = {
        "role": "system",
        "content": """
            ### Role
            - Primary Function: You are an AI chatbot assisting users with inquiries primarily related to the provided topic. Your goal is to deliver helpful, friendly, and clear responses. If a question is unclear, seek clarification. If a query is beyond your knowledge, provide a polite fallback response and guide users to relevant  resources or contacts.

            ### Behavior Rules
            1. **Word Limit**: Keep responses concise, within 60 words, but ensure clarity.
            2. **Language Rules**:
            - Respond in English if the query is in English.
            - Respond in Devanagari Nepali if the query is in Devanagari Nepali or Roman Nepali, using limited English only for unavoidable terms like "JEC."
            - Avoid Roman Nepali entirely.
            3. **Fallback for Unknown Information**:
            - If specific information isn’t available, respond:
            "I do not have the exact information at the moment. Please contact the college administration for more details. The contact number is [phone number, if available]."      
            4. **Clarification of Terms**:
            - If the user mentions unclear terms like "jev," assume it might relate to "JEC" and respond accordingly. If unsure, politely ask for clarification.
            5. **Behavior Consistency**:
            - Always end with a positive note and offer to assist further.
            6. **No Data Divulge**: Never mention access to training data or how your responses are generated.
            7. **Restrictive Role Focus**: Focus on the provided topic, but strive to engage meaningfully. For unrelated queries, redirect users politely and guide them to external resources when possible.      
            8. **Links**: Always mention the link if it's provided in the training data.
            """   
        }
    else:
        system_prompt = {
            "role": "system",
             "content": prompt
        }
    
    print(system_prompt)


    messages = [
        {"role": "system", "content": system_prompt["content"]}
    ]
    
    if last_response and isinstance(last_response, str):
        print("Last_response:", last_response)
        messages.append({"role": "assistant", "content": last_response})
    
    messages.append({"role": "user", "content": user_input})

    # Count input tokens
    input_tokens = count_message_tokens(messages)
    print(temperature)

    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=messages,
            max_tokens=512,
            temperature=temperature,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False,
            extra_body={
                "data_sources": [
                    {
                        "type": "azure_search",
                        "parameters": {
                            "endpoint": f"{search_endpoint}",
                            "index_name": search_index,
                            "semantic_configuration": "default",
                            "query_type": "semantic",
                            "fields_mapping": {},
                            "in_scope": True,
                            "role_information": system_prompt["content"],
                            "filter": None,
                            "strictness": 3,
                            "top_n_documents": 5,
                            "authentication": {
                                "type": "api_key",
                                "key": f"{search_key}"
                            }
                        }
                    }
                ]
            }
        )

        assistant_response = completion.choices[0].message.content
        
        # Count output tokens
        output_tokens = count_tokens(assistant_response)
        
        # Print token usage
        print("\n=== Token Usage ===")
        print(f"Input tokens: {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        print(f"Total tokens: {input_tokens + output_tokens}")
        print("=================\n")

        last_response = assistant_response
        return assistant_response

    except Exception as e:
        return f"Error during conversation: {e}"

# Example usage
if __name__ == "__main__":
    while True:
        user_input = input("You: ")

        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Exiting conversation...")
            break

        response = query_assistant(user_input)
        
        print("Assistant:", response)
         