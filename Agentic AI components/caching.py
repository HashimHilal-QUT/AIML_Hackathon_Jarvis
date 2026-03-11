
import time 
from collections import OrderedDict
from typing import Any,Optional,Dict
import openai 


#Set up your OpenAI API key 
openai.api_key = "key"

class BaseCache:
    """
    Interface for a caching layer for LLMs and Chat Models.
    """

    def get(self,key:str) -> Optional[Any]:
        """Retreive an item from the cache by key"""
        raise NotImplementedError
    
    def set(self,key:str,value: Any) ->None:
        """Store an item in the cache with a specified key"""
        raise NotImplementedError
    
    def clear(self) -> None:
        """Clear all items from the cache"""
        raise NotImplementedError
    

class CachedOpenAIRequest:
    """Handles OpenAI API requests with an LRU cache"""

    def __init__(self,cache : BaseCache):
        """
        Initialize the CachedOpenAIRequest

        Args:
             cache (BaseCache) : The cache implementation to use
        """

        self._cache = cache

    def get_response(self,prompt:str)->str:
        """
        Get a response for the given prompt, using the cache if available
        
        Args:
         prompt(str) : The input prompt for the OpenAI model.

        Returns:
         str: The response from the OpenAI model or cache
        """

        #Check if the response is already in the cache
        cached_reponse = self.
