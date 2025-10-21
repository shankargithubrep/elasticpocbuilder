# Quick Start Guide
## How to Use the Demo Builder UI

---

## 🚀 Which App to Use

We have three versions of the app, each with different capabilities:

### 1. **app_conversational.py** (RECOMMENDED TO START)
Best for first-time users with guided conversation flow
```bash
streamlit run app_conversational.py
```

**Features:**
- ✅ Onboarding with example prompts
- ✅ Guided conversation flow
- ✅ Context gathering tracker
- ✅ Help panel with tips
- ⚠️ Mock LLM responses (not connected to real LLM yet)

### 2. **app_enhanced.py**
Best for seeing the full validation workflow
```bash
streamlit run app_enhanced.py
```

**Features:**
- ✅ Task tracking with visual progress
- ✅ Validation panel
- ✅ GitHub state persistence
- ⚠️ Requires more technical knowledge

### 3. **app.py**
Basic version for simple interactions
```bash
streamlit run app.py
```

---

## 📝 How to Create Your First Demo

### Step 1: Start the Conversational App
```bash
source venv/bin/activate
streamlit run app_conversational.py
```

### Step 2: Use an Example Prompt or Create Your Own

#### Option A: Click an Example Button
The UI provides several example scenarios:
- 🏢 **Enterprise Customer** - Adobe marketing operations
- 🏥 **Healthcare Customer** - Kaiser patient flow
- 🏪 **Retail Customer** - Target e-commerce analytics
- 🏦 **Financial Services** - JPMorgan fraud detection

#### Option B: Write Your Own Prompt

**❌ Poor Initial Prompts:**
- "I need a demo"
- "Customer analytics"
- "Show me ES|QL"

**✅ Good Initial Prompts:**
- "I'm meeting with Adobe's marketing team next week. They manage campaigns across 5 brands and need better ROI visibility."
- "Target's e-commerce team wants to analyze customer journeys and detect fraud in real-time transactions."
- "I need to show Kaiser Permanente how to optimize patient flow in their emergency departments."

### Step 3: Engage in the Conversation

The assistant will ask clarifying questions. Be specific in your responses:

**Assistant:** "Which department at Adobe?"
**You:** "Marketing Operations - they manage Creative Cloud, Document Cloud, and Experience Cloud campaigns"

**Assistant:** "What are their main pain points?"
**You:** "They can't see cross-brand performance in real-time, and it takes hours to calculate campaign ROI"

**Assistant:** "What scale are we talking about?"
**You:** "Thousands of campaigns, millions of customer interactions daily"

### Step 4: Review and Confirm the Plan

The assistant will present a demo plan:
```
📋 Demo Summary:
- Customer: Adobe - Marketing Operations
- Use Case: Campaign Performance Analytics
- Datasets: Campaigns, Brand Assets, Customer Interactions
- Queries: ROI calculations, funnel analysis, anomaly detection
- Agent: Marketing Analytics Assistant
```

Type **"Generate demo"** to proceed.

### Step 5: Download Your Demo Package

After generation, you'll receive:
- 📝 **Demo Guide** - Complete walkthrough and talk track
- 🔍 **ES|QL Queries** - Validated and tested queries
- 📊 **Sample Data** - CSV files with realistic data
- 🤖 **Agent Config** - Ready to deploy configuration

---

## 💡 Tips for Effective Demos

### Information to Gather Before Starting

1. **Company Context**
   - Company name and industry
   - Size and scale of operations
   - Current technology stack

2. **Audience Details**
   - Department and team
   - Technical vs business audience
   - Decision makers present

3. **Business Challenges**
   - Specific pain points
   - Current workarounds
   - Cost of the problem

4. **Success Criteria**
   - What would impress them?
   - Key metrics they track
   - Desired outcomes

### During the Conversation

**Be Specific About:**
- Data volumes and velocity
- Types of queries they run
- Integration requirements
- Performance expectations

**Ask Yourself:**
- What would make them say "wow"?
- What's their biggest skepticism?
- How can I show immediate value?

---

## 🔧 Connecting to Real LLM (For Developers)

The current app uses mock responses. To connect to a real LLM:

### Option 1: Anthropic Claude
```python
# In app_conversational.py, add:
from anthropic import Anthropic
from src.prompts.conversation_prompts import DEMO_BUILDER_SYSTEM_PROMPT

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def process_user_message(message: str) -> str:
    context = {
        "company": st.session_state.demo_context["company_name"],
        "department": st.session_state.demo_context["department"],
        # ... other context
    }

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        system=DEMO_BUILDER_SYSTEM_PROMPT.format(**context),
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ] + [{"role": "user", "content": message}]
    )

    return response.content[0].text
```

### Option 2: OpenAI GPT-4
```python
# In app_conversational.py, add:
from openai import OpenAI
from src.prompts.conversation_prompts import DEMO_BUILDER_SYSTEM_PROMPT

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process_user_message(message: str) -> str:
    context = {
        "company": st.session_state.demo_context["company_name"],
        "department": st.session_state.demo_context["department"],
        # ... other context
    }

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": DEMO_BUILDER_SYSTEM_PROMPT.format(**context)},
            *[{"role": m["role"], "content": m["content"]}
              for m in st.session_state.messages],
            {"role": "user", "content": message}
        ]
    )

    return response.choices[0].message.content
```

---

## 🐛 Troubleshooting

### "Module not found" Error
```bash
# Ensure you're in virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### App Won't Start
```bash
# Check if port is in use
lsof -i :8501
# Kill process if needed
kill -9 <PID>
```

### Mock Mode for Testing
If you don't have Elasticsearch connected:
```bash
echo "ENABLE_MOCK_MODE=true" >> .env
```

### View Logs
```bash
# Run with debug logging
LOG_LEVEL=DEBUG streamlit run app_conversational.py
```

---

## 📊 What Happens Behind the Scenes

When you type **"Generate demo"**, the system:

1. **Customer Research** (< 1 second)
   - Analyzes company and industry
   - Identifies relevant pain points
   - Suggests appropriate use cases

2. **Scenario Generation** (< 1 second)
   - Creates business scenario
   - Defines dataset relationships
   - Plans query progression

3. **Data Generation** (~ 5 seconds)
   - Creates synthetic datasets
   - Maintains referential integrity
   - Generates 100K+ records

4. **Query Generation** (< 1 second)
   - Creates ES|QL queries
   - Validates syntax
   - Auto-fixes common issues

5. **Validation** (~ 5 seconds with Elasticsearch)
   - Tests each query
   - Captures performance metrics
   - Ensures all queries work

6. **Agent Configuration** (< 1 second)
   - Creates tool definitions
   - Writes agent instructions
   - Generates test conversations

Total time: **< 15 seconds** for complete demo generation

---

## 🎯 Next Steps

1. **Try Different Scenarios**
   - Test with various industries
   - Explore different use cases
   - Vary the complexity level

2. **Connect to Elasticsearch**
   - Add your cluster details to `.env`
   - Run with real validation
   - Test query execution

3. **Customize Templates**
   - Add industry templates in `customer_researcher.py`
   - Create query patterns in `esql_generator.py`
   - Design scenarios in `scenario_generator.py`

4. **Share Feedback**
   - What worked well?
   - What was confusing?
   - What features would help?

---

*Ready to create your first demo? Start with `streamlit run app_conversational.py`!*