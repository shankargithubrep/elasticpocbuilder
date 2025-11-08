# Skills Quick Start Guide

Get started with Claude Code Skills for Demo Builder in under 10 minutes.

## What Are Skills?

Skills are specialized capabilities that extend Claude Code to automate demo preparation tasks. Instead of manually creating slides, writing scripts, or testing queries, you simply ask Claude to do it.

## Available Skills

| Skill | Purpose | Example Use |
|-------|---------|-------------|
| **esql-validator** | Test queries against live Elasticsearch | "Validate queries in demos/acme_sales/" |
| **google-slides-generator** | Create presentation decks | "Create slides for the Acme demo" |
| **google-docs-generator** | Generate demo scripts with talk tracks | "Create a demo script for this module" |
| **agent-builder** | ES\|QL patterns and best practices | Automatically used during generation |

## Quick Start: 3 Steps

### Step 1: Configure MCP (One-Time Setup)

Skills use MCP (Model Context Protocol) to connect to Elasticsearch. This enables real-time query validation.

**Prerequisites**:
- Elastic Cloud deployment or self-managed cluster
- Kibana 8.17.0 or later
- API key with read permissions

**Setup** (5 minutes):

1. Generate API key in Kibana:
   - Search "API keys" in Kibana
   - Create new key with read access to your indices

2. Add configuration to `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "elastic-agent-builder": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://your-deployment.kb.region.gcp.cloud.es.io:9243/api/agent_builder/mcp",
        "--header",
        "Authorization:ApiKey YOUR_API_KEY_HERE"
      ]
    }
  }
}
```

3. Restart Claude Code

**Detailed Guide**: See [MCP_CONFIGURATION_GUIDE.md](./MCP_CONFIGURATION_GUIDE.md)

### Step 2: Generate a Demo

Use the Streamlit UI or Claude Code:

**Via Streamlit UI**:
```bash
streamlit run app.py
# Paste customer description → Generate demo
```

**Via Claude Code**:
```
You: "Create a demo for Acme Corp's sales team tracking deal pipeline and churn risk"

Claude: [Generates demo module in demos/acme_sales_20241023_140512/]
```

### Step 3: Use Skills to Enhance

Now leverage Skills to create a complete package:

#### Validate Queries
```
You: "Validate all queries in demos/acme_sales_20241023_140512/"

Claude:
✅ Query validation complete
- Pipeline Overview: 234 rows, 156ms
- Churn Risk: Auto-fixed division, 47 rows, 89ms
- Revenue Forecast: 156 rows, 234ms

All queries ready for demo!
```

#### Generate Slides
```
You: "Create slides for the Acme Corp demo"

Claude: [Generates Google Slides presentation]
📊 Presentation created: https://docs.google.com/presentation/d/...
- 15 slides
- Includes ES|QL queries with syntax highlighting
- Business value messaging
- Architecture diagrams
```

#### Generate Demo Script
```
You: "Create a demo script for this module"

Claude: [Generates Google Docs script]
📝 Demo script created: https://docs.google.com/document/d/...
- Complete talk track (25 minutes)
- Objection handling
- Pre-demo checklist
- Timing cues
```

## Common Workflows

### Workflow 1: Complete Demo Package

**Goal**: Generate everything needed for a customer demo

```
1. You: "Create demo for [Company] [Department] tracking [Use Cases]"
   → Claude generates module

2. You: "Validate queries in demos/[module_name]/"
   → Claude tests queries via Elasticsearch

3. You: "Create slides for this demo"
   → Claude generates presentation

4. You: "Create demo script for this module"
   → Claude generates delivery guide

Total Time: ~30 minutes
Deliverables: Python code + Slides + Script + Validated queries
```

### Workflow 2: Fix Failing Queries

**Goal**: Debug and fix query errors before demo

```
You: "This query is failing: FROM accounts | STATS churn = churned / total"

Claude:
1. Analyzes query
2. Detects integer division issue
3. Auto-fixes: "STATS churn = TO_DOUBLE(churned) / total"
4. Validates via Elasticsearch
5. Reports: "✅ Fixed! Query returns 47 rows in 89ms"
```

### Workflow 3: Refresh Existing Demo

**Goal**: Update old demo with new queries and materials

```
1. You: "Add a query to demos/acme_sales_20241023/ for identifying expansion opportunities"
   → Claude updates query_generator.py

2. You: "Validate the new query"
   → Claude tests via Elasticsearch

3. You: "Update the slides to include this new query"
   → Claude regenerates slides with new content

4. You: "Update the demo script"
   → Claude updates delivery guide
```

## Skill Usage Examples

### ES|QL Validator

**Validate Single Query**:
```
You: "Validate this query: FROM accounts | WHERE status == 'active' | STATS total = COUNT(*)"

Claude: ✅ Query valid. Returned 1 row in 45ms.
```

**Validate All Queries in Module**:
```
You: "Validate demos/acme_sales_20241023/"

Claude: [Runs validation report]
```

**Fix Failing Query**:
```
You: "Fix this query: FROM transactions | STATS total = SUM(amount) | LOOKUP JOIN customers"

Claude: [Analyzes, detects JOIN/STATS order issue, fixes and validates]
```

### Google Slides Generator

**Generate from Demo Module**:
```
You: "Create slides for demos/acme_sales_20241023/"

Claude: [Generates 15-slide deck with company branding]
```

**Customize Slide Content**:
```
You: "Make the slides more technical, include query explain plans"

Claude: [Adjusts slide content for technical audience]
```

### Google Docs Generator

**Generate Demo Script**:
```
You: "Create demo script for demos/acme_sales_20241023/"

Claude: [Generates complete script with talk tracks]
```

**Add Objection Handling**:
```
You: "Add responses for objections about data security and compliance"

Claude: [Updates script with security/compliance responses]
```

## Troubleshooting

### MCP Not Working

**Symptom**: Claude says "Elasticsearch MCP server not configured"

**Fix**:
1. Verify `.claude/settings.local.json` exists
2. Check Kibana URL is correct (no trailing slash)
3. Verify API key is valid: `curl -H "Authorization: ApiKey YOUR_KEY" https://YOUR_KIBANA_URL/api/status`
4. Restart Claude Code

### Queries Fail Validation

**Symptom**: Validation report shows failures

**Common Causes**:
- **Data not indexed**: Load demo data into Elasticsearch first
- **Wrong index names**: Check FROM clause matches actual indices
- **Field name mismatches**: Verify field names in index mapping
- **Permission issues**: Ensure API key has read access

**Fix**:
1. Check index exists: `GET /your_index_name` in Kibana Dev Tools
2. Verify data loaded: `GET /your_index_name/_count`
3. Check field mappings: `GET /your_index_name/_mapping`

### Skills Not Triggering

**Symptom**: Claude doesn't use Skills automatically

**Fix**:
1. Be explicit in your request: "Use the esql-validator skill to..."
2. Check Skill files exist in `.claude/skills/`
3. Verify YAML frontmatter is correct
4. Restart Claude Code to reload Skills

### Google API Integration

**Note**: Google Slides/Docs generators require Google API setup (not yet implemented).

**Current Status**:
- Skills define the structure and content
- Manual Google API integration required
- Alternative: Claude generates markdown that you convert to slides/docs

**Future Enhancement**: Automated Google API integration

## Best Practices

### When to Use Skills

✅ **Do Use**:
- Before every customer demo (validate queries)
- After generating new modules (create slides/script)
- When debugging query errors (auto-fix)
- For performance testing (execution benchmarks)

❌ **Don't Use**:
- During initial exploration (not needed yet)
- For simple single queries (just run in Kibana)
- When Elasticsearch is unavailable (can't validate)

### Skill Combinations

**Best Results**: Use Skills together

```
Generate → Validate → Slides → Script = Complete Package
```

**Why**: Each Skill enhances the output of previous steps:
1. **Generate**: Creates base demo module
2. **Validate**: Ensures queries work and auto-fixes issues
3. **Slides**: Presents validated queries in visual format
4. **Script**: Provides talk track for validated queries

### Performance Tips

- **Validate Early**: Catch query errors before creating slides/script
- **Batch Operations**: Validate all queries at once, not one-by-one
- **Cache Results**: Don't re-validate unchanged queries
- **Use Test Data**: Start with small datasets for faster validation

## Next Steps

### Learn More

- **MCP Configuration**: [MCP_CONFIGURATION_GUIDE.md](./MCP_CONFIGURATION_GUIDE.md)
- **Architecture**: [MODULAR_ARCHITECTURE.md](./MODULAR_ARCHITECTURE.md)
- **Development**: [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)
- **Skills Best Practices**: [Claude Skills Docs](https://docs.claude.com/en/docs/claude-code/skills)

### Advanced Usage

- **Custom Skills**: Create project-specific Skills in `.claude/skills/`
- **Skill Chaining**: Build workflows that combine multiple Skills
- **Testing Integration**: Use esql-validator in CI/CD pipeline
- **Template Customization**: Modify slide/script templates

### Get Help

- **MCP Issues**: Check [MCP_CONFIGURATION_GUIDE.md](./MCP_CONFIGURATION_GUIDE.md) troubleshooting
- **Skill Questions**: Review individual Skill docs in `.claude/skills/`
- **Demo Builder Issues**: See [CLAUDE.md](../CLAUDE.md) project guide
- **Claude Code**: Visit [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)

## Quick Reference

### Essential Commands

```bash
# Run Demo Builder UI
streamlit run app.py

# List all demos
ls demos/

# Check Skill availability
ls .claude/skills/

# View MCP configuration
cat .claude/settings.local.json
```

### Claude Prompts

```
# Generate demo
"Create demo for [Company] [Department] with [Use Cases]"

# Validate queries
"Validate queries in demos/[module_name]/"

# Generate slides
"Create slides for demos/[module_name]/"

# Generate script
"Create demo script for demos/[module_name]/"

# Fix query
"Fix this query: [ES|QL query]"

# Get help
"How do I configure MCP for Elasticsearch?"
```

### File Locations

```
.claude/skills/              # Skill definitions
.claude/settings.local.json  # MCP configuration
docs/                        # Documentation
demos/                       # Generated demo modules
src/framework/               # Core framework
```

---

**Ready to start?** Generate your first demo and use Skills to create a complete package!

1. `streamlit run app.py` → Create demo
2. "Validate queries in demos/[your_module]/"
3. "Create slides for this demo"
4. "Create demo script for this module"

**Questions?** Check [MCP_CONFIGURATION_GUIDE.md](./MCP_CONFIGURATION_GUIDE.md) or ask Claude for help!
