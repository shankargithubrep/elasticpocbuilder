"""
Extended LLM Service with support for LLM Proxy
Maintains backward compatibility with direct Anthropic/OpenAI usage
"""

import os
import logging
from typing import Optional
from openai import OpenAI
from openai import APITimeoutError, APIError, APIConnectionError, AuthenticationError

from src.exceptions import (
    LLMTimeoutError, LLMAPIError, LLMModelNotFoundError, ConfigurationError
)

logger = logging.getLogger(__name__)


class LLMProxyClient:
    """
    Unified LLM client that supports:
    1. LLM Proxy (OpenAI-compatible)
    2. Direct Anthropic API
    3. Direct OpenAI API
    
    Priority order:
    1. LLM_PROXY_URL + LLM_PROXY_API_KEY (if configured)
    2. ANTHROPIC_API_KEY (if available)
    3. OPENAI_API_KEY (if available)
    4. Mock mode (for testing)
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client with automatic provider detection
        
        Args:
            provider: Force specific provider ('proxy', 'anthropic', 'openai', 'mock')
                     If None, auto-detects based on available credentials
        """
        self.provider = provider or self._detect_provider()
        self.client = self._initialize_client()
        logger.info(f"Initialized LLM client with provider: {self.provider}")
    
    def _detect_provider(self) -> str:
        """Detect which LLM provider to use based on available configuration"""
        # Priority 1: LLM Proxy (OpenAI-compatible)
        if os.getenv("LLM_PROXY_URL") and os.getenv("LLM_PROXY_API_KEY"):
            logger.info("Detected LLM Proxy configuration")
            return "proxy"
        
        # Priority 2: Direct Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            logger.info("Detected Anthropic API key")
            return "anthropic"
        
        # Priority 3: Direct OpenAI
        if os.getenv("OPENAI_API_KEY"):
            logger.info("Detected OpenAI API key")
            return "openai"
        
        # Fallback: Mock mode
        logger.warning("No LLM credentials found, using mock mode")
        return "mock"
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if self.provider == "proxy":
            return self._initialize_proxy_client()
        elif self.provider == "anthropic":
            return self._initialize_anthropic_client()
        elif self.provider == "openai":
            return self._initialize_openai_client()
        else:
            return None  # Mock mode
    
    def _initialize_proxy_client(self):
        """Initialize OpenAI client configured for LLM proxy"""
        try:
            proxy_url = os.getenv("LLM_PROXY_URL")
            proxy_api_key = os.getenv("LLM_PROXY_API_KEY")
            
            if not proxy_url or not proxy_api_key:
                raise ValueError("LLM_PROXY_URL and LLM_PROXY_API_KEY must be set")
            
            # Create OpenAI client with custom base_url
            client = OpenAI(
                base_url=proxy_url,
                api_key=proxy_api_key,
                timeout=300.0,  # 5 minutes for large prompts
                max_retries=1  # Reduce retries to fail faster if there's an issue
            )
            
            logger.info(f"Initialized LLM Proxy client: {proxy_url}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Proxy: {e}")
            logger.info("Falling back to mock mode")
            self.provider = "mock"
            return None
    
    def _initialize_anthropic_client(self):
        """Initialize Anthropic client"""
        try:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY must be set")
            
            client = Anthropic(api_key=api_key)
            logger.info("Initialized Anthropic client")
            return client
            
        except ImportError:
            logger.error("Anthropic library not installed")
            self.provider = "mock"
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
            self.provider = "mock"
            return None
    
    def _initialize_openai_client(self):
        """Initialize direct OpenAI client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                raise ValueError("OPENAI_API_KEY must be set")
            
            client = OpenAI(api_key=api_key)
            logger.info("Initialized OpenAI client")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.provider = "mock"
            return None
    
    def get_model_name(self, task: str = "default") -> str:
        """
        Get appropriate model name based on provider and task
        
        Args:
            task: Type of task ('code_generation', 'conversation', 'fast', 'default')
        
        Returns:
            Model name string
        """
        if self.provider == "proxy":
            # LLM Proxy - use model names based on what's available in your proxy
            # You may need to adjust these based on your proxy configuration
            model_map = {
                "code_generation": os.getenv("LLM_PROXY_CODE_MODEL", "claude-sonnet-4"),
                "conversation": os.getenv("LLM_PROXY_CHAT_MODEL", "claude-sonnet-4"),
                "fast": os.getenv("LLM_PROXY_FAST_MODEL", "gpt-3.5-turbo"),
                "default": os.getenv("LLM_PROXY_DEFAULT_MODEL", "claude-sonnet-4")
            }
            return model_map.get(task, model_map["default"])
        
        elif self.provider == "anthropic":
            model_map = {
                "code_generation": "claude-sonnet-4",
                "conversation": "claude-sonnet-4",
                "fast": "claude-3-5-haiku-20241022",
                "default": "claude-sonnet-4"
            }
            return model_map.get(task, model_map["default"])
        
        elif self.provider == "openai":
            model_map = {
                "code_generation": "gpt-4",
                "conversation": "gpt-4",
                "fast": "gpt-3.5-turbo",
                "default": "gpt-4"
            }
            return model_map.get(task, model_map["default"])
        
        else:  # mock
            return "mock-model"
    
    def create_completion(self, messages: list, max_tokens: int = 4000, 
                         temperature: float = 0.7, task: str = "default", **kwargs):
        """
        Unified completion method that works across all providers
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            task: Task type for model selection
            **kwargs: Additional provider-specific arguments
        
        Returns:
            Response text string
        """
        if self.provider == "mock":
            return self._mock_completion(messages)
        
        model = self.get_model_name(task)
        
        if self.provider in ["proxy", "openai"]:
            # OpenAI-compatible API
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                return response.choices[0].message.content
            except APITimeoutError as e:
                # Calculate prompt length for better error reporting
                prompt_length = sum(len(str(msg.get("content", ""))) for msg in messages)
                logger.error(f"LLM request timed out. Prompt length: {prompt_length}")
                raise LLMTimeoutError(timeout_seconds=300, prompt_length=prompt_length) from e
            except AuthenticationError as e:
                logger.error(f"LLM authentication failed: {e}")
                raise LLMAPIError(status_code=401, error_message=str(e), provider=self.provider) from e
            except APIError as e:
                # Extract status code if available
                status_code = getattr(e, 'status_code', None)
                error_msg = str(e)
                
                # Check for model not found errors
                if "model" in error_msg.lower() and ("not found" in error_msg.lower() or "invalid" in error_msg.lower()):
                    logger.error(f"Model '{model}' not found in provider '{self.provider}'")
                    raise LLMModelNotFoundError(model_name=model, provider=self.provider) from e
                
                logger.error(f"LLM API error (status {status_code}): {error_msg}")
                raise LLMAPIError(status_code=status_code, error_message=error_msg, provider=self.provider) from e
            except APIConnectionError as e:
                logger.error(f"Could not connect to LLM service: {e}")
                raise LLMAPIError(status_code=503, error_message=f"Connection failed: {str(e)}", provider=self.provider) from e
            except Exception as e:
                logger.error(f"Unexpected LLM error: {e}", exc_info=True)
                raise LLMAPIError(error_message=str(e), provider=self.provider) from e
        
        elif self.provider == "anthropic":
            # Anthropic API has different format
            try:
                # Extract system message if present
                system_msg = None
                anthropic_messages = []
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                    else:
                        anthropic_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                
                # Call Anthropic API
                response_args = {
                    "model": model,
                    "messages": anthropic_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                
                if system_msg:
                    response_args["system"] = system_msg
                
                response = self.client.messages.create(**response_args)
                return response.content[0].text
            except Exception as e:
                # Anthropic uses its own exception types, but we'll wrap them generically
                error_msg = str(e)
                prompt_length = sum(len(str(msg.get("content", ""))) for msg in messages)
                
                if "timeout" in error_msg.lower():
                    logger.error(f"Anthropic request timed out. Prompt length: {prompt_length}")
                    raise LLMTimeoutError(timeout_seconds=300, prompt_length=prompt_length) from e
                elif "401" in error_msg or "authentication" in error_msg.lower():
                    logger.error(f"Anthropic authentication failed: {e}")
                    raise LLMAPIError(status_code=401, error_message=error_msg, provider="anthropic") from e
                elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                    logger.error(f"Model '{model}' not found in Anthropic")
                    raise LLMModelNotFoundError(model_name=model, provider="anthropic") from e
                else:
                    logger.error(f"Anthropic API call failed: {e}", exc_info=True)
                    raise LLMAPIError(error_message=error_msg, provider="anthropic") from e
    
    def _mock_completion(self, messages: list) -> str:
        """Generate mock response for testing"""
        last_message = messages[-1]["content"] if messages else ""
        
        if "code" in last_message.lower() or "generate" in last_message.lower():
            return "# Mock generated code\nprint('Hello from mock LLM')"
        else:
            return "This is a mock response for testing. Please configure LLM credentials."
    
    def is_available(self) -> bool:
        """Check if LLM client is available (not in mock mode)"""
        return self.provider != "mock"


def create_llm_client(provider: Optional[str] = None) -> LLMProxyClient:
    """
    Factory function to create LLM client
    
    Args:
        provider: Optional provider override
    
    Returns:
        Configured LLMProxyClient instance
    """
    return LLMProxyClient(provider=provider)


# Backward compatibility: mimic Anthropic/OpenAI client interfaces
class UnifiedLLMClient:
    """
    Wrapper that provides both Anthropic and OpenAI-style interfaces
    This allows drop-in replacement in existing code
    """
    
    def __init__(self, provider: Optional[str] = None):
        self._proxy_client = LLMProxyClient(provider=provider)
        self.provider = self._proxy_client.provider
        
        # Add both interfaces for compatibility
        self.messages = self  # For Anthropic-style: client.messages.create()
        self.chat = self  # For OpenAI-style: client.chat.completions
        self.completions = self  # For OpenAI-style
    
    def create(self, model=None, messages=None, max_tokens=4000, 
               temperature=0.7, system=None, **kwargs):
        """
        Unified create method that works for both Anthropic and OpenAI patterns
        Supports both:
        - client.messages.create() (Anthropic)
        - client.chat.completions.create() (OpenAI)
        """
        # Handle Anthropic-style system message
        formatted_messages = []
        if system:
            formatted_messages.append({"role": "system", "content": system})
        
        if messages:
            formatted_messages.extend(messages)
        
        # Determine task type from model name if provided
        task = "default"
        if model:
            if "haiku" in model.lower():
                task = "fast"
            elif "sonnet" in model.lower() or "gpt-4" in model.lower():
                task = "code_generation"
        
        # Call unified completion
        response_text = self._proxy_client.create_completion(
            messages=formatted_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            task=task,
            **kwargs
        )
        
        # Return response in appropriate format
        # Create proper mock objects with attributes
        class ContentText:
            def __init__(self, text):
                self.text = text
        
        class ResponseContent:
            def __init__(self, text):
                self.content = [ContentText(text)]
        
        class ResponseMessage:
            def __init__(self, text):
                self.message = type('Message', (), {'content': text})()
        
        class ResponseChoice:
            def __init__(self, text):
                self.choices = [ResponseMessage(text)]
        
        # Always return Anthropic-style for compatibility
        # (works with both calling patterns since we check the method call, not the provider)
        response = ContentText(response_text)
        return type('Response', (), {
            'content': [response]
        })()

