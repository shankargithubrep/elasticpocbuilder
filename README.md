# Elastic Agent Builder - Demo Builder

Create custom Agent Builder demos for your customer opportunities using AI assistance and proven patterns.

## 🎯 Purpose

This repository helps Elastic Solutions Architects:
1. **Reuse existing demos** - Leverage proven Agent Builder demonstrations
2. **Create custom demos** - Use AI to build tailored demos for your opportunities
3. **Share knowledge** - Contribute successful demos back to the community

## 🚀 Quick Start

### Reuse an Existing Demo
Browse [completed demos](./completed-demos/) and follow the README in each demo folder.

**Available Demos:**
- [Adobe Brand Analytics](./completed-demos/adobe-brand-analytics/) - Multi-dataset analytics with campaign performance, asset management, and usage tracking

### Create a Custom Demo
Follow the [CREATE-DEMO.md](./CREATE-DEMO.md) guide to build a custom demo with AI assistance.

**Process Overview:**
1. **Discovery** - Gather customer context and pain points
2. **Ideation** - Brainstorm use cases with AI
3. **Planning** - Design datasets and queries
4. **Generation** - Create all demo assets
5. **Validation** - Test and refine
6. **Publication** - Share with the community

## 📂 Repository Structure

```
demo-builder/
├── README.md (this file)
├── CREATE-DEMO.md (step-by-step guide)
├── templates/
│   ├── agent-definition.yaml
│   ├── tool-definition.yaml
│   └── demo-checklist.md
├── completed-demos/
│   └── adobe-brand-analytics/
├── in-development/
│   └── (your work-in-progress demos)
└── reference/
    ├── esql-patterns.md
    ├── esql-resources.md
    ├── best-practices.md
    ├── troubleshooting.md
    └── common-use-cases.md
```

## 🛠️ What You'll Find Here

### Templates
Reusable templates for creating new demos:
- Agent definition structure
- Tool definition structure
- Demo creation checklist

### Reference Materials
- [ES|QL Patterns](./reference/esql-patterns.md) - Common query patterns and techniques
- [ES|QL Resources](./reference/esql-resources.md) - Official documentation links
- [Best Practices](./reference/best-practices.md) - Tips for effective demos
- [Troubleshooting](./reference/troubleshooting.md) - Common issues and solutions
- [Common Use Cases](./reference/common-use-cases.md) - Proven use case patterns

### Completed Demos
Fully documented, production-ready demos with:
- Sample datasets (or data generators)
- Agent and tool definitions
- ES|QL queries
- Presentation slides content
- Demo scripts
- Setup instructions

## 🤖 Using AI to Create Demos

This repository is designed to work with Large Language Models (LLMs) like Claude or ChatGPT. The [CREATE-DEMO.md](./CREATE-DEMO.md) file contains comprehensive prompts that guide the AI through:

1. Understanding your customer's needs
2. Suggesting relevant use cases
3. Designing appropriate datasets
4. Creating ES|QL queries
5. Generating all demo materials

**Key Features:**
- Progressive context building through guided conversation
- Validation checkpoints at each phase
- Iterative refinement based on your feedback
- Reference to existing demos for inspiration

## 📥 Contributing Your Demo

When your demo is successful:

1. Create a folder in `in-development/[customer-name]-[use-case]/`
2. Add all demo assets using the templates
3. Test and validate with real customers
4. After successful delivery, move to `completed-demos/`
5. Submit a pull request

**What to Include:**
- README with overview and setup instructions
- All datasets or data generation code
- Agent and tool definitions
- ES|QL queries (tested and working)
- Presentation materials
- Demo script

## 🎓 Learning Resources

### ES|QL Documentation
- [ES|QL Syntax Reference](https://www.elastic.co/docs/reference/query-languages/esql/esql-syntax)
- [ES|QL Functions & Operators](https://www.elastic.co/docs/reference/query-languages/esql/esql-functions-operators)
- [ES|QL Processing Commands](https://www.elastic.co/docs/reference/query-languages/esql/commands/processing-commands)

### Presentation Templates
- [Google Slides Template](https://docs.google.com/presentation/d/1LQxSxOS3tgoRbVO5FD7zdaTn8KoCzeStEwWBUbBLuxA/edit?usp=sharing)
- [Google Docs Script Template](https://docs.google.com/document/d/1KQfnZHL6qDJx_-NzyDsUfYKWXg88BKE0-1EDiMt7zYs/edit?usp=sharing)

## 🔮 Future Enhancements

- [ ] Automated ES|QL query testing via Elastic MCP Server
- [ ] Data generator template library
- [ ] Demo showcase gallery
- [ ] Success metrics tracking
- [ ] Community contribution guidelines

## 📞 Support

Questions? Reach out to the Elastic Solutions Architecture team or open an issue in this repository.

## License

Copyright © Elastic. All rights reserved.
