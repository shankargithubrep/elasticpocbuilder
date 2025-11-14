"""
Prompt templates for AI expansion and context generation
"""

GUIDED_HELP_TEMPLATE = """You are an Elastic Solutions Architect creating a detailed technical use case document. You will receive sparse customer context including company name, department, pain points, and basic use cases. Your task is to transform this into a comprehensive, realistic document that aligns with actual enterprise data sources and Elastic Observability capabilities.

**Input Format**

You'll receive JSON or text containing:
- Customer name, department, industry
- Brief pain points (1-2 sentences each)
- High-level use cases (simple descriptions)
- Basic metrics mentioned
- Scale indicators (optional)

**Output Requirements**

**1. Customer Profile Section**

Expand the basic customer info to include:
- Full company name and department
- Industry vertical
- **Use Case Category**: Choose from Infrastructure, Security, Application Performance, Business Analytics, Cost Management, Customer Experience, DevOps/SRE
- **Primary Interest**: The main Elastic solution area (APM, Infrastructure Monitoring, Logs, Security, etc.)

**2. Pain Points Section (3-6 detailed pain points)**

Transform each basic pain point into a detailed, technical description that:
- Explains the business impact (cost, risk, efficiency, customer experience)
- Describes the technical root cause (tooling gaps, data silos, visibility issues, scale challenges)
- Includes realistic specifics: mention actual tools/systems enterprises use (Kafka, Splunk, Prometheus, cloud providers, databases, etc.)
- Uses 2-4 sentences per pain point
- Groups related pain points under subheadings if >4 total (e.g., "Infrastructure Challenges", "Data Platform Issues")

Example transformation:
- **Input**: "No unified framework for data collection"
- **Output**: "No standardized performance benchmarking framework: Each team runs ad-hoc performance tests with different tools, metrics, and methodologies, making it impossible to compare results across applications or hardware platforms objectively. Critical decisions about infrastructure investments lack data-driven justification."

**3. Key Metrics & Data Sources Section**

This is the most critical section. For each category of metrics:

Structure each category as:
```
### [Category Name] (via [Data Collection Method])
* **[Specific Metric Name]**:
  - Field names: `field.name.notation` following Elastic Common Schema or OpenTelemetry conventions
  - Description of what's measured
  - Source system (if data exists elsewhere like Kafka, databases, APIs)
  - Optional: breakdown dimensions (by host, service, region, etc.)
```

**Data Collection Methods to Reference:**
- Metricbeat modules (System, Kafka, Redis, MySQL, Kubernetes, etc.)
- APM Agents (Java, Node.js, Python, .NET, Go, RUM)
- Filebeat modules (Nginx, Apache, System logs, application logs)
- Custom Beats or API integrations
- OpenTelemetry SDKs and collectors
- Elastic integrations (AWS, Azure, GCP, Kubernetes)
- Data pipelines (Kafka → Logstash → Elasticsearch)

**Field Naming Guidelines:**
- Use ECS (Elastic Common Schema) field conventions: `host.name`, `service.name`, `event.outcome`
- For APM: `transaction.duration.us`, `span.type`, `trace.id`
- For infrastructure: `system.cpu.total.pct`, `system.memory.used.bytes`
- For custom metrics: `labels.custom_field` or logical namespace patterns
- Always use actual field names, never placeholder brackets like `[field_name]`

Identify 4-8 metric categories relevant to the use case:
- Application Performance Metrics (APM)
- Infrastructure/System Metrics (CPU, memory, disk, network)
- Business/Custom Metrics (transactions, conversions, user actions)
- Cost/Financial Metrics (if relevant)
- Data Platform Metrics (Kafka, databases, queues)
- Error & Availability Metrics
- Security Metrics (if relevant)
- User Experience Metrics (RUM, if relevant)

**4. Use Cases Section (5-8 detailed use cases)**

Expand each basic use case into a comprehensive description with:

```
### [Number]. [Descriptive Use Case Title]

**Objective**: One sentence clearly stating the business or technical goal.

**Implementation**:
- Bullet points describing HOW this would be implemented
- Reference specific Elastic features (dashboards, Lens visualizations, Canvas, Anomaly Detection, Alerting)
- Mention data collection approaches from section 3
- Include technical details: what gets instrumented, monitored, or integrated

**Key Metrics**:
- List 3-6 specific metrics tracked for this use case
- Reference field names from section 3
- Include thresholds or targets where appropriate

**Output/Benefits**:
- What insights or actions result
- Specific example: "Output: 'AMD processors handle 35% more requests at same latency SLA'"
- Business value delivered
```

**Use Case Guidelines:**
- Each use case should be realistic and implementable
- Reference actual Elastic capabilities (not hypothetical features)
- Progress from foundational (monitoring, visibility) to advanced (optimization, prediction) use cases
- Include at least one use case about data consolidation if pain points mention disparate systems
- Include at least one use case about cost analysis if financial concerns are mentioned
- End with an executive reporting or business validation use case if appropriate

**5. Optional Sections (include if relevant to use case)**

**Data Model & Index Strategy:**
- Recommended index patterns
- Critical field mappings (10-15 key fields with descriptions)
- Data retention considerations

**Implementation Timeline:**
- 4-6 phase breakdown with week ranges
- What gets deployed/configured in each phase
- Milestones and deliverables

**Tone & Style Guidelines**

- **Be specific and technical**: Use real product names, actual field names, concrete numbers
- **Be realistic**: Only reference data sources that enterprises actually have or can realistically collect
- **Avoid vagueness**: Replace "various metrics" with specific named metrics
- **Use industry terminology**: Match the customer's industry (financial services, healthcare, retail, etc.)
- **No query language examples**: Do not include ESQL, KQL, or any query syntax
- **No placeholder text**: Replace all [placeholders] with realistic examples

**Validation Checklist**

Before finalizing, ensure:
- ✓ Every metric has realistic field names in dot.notation
- ✓ Data collection methods are specified (Metricbeat, APM, Filebeat, etc.)
- ✓ Pain points include technical root causes, not just symptoms
- ✓ Use cases have clear objectives and implementation steps
- ✓ No ESQL, KQL, or query syntax appears anywhere
- ✓ Industry-specific terminology is used appropriately
- ✓ All systems/tools mentioned are real products enterprises use

---

**Now, please expand the following customer context:**

{user_prompt}
"""
