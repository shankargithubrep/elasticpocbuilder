"""
Help Chat Service - LLM-powered contextual assistance for Elastic POC Builder.

Provides:
- Contextual help responses based on current UI state
- Pre-built FAQ responses for common questions
- Integration with CLAUDE.md documentation
- Semantic search over indexed documentation (when enabled)
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.services.llm_proxy_service import UnifiedLLMClient

logger = logging.getLogger(__name__)


# Try to import doc indexer (may not be available if ES not configured)
try:
    from src.services.doc_indexer_service import get_doc_indexer
    DOC_INDEXER_AVAILABLE = True
except ImportError:
    DOC_INDEXER_AVAILABLE = False
    logger.warning("Doc indexer service not available")


# Pre-built FAQ responses for common chip questions
# These avoid LLM calls for frequently asked questions
FAQ_RESPONSES = {
    # Universal FAQ - appears in all contexts
    "How do I use this app?": """
**Getting Started with Elastic POC Builder**

**1. Check Your Setup** (expand Status in sidebar)
- Verify LLM and Elasticsearch are connected
- Both should show green checkmarks

**2. Create a Demo**
Write a customer description including:
- **Company & Department** - Who you're demoing to
- **Pain Points** - What problems they face
- **Desired Outcomes** - What success looks like

**Example prompt:**
> "Acme Corp's Support team handles 10K tickets/month but lacks visibility into trends. They want to identify recurring issues and predict escalations."

**3. Configure Generation Options** (sidebar)
- **Demo Complexity**: Use "Expanded" for brief prompts (LLM enhances your description, generates 5-10 datasets)
- **Dataset Size**: Medium is a good default
- **Data Generation Mode**: Advanced for analytics demos with aggregations

**4. Browse & Refine**
After generation, switch to Browse mode to:
- View generated datasets
- Test and validate queries
- Deploy tools to Agent Builder

**Pro Tips:**
- Be specific about metrics and KPIs
- Check the Status section if something isn't working
""",

    # Create mode FAQs
    "How should I format my prompt?": """
**Formatting Your Demo Prompt**

For best results, include:
1. **Company name** - The customer you're building for
2. **Department/Team** - Who will use this (Sales, Support, etc.)
3. **Industry** - Healthcare, Finance, Retail, etc.
4. **Pain points** - What problems they're trying to solve
5. **Key metrics** - What they want to measure or track

**Example:**
> "We're building a demo for Acme Corp's Customer Success team. They're in the SaaS industry and struggle with churn prediction. Key metrics include NPS, ticket resolution time, and renewal rates."

You can be brief or detailed - the "Expanded" complexity mode will enhance brief prompts automatically.
""",

    "Search vs Analytics demos?": """
**Search vs Analytics Demo Types**

**Search/RAG Demos** are for:
- Finding specific documents or records
- Knowledge base search
- Semantic search with natural language
- RAG (Retrieval Augmented Generation) applications

Uses: `MATCH`, `QSTR`, `RERANK`, `COMPLETION` commands

**Analytics Demos** are for:
- Aggregating data and finding trends
- Dashboards and reporting
- Time-series analysis
- Cross-dataset joins and enrichment

Uses: `STATS`, `INLINESTATS`, `LOOKUP JOIN`, `DATE_TRUNC` commands

The system auto-detects based on your description, or you can manually select.
""",

    "What makes a good description?": """
**Writing Effective Demo Descriptions**

A good description answers:
- **Who** is this for? (company, team, role)
- **What** problem does it solve?
- **Why** do they need it? (pain points, business impact)
- **How** will they measure success? (KPIs, metrics)

**Tips:**
- Include industry context (healthcare has HIPAA, finance has compliance)
- Mention data scale ("500k transactions/month")
- List 2-3 specific use cases
- Be specific about the "aha moment" you want to create

The more context you provide, the more tailored your demo will be.
""",

    "What is expanded mode?": """
**Expanded vs Standard Complexity**

**Standard Mode:**
- Uses your prompt as-is
- Best for detailed, comprehensive descriptions
- Faster generation

**Expanded Mode:**
- AI enhances your brief prompt into detailed context
- Great for quick starts: "Demo for healthcare call center"
- Adds industry-specific details and best practices
- Takes slightly longer but produces richer demos

Use Expanded when you have a short description and want the AI to fill in the gaps.
""",

    # Browse/Data tab FAQs
    "How do I index this data?": """
**Indexing Data to Elasticsearch**

1. **Index All**: Click "Index All Datasets" to index everything at once
2. **Index Individual**: Use the "Index" button next to each dataset

**What happens:**
- Data is sent to your connected Elasticsearch cluster
- Indices are created with appropriate mappings
- Semantic fields get embeddings automatically

**Prerequisites:**
- Valid Elasticsearch connection (check sidebar)
- ELSER model deployed (for semantic search)

After indexing, you can test queries in the Queries tab.
""",

    "What do these fields mean?": """
**Understanding Dataset Fields**

Each dataset has fields with specific purposes:

**Common Field Types:**
- `keyword` - Exact match text (IDs, categories, status)
- `text` - Full-text searchable content
- `semantic_text` - Vector-embedded for semantic search
- `date` / `@timestamp` - Time-based data
- `integer` / `float` - Numeric values
- `boolean` - True/false flags

**Special Fields:**
- `@timestamp` - Required for time-series/data streams
- Fields ending in `.keyword` - Exact match version of text fields

View the "Profile" for each dataset to see field statistics.
""",

    "Can I modify the data?": """
**Modifying Generated Data**

**Option 1: Edit the source code**
Navigate to `demos/{module_name}/data_generator.py` and modify the generation logic.

**Option 2: Regenerate**
In the Config tab, click "Regenerate Assets" to generate new data.

**Option 3: Manual CSV edit**
1. Download the CSV using the download button
2. Edit in your preferred tool
3. Re-index the modified data manually

Note: Regenerating will overwrite existing data. Consider backing up first.
""",

    # Browse/Queries tab FAQs
    "How do I test a query?": """
**Testing ES|QL Queries**

1. **Ensure data is indexed** - Check the Data tab
2. **Click Execute** - Runs the query against your cluster
3. **View results** - Results appear below the query

**Query validation states:**
- **Untested** - Query hasn't been executed yet
- **Validated** - Query ran successfully
- **Modified** - Query was edited since last validation

For parameterized queries, fill in the parameter values first.
""",

    "What does validation mean?": """
**Query Validation Status**

Validation tracks whether queries work correctly:

- **Untested** (gray) - Never executed
- **Validated** (green checkmark) - Ran successfully
- **Modified** (yellow) - Edited since last validation, needs re-test

**Why validate?**
- Ensures queries work before deploying as tools
- Catches syntax errors or missing fields
- Required before deploying to Agent Builder

Click "Execute" to validate a query. The status updates automatically.
""",

    "How to edit and re-run?": """
**Editing and Re-running Queries**

1. **Enable edit mode** - Check the "Edit" checkbox
2. **Modify the query** - Edit in the text area
3. **Execute** - Click to run your modified query
4. **Save** - Changes are auto-saved when you execute

**Tips:**
- Use the original query as a template
- Test small changes incrementally
- If you break it, regenerate from Config tab

Edited queries are marked as "Modified" until re-validated.
""",

    # Browse/Tools tab FAQs
    "How do I deploy a tool?": """
**Deploying Tools to Agent Builder**

1. **Validate the query first** - Tools require validated queries
2. **Fill in tool metadata** - Name and description
3. **Click Deploy** - Sends to Agent Builder

**Tool metadata:**
- **Name**: Short identifier (e.g., "customer_health_score")
- **Description**: What the tool does (shown to the AI agent)

After deployment, the tool appears in your Agent Builder workspace.
""",

    "What is tool metadata?": """
**Understanding Tool Metadata**

Tool metadata tells Agent Builder how to use your ES|QL query:

- **Tool ID**: Unique identifier (auto-generated from name)
- **Name**: Human-readable name
- **Description**: Explains what the tool does - this is critical!
  - The AI agent reads this to decide when to use the tool
  - Be specific: "Calculates customer health score based on engagement metrics"

**For parameterized tools:**
- Parameter descriptions tell the agent what values to provide
- Include examples: "customer_id (e.g., 'CUST-12345')"
""",

    # Browse/Agents tab FAQs
    "How do I create an agent?": """
**Creating an Agent in Agent Builder**

1. **Deploy tools first** - Agents need tools to work with
2. **Configure agent settings**:
   - Name and description
   - System instructions (personality/guidelines)
   - Available tools
3. **Click Create Agent** - Sends to Agent Builder

**Tips:**
- Start with 2-3 focused tools
- Write clear system instructions
- Test the agent in Agent Builder chat interface
""",

    "How do I assign tools?": """
**Assigning Tools to Agents**

Tools are assigned when creating or updating an agent:

1. **Available tools** - Shows all deployed tools
2. **Select tools** - Check the ones this agent should use
3. **Save/Create** - Agent is updated with new tools

**Best practices:**
- Group related tools together
- Don't give an agent too many tools (5-7 max)
- Write tool descriptions that help the agent choose correctly
""",

    # Browse/Guide tab FAQs
    "How do I use this guide?": """
**Using the Demo Guide**

The guide is your demo script with:

1. **Talk track** - What to say during the demo
2. **Key queries** - Which queries to show and why
3. **Insights** - What patterns to highlight
4. **"Aha moments"** - Where to pause for impact

**Tips:**
- Practice the flow before the actual demo
- Adapt the talk track to your audience
- Have backup queries ready
- Know the data well enough to improvise
""",

    "Can I customize the guide?": """
**Customizing the Demo Guide**

**Option 1: Edit directly**
Navigate to `demos/{module_name}/demo_guide.py` and modify the content.

**Option 2: Regenerate**
Use "Regenerate Assets" in Config tab for a fresh guide.

**What to customize:**
- Talk track language and tone
- Emphasis on specific features
- Industry-specific terminology
- Customer-specific examples

The guide is generated Python code, so you can also add conditional logic for different audiences.
""",
}


class HelpChatService:
    """
    LLM-powered contextual help service for Elastic POC Builder.

    Provides intelligent responses about using the demo-builder,
    with awareness of current UI context (mode, tab, loaded module).

    Enhanced with semantic search over indexed documentation when available.
    """

    def __init__(self):
        """Initialize the help chat service."""
        self.llm_client = None
        self._doc_indexer = None
        self.system_prompt = self._build_system_prompt()
        self._initialize_llm()
        self._initialize_doc_search()

    def _initialize_llm(self):
        """Initialize LLM client with error handling."""
        try:
            self.llm_client = UnifiedLLMClient()
            if not self.llm_client._proxy_client.is_available():
                logger.warning("LLM not available, help chat will use FAQ-only mode")
                self.llm_client = None
        except Exception as e:
            logger.error(f"Failed to initialize LLM for help chat: {e}")
            self.llm_client = None

    def _initialize_doc_search(self):
        """Initialize documentation search service if available."""
        if not DOC_INDEXER_AVAILABLE:
            logger.info("Doc indexer not available - semantic doc search disabled")
            return

        try:
            self._doc_indexer = get_doc_indexer()
            if self._doc_indexer.is_available() and self._doc_indexer.check_index_exists():
                logger.info("Doc indexer connected - semantic doc search enabled")
            else:
                logger.info("Doc indexer available but index not created yet")
        except Exception as e:
            logger.warning(f"Could not initialize doc indexer: {e}")
            self._doc_indexer = None

    def is_doc_search_enabled(self) -> bool:
        """Check if documentation search is available and enabled."""
        if not self._doc_indexer:
            return False
        return self._doc_indexer.is_available() and self._doc_indexer.check_index_exists()

    def _search_documentation(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Search indexed documentation for relevant content.

        Args:
            query: User's question
            limit: Max results to return

        Returns:
            List of relevant doc chunks with content previews
        """
        if not self.is_doc_search_enabled():
            return []

        try:
            results = self._doc_indexer.search_docs(query, limit=limit)
            return results
        except Exception as e:
            logger.warning(f"Doc search failed: {e}")
            return []

    def _format_doc_context(self, doc_results: List[Dict[str, Any]]) -> str:
        """Format documentation search results for LLM context."""
        if not doc_results:
            return ""

        parts = ["## Relevant Documentation\n"]

        for i, doc in enumerate(doc_results, 1):
            title = doc.get("doc_title", "Unknown")
            section = doc.get("section_title", "")
            preview = doc.get("content_preview", "")
            category = doc.get("doc_category", "")

            parts.append(f"### {i}. {title}")
            if section:
                parts.append(f"**Section:** {section}")
            if category:
                parts.append(f"**Category:** {category}")
            parts.append(f"\n{preview}\n")

        return "\n".join(parts)

    def _build_system_prompt(self) -> str:
        """Build system prompt with CLAUDE.md documentation."""
        base_prompt = """You are the Elastic POC Builder Help Assistant, an expert guide for the Elastic POC Builder demo-builder platform.

Your role is to help users understand and effectively use Elastic POC Builder to create Elastic Agent Builder demonstrations.

Key responsibilities:
- Explain features and workflows clearly
- Provide actionable guidance
- Answer questions about ES|QL, Elasticsearch, and Agent Builder
- Help troubleshoot issues

Communication style:
- Be concise but thorough
- Use bullet points and formatting for clarity
- Provide examples when helpful
- Be encouraging and supportive

"""
        # Load CLAUDE.md for comprehensive context
        claude_md_content = self._load_claude_md()
        if claude_md_content:
            base_prompt += f"""
Here is comprehensive documentation about Elastic POC Builder:

{claude_md_content}

Use this documentation to provide accurate, detailed answers about the platform.
"""

        return base_prompt

    def _load_claude_md(self) -> Optional[str]:
        """Load CLAUDE.md content for system prompt."""
        try:
            # Try multiple possible locations
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "CLAUDE.md",
                Path.cwd() / "CLAUDE.md",
            ]

            for path in possible_paths:
                if path.exists():
                    content = path.read_text()
                    logger.info(f"Loaded CLAUDE.md from {path}")
                    return content

            logger.warning("CLAUDE.md not found in expected locations")
            return None

        except Exception as e:
            logger.error(f"Failed to load CLAUDE.md: {e}")
            return None

    def get_faq_response(self, question: str) -> Optional[str]:
        """
        Check if question matches a pre-built FAQ response.

        Args:
            question: User's question

        Returns:
            FAQ response if matched, None otherwise
        """
        # Direct match
        if question in FAQ_RESPONSES:
            return FAQ_RESPONSES[question]

        # Fuzzy match (lowercase, strip punctuation)
        normalized = question.lower().strip().rstrip("?")
        for faq_question, response in FAQ_RESPONSES.items():
            faq_normalized = faq_question.lower().strip().rstrip("?")
            if normalized == faq_normalized:
                return response

        return None

    def get_response(
        self,
        user_message: str,
        context: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a contextual help response.

        Enhanced with semantic documentation search when available.

        Args:
            user_message: User's question or message
            context: Current UI context (mode, tab, module info, etc.)
            chat_history: Previous messages in the conversation

        Returns:
            Help response string
        """
        # First, check for FAQ match (avoids LLM call)
        faq_response = self.get_faq_response(user_message)
        if faq_response:
            return faq_response

        # If no LLM available, provide graceful fallback
        if not self.llm_client:
            return self._fallback_response(user_message, context)

        # Search documentation for relevant context (if enabled)
        doc_results = self._search_documentation(user_message)
        doc_context = self._format_doc_context(doc_results)

        # Build enhanced system prompt with doc context
        enhanced_prompt = self._build_enhanced_prompt(context, doc_context)

        # Build messages for LLM
        messages = self._build_messages(user_message, context, chat_history)

        try:
            response = self.llm_client.create(
                messages=messages,
                system=enhanced_prompt,
                max_tokens=1000,
                temperature=0.7
            )
            return response.content[0].text

        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return self._fallback_response(user_message, context)

    def _build_enhanced_prompt(
        self,
        context: Dict[str, Any],
        doc_context: str
    ) -> str:
        """
        Build enhanced system prompt with context and doc search results.

        Args:
            context: Current UI context
            doc_context: Formatted documentation search results

        Returns:
            Enhanced system prompt string
        """
        prompt_parts = [self.system_prompt]

        # Add current context section
        context_section = self._format_enhanced_context(context)
        if context_section:
            prompt_parts.append(f"\n## Current Context\n{context_section}")

        # Add doc search results
        if doc_context:
            prompt_parts.append(f"\n{doc_context}")

        return "\n".join(prompt_parts)

    def _format_enhanced_context(self, context: Dict[str, Any]) -> str:
        """Format enhanced context for system prompt."""
        parts = []

        # New user indicator
        if context.get("is_new_user"):
            parts.append("**User Status:** New user (no demos created yet)")

        # Mode and location
        mode = context.get("mode", "unknown")
        parts.append(f"**Mode:** {mode.title()}")

        if mode == "create":
            # Create mode specific context
            phase = context.get("conversation_phase", "initial")
            parts.append(f"**Conversation Phase:** {phase}")

            demo_ctx = context.get("demo_context", {})
            if demo_ctx:
                if demo_ctx.get("company"):
                    parts.append(f"**Company:** {demo_ctx['company']}")
                if demo_ctx.get("industry"):
                    parts.append(f"**Industry:** {demo_ctx['industry']}")
                if demo_ctx.get("demo_type"):
                    parts.append(f"**Demo Type:** {demo_ctx['demo_type']}")

        elif mode == "browse":
            # Browse mode specific context
            tab = context.get("tab", "config")
            parts.append(f"**Current Tab:** {tab}")

            if context.get("module_name"):
                parts.append(f"**Module:** {context['module_name']}")

            if context.get("module_summary"):
                parts.append(f"**Module Details:** {context['module_summary']}")

            # Data profile
            data_profile = context.get("data_profile_summary", {})
            if data_profile:
                datasets_info = ", ".join(
                    f"{name} ({info.get('records', '?')} records)"
                    for name, info in data_profile.items()
                )
                parts.append(f"**Datasets:** {datasets_info}")

            # Query status with errors
            query_status = context.get("query_status", {})
            if query_status:
                validated = query_status.get("validated", 0)
                failed = query_status.get("failed", 0)
                total = query_status.get("total", 0)
                parts.append(f"**Query Status:** {validated}/{total} validated, {failed} failed")

                # Include sample errors if present
                sample_errors = query_status.get("sample_errors", [])
                if sample_errors:
                    parts.append("**Recent Query Errors:**")
                    for err in sample_errors[:2]:
                        parts.append(f"  - {err.get('query_id', 'unknown')}: {err.get('error', 'Unknown error')[:100]}")

        return "\n".join(parts) if parts else ""

    def _build_messages(
        self,
        user_message: str,
        context: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Build message list for LLM request."""
        messages = []

        # Add context as a system-like user message
        context_msg = self._format_context(context)
        if context_msg:
            messages.append({
                "role": "user",
                "content": f"[Current Context]\n{context_msg}"
            })
            messages.append({
                "role": "assistant",
                "content": "I understand the current context. How can I help?"
            })

        # Add chat history
        if chat_history:
            for msg in chat_history[-6:]:  # Keep last 6 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into readable string."""
        if not context:
            return ""

        parts = []

        # Mode
        mode = context.get("mode", "unknown")
        parts.append(f"Mode: {mode}")

        # Tab (for browse mode)
        if mode == "browse" and context.get("tab"):
            parts.append(f"Current Tab: {context['tab']}")

        # Module info
        if context.get("module_name"):
            parts.append(f"Selected Module: {context['module_name']}")

        # Module summary (if available)
        if context.get("module_summary"):
            parts.append(f"Module Details: {context['module_summary']}")

        # Dataset info
        if context.get("datasets"):
            dataset_info = ", ".join(
                f"{d['name']} ({d.get('record_count', '?')} records)"
                for d in context["datasets"][:3]
            )
            parts.append(f"Datasets: {dataset_info}")

        # Query info
        if context.get("query_count"):
            parts.append(f"Queries: {context['query_count']} total")

        return "\n".join(parts)

    def _fallback_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Provide fallback response when LLM is unavailable."""
        mode = context.get("mode", "unknown")

        # Mode-specific fallback
        if mode == "create":
            return """I'm currently in FAQ-only mode (LLM unavailable).

**Quick Tips for Create Mode:**
- Provide company name, department, and industry
- Describe pain points and use cases
- Mention key metrics you want to track
- Use "Expanded" mode for brief prompts

Click the suggestion chips above for more detailed help on specific topics."""

        elif mode == "browse":
            tab = context.get("tab", "")
            return f"""I'm currently in FAQ-only mode (LLM unavailable).

**Quick Tips for {tab.title()} Tab:**
Click the suggestion chips above for detailed help on:
- How to use features in this tab
- Common workflows and best practices
- Troubleshooting tips

For general questions, check the docs/ folder in the project."""

        else:
            return """I'm currently in FAQ-only mode (LLM unavailable).

Click the suggestion chips for help on common topics, or check the documentation in the docs/ folder."""

    def is_available(self) -> bool:
        """Check if full LLM-powered help is available."""
        return self.llm_client is not None


# Singleton instance for reuse
_help_service_instance: Optional[HelpChatService] = None


def get_help_service() -> HelpChatService:
    """Get or create the help chat service singleton."""
    global _help_service_instance
    if _help_service_instance is None:
        _help_service_instance = HelpChatService()
    return _help_service_instance
