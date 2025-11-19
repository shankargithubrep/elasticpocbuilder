from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class BassProShopsDemoGuide(DemoGuideModule):
    """Demo guide for Bass Pro Shops - Product Management"""

    # DO NOT define __init__ - inherited from base class provides:
    # self.config, self.datasets, self.queries
    # Note: self.aha_moment exists but will be None - do not use it

    def generate_guide(self) -> str:
        """Generate customized demo guide"""
        guide = f"""# Demo Guide: Bass Pro Shops - Product Management
        
## Company Context
**Company:** {self.config.company_name}
**Department:** {self.config.department}
**Industry:** {self.config.industry}

## Opening Hook (First 30 Seconds)
"Thanks for taking the time today. I know at Bass Pro Shops, your Product Management team is juggling thousands of SKUs across categories like fishing, hunting, camping, and marine equipment - all while dealing with highly seasonal demand patterns and the challenge of balancing inventory across 170+ retail locations and your e-commerce platform.

What if you could use AI to predict which products will be your next bestsellers, identify underperforming items before they become dead stock, and get real-time insights into how product features are impacting customer satisfaction - all without waiting weeks for your data science team?"

## Key Pain Points to Address
{self._format_pain_points()}

## Demo Flow (30-Minute Structure)

### Phase 1: The Problem (5 minutes)
**Talk Track:**
"Let me paint a picture of what we typically see with outdoor retail product teams:
- You're launching 500+ new products per season, but only have historical sales data to guide decisions
- Customer reviews are scattered across your website, third-party retailers, and social media
- By the time you identify a trending product category (like kayak fishing gear), competitors have already captured market share
- Your team spends hours in spreadsheets trying to connect inventory data, sales performance, and customer feedback

Does this resonate with your current challenges?"

**[PAUSE FOR RESPONSE - Let them share their specific pain]**

### Phase 2: The Solution Overview (3 minutes)
**Talk Track:**
"Elastic Agent Builder is an AI-powered assistant platform that connects directly to your existing data sources - your POS systems, inventory management, customer reviews, and even external market data. 

What makes it powerful for outdoor retail is that you can build specialized AI agents without coding:
- A 'Product Performance Agent' that analyzes sales velocity across seasons
- A 'Customer Sentiment Agent' that monitors reviews for quality issues
- A 'Competitive Intelligence Agent' that tracks market trends
- An 'Inventory Optimization Agent' that predicts stockouts for seasonal items

Let me show you how this works with scenarios relevant to Bass Pro Shops..."

### Phase 3: Live Demo - Product Intelligence (12 minutes)

**Scenario 1: Seasonal Product Performance Analysis**
**Query:** "Which fishing rod categories showed the strongest growth in Q2 compared to last year, and what price points are driving that growth?"

**Talk Track:**
"It's April, and you're planning your summer fishing inventory. Instead of manually pulling reports from multiple systems, watch this...

[Execute Query]

See how the agent instantly analyzed:
- Sales data across 15 fishing rod subcategories
- Year-over-year growth trends
- Price point performance ($50-$100 vs $100-$200 vs $200+)
- Geographic variations (Southern stores vs Northern stores)

For Bass Pro Shops, this means you can make buy decisions in minutes, not days. If spinning rods in the $75-$125 range are trending up 40%, you can adjust your purchase orders before peak season hits."

**Scenario 2: Customer Review Intelligence**
**Query:** "Analyze negative reviews for our top 10 camping tents and identify the most common product defects or complaints."

**Talk Track:**
"Product quality issues can destroy a category's reputation fast in outdoor retail. Your customers depend on gear that works in the wilderness.

[Execute Query]

The agent just analyzed thousands of reviews and identified:
- Zipper failures mentioned in 23% of 2-3 star reviews for Model X
- Waterproofing issues concentrated in one specific tent line
- Setup difficulty complaints for products marketed as 'easy setup'

This is intelligence your product team can act on immediately - whether that's working with suppliers on quality improvements, updating product descriptions to set proper expectations, or making merchandising decisions for next season."

**Scenario 3: Cross-Category Trend Detection**
**Query:** "Show me emerging product trends in the hunting category based on search behavior, social mentions, and early sales signals in the past 90 days."

**Talk Track:**
"The outdoor industry moves fast. Crossbow hunting, thermal imaging, and saddle hunting have all exploded in recent years. The retailers who spotted these trends early won big.

[Execute Query]

Look at this - the agent is detecting:
- 300% increase in searches for 'saddle hunting platforms'
- Social media mentions of 'lightweight backpack hunting gear' up 180%
- Early sales velocity on specific trail camera models with cellular connectivity

For your Product Management team, this is like having a trend analyst working 24/7, helping you decide which new products to bring in and which categories to expand."

**Scenario 4: Inventory Optimization for Seasonal Items**
**Query:** "Which products are at risk of stockout in the next 30 days based on current inventory levels and historical demand patterns for this time of year?"

**Talk Track:**
"Nothing frustrates customers more than driving to Bass Pro Shops for a specific item and finding it out of stock during peak season.

[Execute Query]

The agent just identified:
- 47 SKUs at high stockout risk in the fishing category (pre-Memorial Day)
- 12 marine products with inventory levels 40% below where they should be for May
- Specific store locations where the risk is highest

Your team can now proactively rebalance inventory across locations or expedite orders from suppliers."

### Phase 4: The Differentiator (5 minutes)

**Talk Track:**
"Now, here's what makes Elastic Agent Builder different from traditional BI tools or even other AI solutions:

1. **No Code Required:** Your product managers can create new agents themselves. Want to track a new KPI or analyze a different data source? Build it in minutes, not months of waiting for IT.

2. **Real-Time Learning:** The more you use it, the smarter it gets about outdoor retail patterns - seasonality, weather impacts, regional preferences.

3. **Connects Everything:** Your existing tech stack stays in place. We connect to your POS, inventory systems, e-commerce platform, review aggregators, even weather data or hunting season calendars.

4. **Built for Elastic:** If you're already using Elastic for search or observability, this integrates seamlessly. If not, we can deploy it with your existing data infrastructure.

Let me show you how easy it is to customize an agent..."

**[DEMO: Quick Agent Customization]**
"Say you want to add a new data source - like tracking competitor pricing from online retailers. Watch how simple this is..."

### Phase 5: ROI & Business Impact (3 minutes)

**Talk Track:**
"Let's talk about what this means for Bass Pro Shops specifically:

**Time Savings:**
- Product managers save 10-15 hours per week on data analysis and reporting
- Faster decision-making on product assortment (weeks → days)

**Revenue Impact:**
- Reduce stockouts by 25-30% during peak seasons (direct revenue capture)
- Identify winning products earlier (expand inventory while margins are good)
- Reduce markdown losses on slow-moving inventory by 15-20%

**Competitive Advantage:**
- Spot outdoor industry trends 2-3 months before competitors
- Respond to customer feedback faster (product improvements, supplier changes)

For a retailer your size, we typically see ROI within 4-6 months, with the biggest impact in:
- Seasonal categories (fishing, hunting, camping)
- New product launches
- Regional assortment optimization"

### Phase 6: Next Steps (2 minutes)

**Talk Track:**
"Here's what I'd recommend as next steps:

1. **Pilot Program (30 days):** We set up Elastic Agent Builder with 2-3 of your priority use cases - maybe seasonal product performance and customer review intelligence.

2. **Connect Your Data:** We'll integrate with your key systems (I'm assuming you have POS data, inventory management, and review data as starting points).

3. **Train Your Team:** 2-3 hour workshop with your product managers so they can start building their own agents.

4. **Measure Impact:** We'll track the specific metrics you care about - time saved, stockout reduction, markdown improvements.

Does this approach make sense? What questions do you have?"

## Key Value Propositions for Bass Pro Shops

### Primary Value Props:
1. **Seasonal Intelligence:** Predict and respond to seasonal demand patterns with AI-powered forecasting
2. **Product Performance Visibility:** Real-time insights into what's selling, what's not, and why
3. **Customer Voice Amplification:** Aggregate and analyze customer feedback across all channels
4. **Trend Detection:** Spot emerging outdoor industry trends before competitors
5. **Inventory Optimization:** Reduce stockouts and overstock situations across 170+ locations

### Quantifiable Benefits:
- **10-15 hours/week saved** per product manager on data analysis
- **25-30% reduction** in seasonal stockouts
- **15-20% reduction** in markdown losses
- **2-3 months faster** trend identification
- **4-6 months** typical ROI timeline

## Industry-Specific Talking Points

### Outdoor Retail Challenges:
- **Extreme Seasonality:** "Your Q2 fishing sales can be 5x your Q4 fishing sales - traditional analytics can't keep up"
- **Weather Dependency:** "Unseasonably cold spring? Your camping gear sales suffer. The agent can help you pivot quickly."
- **SKU Complexity:** "Between rods, reels, lures, line weights, and species-specific gear, you're managing incredible complexity"
- **Passionate Customer Base:** "Outdoor enthusiasts are vocal - they'll tell you exactly what's wrong with a product. Are you capturing all that feedback?"
- **Regional Variations:** "What sells in your Texas stores is completely different from your Minnesota locations"

### Competitive Landscape:
- "Cabela's, Sportsman's Warehouse, and Academy Sports are all fighting for the same customers"
- "Amazon is increasingly competitive in outdoor gear, especially in camping and fishing"
- "Specialty retailers like REI dominate certain categories - you need data-driven differentiation"

## Demo Customization Options

### If They Mention Specific Pain Points:

**"We struggle with new product launches"**
→ Pivot to: Agent that analyzes early sales signals, review sentiment, and return rates for new SKUs

**"Our stores have different needs regionally"**
→ Pivot to: Geographic performance analysis, regional assortment optimization

**"We can't keep up with e-commerce data"**
→ Pivot to: Omnichannel analysis, online vs in-store performance comparison

**"Supplier quality issues are killing us"**
→ Pivot to: Supplier performance tracking, defect pattern analysis from reviews

**"We need better competitive intelligence"**
→ Pivot to: Market trend analysis, competitive pricing monitoring

## Datasets to Highlight

{self._format_datasets()}

## Success Metrics to Track

### Immediate (Week 1-4):
- Time saved on routine reporting
- Number of agents created by product team
- User adoption rate

### Short-term (Month 2-3):
- Improved stockout rates for tracked categories
- Faster response time to customer feedback
- Reduction in manual data analysis tasks

### Long-term (Month 4-6):
- Markdown reduction percentage
- Revenue capture from better inventory positioning
- New product success rate improvement

## Technical Integration Points

**Likely Systems at Bass Pro Shops:**
- POS System (Oracle Retail, SAP, or similar)
- Inventory Management (Manhattan Associates, Blue Yonder)
- E-commerce Platform (custom or enterprise solution)
- Review Management (PowerReviews, Bazaarvoice)
- CRM/Customer Data
- Supplier/Vendor Management Systems

**Integration Approach:**
"We can connect to these systems via APIs, database connections, or file exports - whatever works best with your IT security policies. Most outdoor retailers are up and running within 2-3 weeks."

## Closing Questions

1. "What's your biggest product management challenge heading into [upcoming season]?"
2. "How do you currently identify which products to expand vs discontinue?"
3. "What does your process look like for analyzing customer reviews and feedback?"
4. "How much time does your team spend pulling together reports vs actually analyzing and making decisions?"
5. "If you could wave a magic wand and get one insight about your product portfolio instantly, what would it be?"

---

## Quick Reference: Objection Handling

{self._format_objection_handling()}

"""
        return guide

    def get_talk_track(self) -> Dict[str, str]:
        """Generate talk track for each query"""
        return {
            'Seasonal Product Performance': 
                "It's crucial for Bass Pro Shops to understand seasonal patterns. This query shows which product categories are trending up or down compared to last year, helping you make smarter buying decisions before peak season. Notice how it breaks down by price point and region - that's the level of detail your product managers need.",
            
            'Customer Review Analysis': 
                "Your customers are telling you exactly what's wrong with products - but that feedback is scattered everywhere. This agent aggregates reviews from your website, third-party retailers, and social media, then identifies patterns. See how it's flagging that zipper issue? That's actionable intelligence you can take to your supplier today.",
            
            'Trend Detection': 
                "The outdoor industry evolves fast. Saddle hunting, kayak fishing, backcountry hunting - these trends can explode in a single season. This query analyzes search behavior, social mentions, and early sales signals to help you spot what's coming next. Being 60 days ahead of competitors means you get the sales while margins are still healthy.",
            
            'Inventory Stockout Risk': 
                "Nothing kills customer satisfaction like driving to Bass Pro Shops for a specific fishing rod and finding it out of stock during pre-Memorial Day rush. This agent predicts stockout risk 30 days out, giving you time to rebalance inventory across stores or expedite supplier orders. For seasonal products, this is critical.",
            
            'New Product Performance': 
                "You launch hundreds of new products each season. This query tracks early performance indicators - sales velocity, review sentiment, return rates - to help you identify winners and losers fast. If a new kayak model is trending 3x above forecast, you can expand inventory. If it's underperforming, you can adjust marketing or pricing before you're stuck with dead stock.",
            
            'Cross-Category Insights': 
                "Outdoor enthusiasts often buy across categories - someone buying a fishing kayak might need paddles, PFDs, and rod holders. This agent identifies cross-sell opportunities and bundling possibilities based on actual purchase behavior. It's like having a merchandising analyst working 24/7.",
            
            'Supplier Performance': 
                "Quality issues from suppliers can damage your brand reputation. This query tracks defect rates, return reasons, and review sentiment by supplier and product line. If one supplier's tent line is generating 3x more complaints than others, you have data to drive that conversation.",
            
            'Regional Assortment Optimization': 
                "What sells in your Denham Springs, Louisiana store is completely different from your Anchorage, Alaska location. This agent analyzes regional performance to help you optimize assortment by geography. Maybe your Southern stores need more bass fishing gear while Northern stores need more walleye and muskie products.",
            
            'Competitive Price Intelligence': 
                "Your customers are comparison shopping online before they come to your stores. This agent monitors competitor pricing across key categories and products, alerting you when you're significantly out of position. For price-sensitive categories like ammunition or basic camping gear, this is essential.",
            
            'Weather Impact Analysis': 
                "Outdoor retail is uniquely weather-dependent. An unseasonably cold May crushes camping gear sales. This agent correlates weather patterns with sales performance to help you understand what's a trend vs what's weather-driven, and adjust your forecasts accordingly."
        }

    def get_objection_handling(self) -> Dict[str, str]:
        """Industry-specific objection handling"""
        return {
            "We already have business intelligence tools": 
                "I completely understand - most outdoor retailers have BI tools like Tableau or Power BI. Here's the difference: those tools are great for reporting what happened, but they require someone to build every dashboard and query. Elastic Agent Builder lets your product managers ask questions in plain English and get answers immediately - no waiting for IT or data analysts. Think of it as the difference between a static report and having a data analyst sitting next to each product manager. Plus, the AI learns outdoor retail patterns - seasonality, weather impacts, regional preferences - that generic BI tools don't understand.",
            
            "Our data is too messy or siloed": 
                "That's actually the most common situation we see in retail - POS data in one system, inventory in another, reviews scattered across platforms. The good news is that Elastic Agent Builder is built to handle messy, distributed data. We'll start with your most reliable data sources - probably POS and inventory - and add others over time. You don't need perfect data to get value; you need better insights than you have today. Many outdoor retailers start with 2-3 data sources and expand from there.",
            
            "We don't have data scientists on our team": 
                "That's exactly why Elastic Agent Builder exists. You don't need data scientists - your product managers can use it directly. It's designed for business users, not technical experts. If someone can use Google or ChatGPT, they can use this. We've had product managers at sporting goods retailers build their first agent in under an hour. The whole point is to democratize data access so your team doesn't have to wait for technical resources.",
            
            "This sounds expensive": 
                "Let's talk about ROI. If Elastic Agent Builder saves each of your product managers 10 hours per week - which is conservative based on what we see - that's 40+ hours per month per person. More importantly, let's talk about the revenue side: if you reduce stockouts by even 10% during peak fishing season, what's that worth in captured sales? If you reduce markdowns by 15% by identifying slow-movers earlier, what does that do to your margin? Most outdoor retailers see ROI in 4-6 months. We can model this specifically for Bass Pro Shops based on your priorities.",
            
            "We're already working with [competitor solution]": 
                "That's great - what's working well with that solution, and where are the gaps? [Listen] What we often hear is that other AI tools are either too generic (not understanding outdoor retail nuances) or too rigid (can't customize for your specific needs). Elastic Agent Builder is purpose-built to be flexible and learns your industry patterns. We're also happy to run a side-by-side pilot - let's pick one use case and see which solution delivers better insights faster. Would that be valuable?",
            
            "Our IT team won't approve another tool": 
                "I appreciate that concern - IT teams are rightfully protective of the tech stack. The good news is Elastic Agent Builder integrates with your existing systems; it doesn't replace them. We work with your current data infrastructure, and if you're already using Elastic for search or observability, this is a natural extension. We also have a proven security and compliance framework that's been approved by major retailers. What if we set up a conversation with your IT team early in the process to address their specific concerns? We can also start with a sandboxed pilot that doesn't touch production systems.",
            
            "We need to see proof this works for outdoor retail": 
                "Absolutely fair. We work with several sporting goods and outdoor retailers - I can't name them publicly due to NDAs, but I can share anonymized case studies showing 20-30% stockout reduction and 15-20% markdown improvements in seasonal categories. What would be most convincing for you? Would you like to speak with a reference customer, or would a 30-day pilot with your own data be more valuable? We can focus on one high-impact use case - maybe seasonal inventory optimization or customer review intelligence - and measure the results.",
            
            "Our team is too busy to learn a new system": 
                "I hear this a lot, and it's a valid concern. Here's the thing: Elastic Agent Builder actually saves time, it doesn't add work. The learning curve is minimal - we're talking 2-3 hours of training, not weeks. And think about it this way: if your product managers are spending 10-15 hours a week pulling data from multiple systems and building spreadsheets, wouldn't it be worth a few hours upfront to eliminate that ongoing burden? We can also start with just 1-2 power users who learn the system and then train others.",
            
            "What about data security and customer privacy": 
                "Critical question, especially in retail. Elastic Agent Builder is built with enterprise-grade security - encryption at rest and in transit, role-based access controls, audit logging, and compliance with SOC 2, GDPR, and retail-specific regulations. Your customer PII stays protected, and we can configure the system to anonymize or exclude sensitive data fields. We also offer on-premise deployment if that's preferred. Your data never leaves your control, and we never train our models on your proprietary information. Would you like me to connect you with our security team for a deeper dive?",
            
            "We're in the middle of other initiatives right now": 
                "I totally understand - retail is always juggling multiple priorities. Here's what I'd suggest: let's time this to support your current initiatives rather than compete with them. Are you planning for fall hunting season? Launching new product lines? Dealing with supply chain challenges? Elastic Agent Builder can actually accelerate those initiatives by providing faster insights. We can also start small - a 30-day pilot with minimal resource commitment - so you can see value without derailing other projects. What's your most pressing initiative in the next 90 days? Let's see if we can help.",
            
            "How is this different from ChatGPT or other AI tools": 
                "Great question. ChatGPT is amazing for general knowledge, but it doesn't know anything about YOUR data - your sales, your inventory, your customers. Elastic Agent Builder connects directly to your systems and analyzes your actual business data. It's also purpose-built for analytics and decision-making, not general conversation. Think of it as ChatGPT's intelligence combined with your BI tool's data access, but easier to use than either. Plus, it learns outdoor retail patterns specifically - seasonality, weather impacts, regional preferences - that generic AI tools don't understand.",
            
            "We need buy-in from executives first": 
                "Smart approach - executive sponsorship is important for success. What would help you build that business case? We can provide ROI models specific to Bass Pro Shops, showing time savings, revenue impact from better inventory positioning, and margin improvements from reduced markdowns. We can also do an executive briefing - 30 minutes to show the art of the possible and answer their questions. What metrics do your executives care most about? Let's make sure we're speaking their language when we present this."
        }

    def _format_pain_points(self) -> str:
        """Format pain points from config"""
        if hasattr(self.config, 'pain_points') and self.config.pain_points:
            points = [f"- {point}" for point in self.config.pain_points]
            return "\n".join(points)
        return """- Managing thousands of SKUs across highly seasonal categories
- Balancing inventory across 170+ retail locations and e-commerce
- Identifying product trends before competitors
- Aggregating customer feedback from multiple channels
- Optimizing product assortment by region and season
- Reducing stockouts during peak seasons
- Minimizing markdown losses on slow-moving inventory"""

    def _format_datasets(self) -> str:
        """Format available datasets"""
        if self.datasets:
            dataset_list = []
            for name, dataset in self.datasets.items():
                dataset_list.append(f"- **{name}**: {len(dataset)} records")
            return "\n".join(dataset_list)
        return """**Recommended Datasets for Demo:**
- Product Sales Data (by SKU, category, store, date)
- Inventory Levels (current stock, historical trends)
- Customer Reviews (ratings, text feedback, product IDs)
- Seasonal Performance Metrics (YoY comparisons)
- Geographic Sales Data (performance by region/store)
- Product Launch Data (new SKU performance tracking)
- Supplier/Vendor Information (quality metrics, lead times)"""

    def _format_objection_handling(self) -> str:
        """Format objection handling as quick reference"""
        objections = self.get_objection_handling()
        formatted = []
        for objection, response in objections.items():
            # Create shortened version for quick reference
            short_response = response.split('.')[0] + '...'
            formatted.append(f"**{objection}**\n→ {short_response}\n")
        return "\n".join(formatted)

    def get_discovery_questions(self) -> List[str]:
        """Generate discovery questions for Bass Pro Shops"""
        return [
            "How many SKUs are you currently managing across all categories?",
            "What's your biggest challenge heading into [upcoming peak season - fishing/hunting/camping]?",
            "How do you currently decide which new products to bring in each season?",
            "What's your process for analyzing customer reviews and feedback?",
            "How much time does your product team spend pulling data vs. actually analyzing and making decisions?",
            "How do you currently identify products that should be discontinued or marked down?",
            "What regional differences do you see in product performance across your store locations?",
            "How do you currently track and respond to competitive pricing?",
            "What's your biggest inventory challenge - stockouts, overstock, or both?",
            "How do you identify emerging trends in the outdoor industry?",
            "What data sources do you wish you could access more easily?",
            "How do you currently measure product manager productivity and effectiveness?",
            "What role does customer feedback play in your product decisions today?",
            "How do you handle the extreme seasonality of outdoor retail categories?",
            "What would change for your team if you could get answers to data questions in minutes instead of days?"
        ]

    def get_success_criteria(self) -> Dict[str, Any]:
        """Define success criteria for Bass Pro Shops engagement"""
        return {
            "immediate_wins": [
                "Product managers can query sales data without IT support",
                "Customer review insights aggregated across all channels",
                "Seasonal trend analysis completed in minutes vs. hours"
            ],
            "30_day_goals": [
                "10+ hours per week saved per product manager",
                "3-5 custom agents built by the product team",
                "Identification of 5-10 high-risk stockout items prevented"
            ],
            "90_day_goals": [
                "15-20% reduction in seasonal stockouts",
                "10-15% reduction in markdown losses",
                "Faster new product launch decisions (50% time reduction)",
                "Early identification of 2-3 emerging product trends"
            ],
            "key_metrics": [
                "Time saved on data analysis (hours per week)",
                "Stockout rate reduction (%)",
                "Markdown reduction (%)",
                "New product success rate improvement (%)",
                "User adoption rate (% of product team actively using)",
                "Number of data-driven decisions made per week"
            ]
        }

    def get_competitive_positioning(self) -> Dict[str, str]:
        """Positioning against alternatives"""
        return {
            "vs_traditional_bi": 
                "Traditional BI tools (Tableau, Power BI) require technical skills and pre-built dashboards. Elastic Agent Builder lets product managers ask questions in plain English and get immediate answers. It's self-service analytics without the complexity.",
            
            "vs_spreadsheets": 
                "Spreadsheets break at outdoor retail scale and complexity. With thousands of SKUs, seasonal patterns, and multiple data sources, you need something purpose-built. Plus, Elastic Agent Builder learns patterns over time - spreadsheets don't.",
            
            "vs_generic_ai": 
                "ChatGPT and generic AI tools don't connect to your data. Elastic Agent Builder analyzes YOUR sales, inventory, and customer feedback. It also understands outdoor retail nuances like seasonality and regional variations.",
            
            "vs_custom_development": 
                "Building custom analytics tools takes 6-12 months and costs hundreds of thousands. Elastic Agent Builder is ready in weeks, costs a fraction, and your team can customize it themselves without developers.",
            
            "vs_doing_nothing": 
                "The cost of inaction is high in outdoor retail. Every stockout is lost revenue. Every slow-moving product that gets marked down hurts margin. Every trend you miss is an opportunity for competitors. Elastic Agent Builder helps you move faster and smarter than the competition."
        }