"""
Elastic Agent Builder Demo Generator
Modular architecture with LLM-generated custom demos
"""

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import sys
import pandas as pd

# Add project modules to path
sys.path.insert(0, str(Path(__file__).parent))

# Import modular framework
from src.framework import (
    ModularDemoOrchestrator,
    DemoModuleManager,
    list_demos
)

# Import UI components
from src.ui import QueryResultsDisplay

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Elastic Demo Builder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Automated demo generation for Elastic Agent Builder",
    },
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .context-badge {
        background-color: rgba(0, 123, 255, 0.2);
        border: 1px solid #007BFF;
        border-radius: 15px;
        padding: 5px 10px;
        margin: 2px;
        display: inline-block;
        font-size: 0.9em;
    }
    .success-badge {
        background-color: rgba(0, 255, 0, 0.2);
        border: 1px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "demo_context" not in st.session_state:
    st.session_state.demo_context = {
        "company_name": None,
        "department": None,
        "industry": None,
        "pain_points": [],
        "use_cases": [],
        "metrics": [],
        "scale": None,
        "urgency": None,
    }

if "conversation_phase" not in st.session_state:
    st.session_state.conversation_phase = "initial"

if "needs_processing" not in st.session_state:
    st.session_state.needs_processing = False

if "current_demo_module" not in st.session_state:
    st.session_state.current_demo_module = None

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "create"  # "create" or "browse"


class SmartContextExtractor:
    """Intelligent context extraction from user messages using LLM"""

    def __init__(self):
        self.llm_client = None
        try:
            import anthropic
            import os

            # Try to get API key from environment or Streamlit secrets
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key and hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
                api_key = st.secrets["ANTHROPIC_API_KEY"]

            if api_key:
                self.llm_client = anthropic.Anthropic(api_key=api_key)
            else:
                # Don't show warning in __init__, will show if extraction fails
                pass
        except Exception as e:
            # Silently fail, will fallback to basic extraction
            pass

    def extract_context(self, message: str) -> Dict:
        """Extract all possible context from the message using LLM"""

        if not self.llm_client:
            # Fallback to basic extraction if LLM not available
            st.info("💡 Using basic extraction. For better results, set ANTHROPIC_API_KEY environment variable.")
            return self._basic_extract(message)

        try:
            # Use LLM to extract context
            extraction_prompt = f"""Extract the following information from this customer description. Return ONLY valid JSON.

Customer Message:
{message}

Extract:
- company_name: The company name (string or null)
- department: The department/team (string or null)
- industry: The industry (string or null)
- pain_points: List of specific pain points or challenges (array of strings, extract as many as mentioned)
- use_cases: List of use cases or goals (array of strings)
- metrics: List of metrics they care about (array of strings)
- scale: Data scale mentioned (string or null, e.g., "5000+ accounts", "millions of transactions")

Return ONLY a JSON object with these keys. If a field is not found, use null or empty array.

JSON:"""

            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": extraction_prompt}]
            )

            # Parse JSON response
            content = response.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            context = json.loads(content)

            # Clean up nulls
            result = {}
            for key, value in context.items():
                if value is not None and value != [] and value != "":
                    result[key] = value

            return result

        except Exception as e:
            st.error(f"LLM extraction failed: {e}")
            return self._basic_extract(message)

    def _basic_extract(self, message: str) -> Dict:
        """Fallback basic extraction using regex"""
        context = {}

        # Basic company extraction
        company_match = re.search(r"(?:Customer is|for|with|at)\s+([A-Z][A-Za-z0-9\s&'.-]+?)(?:\.|,|Department|\s+is)", message, re.IGNORECASE)
        if company_match:
            context["company_name"] = company_match.group(1).strip()

        # Basic department extraction
        dept_keywords = ["Call Center", "Customer Success", "Sales", "Marketing", "Operations", "Supply Chain", "Finance"]
        for dept in dept_keywords:
            if dept.lower() in message.lower():
                context["department"] = dept
                break

        return context


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
    import os

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


def display_context_summary():
    """Display extracted context in sidebar with progress tracking"""
    from src.services.context_tracker import ContextTracker

    tracker = ContextTracker()
    context = st.session_state.demo_context

    # Calculate progress
    progress, missing = tracker.calculate_progress(context)
    status = tracker.get_completion_status(context)

    st.markdown("### 📋 Demo Context")

    # Show demo type if detected
    demo_type = context.get('demo_type')
    if demo_type:
        type_emoji = "🔍" if demo_type == "search" else "📊"
        type_label = "Search/RAG" if demo_type == "search" else "Analytics"
        st.info(f"{type_emoji} **Demo Type:** {type_label}")

    # Progress bar at top
    st.progress(progress, text=f"{int(progress * 100)}% complete")

    # Display fields as simple list with emoji indicators
    st.markdown("#### Extracted Context")

    for field_key, field_status in status.items():
        name = field_status['display_name']
        value = field_status['display_value']

        if field_status['is_complete']:
            # Complete: show green checkmark
            st.markdown(f"✅ **{name}:** {value}")
        else:
            # Incomplete: show red X
            st.markdown(f"❌ **{name}:** *(not set)*")

    # Status message
    st.markdown("---")

    if tracker.is_ready_to_generate(context):
        st.success("✅ Ready to generate!\n\nType **'generate'** to create your demo.")
    else:
        missing_count = len(missing)
        st.warning(f"⚠️ Need more info ({missing_count} fields)")

        # Show what's missing
        prompt = tracker.generate_prompt_for_missing(missing)
        if prompt:
            with st.expander("What's missing?"):
                st.info(prompt)


def render_create_demo_view():
    """Render the demo creation interface"""
    st.title("🚀 Elastic Agent Builder Demo Generator")
    st.markdown("*Create custom demos with LLM-generated modules*")

    # Display messages
    if not st.session_state.messages:
        st.info("""
        👋 **Welcome!** Paste your customer description and I'll extract context automatically.

        **Example:** *"Salesforce's Customer Success team wants to prevent churn in their 5,000+
        enterprise accounts worth $10B in ARR..."*
        """)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Process programmatically added messages
    if st.session_state.needs_processing and st.session_state.messages:
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "user":
            st.session_state.needs_processing = False

            with st.chat_message("assistant"):
                with st.spinner("Analyzing context..."):
                    response = process_smart_message(last_message["content"])
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

    # Chat input
    if prompt := st.chat_input("Paste your customer description or type your response..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Check if this is a generate command
        if prompt.lower().strip() == "generate" and st.session_state.conversation_phase == "ready_to_generate":
            with st.chat_message("assistant"):
                with st.spinner("🚀 Generating custom demo module..."):
                    try:
                        # Create config from context
                        context = st.session_state.demo_context
                        config = {
                            "company_name": context.get("company_name", "Demo Company"),
                            "department": context.get("department", "Operations"),
                            "industry": context.get("industry", "Enterprise"),
                            "pain_points": context.get("pain_points", []),
                            "use_cases": context.get("use_cases", []),
                            "scale": context.get("scale", "10000 records"),
                            "metrics": context.get("metrics", []),
                            "demo_type": context.get("demo_type", "analytics"),
                            "dataset_size_preference": st.session_state.get("dataset_size_preference", "medium")
                        }

                        # Create enhanced progress display with phase tracking using empty placeholders
                        st.markdown(f"### 🚀 Demo Generation Progress")

                        # Define all 8 phases
                        phases = [
                            {"name": "Strategy", "icon": "🎯", "desc": "Planning query strategy"},
                            {"name": "Data Module", "icon": "🤖", "desc": "Generating data module"},
                            {"name": "Datasets", "icon": "📦", "desc": "Creating datasets"},
                            {"name": "Indexing", "icon": "🔍", "desc": "Indexing in Elasticsearch"},
                            {"name": "Profiling", "icon": "📊", "desc": "Profiling indexed data"},
                            {"name": "Queries", "icon": "🔧", "desc": "Generating ES|QL queries"},
                            {"name": "Testing", "icon": "🧪", "desc": "Testing queries"},
                            {"name": "Cleanup", "icon": "✨", "desc": "Finalizing demo"}
                        ]

                        # Create placeholders for dynamic updates
                        progress_bar_placeholder = st.empty()
                        phases_placeholder = st.empty()
                        current_status_placeholder = st.empty()

                        phase_status = {phase["name"]: "pending" for phase in phases}
                        last_update_state = {"progress": 0.0, "phase": None}

                        def update_progress(progress: float, message: str):
                            """Update progress with enhanced phase tracking (only updates changed elements)"""
                            # Determine current phase based on progress and message
                            if progress <= 0.05:
                                current_phase = "Strategy"
                                current_phase_num = 1
                            elif progress <= 0.15:
                                phase_status["Strategy"] = "complete"
                                current_phase = "Data Module"
                                current_phase_num = 2
                            elif progress <= 0.3:
                                phase_status["Data Module"] = "complete"
                                current_phase = "Datasets"
                                current_phase_num = 3
                            elif progress <= 0.5:
                                phase_status["Datasets"] = "complete"
                                current_phase = "Indexing"
                                current_phase_num = 4
                            elif progress <= 0.6:
                                phase_status["Indexing"] = "complete"
                                current_phase = "Profiling"
                                current_phase_num = 5
                            elif progress <= 0.65:
                                phase_status["Profiling"] = "complete"
                                current_phase = "Queries"
                                current_phase_num = 6
                            elif progress <= 0.85:
                                phase_status["Queries"] = "complete"
                                current_phase = "Testing"
                                current_phase_num = 7
                            else:
                                phase_status["Testing"] = "complete"
                                current_phase = "Cleanup"
                                current_phase_num = 8

                            if current_phase in phase_status:
                                phase_status[current_phase] = "in_progress"

                            # Only update UI if phase changed OR progress increased by at least 5%
                            phase_changed = last_update_state["phase"] != current_phase
                            progress_jump = progress - last_update_state["progress"] >= 0.05

                            if not (phase_changed or progress_jump):
                                return  # Skip update to reduce UI churn

                            last_update_state["progress"] = progress
                            last_update_state["phase"] = current_phase

                            # Update progress bar with phase name
                            progress_bar_placeholder.progress(
                                progress,
                                text=f"{int(progress * 100)}% - Step {current_phase_num}/8: {current_phase}"
                            )

                            # Update phase checklist (only if phase changed)
                            if phase_changed:
                                with phases_placeholder.container():
                                    st.markdown("#### Pipeline Steps:")
                                    for idx, phase in enumerate(phases, 1):
                                        status = phase_status.get(phase["name"], "pending")
                                        if status == "complete":
                                            st.markdown(f"**{idx}.** ✅ {phase['icon']} {phase['name']}")
                                        elif status == "in_progress":
                                            st.markdown(f"**{idx}.** 🔄 {phase['icon']} **{phase['name']}** - _{phase['desc']}_")
                                        else:
                                            st.markdown(f"**{idx}.** ⏸️ {phase['icon']} {phase['name']}")

                            # Always update current status (this is the only line that changes frequently)
                            current_status_placeholder.info(f"**Current:** {message}")


                        # Generate demo using modular orchestrator
                        # Pass inference endpoints from sidebar configuration
                        inference_endpoints = st.session_state.get("inference_endpoints", {
                            "rerank": ".rerank-v1-elasticsearch",
                            "completion": "completion-vulcan"
                        })
                        orchestrator = ModularDemoOrchestrator(inference_endpoints=inference_endpoints)

                        # Use Path 2: Query-first strategy with LOOKUP JOIN support
                        # Generates all three query types: scripted, parameterized, and RAG
                        results = orchestrator.generate_new_demo_with_strategy(
                            config,
                            update_progress,
                            conversation=st.session_state.messages
                        )

                        st.session_state.current_demo_module = results['module_name']

                        st.balloons()
                        st.success(f"✅ Demo module created: **{results['module_name']}**")

                        response = f"""Your custom demo module is ready! 🎉

**Module:** `{results['module_name']}`

**Generated:**
- ✅ Custom data generator ({len(results['datasets'])} datasets)
- ✅ ES|QL queries ({len(results['queries'])} queries)
- ✅ Demo guide and talk track

**Next Steps:**
1. Click "Browse Demos" in the sidebar to view all details
2. Download the demo guide and queries
3. The module is saved in `demos/{results['module_name']}/` for customization

You can now refine the generated modules or start a new demo!"""

                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

                        # Add button to view in browse mode
                        if st.button("📂 View Demo Details", key="view_demo_btn", type="primary"):
                            st.session_state.view_mode = "browse"
                            st.session_state.current_demo_module = results['module_name']
                            st.rerun()

                    except Exception as e:
                        error_msg = f"Error generating demo: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"Demo generation failed: {e}", exc_info=True)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

        else:
            # Normal conversation
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    response = process_smart_message(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
            # Force rerun to update sidebar with new context
            st.rerun()


@st.cache_data(ttl=3600)
def load_demo_datasets(module_name: str):
    """Cache dataset generation for faster loading"""
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        data_gen = loader.load_data_generator()
        return data_gen.generate_datasets()
    return {}

@st.cache_data(ttl=3600)
def load_demo_queries(module_name: str):
    """Cache query generation for faster loading

    Returns dict with three query types:
    {
        'scripted': [...],
        'parameterized': [...],
        'rag': [...]
    }

    Automatically merges in auto-fixed queries from query_testing_results.json if available.
    """
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        datasets = load_demo_datasets(module_name)
        query_gen = loader.load_query_generator(datasets)

        # Always call all three methods - modern modules implement all three
        scripted = query_gen.generate_queries()
        parameterized = query_gen.generate_parameterized_queries()
        rag = query_gen.generate_rag_queries()

        # Merge in auto-fixed queries from test results if available
        try:
            from pathlib import Path
            import json
            test_results_path = Path('demos') / module_name / 'query_testing_results.json'
            if test_results_path.exists():
                with open(test_results_path, 'r') as f:
                    test_results = json.load(f)

                # Create a map of query names to fixed queries
                fixed_queries = {}
                for result in test_results.get('queries', []):
                    if result.get('was_fixed') and result.get('final_esql'):
                        fixed_queries[result['name']] = result['final_esql']

                # Replace original queries with fixed versions
                for i, query in enumerate(scripted):
                    if query['name'] in fixed_queries:
                        scripted[i] = query.copy()
                        scripted[i]['query'] = fixed_queries[query['name']]
                        scripted[i]['_auto_fixed'] = True  # Mark as auto-fixed
        except Exception as e:
            # Silently fail - just use original queries
            pass

        return {
            'scripted': scripted,
            'parameterized': parameterized,
            'rag': rag,
            'all': scripted + parameterized + rag  # For backward compatibility
        }
    return {'scripted': [], 'parameterized': [], 'rag': [], 'all': []}

@st.cache_data(ttl=3600)
def load_demo_guide(module_name: str):
    """Cache guide generation for faster loading"""
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        datasets = load_demo_datasets(module_name)
        queries_dict = load_demo_queries(module_name)
        # Pass all queries to guide generator
        guide_gen = loader.load_demo_guide(datasets, queries_dict['all'])
        return guide_gen.generate_guide()
    return ""

@st.cache_data(ttl=3600)
def load_demo_data_profile(module_name: str):
    """Load data profile from demo module

    Returns:
        dict: Data profile with field statistics and sample values
    """
    try:
        profile_path = Path("demos") / module_name / "data_profile.json"
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load data profile for {module_name}: {e}")
    return None

def get_sample_values_for_parameters(data_profile: dict, parameters: List[Dict]) -> Dict[str, List[str]]:
    """Extract sample values from data profile for query parameters

    Args:
        data_profile: Data profile dictionary with field statistics
        parameters: List of parameter definitions from query

    Returns:
        dict: Parameter name to list of sample values
    """
    if not data_profile or 'datasets' not in data_profile:
        return {}

    sample_values = {}

    for param in parameters:
        param_name = param.get('name', '')
        param_type = param.get('type', 'string')

        # Search across all datasets for matching fields
        matches = []
        for dataset_name, dataset_info in data_profile['datasets'].items():
            fields = dataset_info.get('fields', {})

            # Look for exact match first
            if param_name in fields:
                field_data = fields[param_name]
                unique_vals = field_data.get('unique_values', [])
                if unique_vals:
                    matches.extend(unique_vals[:10])  # Take first 10
            else:
                # Look for partial match (e.g., "session_id" in "user_session_id")
                for field_name, field_data in fields.items():
                    if param_name in field_name or field_name in param_name:
                        unique_vals = field_data.get('unique_values', [])
                        if unique_vals:
                            matches.extend(unique_vals[:10])

        # Deduplicate and limit to first 5-7 unique values
        if matches:
            unique_matches = list(dict.fromkeys(matches))[:7]
            sample_values[param_name] = unique_matches

    return sample_values

def generate_sample_question(query: Dict, param: Dict, data_profile: dict) -> str:
    """Use LLM to generate a contextual sample question for semantic search parameters

    Args:
        query: Query definition with name, description, query text
        param: Parameter definition with name, description, example
        data_profile: Data profile with available fields and values

    Returns:
        str: Generated sample question
    """
    import anthropic
    import os

    try:
        llm_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        # Build context about available data
        data_context = ""
        if data_profile and 'datasets' in data_profile:
            data_context = "Available datasets and fields:\n"
            for dataset_name, dataset_info in data_profile['datasets'].items():
                fields = dataset_info.get('fields', {})
                field_names = list(fields.keys())[:10]  # First 10 fields
                data_context += f"- {dataset_name}: {', '.join(field_names)}\n"

        prompt = f"""Generate a realistic sample question for testing this ES|QL semantic search query.

Query Name: {query.get('name', 'Unknown')}
Query Description: {query.get('description', 'No description')}

Parameter: {param.get('name', 'unknown')}
Parameter Description: {param.get('description', 'Natural language question')}
Parameter Example: {param.get('example', 'N/A')}

{data_context}

Generate a single, specific natural language question that:
1. Matches the query's purpose
2. Would return relevant results from the available data
3. Is something a real user might ask

Return ONLY the question text, no explanation or formatting."""

        response = llm_client.messages.create(
            model="claude-3-5-haiku-20241022",  # Fast, cheap model for suggestions
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        suggested_question = response.content[0].text.strip()
        return suggested_question

    except Exception as e:
        logger.error(f"Failed to generate sample question: {e}")
        # Fallback to example if LLM fails
        return param.get('example', 'What is the most common issue?')

def render_browse_demos_view():
    """Render the demo browsing interface - demo details only (list is in sidebar)"""
    # Show details if a module is selected
    if st.session_state.current_demo_module:
        st.title(f"📊 {st.session_state.current_demo_module}")

        manager = DemoModuleManager()
        loader = manager.get_module(st.session_state.current_demo_module)

        if loader:
            tabs = st.tabs(["📋 Config", "🗂️ Data", "🔍 Queries", "📝 Guide", "💬 Conversation"])

            with tabs[0]:
                st.markdown("### Generate Demo Assets")
                st.info("⚠️ **Generation may take 5-20 minutes** — Page will appear frozen. Data: 80-90% | Queries: 5-10% | Guide: 5-10%")

                if st.button("🚀 Generate Assets", use_container_width=True):
                    with st.spinner("Generating demo assets..."):
                        try:
                            # Force regeneration by clearing cache and loading
                            load_demo_datasets.clear()
                            load_demo_queries.clear()
                            load_demo_guide.clear()

                            # Generate all assets
                            datasets = load_demo_datasets(st.session_state.current_demo_module)
                            queries = load_demo_queries(st.session_state.current_demo_module)
                            guide = load_demo_guide(st.session_state.current_demo_module)

                            # Mark assets as generated
                            st.session_state.assets_generated = True

                            st.success(f"✅ Generated {len(datasets)} datasets, {len(queries)} queries, and demo guide!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating assets: {e}")
                            import traceback
                            st.code(traceback.format_exc())

                st.divider()
                st.markdown("### Demo Configuration")
                st.json(loader.config)

            with tabs[1]:
                # Only load if assets have been generated
                if st.session_state.get("assets_generated", False):
                    try:
                        datasets = load_demo_datasets(st.session_state.current_demo_module)

                        # Get semantic fields specification from data generator
                        manager = DemoModuleManager()
                        loader = manager.get_module(st.session_state.current_demo_module)
                        data_gen = loader.load_data_generator()

                        # Try to get semantic fields (may not exist in older modules)
                        try:
                            semantic_fields_spec = data_gen.get_semantic_fields()
                        except AttributeError:
                            semantic_fields_spec = {}

                        # Load index_mode mapping from query_strategy.json
                        index_mode_map = {}
                        try:
                            from pathlib import Path
                            import json
                            strategy_path = Path('demos') / st.session_state.current_demo_module / 'query_strategy.json'
                            if strategy_path.exists():
                                with open(strategy_path, 'r') as f:
                                    query_strategy = json.load(f)
                                    for dataset in query_strategy.get('datasets', []):
                                        dataset_name = dataset.get('name')
                                        if dataset_name:
                                            # Prefer explicit index_mode, fallback to type-based mapping
                                            if 'index_mode' in dataset:
                                                index_mode_map[dataset_name] = dataset['index_mode']
                                            else:
                                                # Fallback logic
                                                dataset_type = dataset.get('type')
                                                if dataset_type == 'reference':
                                                    index_mode_map[dataset_name] = 'lookup'
                                                elif dataset_type == 'timeseries':
                                                    index_mode_map[dataset_name] = 'data_stream'
                                                elif dataset_type in ['documents', 'records']:
                                                    index_mode_map[dataset_name] = 'lookup'
                                                else:
                                                    index_mode_map[dataset_name] = 'lookup'  # Safe default
                        except Exception as e:
                            import logging
                            logging.warning(f"Could not load index_mode mapping: {e}")

                        if datasets:
                            # Index All button at the top
                            if st.button("📤 Index All Datasets", use_container_width=True, type="primary"):
                                from src.services.elasticsearch_indexer import ElasticsearchIndexer

                                st.info(f"Starting batch indexing for {len(datasets)} datasets...")

                                indexer = ElasticsearchIndexer()
                                for idx, (name, df) in enumerate(datasets.items(), 1):
                                    st.markdown(f"**[{idx}/{len(datasets)}] Indexing {name}...**")

                                    # Get semantic fields for this dataset
                                    semantic_fields = semantic_fields_spec.get(name, [])

                                    # Get index_mode for this dataset
                                    index_mode = index_mode_map.get(name, 'lookup')  # Default to lookup

                                    progress_bar = st.progress(0)
                                    status_text = st.empty()

                                    def progress_callback(pct, msg):
                                        progress_bar.progress(pct)
                                        status_text.text(msg)

                                    try:
                                        result = indexer.index_dataset(
                                            df,
                                            name,
                                            semantic_fields=semantic_fields,
                                            index_mode=index_mode,
                                            progress_callback=progress_callback
                                        )

                                        if result.success:
                                            st.success(f"✅ {name}: {result.documents_indexed:,} docs indexed in {result.duration_seconds}s")
                                        else:
                                            st.error(f"❌ {name}: Indexing failed")
                                    except Exception as e:
                                        st.error(f"❌ {name}: {str(e)}")

                                st.success("🎉 Batch indexing complete!")

                            st.divider()

                            for name, df in datasets.items():
                                st.markdown(f"### {name}")

                                # Action buttons
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    # Download CSV
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        "📥 CSV",
                                        csv,
                                        f"{name}.csv",
                                        "text/csv",
                                        key=f"download_data_{st.session_state.current_demo_module}_{name}",
                                        use_container_width=True
                                    )

                                with col2:
                                    # View data
                                    if st.button("👁️ View", key=f"view_{name}", use_container_width=True):
                                        st.session_state[f"show_data_{name}"] = not st.session_state.get(f"show_data_{name}", False)

                                with col3:
                                    # Index in Elasticsearch button
                                    if st.button("📤 Index", key=f"index_{name}", use_container_width=True):
                                        from src.services.elasticsearch_indexer import ElasticsearchIndexer

                                        # Get semantic fields for this dataset
                                        semantic_fields = semantic_fields_spec.get(name, [])

                                        # Get index_mode for this dataset
                                        index_mode = index_mode_map.get(name, 'lookup')  # Default to lookup

                                        # Show progress and stop button
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()
                                        stop_button_container = st.empty()

                                        # Track stop request in session state
                                        stop_key = f"stop_indexing_{name}"
                                        st.session_state[stop_key] = False

                                        def progress_callback(pct, msg):
                                            progress_bar.progress(pct)
                                            status_text.text(msg)

                                        def stop_callback():
                                            return st.session_state.get(stop_key, False)

                                        # Show stop button
                                        if stop_button_container.button("⏸️ Stop Indexing", key=f"stop_{name}"):
                                            st.session_state[stop_key] = True

                                        try:
                                            # Index the dataset
                                            indexer = ElasticsearchIndexer()
                                            result = indexer.index_dataset(
                                                df,
                                                name,
                                                semantic_fields=semantic_fields,
                                                index_mode=index_mode,
                                                progress_callback=progress_callback,
                                                stop_callback=stop_callback
                                            )

                                            # Clear stop button
                                            stop_button_container.empty()

                                            # Store result in session state to display outside column
                                            st.session_state[f"index_result_{name}"] = {
                                                'success': result.success,
                                                'documents_indexed': result.documents_indexed,
                                                'total_docs': len(df),
                                                'index_name': result.index_name,
                                                'index_type': result.index_type,
                                                'semantic_fields': result.semantic_fields,
                                                'duration_seconds': result.duration_seconds,
                                                'errors': result.errors if not result.success else [],
                                                'was_stopped': st.session_state.get(stop_key, False)
                                            }

                                        except Exception as e:
                                            stop_button_container.empty()
                                            st.session_state[f"index_result_{name}"] = {
                                                'success': False,
                                                'error': str(e),
                                                'traceback': __import__('traceback').format_exc()
                                            }

                                # Display indexing result outside columns (full width)
                                if f"index_result_{name}" in st.session_state:
                                    result_data = st.session_state[f"index_result_{name}"]

                                    if 'error' in result_data:
                                        # Exception occurred
                                        st.error(f"❌ Indexing error: {result_data['error']}")
                                        st.code(result_data['traceback'])
                                    elif result_data['success']:
                                        # Check if actually stopped by user
                                        was_stopped_by_user = result_data['was_stopped']
                                        incomplete_indexing = result_data['documents_indexed'] < result_data['total_docs']

                                        if was_stopped_by_user and incomplete_indexing:
                                            st.warning(
                                                f"⏸️ Indexing stopped by user\n\n"
                                                f"**Indexed:** {result_data['documents_indexed']:,} / {result_data['total_docs']:,} documents\n\n"
                                                f"**Index:** {result_data['index_name']} ({result_data['index_type']})\n\n"
                                                f"**Semantic fields:** {', '.join(result_data['semantic_fields']) if result_data['semantic_fields'] else 'None'}\n\n"
                                                f"**Duration:** {result_data['duration_seconds']}s"
                                            )
                                        elif incomplete_indexing and result_data['documents_indexed'] == 0:
                                            st.error(
                                                f"❌ Indexing failed: No documents were indexed\n\n"
                                                f"This usually indicates a connection issue or mapping error. "
                                                f"Check your Elasticsearch connection and try again."
                                            )
                                        elif incomplete_indexing:
                                            st.warning(
                                                f"⚠️ Partial indexing\n\n"
                                                f"**Indexed:** {result_data['documents_indexed']:,} / {result_data['total_docs']:,} documents\n\n"
                                                f"**Index:** {result_data['index_name']} ({result_data['index_type']})\n\n"
                                                f"**Semantic fields:** {', '.join(result_data['semantic_fields']) if result_data['semantic_fields'] else 'None'}\n\n"
                                                f"**Duration:** {result_data['duration_seconds']}s"
                                            )
                                        else:
                                            st.success(
                                                f"✅ Indexed {result_data['documents_indexed']:,} documents\n\n"
                                                f"**Index:** {result_data['index_name']} ({result_data['index_type']})\n\n"
                                                f"**Semantic fields:** {', '.join(result_data['semantic_fields']) if result_data['semantic_fields'] else 'None'}\n\n"
                                                f"**Duration:** {result_data['duration_seconds']}s"
                                            )
                                    else:
                                        st.error(f"❌ Indexing failed:\n{chr(10).join(result_data['errors'])}")

                                # Show semantic fields info if specified
                                if name in semantic_fields_spec and semantic_fields_spec[name]:
                                    st.info(f"🧠 **Semantic fields:** {', '.join(semantic_fields_spec[name])}")

                                # Show data if view button was clicked
                                if st.session_state.get(f"show_data_{name}", False):
                                    st.dataframe(df.head(100), use_container_width=True)
                                    st.caption(f"Showing first 100 of {len(df)} rows")
                                else:
                                    st.caption(f"Total rows: {len(df)} | Columns: {len(df.columns)}")

                                st.divider()
                        else:
                            st.info("No datasets found. Try regenerating assets from the Config tab.")
                    except Exception as e:
                        st.error(f"Error loading data: {e}")
                        st.info("Try clicking 'Generate Assets' in the Config tab.")
                else:
                    st.info("📋 Click 'Generate Assets' in the Config tab to view datasets")

            with tabs[2]:
                # Only load if assets have been generated
                if st.session_state.get("assets_generated", False):
                    try:
                        queries_dict = load_demo_queries(st.session_state.current_demo_module)

                        # Create sub-tabs for query types
                        query_tabs = st.tabs([
                            f"📝 Scripted ({len(queries_dict['scripted'])})",
                            f"🔧 Parameterized ({len(queries_dict['parameterized'])})",
                            f"🤖 RAG ({len(queries_dict['rag'])})"
                        ])

                        # Initialize QueryResultsDisplay for clean rendering
                        display = QueryResultsDisplay()

                        # Helper function to render queries using the new display module
                        def render_query_list(queries, query_type, can_execute=True):
                            if queries:
                                for i, query in enumerate(queries, 1):
                                    # Use the new QueryResultsDisplay for clean rendering
                                    display.render_query_with_results(
                                        query,
                                        results=None,  # No results by default - clean queries only
                                        show_pipeline_view=False  # Don't show educational view by default
                                    )

                                    # Add execution capability for scripted, parameterized, and RAG queries
                                    if can_execute and query_type in ['scripted', 'parameterized', 'rag']:
                                        query_key = f"{query_type}_query_{i}"

                                        # For parameterized and RAG queries, show parameter inputs
                                        if query_type in ['parameterized', 'rag'] and query.get('parameters'):
                                            with st.expander("⚙️ Test with Parameters", expanded=False):
                                                # Load data profile for sample values
                                                data_profile = load_demo_data_profile(st.session_state.current_demo_module)

                                                # Show sample values from data profile if available
                                                if data_profile:
                                                    sample_values_dict = get_sample_values_for_parameters(
                                                        data_profile,
                                                        query['parameters']
                                                    )

                                                    # Show sample values if found
                                                    if sample_values_dict:
                                                        with st.expander("💡 Sample Values from Data Profile", expanded=False):
                                                            st.caption("Copy these sample values to test the query with real data")
                                                            for param_name, values in sample_values_dict.items():
                                                                if values:
                                                                    st.markdown(f"**{param_name}:**")
                                                                    # Display as copyable code blocks
                                                                    for val in values:
                                                                        st.code(val, language=None)
                                                            st.divider()

                                                    # For parameters without sample values, offer "Suggest Question"
                                                    params_without_values = [
                                                        p for p in query['parameters']
                                                        if p.get('name') not in sample_values_dict
                                                    ]

                                                    if params_without_values:
                                                        with st.expander("💭 Generate Sample Questions (LLM)", expanded=False):
                                                            st.caption("Use AI to generate contextual sample questions based on query purpose and available data")
                                                            for param in params_without_values:
                                                                param_name = param.get('name', 'unknown')
                                                                col1, col2 = st.columns([3, 1])
                                                                with col1:
                                                                    st.markdown(f"**{param_name}:** {param.get('description', 'No description')}")
                                                                with col2:
                                                                    suggest_key = f"suggest_{query_key}_{param_name}"
                                                                    if st.button("✨ Suggest", key=suggest_key, use_container_width=True):
                                                                        with st.spinner("Generating suggestion..."):
                                                                            suggested = generate_sample_question(query, param, data_profile)
                                                                            st.session_state[f"{suggest_key}_value"] = suggested
                                                                            st.rerun()

                                                                # Show generated suggestion
                                                                if f"{suggest_key}_value" in st.session_state:
                                                                    st.code(st.session_state[f"{suggest_key}_value"], language=None)
                                                            st.divider()

                                                param_values = display._render_parameter_inputs(
                                                    query['parameters'],
                                                    unique_key=query_key
                                                )

                                                # Test button
                                                if st.button("▶️ Test with These Parameters", key=f"test_{query_key}", use_container_width=True):
                                                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                                    query_name = query.get('name', f'Query {i}')

                                                    with st.spinner(f"Executing {query_name}..."):
                                                        try:
                                                            # Substitute parameters into query
                                                            query_text = display._get_query_text(query)
                                                            substituted_query = display.substitute_parameters(query_text, param_values)

                                                            # Execute
                                                            indexer = ElasticsearchIndexer()
                                                            success, result, error = indexer.execute_esql(substituted_query)

                                                            if success:
                                                                st.success("✅ Query executed successfully!")
                                                                # Store results and substituted query
                                                                st.session_state[f"{query_key}_results"] = result
                                                                st.session_state[f"{query_key}_substituted"] = substituted_query
                                                                st.rerun()
                                                            else:
                                                                st.error(f"❌ Query failed: {error}")
                                                        except Exception as e:
                                                            st.error(f"❌ Error: {e}")

                                        # For scripted queries, simple test button
                                        elif query_type == 'scripted':
                                            col1, col2 = st.columns([1, 3])
                                            with col1:
                                                if st.button("▶️ Test Query", key=f"test_{query_key}", use_container_width=True):
                                                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                                    query_name = query.get('name', f'Query {i}')

                                                    with st.spinner(f"Executing {query_name}..."):
                                                        try:
                                                            indexer = ElasticsearchIndexer()
                                                            query_text = display._get_query_text(query)
                                                            success, result, error = indexer.execute_esql(query_text)

                                                            if success:
                                                                st.success("✅ Query executed successfully!")
                                                                # Store results in session state for display
                                                                st.session_state[f"{query_key}_results"] = result
                                                                st.rerun()
                                                            else:
                                                                st.error(f"❌ Query failed: {error}")
                                                        except Exception as e:
                                                            st.error(f"❌ Error: {e}")

                                        # Display substituted query if available (for parameterized)
                                        if f"{query_key}_substituted" in st.session_state:
                                            with st.expander("📝 Executed Query (with parameters)", expanded=False):
                                                st.code(st.session_state[f"{query_key}_substituted"], language='sql')

                                        # Display results if available in session state
                                        if f"{query_key}_results" in st.session_state:
                                            with st.expander("📊 Query Results", expanded=True):
                                                display._render_query_results(st.session_state[f"{query_key}_results"], unique_key=query_key)

                                            # Check if query returned zero results - offer optimization
                                            results = st.session_state[f"{query_key}_results"]
                                            if (query_type == 'scripted' and results and
                                                'columns' in results and 'values' in results and
                                                len(results['values']) == 0):

                                                # Show optimize button for zero-results queries
                                                optimize_key = f"{query_key}_optimize"
                                                if st.button("🔧 Optimize Constraints", key=optimize_key, help="Use LLM to relax constraints and improve results"):
                                                    with st.spinner("Analyzing constraints..."):
                                                        try:
                                                            # Import optimizer
                                                            from src.services.query_optimizer import relax_query_constraints
                                                            import anthropic
                                                            import os
                                                            import json
                                                            from pathlib import Path

                                                            # Get LLM client
                                                            llm_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

                                                            # Load data profile from demo directory if available
                                                            data_profile = None
                                                            demo_module_name = st.session_state.current_demo_module
                                                            profile_path = Path("demos") / demo_module_name / "data_profile.json"
                                                            if profile_path.exists():
                                                                try:
                                                                    with open(profile_path, 'r') as f:
                                                                        data_profile = json.load(f)
                                                                except Exception as e:
                                                                    st.warning(f"Could not load data profile: {e}")

                                                            # Get current query
                                                            current_esql = display._get_query_text(query)

                                                            # Optimize
                                                            optimized_esql, explanation = relax_query_constraints(
                                                                query=query,
                                                                current_esql=current_esql,
                                                                data_profile=data_profile,
                                                                llm_client=llm_client
                                                            )

                                                            # Show optimized query
                                                            st.success(f"✅ {explanation}")
                                                            st.code(optimized_esql, language='sql')

                                                            # Offer to test the optimized query
                                                            if st.button("▶️ Test Optimized Query", key=f"{optimize_key}_test"):
                                                                from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                                                try:
                                                                    indexer = ElasticsearchIndexer()
                                                                    success, test_results, error = indexer.execute_esql(optimized_esql)
                                                                    if success:
                                                                        st.session_state[f"{query_key}_results"] = test_results
                                                                        st.success(f"Found {len(test_results.get('values', []))} results!")
                                                                        st.rerun()
                                                                    else:
                                                                        st.error(f"Test failed: {error}")
                                                                except Exception as e:
                                                                    st.error(f"Test failed: {e}")
                                                        except Exception as e:
                                                            st.error(f"Optimization failed: {e}")

                                    # Pain point and dataset info
                                    if query.get('pain_point'):
                                        st.caption(f"📌 **Addresses:** {query['pain_point']}")
                                    if query.get('datasets'):
                                        st.caption(f"📊 **Uses datasets:** {', '.join(query['datasets'])}")

                                    st.divider()
                            else:
                                st.info(f"No {query_type} queries found.")

                        # Render each query type in its tab
                        with query_tabs[0]:
                            st.markdown("### Scripted Queries")
                            st.caption("Non-parameterized, fully tested ES|QL queries. These can be executed directly.")
                            render_query_list(queries_dict['scripted'], 'scripted', can_execute=True)

                        with query_tabs[1]:
                            st.markdown("### Parameterized Queries")
                            st.caption("Agent Builder ES|QL tool definitions with `?parameter` syntax. You can test these by providing parameter values!")
                            render_query_list(queries_dict['parameterized'], 'parameterized', can_execute=True)

                        with query_tabs[2]:
                            st.markdown("### RAG Queries")
                            st.caption("Semantic search queries using MATCH → RERANK → COMPLETION pipeline for open-ended Q&A.")
                            render_query_list(queries_dict['rag'], 'rag', can_execute=True)

                    except Exception as e:
                        st.error(f"Error loading queries: {e}")
                        st.info("Try clicking 'Generate Assets' in the Config tab.")
                        import traceback
                        with st.expander("Show traceback"):
                            st.code(traceback.format_exc())
                else:
                    st.info("📋 Click 'Generate Assets' in the Config tab to view queries")

            with tabs[3]:
                # Only load if assets have been generated
                if st.session_state.get("assets_generated", False):
                    try:
                        guide = load_demo_guide(st.session_state.current_demo_module)
                        if guide:
                            st.markdown(guide)
                        else:
                            st.info("No demo guide found. Try regenerating assets from the Config tab.")
                    except Exception as e:
                        st.error(f"Error loading guide: {e}")
                        st.info("Try clicking 'Generate Assets' in the Config tab.")
                else:
                    st.info("📋 Click 'Generate Assets' in the Config tab to view the demo guide")

            with tabs[4]:
                # Load and display conversation history
                st.markdown("### Original Conversation")
                st.markdown("This is the conversation that led to the creation of this demo.")

                conversation_file = loader.module_path / 'conversation.json'
                if conversation_file.exists():
                    try:
                        import json
                        with open(conversation_file, 'r') as f:
                            conversation_data = json.load(f)

                        messages = conversation_data.get('messages', [])

                        if messages:
                            st.markdown(f"**Generated:** {conversation_data.get('timestamp', 'Unknown')}")
                            st.divider()

                            # Display messages in chat format
                            for msg in messages:
                                role = msg.get('role', 'unknown')
                                content = msg.get('content', '')

                                if role == 'user':
                                    with st.chat_message("user"):
                                        st.markdown(content)
                                elif role == 'assistant':
                                    with st.chat_message("assistant"):
                                        st.markdown(content)
                        else:
                            st.info("No conversation messages found.")
                    except Exception as e:
                        st.error(f"Error loading conversation: {e}")
                        st.code(str(e))
                else:
                    st.info("💬 No conversation history found for this demo. This feature was added in a recent update.")

    else:
        st.info("👈 Select a demo from the sidebar to view details")


def main():
    """Main application entry point"""

    # Sidebar
    with st.sidebar:
        # Demo Builder header
        st.markdown("### Demo Builder")

        # Prominent mode toggle buttons with custom styling
        col1, col2 = st.columns(2)

        with col1:
            create_selected = st.session_state.view_mode == "create"
            if st.button(
                "Create",
                use_container_width=True,
                type="primary" if create_selected else "secondary",
                key="create_mode_btn"
            ):
                st.session_state.view_mode = "create"
                st.rerun()

        with col2:
            browse_selected = st.session_state.view_mode == "browse"
            if st.button(
                "Browse",
                use_container_width=True,
                type="primary" if browse_selected else "secondary",
                key="browse_mode_btn"
            ):
                st.session_state.view_mode = "browse"
                st.rerun()

        if st.session_state.view_mode == "create":
            display_context_summary()

            # Dataset size preference (only in create mode)
            st.markdown("---")
            st.markdown("#### Dataset Size")

            # Initialize dataset_size_preference if not exists
            if "dataset_size_preference" not in st.session_state:
                st.session_state.dataset_size_preference = "small"

            # Slider with options
            size_options = ["small", "medium", "large"]
            size_index = size_options.index(st.session_state.dataset_size_preference)

            selected_index = st.select_slider(
                "Size",
                options=range(len(size_options)),
                value=size_index,
                format_func=lambda x: size_options[x].capitalize(),
                key="dataset_size_slider",
                label_visibility="collapsed"
            )

            st.session_state.dataset_size_preference = size_options[selected_index]

            # Display legend based on selection
            size_legends = {
                "small": "**Small:** < 5,000 records per dataset",
                "medium": "**Medium:** 5,000-15,000 records per dataset",
                "large": "**Large:** 15,000-50,000 records per dataset"
            }

            st.caption(size_legends[st.session_state.dataset_size_preference])

            st.markdown("---")

            if st.button("🔄 Start Fresh", use_container_width=True):
                st.session_state.messages = []
                st.session_state.demo_context = {
                    "company_name": None,
                    "department": None,
                    "industry": None,
                    "pain_points": [],
                    "use_cases": [],
                    "metrics": [],
                    "scale": None,
                }
                st.session_state.conversation_phase = "initial"
                st.rerun()

            if st.button("📋 Use Test Prompt", use_container_width=True):
                test_prompt = """Salesforce's Customer Success team wants to prevent churn in their enterprise accounts. They manage 5,000+ accounts worth $10B in ARR but can only do quarterly business reviews. They need real-time health scores, usage analytics, and early warning signals. The CCO wants agents that can answer 'Which accounts are at risk this month and why?'"""
                st.session_state.messages.append({"role": "user", "content": test_prompt})
                st.session_state.needs_processing = True
                st.rerun()

            st.markdown("---")
            st.markdown("### 🔗 Elasticsearch")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Test Connection", use_container_width=True):
                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                    try:
                        indexer = ElasticsearchIndexer()
                        success, message = indexer.verify_connection()

                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")

            with col2:
                if st.button("Check ELSER", use_container_width=True):
                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                    try:
                        indexer = ElasticsearchIndexer()
                        is_ready, message = indexer.check_elser_deployment()

                        if is_ready:
                            st.success(f"✅ {message}")
                        else:
                            st.warning(f"⚠️ {message}")

                            # Offer to deploy
                            if "not deployed" in message.lower():
                                if st.button("Deploy ELSER", use_container_width=True):
                                    with st.spinner("Deploying ELSER..."):
                                        deploy_success, deploy_msg = indexer.deploy_elser()
                                        if deploy_success:
                                            st.success(f"✅ {deploy_msg}")
                                        else:
                                            st.error(f"❌ {deploy_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

            # Inference Endpoints Configuration
            st.markdown("---")
            st.markdown("### ⚙️ Inference Endpoints")

            # Initialize inference endpoints in session state if not exists
            if "inference_endpoints" not in st.session_state:
                st.session_state.inference_endpoints = {
                    "rerank": ".rerank-v1-elasticsearch",
                    "completion": "completion-vulcan"
                }

            # RERANK endpoint input
            rerank_endpoint = st.text_input(
                "RERANK Endpoint",
                value=st.session_state.inference_endpoints["rerank"],
                help="Inference endpoint ID for RERANK command (default: .rerank-v1-elasticsearch)",
                key="rerank_endpoint_input"
            )
            st.session_state.inference_endpoints["rerank"] = rerank_endpoint

            # COMPLETION endpoint input
            completion_endpoint = st.text_input(
                "COMPLETION Endpoint",
                value=st.session_state.inference_endpoints["completion"],
                help="Inference endpoint ID for COMPLETION command (default: completion-vulcan)",
                key="completion_endpoint_input"
            )
            st.session_state.inference_endpoints["completion"] = completion_endpoint

            # Show current values
            st.caption(f"🔄 RERANK: `{st.session_state.inference_endpoints['rerank']}`")
            st.caption(f"🤖 COMPLETION: `{st.session_state.inference_endpoints['completion']}`")

        else:  # Browse mode
            st.markdown("### 📚 Demo Modules")

            manager = DemoModuleManager()
            demos = manager.list_modules()

            if not demos:
                st.info("No demos yet. Switch to Create mode to make one!")
            else:
                # Show count
                st.caption(f"{len(demos)} modules")

                # List demos as clickable buttons
                for demo in demos:
                    # Make button show selected state
                    is_selected = st.session_state.current_demo_module == demo['name']
                    button_type = "primary" if is_selected else "secondary"

                    if st.button(
                        f"{demo.get('customer', 'Unknown')} - {demo.get('department', 'N/A')}",
                        key=f"select_{demo['name']}",
                        use_container_width=True,
                        type=button_type
                    ):
                        # Only rerun if selection changed
                        if st.session_state.current_demo_module != demo['name']:
                            st.session_state.current_demo_module = demo['name']
                            st.rerun()

    # Main content area
    if st.session_state.view_mode == "create":
        render_create_demo_view()
    else:
        render_browse_demos_view()


if __name__ == "__main__":
    main()
