"""
Message processing and conversation flow management

Handles intelligent context extraction, suggestions generation,
and conversation flow for demo creation.
"""

import streamlit as st
import json
import logging
import os
from typing import Dict

from .context_extractor import SmartContextExtractor

logger = logging.getLogger(__name__)


def generate_suggestions() -> str:
    """Generate AI suggestions for missing context fields"""
    from src.services.context_tracker import ContextTracker
    import anthropic

    context = st.session_state.demo_context
    tracker = ContextTracker()
    progress, missing = tracker.calculate_progress(context)

    if not missing:
        return "✅ You have all the information needed! Type **'generate'** to create your demo."

    # Build prompt with what we have
    known_info = []
    if context.get("company_name"):
        known_info.append(f"Company: {context['company_name']}")
    if context.get("department"):
        known_info.append(f"Department: {context['department']}")
    if context.get("industry"):
        known_info.append(f"Industry: {context['industry']}")
    if context.get("pain_points"):
        known_info.append(f"Pain Points: {', '.join(context['pain_points'])}")
    if context.get("use_cases"):
        known_info.append(f"Use Cases: {', '.join(context['use_cases'])}")

    known_context = "\n".join(known_info) if known_info else "No context provided yet"

    # List missing fields
    missing_fields = [field_name for field_name, _ in missing]

    suggestion_prompt = f"""Based on this customer context, suggest realistic and relevant information for the missing fields.

**Known Context:**
{known_context}

**Missing Fields:** {', '.join(missing_fields)}

For each missing field, provide 2-3 specific, realistic suggestions that would make sense for this customer scenario.

Format your response as JSON with this structure:
{{
  "pain_points": ["suggestion 1", "suggestion 2", "suggestion 3"],
  "use_cases": ["suggestion 1", "suggestion 2"],
  "metrics": ["suggestion 1", "suggestion 2"],
  "scale": "suggested scale description"
}}

Only include fields that are actually missing. Be specific and relevant to their industry and department.

JSON:"""

    try:
        # Get API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "❌ Cannot generate suggestions: ANTHROPIC_API_KEY not set. Please provide the missing information manually."

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            temperature=0.7,  # Higher temperature for creative suggestions
            messages=[{"role": "user", "content": suggestion_prompt}]
        )

        content = response.content[0].text.strip()

        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        suggestions = json.loads(content)

        # Update context with suggestions
        for key, value in suggestions.items():
            if value and key in context:
                if isinstance(value, list):
                    context[key] = value
                else:
                    context[key] = value

        # Format response
        response_parts = ["🤖 **AI-Generated Suggestions Applied!**\n"]

        for key, value in suggestions.items():
            field_name = key.replace("_", " ").title()
            if isinstance(value, list):
                response_parts.append(f"\n**{field_name}:**")
                for item in value:
                    response_parts.append(f"  • {item}")
            else:
                response_parts.append(f"\n**{field_name}:** {value}")

        response_parts.append("\n\n✅ Context updated! Review the sidebar and type **'generate'** when ready, or provide more details to refine.")

        return "\n".join(response_parts)

    except Exception as e:
        return f"❌ Error generating suggestions: {e}\n\nPlease provide the missing information manually."


def process_smart_message(message: str) -> str:
    """Process message with intelligent context extraction and progress tracking using LLM"""
    from src.services.context_tracker import ContextTracker
    import anthropic

    # Check if user is asking for suggestions
    if message.strip().lower() in ['suggestions', 'suggest', 'generate suggestions', 'help']:
        return generate_suggestions()

    # Check if user wants to skip missing fields and use defaults
    if message.strip().lower() in ['skip', "i don't know", "don't know", "use defaults", "not sure"]:
        return _handle_skip_defaults()

    # Get current context
    current_context = st.session_state.demo_context
    tracker = ContextTracker()

    # Build conversation history for context
    conversation_history = []
    for msg in st.session_state.messages[-3:]:  # Last 3 messages for context
        conversation_history.append(f"{msg['role']}: {msg['content'][:200]}")

    # Create structured prompt for LLM
    prompt = f"""You are a demo assistant helping gather information to build an Elastic Agent Builder demo.

**Current Context:**
- Company: {current_context.get('company_name') or 'Not provided'}
- Department: {current_context.get('department') or 'Not provided'}
- Industry: {current_context.get('industry') or 'Not provided'}
- Pain Points: {len(current_context.get('pain_points', []))} identified
- Use Cases: {len(current_context.get('use_cases', []))} identified
- Scale: {current_context.get('scale') or 'Not provided'}
- Metrics: {len(current_context.get('metrics', []))} identified

**Recent Conversation:**
{chr(10).join(conversation_history) if conversation_history else 'None'}

**User's New Message:**
{message}

**CRITICAL INSTRUCTIONS:**
You MUST return valid JSON in this EXACT format. No other text before or after the JSON.

{{
  "extracted_context": {{
    "company_name": null,
    "department": null,
    "industry": null,
    "pain_points": [],
    "use_cases": [],
    "scale": null,
    "metrics": [],
    "demo_type": null
  }},
  "compound_request_detected": false,
  "suggested_analytics_prompt": null,
  "suggested_search_prompt": null,
  "user_response": ""
}}

**Guidelines:**
1. Extract ALL new information from the user's message into extracted_context
2. For pain_points and use_cases, extract specific items from lists or paragraphs
3. **Detect Compound Requests** (MOST IMPORTANT - READ CAREFULLY):

   **Detection Criteria:** Set compound_request_detected to true if BOTH conditions are met:

   A) The user's message contains use cases matching "search" keywords:
      - Words: search, find, retrieve, lookup, knowledge base, documents, RAG, semantic search, discovery, locate
      - Examples: "find provider info", "lookup policies", "search knowledge base", "retrieve patient records"

   B) AND the message also contains use cases matching "analytics" keywords:
      - Words: analyze, trend, pattern, metric, aggregate, dashboard, report, insight, forecast, statistics
      - Examples: "analyze denial trends", "track metrics", "identify patterns", "forecast demand"

   **Explicit Examples:**
   - ✅ COMPOUND: "Provider lookup (search) + denial trend analysis (analytics)"
   - ✅ COMPOUND: "Knowledge base search (search) + call volume metrics (analytics)"
   - ✅ COMPOUND: "Document retrieval (search) + performance dashboards (analytics)"
   - ❌ NOT compound: "Provider lookup + policy search" (both search)
   - ❌ NOT compound: "Trend analysis + metric tracking" (both analytics)

   **If compound detected**:
   - Set compound_request_detected to true
   - Set suggested_analytics_prompt to a SHORT summary (1-2 sentences) of analytics use cases only
   - Set suggested_search_prompt to a SHORT summary (1-2 sentences) of search use cases only
   - Keep these summaries BRIEF - just enough to show the split, NOT full prompts

4. **Classify demo_type** (CRITICAL):
   - Set to "search" if use case involves: finding/retrieving documents, RAG, knowledge bases, patient records, policy lookup, semantic search, relevance
   - Set to "analytics" if use case involves: analyzing trends, metrics, aggregations, dashboards, BI, time-series, forecasting
   - If compound_request_detected is true, pick the type that appears FIRST or most prominently in the user's message
5. For user_response:
   - **SPECIAL CASE - Compound Request:** If compound_request_detected is true, INSTEAD of normal response:
      - Explain that you detected BOTH search and analytics use cases
      - Briefly mention the analytics use cases
      - Briefly mention the search use cases
      - Ask which type of demo they want to build (analytics or search)
      - Remind them they can build the other type in a second run
      - Keep this response concise (2-3 sentences max)
   - **NORMAL CASE - Single Demo Type:**
      - If ≥80% complete: Say ready and ask them to type 'generate' (just the word "generate")
      - If 50-79%: Acknowledge what was captured, then ask for missing fields AS BULLETS
      - If <50%: Welcome and ask for key info AS BULLETS
      - Be specific about what was found
      - When asking for missing info, format as bullet points (one per field)
      - ALWAYS end with: "💡 Don't have all the details? Just type **'skip'** and I'll use reasonable defaults."

**Example user_response format when info is missing:**
"Great! I've captured [what you found]. To complete the demo, I need:

• **Scale:** How many [relevant unit]? (e.g., agents, transactions, customers)
• **Metrics:** What KPIs matter most? (e.g., response time, conversion rate)

💡 Don't have all the details? Just type **'skip'** and I'll use reasonable defaults."

RETURN ONLY JSON. NO MARKDOWN CODE BLOCKS. NO EXPLANATIONS."""

    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            # Fallback to basic extraction if no API key
            st.warning("⚠️ API key not found, using basic extraction")
            return _fallback_processing(message)

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,  # Increased for compound requests - need room for two full high-fidelity prompts
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()

        # Debug logging
        logger.info(f"LLM raw response length: {len(content)}")
        logger.debug(f"LLM response preview: {content[:500]}")
        print(f"\n{'='*70}")
        print(f"LLM RESPONSE DEBUG")
        print(f"{'='*70}")
        print(f"Length: {len(content)}")
        print(f"First 500 chars:\n{content[:500]}")
        print(f"{'='*70}\n")

        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        # Try to parse JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}")
            logger.error(f"Content was: {content[:1000]}")
            raise

        # Update session state with extracted context
        extracted = result.get('extracted_context', {})
        context = st.session_state.demo_context

        for key, value in extracted.items():
            if value:
                if isinstance(value, list) and value:  # Non-empty list
                    # Merge with existing, removing duplicates
                    existing = context.get(key, [])
                    context[key] = list(set(existing + value))
                elif not isinstance(value, list):  # String value
                    context[key] = value

        # Calculate progress for phase tracking
        progress, missing = tracker.calculate_progress(context)
        is_ready = tracker.is_ready_to_generate(context)

        if is_ready:
            st.session_state.conversation_phase = "ready_to_generate"
        else:
            st.session_state.conversation_phase = "gathering"

        # Return the user-facing response from LLM
        return result.get('user_response', 'Processing your request...')

    except Exception as e:
        logger.error(f"LLM processing failed: {e}", exc_info=True)
        st.warning(f"⚠️ Using fallback processing due to error: {e}")
        return _fallback_processing(message)


def _handle_skip_defaults() -> str:
    """Handle when user wants to skip missing fields and use defaults"""
    from src.services.context_tracker import ContextTracker

    context = st.session_state.demo_context
    tracker = ContextTracker()

    # Fill in reasonable defaults for missing fields
    if not context.get('scale'):
        # Infer scale from company/department context
        if 'enterprise' in str(context.get('company_name', '')).lower() or \
           'call center' in str(context.get('department', '')).lower():
            context['scale'] = "1000+ agents handling 10,000+ daily interactions"
        else:
            context['scale'] = "100+ team members managing 1,000+ transactions daily"

    if not context.get('metrics') or len(context.get('metrics', [])) == 0:
        # Infer metrics from department
        dept = str(context.get('department', '')).lower()
        if 'sales' in dept:
            context['metrics'] = ['conversion rate', 'pipeline velocity', 'deal size']
        elif 'support' in dept or 'service' in dept or 'call center' in dept:
            context['metrics'] = ['first call resolution', 'average handle time', 'customer satisfaction']
        elif 'operations' in dept:
            context['metrics'] = ['efficiency rate', 'cost per transaction', 'processing time']
        else:
            context['metrics'] = ['user engagement', 'task completion rate', 'response time']

    # Check if now ready
    progress, missing = tracker.calculate_progress(context)
    is_ready = tracker.is_ready_to_generate(context)

    if is_ready:
        st.session_state.conversation_phase = "ready_to_generate"
        return f"""Perfect! I've filled in reasonable defaults:

• **Scale:** {context.get('scale')}
• **Metrics:** {', '.join(context.get('metrics', []))}

You're all set! Type **'generate'** to create your custom demo module."""
    else:
        st.session_state.conversation_phase = "gathering"
        return f"""I've added some defaults, but I still need a bit more information. Currently at **{int(progress * 100)}% complete**.

{tracker.generate_prompt_for_missing(missing)}"""


def _fallback_processing(message: str) -> str:
    """Fallback processing when LLM is unavailable"""
    from src.services.context_tracker import ContextTracker

    extractor = SmartContextExtractor()
    extracted = extractor.extract_context(message)

    # Update session state with extracted context
    context = st.session_state.demo_context

    for key, value in extracted.items():
        if value:
            if isinstance(value, list):
                context[key] = list(set(context.get(key, []) + value))
            else:
                context[key] = value

    # Use ContextTracker for intelligent response
    tracker = ContextTracker()
    progress, missing = tracker.calculate_progress(context)
    is_ready = tracker.is_ready_to_generate(context)

    # Generate intelligent response based on progress
    if is_ready:
        company = context.get("company_name", "this customer")
        dept = context.get("department", "team")

        response = f"""Perfect! I have all the information needed to create a demo for **{company}'s {dept}** team.

{tracker.get_summary(context)}

**Ready to build?** Type **'generate'** to proceed!
"""
        st.session_state.conversation_phase = "ready_to_generate"
        return response

    else:
        response = f"""Great! I'm gathering information for your demo. **({int(progress * 100)}% complete)**\n\n"""

        if context.get("company_name"):
            response += f"✅ **Company:** {context['company_name']}\n"
        if context.get("department"):
            response += f"✅ **Department:** {context['department']}\n"
        if context.get("pain_points"):
            response += f"✅ **Pain Points:** {len(context['pain_points'])} identified\n"
        if context.get("use_cases"):
            response += f"✅ **Use Cases:** {len(context['use_cases'])} defined\n"

        response += "\n---\n\n"

        missing_prompt = tracker.generate_prompt_for_missing(missing)
        if missing_prompt:
            response += missing_prompt

        st.session_state.conversation_phase = "gathering"
        return response
