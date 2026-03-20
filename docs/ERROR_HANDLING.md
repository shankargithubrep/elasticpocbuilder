# Error Handling System

This document describes the comprehensive error handling system implemented in Elastic Demo Builder to provide user-friendly error messages and actionable guidance when things go wrong.

## Overview

The error handling system consists of:

1. **Custom Exception Classes** (`src/exceptions.py`) - Structured errors with user-friendly messages
2. **Error Display Utilities** (`src/ui/error_display.py`) - Consistent error formatting in the UI
3. **Enhanced Service Error Handling** - Services wrap errors with context and suggestions

## Custom Exception Classes

### Base Exception: `VulcanException`

All custom exceptions inherit from `VulcanException` and include:

- `user_message`: User-friendly error description
- `suggestion`: Actionable steps to resolve the issue
- `technical_details`: Additional debugging information
- `get_display_message()`: Formatted message for UI display

### Exception Types

#### `LLMTimeoutError`
**When:** LLM requests timeout (typically after 300 seconds)

**User Message Example:**
```
The LLM request took too long and timed out after 300 seconds. 
This usually happens with complex prompts or when the LLM service is under heavy load.

💡 Suggestion:
1. Wait a moment and try again - the service may be temporarily busy
2. Simplify your request by providing less detail
3. Check your LLM proxy service status
4. If using a proxy, verify it's properly configured and has capacity
```

#### `LLMAPIError`
**When:** LLM API returns errors (auth, rate limits, server errors)

**Handles:**
- 401 Authentication failures → Check API keys
- 400 Bad requests → Check model names
- 429 Rate limits → Wait and retry
- 500+ Server errors → Service is down

#### `LLMModelNotFoundError`
**When:** Requested model doesn't exist in the provider

**User Message Example:**
```
The model 'claude-sonnet-4-5-20250929' is not available in your LLM configuration.

💡 Suggestion:
1. The model 'claude-sonnet-4-5-20250929' doesn't exist in your LLM provider
2. Available models: claude-sonnet-4, gpt-3.5-turbo, gpt-4
3. Update model names in .env or use defaults from .env.example
4. For LLM proxies, call /v1/models endpoint to list available models
```

#### `ConfigurationError`
**When:** Required environment variables are missing

**Detects:**
- Missing LLM credentials
- Missing Elasticsearch configuration
- Other required settings

#### `DataGenerationError`
**When:** Synthetic data generation fails

#### `IndexingError`
**When:** Elasticsearch indexing fails

**Handles:**
- Connection failures
- Authentication errors
- Mapping issues

#### `QueryGenerationError`
**When:** Query module generation fails

## Error Display Utilities

Located in `src/ui/error_display.py`, these functions provide consistent error formatting:

### `display_error(error, title, show_technical_details=True)`

Displays an error with:
- Clear title (🚨 prefix)
- User message and suggestions
- Optional expandable technical details
- Automatic logging

**Usage:**
```python
from src.ui.error_display import display_error

try:
    # Some operation
    result = generate_demo(config)
except Exception as e:
    display_error(e, title="Demo Generation Failed")
```

### Other Helper Functions

- `display_warning(message, title)` - Warning messages with ⚠️
- `display_success(message, title)` - Success messages with ✅
- `display_info(message, title)` - Info messages with ℹ️

## Service-Level Error Handling

### LLM Proxy Service (`src/services/llm_proxy_service.py`)

The LLM proxy service catches specific exceptions and wraps them:

```python
try:
    response = self.client.chat.completions.create(...)
    return response.choices[0].message.content
except APITimeoutError as e:
    # Calculate prompt length for context
    prompt_length = sum(len(str(msg.get("content", ""))) for msg in messages)
    raise LLMTimeoutError(timeout_seconds=300, prompt_length=prompt_length) from e
except AuthenticationError as e:
    raise LLMAPIError(status_code=401, error_message=str(e), provider=self.provider) from e
# ... more specific handlers
```

### Orchestrator (`src/framework/orchestrator.py`)

The orchestrator wraps phase-specific errors:

```python
try:
    self.module_generator.generate_query_module_with_profile(...)
except VulcanException:
    # Re-raise custom exceptions as-is
    raise
except Exception as e:
    # Wrap generic errors with context
    raise QueryGenerationError(error_message=str(e), phase="query_generation") from e
```

## UI Integration

### Create Demo View (`src/ui/views/create_demo.py`)

```python
from src.ui.error_display import display_error
from src.exceptions import VulcanException

try:
    results = orchestrator.generate_new_demo_with_strategy(...)
    # Display success
except Exception as e:
    # Display user-friendly error
    display_error(e, title="Demo Generation Failed")
    
    # Add to chat history
    if isinstance(e, VulcanException):
        error_msg = e.user_message
    else:
        error_msg = f"Error generating demo: {str(e)}"
    
    st.session_state.messages.append({"role": "assistant", "content": error_msg})
```

### Message Processor (`src/ui/message_processor.py`)

Gracefully falls back to basic extraction when LLM errors occur:

```python
try:
    # LLM-powered extraction
    response = client.messages.create(...)
except VulcanException as e:
    # Show user-friendly error
    display_error(e, title="Message Processing Issue", show_technical_details=False)
    st.info("💡 Falling back to basic text extraction...")
    return _fallback_processing(message)
```

## Benefits

### For End Users
- Clear, non-technical error messages
- Actionable suggestions for fixing issues
- No scary stack traces (hidden in expandable sections)
- Guided troubleshooting steps

### For Developers
- Technical details available in expanders
- All errors logged with full context
- Consistent error display across the app
- Easy to add new error types

### For Support
- Users can share clear error messages
- Common issues have standard resolutions
- Technical details available when needed
- Error patterns easy to identify in logs

## Adding New Error Types

To add a new error type:

1. **Create exception class in `src/exceptions.py`:**

```python
class MyCustomError(VulcanException):
    """Description of when this occurs"""
    
    def __init__(self, context_info: str):
        message = f"Technical error message"
        user_message = "User-friendly description of what went wrong"
        suggestion = """
        **Fix this by:**
        1. Step one
        2. Step two
        3. Step three
        """
        technical_details = f"Context: {context_info}"
        
        super().__init__(message, user_message, suggestion, technical_details)
```

2. **Raise it where appropriate:**

```python
from src.exceptions import MyCustomError

try:
    # Some operation
    pass
except SomeSpecificError as e:
    raise MyCustomError(context_info=str(e)) from e
```

3. **Display in UI:**

```python
from src.ui.error_display import display_error

try:
    # Operation that might raise MyCustomError
    pass
except Exception as e:
    display_error(e, title="Operation Failed")
```

## Testing Error Display

To test error display during development:

```python
from src.exceptions import LLMTimeoutError
from src.ui.error_display import display_error

# Simulate a timeout
error = LLMTimeoutError(timeout_seconds=300, prompt_length=50000)
display_error(error, title="Test Error")
```

## Common Error Scenarios

### Scenario 1: LLM Proxy Timeout
**Error:** `LLMTimeoutError`  
**Common Cause:** Large prompt + slow model  
**User Guidance:** Wait and retry, or simplify request  

### Scenario 2: Invalid API Key
**Error:** `LLMAPIError` (401)  
**Common Cause:** Incorrect API key in `.env`  
**User Guidance:** Check API key format, verify credentials  

### Scenario 3: Model Not Found
**Error:** `LLMModelNotFoundError`  
**Common Cause:** Using old model name or model not in proxy  
**User Guidance:** List available models, update .env  

### Scenario 4: Elasticsearch Connection Failed
**Error:** `IndexingError`  
**Common Cause:** Wrong credentials or cluster offline  
**User Guidance:** Verify credentials, check cluster status  

## Future Enhancements

Potential improvements to the error handling system:

1. **Error Recovery Actions** - Automatic retry with exponential backoff
2. **Error Analytics** - Track common error patterns
3. **Contextual Help Links** - Link to relevant documentation
4. **Error Grouping** - Group similar errors in UI
5. **Notification System** - Alert for critical errors
6. **Error Export** - Export error reports for support tickets

