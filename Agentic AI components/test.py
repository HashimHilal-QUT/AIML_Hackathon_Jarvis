import time
from collections import OrderedDict
from typing import Any, Optional, Dict
import openai  # OpenAI Python SDK

# Set up OpenAI API key (replace with your actual API key)
openai.api_key = "your-openai-api-key"

class BaseCache:
    """Interface for a caching layer for LLMs and Chat models."""
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve an item from the cache by key."""
        raise NotImplementedError
    
    def set(self, key: str, value: Any) -> None:
        """Store an item in the cache with a specific key."""
        raise NotImplementedError
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        raise NotImplementedError

class LRUCache(BaseCache):
    """LRU (Least Recently Used) cache that stores things in memory."""
    
    def __init__(self, maxsize: int):
        """
        Initialize the LRU cache.
        
        Args:
            maxsize (int): Maximum number of items to store in the cache.
        """
        if maxsize <= 0:
            raise ValueError("maxsize must be a positive integer")
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._maxsize = maxsize
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve an item from the cache by key."""
        if key not in self._cache:
            return None
        # Move the accessed item to the end to mark it as recently used
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Store an item in the cache with a specific key."""
        if key in self._cache:
            # Update the value and move it to the end to mark it as recently used
            self._cache.move_to_end(key)
        self._cache[key] = value
        # If the cache exceeds maxsize, evict the least recently used item
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)  # Remove the first item (LRU)
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        self._cache.clear()

class CachedOpenAIRequest:
    """Handles OpenAI API requests with an LRU cache."""
    
    def __init__(self, cache: BaseCache):
        """
        Initialize the CachedOpenAIRequest.
        
        Args:
            cache (BaseCache): The cache implementation to use.
        """
        self._cache = cache
    
    def get_response(self, prompt: str) -> str:
        """
        Get a response for the given prompt, using the cache if available.
        
        Args:
            prompt (str): The input prompt for the OpenAI model.
        
        Returns:
            str: The response from the OpenAI model or cache.
        """
        # Check if the response is already in the cache
        cached_response = self._cache.get(prompt)
        if cached_response is not None:
            print(f"Cache hit for prompt: {prompt}")
            return cached_response
        
        # If not in cache, make an API request
        print(f"Cache miss for prompt: {prompt}. Making API request...")
        response = self._make_openai_api_request(prompt)
        
        # Store the response in the cache
        self._cache.set(prompt, response)
        return response
    
    def _make_openai_api_request(self, prompt: str) -> str:
        """
        Make an actual API request to the OpenAI model.
        
        Args:
            prompt (str): The input prompt for the OpenAI model.
        
        Returns:
            str: The response from the OpenAI model.
        """
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",  # Use the appropriate OpenAI model
                prompt=prompt,
                max_tokens=100,  # Limit the response length
                n=1,  # Number of responses to generate
                stop=None,  # Stop sequence (if any)
                temperature=0.7,  # Controls randomness
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"Error: {str(e)}"

# Example usage:
if __name__ == "__main__":
    # Create an LRU cache with a maximum size of 5
    cache = LRUCache(maxsize=5)
    
    # Initialize the CachedOpenAIRequest with the cache
    cached_openai = CachedOpenAIRequest(cache)
    
    # Simulate a real-world customer support chatbot
    prompts = [
        "What is your refund policy?",
        "How do I reset my password?",
        "What are your business hours?",
        "How do I contact customer support?",
        "What is your refund policy?",  # Repeated prompt
        "Do you offer international shipping?",
        "How do I reset my password?",  # Repeated prompt
        "What payment methods do you accept?",
        "What is your refund policy?",  # Repeated prompt
    ]
    
    for prompt in prompts:
        start_time = time.time()
        response = cached_openai.get_response(prompt)
        elapsed_time = time.time() - start_time
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")
        print(f"Time taken: {elapsed_time:.2f} seconds")
        print("---")