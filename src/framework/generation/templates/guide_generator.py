"""
Demo guide templates for module generation.

This module provides templates for generating demo guide modules
that create narrative documentation for demos.
"""

from typing import Dict, Any, List


def get_demo_guide_prompt(config: Dict[str, Any],
                         datasets_info: List[str],
                         queries_info: List[str]) -> str:
    """Get prompt for generating comprehensive demo guide content

    Creates a complete demo guide with setup instructions, query walkthrough,
    agent configuration, and Q&A talking points.

    Args:
        config: Demo configuration with company context
        datasets_info: List of dataset descriptions
        queries_info: List of query descriptions

    Returns:
        LLM prompt for generating comprehensive demo guide
    """
    # Template guide structure to show LLM the desired format
    template_guide = """# **Elastic Agent Builder Demo for {COMPANY}**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** {DEPARTMENT} technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered {DEMO_TYPE} on {COMPANY} data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

{DATASETS_SECTION}

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

{DATASET_UPLOAD_INSTRUCTIONS}

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent a complex business question."

**Sample questions to demonstrate:**

{TEASER_QUESTIONS}

**Transition:** "So how does this actually work? Let's go under the hood and build these queries from scratch."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "{COMPANY} wants to know: {SIMPLE_QUERY_QUESTION}"

**Copy/paste into console:**

```
{SIMPLE_QUERY}
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our data
- STATS: Aggregate with grouping
- SORT and LIMIT: Top results

The syntax is intuitive - it reads like English."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to get deeper insights."

**Copy/paste:**

```
{EVAL_QUERY}
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly
- TO_DOUBLE: Critical for decimal division
- Multiple STATS: Aggregating multiple metrics
- Business-relevant calculations

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine data from multiple sources using ES|QL's JOIN capability."

**Copy/paste:**

```
{JOIN_QUERY}
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines datasets using a join key
- Now we have access to fields from both datasets
- This is a LEFT JOIN: All records kept, enriched with additional data
- For LOOKUP JOIN to work, the joined index must have 'index.mode: lookup'"

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing {COMPLEX_QUERY_PURPOSE}"

**Copy/paste:**

```
{COMPLEX_QUERY}
```

**Run and break down:** {COMPLEX_QUERY_EXPLANATION}

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `{AGENT_ID}`

**Display Name:** `{AGENT_NAME}`

**Custom Instructions:** {AGENT_INSTRUCTIONS_SUMMARY}

---

### **Creating Tools**

{TOOLS_SUMMARY}

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

**Warm-up:**
{WARMUP_QUESTIONS}

**Business-focused:**
{BUSINESS_QUESTIONS}

**Trend analysis:**
{TREND_QUESTIONS}

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, built for analytics"
- "Piped syntax is intuitive and readable"
- "Operates on blocks, not rows - extremely performant"
- "Supports complex operations: joins, window functions, time-series"

### **On Agent Builder:**
- "Bridges AI and enterprise data"
- "No custom development - configure, don't code"
- "Works with existing Elasticsearch indices"
- "Agent automatically selects right tools"

### **On Business Value:**
- "Democratizes data access - anyone can ask questions"
- "Real-time insights, always up-to-date"
- "Reduces dependency on data teams"
- "Faster decision-making"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly
- Verify field names are case-sensitive correct
- Ensure joined indices are in lookup mode

**If agent gives wrong answer:**
- Check tool descriptions - are they clear?
- Review custom instructions

**If join returns no results:**
- Verify join key format is consistent across datasets
- Check that lookup index has data

---

## **🎬 Closing**

"What we've shown today:
✅ Complex analytics on interconnected datasets
✅ Natural language interface for non-technical users
✅ Real-time insights without custom development
✅ Queries that would take hours, answered in seconds

Agent Builder can be deployed in days, not months.

Questions?"
"""

    prompt = f"""Generate a comprehensive, detailed demo guide for an Elastic Agent Builder demonstration.

**Customer Context:**
- Company: {config['company_name']}
- Department: {config['department']}
- Industry: {config['industry']}
- Demo Type: {config.get('demo_type', 'analytics')}

**Pain Points:**
{chr(10).join('- ' + p for p in config.get('pain_points', [])[:5])}

**Use Cases:**
{chr(10).join('- ' + uc for uc in config.get('use_cases', [])[:5])}

**Available Datasets:**
{chr(10).join(datasets_info)}

**Key Queries:**
{chr(10).join(queries_info)}

**Your Task:**
Using the template structure provided below, generate a COMPLETE, DETAILED demo guide with:

1. **Real content** - Not placeholders. Use the actual company name, datasets, and query information provided above.

2. **Dataset Architecture section** - Describe each dataset with record counts, primary keys, fields, relationships. Be specific using the dataset info above.

3. **Demo Setup Instructions** - Specific steps for uploading CSVs and creating lookup mode indices for each dataset.

4. **Part 1: AI Agent Teaser** - 5-7 example questions that showcase different capabilities (ROI analysis, trend detection, cross-dataset joins, etc.)

5. **Part 2: ES|QL Query Building** - Create 3-4 progressive queries:
   - Query 1: Simple aggregation (2-3 lines)
   - Query 2: Add EVAL calculations (5-8 lines)
   - Query 3: LOOKUP JOIN enrichment (8-12 lines)
   - Query 4: Complex multi-dataset analytics (15-25 lines)

   Use ACTUAL query concepts from the key queries listed above. Make them realistic and runnable.

6. **Part 3: Agent & Tool Creation** - Summarize agent configuration with 3-4 key tool examples

7. **Part 4: Q&A Questions** - 10-12 diverse questions organized by category (warmup, business, trends, optimization)

8. **Talking Points** - Keep the standard ES|QL/Agent Builder/Business Value points from template

**CRITICAL FORMATTING RULES:**
- Output ONLY the markdown content (no code fences around the entire guide)
- Use proper markdown syntax
- Keep the emoji section headers (📋, 🗂️, 🚀, 🎯, etc.)
- Queries should be in ```esql``` code blocks
- Make it feel like a real internal demo script with specific, actionable content

**Template Structure to Follow:**
{template_guide}

Generate the complete guide now:"""

    return prompt


def get_demo_guide_module_template(config: Dict[str, Any], guide_content: str) -> str:
    """Get the Python module template for the demo guide class

    Creates a DemoGuideModule implementation with the generated guide content.

    Args:
        config: Demo configuration with company context
        guide_content: Generated markdown guide content

    Returns:
        Complete Python module code for demo guide
    """
    import re
    company_class = re.sub(r'[^a-zA-Z0-9_]', '', config['company_name'].replace(' ', ''))

    return f"""from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class {company_class}DemoGuide(DemoGuideModule):
    \"\"\"Demo guide for {config['company_name']} - {config['department']}\"\"\"

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        \"\"\"Initialize with demo context\"\"\"
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        \"\"\"Generate customized demo guide\"\"\"
        return '''{guide_content}'''

    def get_talk_track(self) -> Dict[str, str]:
        \"\"\"Talk track for each query\"\"\"
        # Can be customized per demo as needed
        return {{}}

    def get_objection_handling(self) -> Dict[str, str]:
        \"\"\"Common objections and responses\"\"\"
        return {{
            "complexity": "ES|QL syntax is SQL-like and easier than complex aggregations",
            "performance": "Queries run on indexed data with millisecond response times",
            "learning_curve": "Most teams productive within days, not weeks"
        }}
"""


def get_fallback_demo_guide(config: Dict[str, Any],
                           query_strategy: Dict[str, Any],
                           data_profile: Dict[str, Any]) -> str:
    """Generate basic fallback demo guide if LLM fails

    Provides a minimal but functional demo guide using available data.

    Args:
        config: Demo configuration
        query_strategy: Query strategy with available queries
        data_profile: Data profile information

    Returns:
        Fallback markdown guide content
    """
    pain_points = ', '.join(config.get('pain_points', [])[:2]) if config.get('pain_points') else 'operational challenges'

    datasets = query_strategy.get('datasets', [])
    queries = query_strategy.get('queries', [])

    dataset_list = '\n'.join([f"- **{d['name']}** ({d.get('type', 'unknown')} - {d.get('row_count', 'unknown')} records)"
                              for d in datasets[:5]])

    query_list = '\n'.join([f"{i+1}. **{q['name']}**" for i, q in enumerate(queries[:8])])

    return f"""# Demo Guide: {config['company_name']} - {config['department']}

## 📋 Demo Overview

**Industry:** {config['industry']}
**Focus Areas:** {pain_points}
**Total Time:** 25-30 minutes

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## 🗂️ Datasets

{dataset_list}

---

## 🚀 Key Queries

{query_list}

---

## 🎯 Value Proposition

- **Speed:** Insights in seconds vs hours/days
- **Scalability:** Handles growing data volumes
- **Self-Service:** Empowers teams with intuitive query language

---

## Closing Points

- ES|QL provides SQL-like simplicity with Elasticsearch power
- Queries run directly on indexed data (millisecond response times)
- Agent Builder enables natural language access to data
- Most teams productive within days, not weeks
"""
