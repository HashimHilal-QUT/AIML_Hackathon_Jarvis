import requests
import json
import os

def perform_research(query):
    """
    Performs a query using the Perplexity API.
    """
    # It's recommended to set the API key as an environment variable.
    # For example, in your terminal: export PERPLEXITY_API_KEY='your_real_api_key'
    api_key = os.environ.get("PERPLEXITY_API_KEY", "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")
    
    if api_key == "pplx-YOUR-KEY-HERE":
        print("Warning: Using a placeholder API key.")
        print("Please set the PERPLEXITY_API_KEY environment variable or edit the script.")

    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar",  # A capable and cost-effective model
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query}
        ],
        "max_tokens": 150,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # This will raise an exception for HTTP error codes (4xx or 5xx)
        response.raise_for_status()
        
        result = response.json()
        print("API call successful!")
        print("Response:", json.dumps(result, indent=2))
        return result

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Status Code: {http_err.response.status_code}")
        # The API might return a JSON object with error details
        try:
            error_details = http_err.response.json()
            print("Error details:", json.dumps(error_details, indent=2))
        except json.JSONDecodeError:
            # If the response isn't JSON, print the raw text
            print(f"Error details (raw): {http_err.response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API call: {e}")
        
    return None

if __name__ == "__main__":
    test_query = "What are the latest advancements in AI-powered drug discovery?"
    
    print(f"Running query: '{test_query}'")
    research_result = perform_research(test_query)
    
    if research_result and "choices" in research_result and research_result["choices"]:
        print("\\n--- Query Result ---")
        content = research_result["choices"][0]["message"]["content"]
        print(content)
    else:
        print("\\n--- No result obtained ---")
        print("This is likely because the API key is invalid or has no credits.")
        print("Please check your key and account balance on perplexity.ai.") 