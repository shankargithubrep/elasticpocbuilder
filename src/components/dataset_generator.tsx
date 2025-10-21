import React, { useState } from 'react';
import { Download, FileText, Database, TrendingUp } from 'lucide-react';

const DatasetGenerator = () => {
  const [generated, setGenerated] = useState(false);
  
  const generateCampaignPerformance = () => {
    const assetIds = Array.from({length: 289}, (_, i) => `BA-${1001 + i}`);
    const campaigns = [
      "Year-End Review 2024", "NextGen Launch", "Future Forward 2025", 
      "Project Nova", "Innovate & Elevate", "Brand Unification 2023",
      "Summer Splash Sale", "Q3 Growth Initiative", "Spring Refresh",
      "Digital Transform 2024", "Global Expansion", "Product Launch Q4",
      "Holiday Campaign 2024", "Sustainability Initiative", "Tech Summit 2025"
    ];
    const regions = ['Global', 'EMEA', 'APAC', 'North America', 'LATAM'];
    const channels = ['Social Media', 'Email', 'Web', 'Display Ads', 'Video', 'Print'];
    const audienceSegments = ['Enterprise', 'SMB', 'Consumer', 'Developer', 'Creative Professional'];
    
    const campaignPerformance = [];
    let perfId = 1;
    
    const startDate = new Date('2024-01-01');
    const endDate = new Date('2025-06-30');
    
    campaigns.forEach(campaign => {
      const campaignDuration = 30 + Math.floor(Math.random() * 60);
      const campaignStart = new Date(startDate.getTime() + Math.random() * (endDate.getTime() - startDate.getTime() - campaignDuration * 24 * 60 * 60 * 1000));
      
      const numAssets = 3 + Math.floor(Math.random() * 6);
      const campaignAssets = [];
      while (campaignAssets.length < numAssets) {
        const asset = assetIds[Math.floor(Math.random() * assetIds.length)];
        if (!campaignAssets.includes(asset)) campaignAssets.push(asset);
      }
      
      for (let day = 0; day < campaignDuration; day++) {
        const date = new Date(campaignStart);
        date.setDate(date.getDate() + day);
        
        campaignAssets.forEach(assetId => {
          const numChannels = 1 + Math.floor(Math.random() * 3);
          const selectedChannels = [];
          while (selectedChannels.length < numChannels) {
            const channel = channels[Math.floor(Math.random() * channels.length)];
            if (!selectedChannels.includes(channel)) selectedChannels.push(channel);
          }
          
          selectedChannels.forEach(channel => {
            const region = regions[Math.floor(Math.random() * regions.length)];
            const audience = audienceSegments[Math.floor(Math.random() * audienceSegments.length)];
            
            const baseImpressions = channel === 'Social Media' ? 50000 : 
                                   channel === 'Display Ads' ? 100000 :
                                   channel === 'Email' ? 20000 :
                                   channel === 'Web' ? 30000 : 15000;
            
            const impressions = Math.floor(baseImpressions * (0.5 + Math.random()));
            const clicks = Math.floor(impressions * (0.01 + Math.random() * 0.05));
            const conversions = Math.floor(clicks * (0.02 + Math.random() * 0.08));
            const engagement_rate = parseFloat((clicks / impressions * 100).toFixed(2));
            const conversion_rate = parseFloat((conversions / clicks * 100).toFixed(2));
            const spend = parseFloat((impressions * (0.002 + Math.random() * 0.008)).toFixed(2));
            const revenue = parseFloat((conversions * (50 + Math.random() * 200)).toFixed(2));
            
            campaignPerformance.push([
              `CP-${perfId++}`,
              campaign,
              assetId,
              date.toISOString().split('T')[0],
              channel,
              region,
              audience,
              impressions,
              clicks,
              conversions,
              engagement_rate,
              conversion_rate,
              spend,
              revenue
            ]);
          });
        });
      }
    });
    
    const csv = [
      'Performance ID,Campaign Name,Asset ID,Date,Channel,Region,Audience Segment,Impressions,Clicks,Conversions,Engagement Rate,Conversion Rate,Spend,Revenue',
      ...campaignPerformance.map(row => row.join(','))
    ].join('\n');
    
    return csv;
  };
  
  const generateAssetUsage = () => {
    const assetIds = Array.from({length: 289}, (_, i) => `BA-${1001 + i}`);
    const assetUsageEvents = [];
    let eventId = 1;
    
    const actionTypes = ['Download', 'View', 'Share', 'Edit Request', 'Approval Submitted', 'Approved', 'Rejected', 'Comment Added'];
    const departments = ['Marketing', 'Creative', 'Sales', 'Product', 'Regional Marketing', 'Brand Management', 'Digital'];
    const deviceTypes = ['Desktop', 'Mobile', 'Tablet'];
    
    const eventStartDate = new Date('2024-01-01');
    const eventEndDate = new Date('2025-06-30');
    
    assetIds.forEach(assetId => {
      const numEvents = 10 + Math.floor(Math.random() * 90);
      
      for (let i = 0; i < numEvents; i++) {
        const timestamp = new Date(eventStartDate.getTime() + Math.random() * (eventEndDate.getTime() - eventStartDate.getTime()));
        const actionType = actionTypes[Math.floor(Math.random() * actionTypes.length)];
        const department = departments[Math.floor(Math.random() * departments.length)];
        const deviceType = deviceTypes[Math.floor(Math.random() * deviceTypes.length)];
        const userId = `user-${1000 + Math.floor(Math.random() * 500)}`;
        
        let durationSeconds = '';
        if (actionType === 'View') {
          durationSeconds = 15 + Math.floor(Math.random() * 600);
        } else if (actionType === 'Edit Request') {
          durationSeconds = 300 + Math.floor(Math.random() * 3600);
        }
        
        assetUsageEvents.push({
          timestamp,
          row: [
            `AE-${eventId++}`,
            assetId,
            timestamp.toISOString(),
            actionType,
            userId,
            department,
            deviceType,
            durationSeconds,
            `session-${Math.floor(Math.random() * 10000)}`
          ]
        });
      }
    });
    
    assetUsageEvents.sort((a, b) => a.timestamp - b.timestamp);
    
    const csv = [
      'Event ID,Asset ID,Timestamp,Action Type,User ID,Department,Device Type,Duration Seconds,Session ID',
      ...assetUsageEvents.map(e => e.row.join(','))
    ].join('\n');
    
    return csv;
  };
  
  const downloadCSV = (content, filename) => {
    const blob = new Blob([content], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    setGenerated(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            Elastic Agent Builder Demo
          </h1>
          <p className="text-xl text-purple-200 mb-2">
            Adobe Brand Assets Analytics Demo
          </p>
          <p className="text-slate-300">
            Generate sample datasets and explore powerful ES|QL queries
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-purple-300/20">
            <div className="flex items-center gap-3 mb-4">
              <TrendingUp className="w-8 h-8 text-purple-400" />
              <h2 className="text-2xl font-bold text-white">Campaign Performance</h2>
            </div>
            <p className="text-slate-200 mb-4">
              ~11,000 records tracking campaign metrics across channels, regions, and audience segments
            </p>
            <ul className="text-sm text-slate-300 space-y-2 mb-6">
              <li>• 15 marketing campaigns</li>
              <li>• 6 channels (Social, Email, Web, Display, Video, Print)</li>
              <li>• Metrics: impressions, clicks, conversions, spend, revenue</li>
              <li>• 18 months of daily data (Jan 2024 - Jun 2025)</li>
            </ul>
            <button
              onClick={() => downloadCSV(generateCampaignPerformance(), 'campaign_performance.csv')}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              <Download className="w-5 h-5" />
              Download campaign_performance.csv
            </button>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-purple-300/20">
            <div className="flex items-center gap-3 mb-4">
              <Database className="w-8 h-8 text-purple-400" />
              <h2 className="text-2xl font-bold text-white">Asset Usage Events</h2>
            </div>
            <p className="text-slate-200 mb-4">
              ~16,000 event records tracking asset interactions and workflow activities
            </p>
            <ul className="text-sm text-slate-300 space-y-2 mb-6">
              <li>• 8 action types (Download, View, Share, Approvals, etc.)</li>
              <li>• 7 departments tracking usage patterns</li>
              <li>• User, device, and session tracking</li>
              <li>• Approval workflow metrics</li>
            </ul>
            <button
              onClick={() => downloadCSV(generateAssetUsage(), 'asset_usage_events.csv')}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              <Download className="w-5 h-5" />
              Download asset_usage_events.csv
            </button>
          </div>
        </div>

        {generated && (
          <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4 mb-8">
            <p className="text-green-200 text-center font-semibold">
              ✓ Datasets generated successfully! Check your downloads folder.
            </p>
          </div>
        )}

        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 border border-purple-300/20">
          <div className="flex items-center gap-3 mb-6">
            <FileText className="w-8 h-8 text-purple-400" />
            <h2 className="text-3xl font-bold text-white">Demo ES|QL Queries</h2>
          </div>

          <div className="space-y-8">
            <div className="border-l-4 border-purple-500 pl-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">1. Campaign ROI Analysis with Asset Enrichment</h3>
              <p className="text-slate-300 mb-3">Calculate ROI by campaign and enrich with asset type information</p>
              <pre className="bg-black/40 p-4 rounded-lg text-sm text-green-300 overflow-x-auto">
{`FROM campaign_performance
| EVAL roi = (Revenue - Spend) / Spend * 100
| STATS 
    total_spend = SUM(Spend),
    total_revenue = SUM(Revenue),
    avg_roi = AVG(roi),
    total_conversions = SUM(Conversions)
  BY \`Campaign Name\`
| EVAL roi_percentage = (total_revenue - total_spend) / total_spend * 100
| LOOKUP JOIN brand_assets ON \`Asset ID\`
| SORT roi_percentage DESC
| LIMIT 10`}
              </pre>
            </div>

            <div className="border-l-4 border-purple-500 pl-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">2. Channel Performance by Region with Filtering</h3>
              <p className="text-slate-300 mb-3">Analyze which channels perform best in each region for active campaigns</p>
              <pre className="bg-black/40 p-4 rounded-lg text-sm text-green-300 overflow-x-auto">
{`FROM campaign_performance
| WHERE Date >= "2024-06-01" AND Date <= "2025-06-30"
| EVAL ctr = Clicks / Impressions * 100
| EVAL cvr = Conversions / Clicks * 100
| STATS 
    total_impressions = SUM(Impressions),
    avg_ctr = AVG(ctr),
    avg_cvr = AVG(cvr),
    total_revenue = SUM(Revenue)
  BY Region, Channel
| WHERE total_impressions > 100000
| SORT total_revenue DESC`}
              </pre>
            </div>

            <div className="border-l-4 border-purple-500 pl-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">3. Asset Utilization vs Performance Analysis</h3>
              <p className="text-slate-300 mb-3">Join usage events with performance to find high-engagement, underutilized assets</p>
              <pre className="bg-black/40 p-4 rounded-lg text-sm text-green-300 overflow-x-auto">
{`FROM asset_usage_events
| WHERE \`Action Type\` IN ("Download", "View", "Share")
| STATS usage_count = COUNT(*) BY \`Asset ID\`
| LOOKUP JOIN campaign_performance ON \`Asset ID\`
| STATS 
    total_usage = MAX(usage_count),
    avg_engagement = AVG(\`Engagement Rate\`),
    total_conversions = SUM(Conversions)
  BY \`Asset ID\`
| WHERE total_usage < 50 AND avg_engagement > 4.0
| SORT avg_engagement DESC
| LIMIT 20`}
              </pre>
            </div>

            <div className="border-l-4 border-purple-500 pl-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">4. Approval Workflow Efficiency</h3>
              <p className="text-slate-300 mb-3">Calculate approval cycle time and success rate by department</p>
              <pre className="bg-black/40 p-4 rounded-lg text-sm text-green-300 overflow-x-auto">
{`FROM asset_usage_events
| WHERE \`Action Type\` IN ("Approval Submitted", "Approved", "Rejected")
| EVAL approval_status = CASE(
    \`Action Type\` == "Approved", "Approved",
    \`Action Type\` == "Rejected", "Rejected",
    "Pending"
  )
| STATS 
    total_submissions = COUNT(*),
    approved = COUNT(CASE(\`Action Type\` == "Approved", 1)),
    rejected = COUNT(CASE(\`Action Type\` == "Rejected", 1))
  BY Department
| EVAL approval_rate = approved / total_submissions * 100
| SORT approval_rate DESC`}
              </pre>
            </div>

            <div className="border-l-4 border-purple-500 pl-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">5. Time-Series Trend Analysis</h3>
              <p className="text-slate-300 mb-3">Monthly trend analysis with aggregations and EVAL transformations</p>
              <pre className="bg-black/40 p-4 rounded-lg text-sm text-green-300 overflow-x-auto">
{`FROM campaign_performance
| EVAL month = DATE_TRUNC(1 month, TO_DATETIME(Date))
| EVAL roi = (Revenue - Spend) / Spend * 100
| STATS 
    monthly_spend = SUM(Spend),
    monthly_revenue = SUM(Revenue),
    avg_engagement = AVG(\`Engagement Rate\`),
    total_conversions = SUM(Conversions),
    avg_roi = AVG(roi)
  BY month
| EVAL revenue_growth = (monthly_revenue - LAG(monthly_revenue, 1)) / LAG(monthly_revenue, 1) * 100
| SORT month ASC`}
              </pre>
            </div>

            <div className="border-l-4 border-purple-500 pl-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">6. Asset Type Performance Ranking</h3>
              <p className="text-slate-300 mb-3">Multi-way join showing which asset types drive best campaign performance</p>
              <pre className="bg-black/40 p-4 rounded-lg text-sm text-green-300 overflow-x-auto">
{`FROM brand_assets
| LOOKUP JOIN campaign_performance ON \`Asset ID\`
| EVAL revenue_per_impression = Revenue / Impressions * 1000
| STATS 
    total_campaigns = COUNT_DISTINCT(\`Campaign Name\`),
    total_revenue = SUM(Revenue),
    avg_engagement = AVG(\`Engagement Rate\`),
    avg_revenue_per_1k = AVG(revenue_per_impression)
  BY \`Asset Type\`, Status
| WHERE Status == "Active"
| SORT total_revenue DESC
| LIMIT 15`}
              </pre>
            </div>

            <div className="border-l-4 border-purple-500 pl-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">7. Audience Segment Profitability</h3>
              <p className="text-slate-300 mb-3">Complex aggregation showing which audience segments are most profitable</p>
              <pre className="bg-black/40 p-4 rounded-lg text-sm text-green-300 overflow-x-auto">
{`FROM campaign_performance
| WHERE Date >= "2024-01-01"
| EVAL cost_per_conversion = Spend / Conversions
| EVAL revenue_per_conversion = Revenue / Conversions
| EVAL profit_margin = (Revenue - Spend) / Revenue * 100
| STATS 
    total_conversions = SUM(Conversions),
    avg_cpc = AVG(cost_per_conversion),
    avg_revenue_per_conv = AVG(revenue_per_conversion),
    avg_profit_margin = AVG(profit_margin),
    total_profit = SUM(Revenue - Spend)
  BY \`Audience Segment\`, Channel
| WHERE total_conversions > 100
| EVAL efficiency_score = (avg_revenue_per_conv / avg_cpc) * avg_profit_margin
| SORT efficiency_score DESC`}
              </pre>
            </div>

            <div className="border-l-4 border-purple-500 pl-6">
              <h3 className="text-xl font-bold text-purple-300 mb-3">8. Cross-Dataset Engagement Analysis</h3>
              <p className="text-slate-300 mb-3">Find assets with high internal usage but low campaign deployment</p>
              <pre className="bg-black/40 p-4 rounded-lg text-sm text-green-300 overflow-x-auto">
{`FROM asset_usage_events
| STATS 
    internal_views = COUNT(CASE(\`Action Type\` == "View", 1)),
    downloads = COUNT(CASE(\`Action Type\` == "Download", 1)),
    shares = COUNT(CASE(\`Action Type\` == "Share", 1))
  BY \`Asset ID\`
| LOOKUP JOIN campaign_performance ON \`Asset ID\`
| STATS 
    total_internal_engagement = MAX(internal_views + downloads + shares),
    campaign_count = COUNT_DISTINCT(\`Campaign Name\`),
    total_revenue = SUM(Revenue)
  BY \`Asset ID\`
| WHERE total_internal_engagement > 100 AND campaign_count < 3
| LOOKUP JOIN brand_assets ON \`Asset ID\`
| KEEP \`Asset ID\`, \`Product Name\`, \`Asset Type\`, total_internal_engagement, campaign_count, total_revenue
| SORT total_internal_engagement DESC
| LIMIT 25`}
              </pre>
            </div>
          </div>
        </div>

        <div className="mt-8 bg-blue-500/20 border border-blue-500/50 rounded-lg p-6">
          <h3 className="text-xl font-bold text-blue-200 mb-3">Key ES|QL Features Demonstrated:</h3>
          <div className="grid md:grid-cols-2 gap-4 text-slate-200">
            <ul className="space-y-2">
              <li>✓ <span className="font-semibold">LOOKUP JOIN</span> - Multi-table joins</li>
              <li>✓ <span className="font-semibold">EVAL</span> - Variable definition & calculations</li>
              <li>✓ <span className="font-semibold">STATS</span> - Advanced aggregations</li>
              <li>✓ <span className="font-semibold">WHERE</span> - Filtering conditions</li>
            </ul>
            <ul className="space-y-2">
              <li>✓ <span className="font-semibold">CASE</span> - Conditional logic</li>
              <li>✓ <span className="font-semibold">DATE_TRUNC</span> - Time bucketing</li>
              <li>✓ <span className="font-semibold">COUNT_DISTINCT</span> - Unique counts</li>
              <li>✓ <span className="font-semibold">LAG</span> - Window functions</li>
            </ul>
          </div>
        </div>

        <div className="mt-8 text-center text-slate-400 text-sm">
          <p>Demo prepared for Adobe • Elastic Agent Builder • ES|QL Query Language</p>
        </div>
      </div>
    </div>
  );
};

export default DatasetGenerator;