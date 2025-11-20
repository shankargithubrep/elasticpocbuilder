"""
Custom exceptions for Vulcan demo generation

These exceptions provide user-friendly error messages and actionable guidance
for common failure scenarios.
"""


class VulcanException(Exception):
    """Base exception for all Vulcan errors"""
    
    def __init__(self, message: str, user_message: str = None, 
                 suggestion: str = None, technical_details: str = None):
        """
        Initialize a Vulcan exception
        
        Args:
            message: Technical error message
            user_message: User-friendly error message
            suggestion: Actionable suggestion for fixing the error
            technical_details: Additional technical details for debugging
        """
        super().__init__(message)
        self.user_message = user_message or message
        self.suggestion = suggestion
        self.technical_details = technical_details
    
    def get_display_message(self) -> str:
        """Get formatted message for UI display"""
        parts = [f"**Error:** {self.user_message}"]
        
        if self.suggestion:
            parts.append(f"\n\n**💡 Suggestion:** {self.suggestion}")
        
        if self.technical_details:
            parts.append(f"\n\n<details><summary>Technical Details</summary>\n\n```\n{self.technical_details}\n```\n</details>")
        
        return "\n".join(parts)


class LLMTimeoutError(VulcanException):
    """LLM request timed out"""
    
    def __init__(self, timeout_seconds: int, prompt_length: int = None):
        message = f"LLM request timed out after {timeout_seconds} seconds"
        
        user_message = (
            f"The LLM request took too long and timed out after {timeout_seconds} seconds. "
            "This usually happens with complex prompts or when the LLM service is under heavy load."
        )
        
        suggestion = (
            "**Try these solutions:**\n"
            "1. Wait a moment and try again - the service may be temporarily busy\n"
            "2. Simplify your request by providing less detail\n"
            "3. Check your LLM proxy service status\n"
            "4. If using a proxy, verify it's properly configured and has capacity"
        )
        
        technical_details = f"Timeout: {timeout_seconds}s"
        if prompt_length:
            technical_details += f"\nPrompt length: {prompt_length:,} characters"
        
        super().__init__(message, user_message, suggestion, technical_details)


class LLMAPIError(VulcanException):
    """LLM API returned an error"""
    
    def __init__(self, status_code: int = None, error_message: str = None, provider: str = None):
        message = f"LLM API error: {error_message or 'Unknown error'}"
        
        # Check for expired key specifically
        if error_message and "expired" in error_message.lower() and "key" in error_message.lower():
            user_message = "Your LLM API key has expired."
            suggestion = (
                "**Your API key needs to be renewed:**\n"
                "1. Get a new API key from your LLM provider\n"
                "2. Update `LLM_PROXY_API_KEY` in your `.env` file\n"
                "3. Restart the application\n"
                "4. For LLM proxy services, check your admin dashboard to renew keys\n\n"
                "**Note:** Some proxy services expire keys daily for security."
            )
        elif status_code == 401:
            user_message = "Authentication failed with the LLM service."
            suggestion = (
                "**Check your credentials:**\n"
                "1. Verify your API key is correct in the `.env` file\n"
                "2. For LLM proxy: Check `LLM_PROXY_API_KEY` starts with 'sk-'\n"
                "3. For Anthropic: Check `ANTHROPIC_API_KEY` is valid\n"
                "4. For OpenAI: Check `OPENAI_API_KEY` is valid"
            )
        elif status_code == 400:
            user_message = "The LLM service rejected the request - this is usually a model name issue."
            suggestion = (
                "**Check your model configuration:**\n"
                "1. Verify the model name exists in your LLM provider\n"
                f"2. Current provider: {provider or 'Unknown'}\n"
                "3. For proxies, call `/v1/models` to see available models\n"
                "4. Check `.env.example` for correct model names"
            )
        elif status_code == 429:
            user_message = "Rate limit exceeded - too many requests to the LLM service."
            suggestion = (
                "**Wait and retry:**\n"
                "1. Wait a minute before trying again\n"
                "2. Your LLM provider has rate limits\n"
                "3. Consider upgrading your LLM service tier if this happens frequently"
            )
        elif status_code and status_code >= 500:
            user_message = "The LLM service is experiencing problems (server error)."
            suggestion = (
                "**Service issue:**\n"
                "1. The LLM provider is having technical difficulties\n"
                "2. Wait a few minutes and try again\n"
                "3. Check the service status page of your LLM provider\n"
                "4. Consider using a backup API key if available"
            )
        else:
            user_message = f"The LLM service returned an error: {error_message or 'Unknown error'}"
            suggestion = (
                "**Troubleshooting steps:**\n"
                "1. Check the technical details below\n"
                "2. Verify your LLM configuration in `.env`\n"
                "3. Try simplifying your request\n"
                "4. Check application logs for more details"
            )
        
        technical_details = f"Status: {status_code}\nProvider: {provider}\nError: {error_message}"
        
        super().__init__(message, user_message, suggestion, technical_details)


class LLMModelNotFoundError(VulcanException):
    """Requested LLM model not found"""
    
    def __init__(self, model_name: str, provider: str = None, available_models: list = None):
        message = f"Model '{model_name}' not found"
        
        user_message = f"The model '{model_name}' is not available in your LLM configuration."
        
        suggestion_parts = [
            "**Fix the model name:**",
            f"1. The model '{model_name}' doesn't exist in your LLM provider"
        ]
        
        if available_models:
            suggestion_parts.append(f"2. Available models: {', '.join(available_models[:5])}")
            if len(available_models) > 5:
                suggestion_parts.append(f"   (and {len(available_models) - 5} more)")
        else:
            suggestion_parts.append("2. Check your LLM provider's documentation for available models")
        
        suggestion_parts.extend([
            "3. Update model names in `.env` or use defaults from `.env.example`",
            "4. For LLM proxies, call `/v1/models` endpoint to list available models"
        ])
        
        suggestion = "\n".join(suggestion_parts)
        
        technical_details = f"Model: {model_name}\nProvider: {provider}"
        if available_models:
            technical_details += f"\nAvailable: {', '.join(available_models)}"
        
        super().__init__(message, user_message, suggestion, technical_details)


class ConfigurationError(VulcanException):
    """Configuration error"""
    
    def __init__(self, missing_config: str, config_type: str = "environment variable"):
        message = f"Missing configuration: {missing_config}"
        
        user_message = f"Required {config_type} '{missing_config}' is not set."
        
        if "LLM" in missing_config or "API_KEY" in missing_config:
            suggestion = (
                "**Configure LLM credentials:**\n"
                "1. Copy `.env.example` to `.env`\n"
                "2. Add your LLM credentials (proxy, Anthropic, or OpenAI)\n"
                "3. For LLM proxy: Set `LLM_PROXY_URL` and `LLM_PROXY_API_KEY`\n"
                "4. For Anthropic: Set `ANTHROPIC_API_KEY`\n"
                "5. For OpenAI: Set `OPENAI_API_KEY`\n"
                "6. Restart the application"
            )
        elif "ELASTICSEARCH" in missing_config:
            suggestion = (
                "**Configure Elasticsearch:**\n"
                "1. Copy `.env.example` to `.env`\n"
                "2. Add your Elasticsearch credentials:\n"
                "   - `ELASTICSEARCH_CLOUD_ID` and `ELASTICSEARCH_API_KEY` (for Elastic Cloud)\n"
                "   - OR `ELASTICSEARCH_HOST` and `ELASTICSEARCH_API_KEY` (for self-managed)\n"
                "3. Add Kibana URL: `ELASTICSEARCH_KIBANA_URL`\n"
                "4. Restart the application"
            )
        else:
            suggestion = (
                f"**Set {config_type}:**\n"
                "1. Check `.env.example` for required configuration\n"
                "2. Copy it to `.env` and fill in your values\n"
                "3. Restart the application"
            )
        
        technical_details = f"Missing: {missing_config}\nType: {config_type}"
        
        super().__init__(message, user_message, suggestion, technical_details)


class DataGenerationError(VulcanException):
    """Error during data generation"""
    
    def __init__(self, dataset_name: str, error_message: str):
        message = f"Failed to generate data for '{dataset_name}': {error_message}"
        
        user_message = f"Could not generate synthetic data for dataset '{dataset_name}'."
        
        suggestion = (
            "**Data generation failed:**\n"
            "1. Check the technical details below\n"
            "2. The LLM may have generated invalid code\n"
            "3. Try regenerating the demo with simpler requirements\n"
            "4. Check application logs for Python errors"
        )
        
        technical_details = f"Dataset: {dataset_name}\nError: {error_message}"
        
        super().__init__(message, user_message, suggestion, technical_details)


class IndexingError(VulcanException):
    """Error during Elasticsearch indexing"""
    
    def __init__(self, index_name: str, error_message: str):
        message = f"Failed to index data to '{index_name}': {error_message}"
        
        if "ConnectionError" in error_message or "connection refused" in error_message.lower():
            user_message = "Could not connect to Elasticsearch."
            suggestion = (
                "**Connection failed:**\n"
                "1. Check your Elasticsearch credentials in `.env`\n"
                "2. Verify your cluster is running and accessible\n"
                "3. For Elastic Cloud: Check `ELASTICSEARCH_CLOUD_ID` is correct\n"
                "4. For self-managed: Check `ELASTICSEARCH_HOST` is reachable\n"
                "5. Verify network/firewall settings"
            )
        elif "AuthenticationException" in error_message or "401" in error_message:
            user_message = "Authentication failed with Elasticsearch."
            suggestion = (
                "**Invalid credentials:**\n"
                "1. Check `ELASTICSEARCH_API_KEY` in `.env`\n"
                "2. Verify the API key has proper permissions\n"
                "3. Try regenerating the API key in your Elasticsearch deployment\n"
                "4. For Elastic Cloud, verify in deployment settings"
            )
        else:
            user_message = f"Failed to index data to Elasticsearch index '{index_name}'."
            suggestion = (
                "**Indexing failed:**\n"
                "1. Check the technical details below\n"
                "2. Verify your Elasticsearch version is compatible\n"
                "3. Check if the data format matches the mapping\n"
                "4. Review Elasticsearch logs for more details"
            )
        
        technical_details = f"Index: {index_name}\nError: {error_message}"
        
        super().__init__(message, user_message, suggestion, technical_details)


class QueryGenerationError(VulcanException):
    """Error during query generation"""
    
    def __init__(self, error_message: str, phase: str = None):
        message = f"Failed to generate queries: {error_message}"
        
        user_message = "Could not generate Elasticsearch queries for the demo."
        
        if "timeout" in error_message.lower():
            suggestion = (
                "**LLM timeout during query generation:**\n"
                "1. The query generation prompt is very large\n"
                "2. Wait a moment and try again\n"
                "3. Try simplifying your use case or reducing the number of datasets\n"
                "4. Check your LLM service status"
            )
        elif "invalid" in error_message.lower() or "syntax" in error_message.lower():
            suggestion = (
                "**Invalid query code generated:**\n"
                "1. The LLM generated invalid Python code\n"
                "2. Try regenerating the demo\n"
                "3. Consider simplifying your requirements\n"
                "4. Check the technical details for specific syntax errors"
            )
        else:
            suggestion = (
                "**Query generation failed:**\n"
                "1. Review the technical details below\n"
                "2. Try regenerating with simpler requirements\n"
                "3. Check application logs for more context\n"
                "4. Verify your LLM service is working correctly"
            )
        
        technical_details = f"Error: {error_message}"
        if phase:
            technical_details = f"Phase: {phase}\n{technical_details}"
        
        super().__init__(message, user_message, suggestion, technical_details)

