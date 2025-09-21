# AI Prompt Templates for Innovate AI Chatbot
# Amazon Bedrock Nova Pro Model Integration

# Nova Pro Model Configuration
BEDROCK_MODEL_ID = 'amazon.nova-pro-v1:0'
MODEL_CONFIG = {
    'max_tokens': 1000,
    'temperature': 0.7,  # balanced creativity and accuracy
    'top_p': 0.9
}

# 1. Customer Payment Analysis Prompts

PAYMENT_ANALYSIS_PROMPT = """
You are a financial AI analyst for Innovate AI, specializing in accounts receivable and customer payment behavior analysis.

Customer Payment Data:
{customer_summary}

Analysis Requirements:
1. RISK ASSESSMENT: Categorize customers by payment risk (Low/Medium/High)
2. TREND IDENTIFICATION: Identify patterns in late payment behavior
3. COLLECTION STRATEGY: Recommend specific actions for high-risk customers  
4. BUSINESS INSIGHTS: Provide actionable insights for the billing team

Criteria for Analysis:
- Frequent Late Payer: 3+ payments more than 7 days late
- High Risk: Late payment rate > 50% or average 14+ days late
- Medium Risk: Late payment rate 20-50% or average 7-14 days late
- Low Risk: Late payment rate < 20% and average < 7 days late

Output Format:
- Executive Summary (2-3 sentences)
- Risk Categories with customer counts
- Top 3 recommended actions
- Payment trend insights

Keep response professional, data-driven, and actionable.
"""

CUSTOMER_RISK_PROMPT = """
Analyze payment behavior for {customer_name} (ID: {customer_id}):

Payment History:
- Total Invoices: {total_invoices}
- Late Payments: {late_payments} 
- Late Payment Rate: {late_rate}%
- Average Days Late: {avg_days_late}
- Recent Payment Pattern: {recent_pattern}

Outstanding Invoices:
{outstanding_invoices}

Provide:
1. Risk Level (Low/Medium/High) with justification
2. Payment behavior pattern description
3. Recommended collection approach
4. Suggested timeline for follow-up actions

Consider Innovate AI's professional approach and focus on maintaining customer relationships while ensuring timely payments.
"""

# 2. Email Draft Generation Prompts

FIRST_REMINDER_PROMPT = """
Draft a professional first payment reminder email for Innovate AI.

Customer: {customer_name}
Email: {customer_email}
Total Outstanding: ${total_amount:,.2f}

Overdue Invoices:
{invoice_details}

Requirements:
- Professional, friendly tone
- Innovate AI branding and signature
- Clear payment details and due dates
- Multiple payment options
- Contact information for questions
- Subtle urgency without being aggressive

Email Structure:
Subject: [Create compelling subject line]

Dear {customer_name},

[Professional greeting and relationship acknowledgment]
[Invoice details and payment request]
[Payment options and instructions]
[Contact information for assistance]
[Professional closing with Innovate AI signature]

Maintain a helpful, solution-oriented approach that preserves the business relationship.
"""

SECOND_REMINDER_PROMPT = """
Draft a more urgent second payment reminder for Innovate AI.

Customer: {customer_name}
Days Overdue: {days_overdue}
Total Outstanding: ${total_amount:,.2f}
Previous Reminder Sent: {last_reminder_date}

Overdue Invoices:
{invoice_details}

Requirements:
- More urgent tone while remaining professional
- Reference previous communication
- Emphasize impact of delayed payment
- Offer payment plan options
- Include consequences of continued delay
- Innovate AI branding

Email Structure:
Subject: [Urgent but professional subject]

Dear {customer_name},

[Reference to previous reminder]
[Escalated urgency with professional tone]
[Clear consequences and next steps]
[Payment plan options]
[Direct contact for immediate resolution]
[Professional but firm closing]

Balance firmness with maintaining the customer relationship.
"""

FINAL_NOTICE_PROMPT = """
Draft a firm final notice email for Innovate AI before collection actions.

Customer: {customer_name}
Days Overdue: {days_overdue}
Total Outstanding: ${total_amount:,.2f}
Previous Reminders: {reminder_count}

Critical Details:
{invoice_details}

Requirements:
- Firm, professional tone
- Clear final deadline (e.g., 10 business days)
- Specific consequences (collection agency, credit reporting)
- Last opportunity language
- Legal compliance considerations
- Innovate AI professional standards

Email Structure:
Subject: [Final Notice - Action Required]

Dear {customer_name},

[Final notice declaration]
[Summary of previous attempts]
[Clear deadline and consequences]
[Final payment options]
[Contact for immediate resolution]
[Professional legal-compliant closing]

Maintain professionalism while being absolutely clear about consequences.
"""

# 3. Conversational AI Prompts

CHATBOT_SYSTEM_PROMPT = """
You are an AI assistant for Innovate AI's invoice management and billing system. Your role is to help users with:

1. Customer payment analysis and insights
2. Invoice management and tracking
3. Collection strategy recommendations  
4. Email template generation and approval
5. Payment trend analysis
6. Risk assessment and reporting

Personality:
- Professional and knowledgeable
- Helpful and solution-oriented
- Data-driven in recommendations
- Respectful of customer relationships
- Compliant with business standards

Capabilities:
- Analyze customer payment patterns
- Generate personalized email drafts
- Provide collection strategy advice
- Track email sending history
- Prevent duplicate communications
- Generate business insights

Limitations:
- Cannot directly send emails (requires human approval)
- Cannot access external credit data
- Cannot make legal judgments
- Must maintain customer privacy

Always provide actionable, professional advice that aligns with Innovate AI's values and business objectives.
"""

TEMPLATE_QUESTIONS = {
    "analyze_late_payers": """
    Analyze all customers to identify frequent late payers (those who pay more than 7 days late consistently). 
    
    I'll examine:
    - Payment history patterns
    - Late payment frequency  
    - Average days overdue
    - Risk categorization
    - Recommended actions
    
    Would you like me to focus on any specific time period or customer segment?
    """,
    
    "draft_reminders": """
    I can help draft personalized reminder emails for overdue invoices.
    
    Please specify:
    - Customer ID or name
    - Reminder type (first, second, final)
    - Any special circumstances
    
    I'll create a professional email with Innovate AI branding that maintains good customer relationships while encouraging prompt payment.
    """,
    
    "payment_patterns": """
    I'll analyze payment patterns to identify trends and insights.
    
    Analysis includes:
    - Seasonal payment trends
    - Customer segment behavior
    - Risk indicators
    - Collection effectiveness
    - Recommended improvements
    
    What specific aspect of payment patterns interests you most?
    """,
    
    "bulk_campaign": """
    I can help plan a bulk reminder campaign for multiple overdue accounts.
    
    Process:
    1. Identify eligible customers (no recent reminders)
    2. Segment by risk level and overdue amount
    3. Generate personalized email drafts
    4. Queue for human review and approval
    5. Track sending and responses
    
    What criteria should I use to select customers for this campaign?
    """
}

# 4. Data Analysis Prompts

METRICS_ANALYSIS_PROMPT = """
Analyze payment performance metrics for Innovate AI:

Current Metrics:
- Total Outstanding: ${total_outstanding:,.2f}
- Number of Overdue Accounts: {overdue_count}
- Average Days Sales Outstanding (DSO): {dso}
- Collection Rate: {collection_rate}%
- Late Payment Rate: {late_rate}%

Historical Trends:
{historical_data}

Customer Segments:
{segment_analysis}

Provide:
1. Performance assessment vs industry benchmarks
2. Trend analysis and trajectory
3. Areas of concern requiring immediate attention
4. Recommended process improvements
5. Target metrics for improvement

Focus on actionable insights that can improve cash flow and reduce collection costs.
"""

BENCHMARK_COMPARISON_PROMPT = """
Compare Innovate AI's collection performance against industry standards:

Our Performance:
- DSO: {our_dso} days
- Collection Rate: {our_collection_rate}%  
- Late Payment Rate: {our_late_rate}%
- First Contact Resolution: {our_fcr}%

Industry Context: B2B Software/Services
- Typical DSO: 30-45 days
- Good Collection Rate: 95%+
- Average Late Rate: 15-25%
- Best Practice FCR: 60%+

Analysis Required:
1. Gap identification and impact
2. Strengths to leverage
3. Priority improvement areas
4. Realistic improvement targets
5. Implementation recommendations

Provide specific, measurable recommendations for improvement.
"""

# 5. Compliance and Legal Prompts

COMPLIANCE_CHECK_PROMPT = """
Review the following communication for compliance with collection regulations:

Email Content:
{email_content}

Customer Information:
- Location: {customer_location}
- Account Type: {account_type}
- Previous Communications: {communication_history}

Compliance Requirements:
- Fair Debt Collection Practices Act (FDCPA)
- State-specific regulations
- Industry best practices
- Company policy alignment

Verification Points:
1. Professional tone and language
2. Accurate account information
3. Clear payment instructions
4. Appropriate contact information
5. Compliance with timing restrictions
6. Respectful customer treatment

Provide compliance assessment and any recommended modifications.
"""