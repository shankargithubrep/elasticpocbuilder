# Quick Start Guide
## One App for Everything

---

## 🚀 Getting Started

We've consolidated everything into **one unified app** that handles demo creation, browsing, and management.

### Launch the App
```bash
source venv/bin/activate
streamlit run app.py
```

The app will start at **http://localhost:8501**

---

## 🎯 Two Modes in One Interface

The app has two modes accessible via the sidebar:

### 1. **Create Demo** Mode
Conversational interface for building new custom demos
- ✅ Smart context extraction
- ✅ LLM-generated custom modules
- ✅ Test prompt button
- ✅ Real-time progress tracking

### 2. **Browse Demos** Mode
Library for managing all generated demo modules
- ✅ View all generated demos
- ✅ Inspect datasets, queries, and guides
- ✅ Delete unwanted modules
- ✅ Export and share modules

---

## 📝 Creating Your First Demo

### Step 1: Launch and Choose Mode

Start the app and ensure you're in **"Create Demo"** mode (default).

### Step 2: Provide Customer Context

You have two options:

#### Option A: Use the Test Prompt Button
Click **"📋 Use Test Prompt"** in the sidebar to try a pre-built Salesforce example.

#### Option B: Write Your Own Description

Paste a detailed customer description. The more detail, the better!

**❌ Poor Initial Prompts:**
- "I need a demo"
- "Customer analytics"
- "Show me ES|QL"

**✅ Excellent Initial Prompts:**
```
Salesforce's Customer Success team wants to prevent churn in their
enterprise accounts. They manage 5,000+ accounts worth $10B in ARR
but can only do quarterly business reviews. They need real-time
health scores, usage analytics, and early warning signals. The CCO
wants agents that can answer 'Which accounts are at risk this month
and why?'
```

```
Target's e-commerce team is struggling with cart abandonment and
wants to understand customer journey patterns. They process 2M+
transactions daily but lack visibility into drop-off points. They
need real-time fraud detection and personalized recommendations.
```

### Step 3: Watch the Magic Happen

As you provide information, the sidebar shows **extracted context**:

- 🏢 **Company:** Salesforce
- 🏭 **Industry:** Technology
- 👥 **Department:** Customer Success
- 📊 **Scale:** 10B ARR
- 🎯 **Pain Points:**
  - Lack of real-time visibility
  - Lack of predictive capabilities
- 📈 **Metrics:** Churn, Revenue, Risk

**Progress indicator** shows when you have enough context (≥50%) to generate.

### Step 4: Generate the Demo

When the assistant says you're ready, type:
```
Generate demo
```

The system will:
1. 🤖 **Generate custom Python modules** using LLM
2. 🏗️ **Create data generators** specific to the company's needs
3. 🔍 **Build ES|QL queries** that solve their problems
4. 📝 **Write demo guide** with talk track and objection handling

### Step 5: Access Your Demo Module

After generation completes, you'll see:
```
✅ Demo module created: salesforce_customer_success_20241021_143022

Generated:
- Custom data generator (3 datasets)
- ES|QL queries (8 queries)
- Demo guide and talk track

Next Steps:
1. Click "Browse Demos" to view all details
2. The module is saved in demos/salesforce_customer_success_20241021_143022/
```

---

## 📚 Browsing and Managing Demos

### Switch to Browse Mode

Click **"Browse Demos"** in the sidebar radio selector.

### View Demo Library

You'll see all generated demo modules with:
- Customer name
- Department
- Creation date
- Module path

### Inspect a Demo Module

Click **"🔍 View Details"** on any demo to see:

#### 📋 Config Tab
View the complete module configuration and customer context.

#### 🗂️ Data Tab
See generated datasets with:
- Sample data preview (first 10 rows)
- Total row counts
- Data types and relationships

#### 🔍 Queries Tab
View all ES|QL queries with:
- Query name and description
- Full ES|QL syntax
- Expected insights

#### 📝 Guide Tab
Read the complete demo guide including:
- Opening hook
- Demo flow
- Talk track for each query
- Objection handling

### Delete Unwanted Demos

Click **"🗑️ Delete"** to remove demo modules you no longer need.

---

## 🏗️ Understanding the Modular Architecture

### What Makes This Different?

Unlike traditional demo builders, this system uses **LLM-generated modules** that are:

1. **Customer-Specific**
   - Each demo gets custom Python code
   - Data generators match their business model
   - Queries solve their specific problems

2. **Reusable & Shareable**
   - Modules saved as Python files
   - Version controlled in Git
   - Can be refined and improved

3. **Maintainable**
   - Framework code stays stable
   - Each demo is isolated
   - Updates don't break existing demos

### Module Structure

Each demo creates a directory like:
```
demos/salesforce_customer_success_20241021_143022/
├── __init__.py              # Module init
├── config.json              # Customer context
├── data_generator.py        # Custom data generation
├── query_generator.py       # Custom ES|QL queries
└── demo_guide.py           # Demo narrative
```

### Customization After Generation

You can manually edit any generated module:

1. Navigate to `demos/your_module_name/`
2. Edit Python files directly
3. Re-run the demo to see changes
4. Share refined modules with your team

---

## 💡 Tips for Effective Demos

### Provide Rich Context

**Include:**
- Specific company name
- Department/team details
- Concrete pain points with examples
- Scale metrics (revenue, volume, users)
- Urgency indicators (meeting dates, timelines)

**Example:**
```
I'm presenting to Walmart's Supply Chain Operations next Monday.
They're struggling with inventory forecasting across 4,700 stores.
Current system takes 24 hours to update, causing $50M in excess
inventory costs. They need real-time visibility into stock levels
and predictive alerts for stockouts.
```

### Be Conversational

The assistant will ask follow-up questions. Respond naturally:

**Assistant:** "Which team at Walmart will be the primary users?"
**You:** "Supply chain managers and store operations - about 200 users"

### Use the Test Prompt

The **"📋 Use Test Prompt"** button shows a perfectly formatted example. Use it to:
- See what good context looks like
- Test the system quickly
- Learn the conversation flow

---

## 🎨 Special Features

### 💡 A-ha Moment (Coming Soon)

Currently showing as disabled button. Future feature will generate:
- Powerful demo moment that "wows" the customer
- Shows exactly how Agent Builder solves their biggest pain
- Includes specific metrics and business impact

### 🔄 Start Fresh

Clear all context and messages to begin a new demo.

### 📊 Context Progress Tracker

Watch the sidebar progress bar fill as you provide information:
- **< 50%**: Need more context
- **≥ 50%**: ✅ Ready to generate!

---

## 🔧 Behind the Scenes

### What Happens During Generation

1. **Module Setup** (< 1 sec)
   - Creates unique module directory
   - Initializes configuration

2. **LLM Code Generation** (5-10 sec)
   - Generates data_generator.py implementation
   - Creates query_generator.py with ES|QL queries
   - Writes demo_guide.py with narrative

3. **Module Execution** (2-5 sec)
   - Loads generated modules dynamically
   - Executes data generation
   - Runs query generation
   - Produces demo guide

4. **Save and Index** (< 1 sec)
   - Saves all artifacts
   - Indexes in module library
   - Ready for browsing

**Total Time:** ~10-20 seconds for complete custom demo

### Module Loading System

The framework uses **dynamic module loading**:

```python
# Framework loads your generated code at runtime
loader = ModuleLoader('demos/salesforce_customer_success_20241021/')
data_gen = loader.load_data_generator()
datasets = data_gen.generate_datasets()
```

This means:
- No static templates
- Pure customer-specific code
- Full Python flexibility

---

## 🐛 Troubleshooting

### App Won't Start

```bash
# Check if port is in use
lsof -i :8501

# Kill existing process
kill -9 <PID>

# Restart
source venv/bin/activate
streamlit run app.py
```

### Test Prompt Button Does Nothing

The button has been fixed! If it's not working:
1. Check browser console for errors
2. Refresh the page
3. Check that streamlit is running latest version

### Module Generation Fails

Check the logs in the terminal where streamlit is running. Common issues:
- Missing LLM API keys (will use mock generation)
- Invalid customer context
- Python syntax errors in generated code

### Can't See Generated Demos

1. Switch to "Browse Demos" mode
2. Check `demos/` directory exists
3. Verify config.json files are present

---

## 📊 Example Workflow

Here's a complete example session:

### 1. Start App
```bash
streamlit run app.py
```

### 2. Provide Context
```
Adobe's Marketing Operations team manages campaigns across 5 major
product lines (Creative Cloud, Document Cloud, Experience Cloud,
Commerce Cloud, and Advertising Cloud). They need real-time ROI
analytics across $2B in annual marketing spend. Current BI tool
takes hours to update, causing missed optimization opportunities.
```

### 3. Watch Sidebar Fill
- Company: Adobe ✅
- Industry: Technology ✅
- Department: Marketing ✅
- Scale: $2B ✅
- Pain Points: Performance issues ✅
- Progress: 71% ✅

### 4. Generate
```
Generate demo
```

### 5. Browse Results
- Switch to "Browse Demos"
- Click "View Details" on adobe_marketing_*
- Review datasets, queries, guide

### 6. Customize (Optional)
```bash
cd demos/adobe_marketing_operations_20241021_143022/
vim data_generator.py  # Add more columns
vim query_generator.py  # Add custom query
```

### 7. Share with Team
```bash
git add demos/adobe_marketing_*
git commit -m "Add Adobe marketing demo"
git push
```

---

## 🎯 Next Steps

### 1. Create Your First Demo
- Use test prompt or write your own
- Experience the full workflow
- Browse the generated module

### 2. Explore the Modular Architecture
- Read `docs/MODULAR_ARCHITECTURE.md`
- Inspect generated Python files
- Try customizing a module

### 3. Build Your Demo Library
- Create demos for different customers
- Reuse successful patterns
- Build industry templates

### 4. Connect to Elasticsearch (Optional)
- Add cluster details to `.env`
- Validate queries against real cluster
- Test with actual data ingestion

---

## 📚 Additional Resources

- **Architecture:** `docs/MODULAR_ARCHITECTURE.md`
- **Developer Guide:** `docs/DEVELOPER_GUIDE.md`
- **API Reference:** `docs/API_REFERENCE.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING_GUIDE.md`

---

*Ready to build? Run `streamlit run app.py` and create your first demo!*
