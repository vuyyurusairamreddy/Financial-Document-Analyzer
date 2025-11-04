## Importing libraries and files
from crewai import Task
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
#from agents import financial_analyst, verifier, investment_advisor, risk_assessor, tax_analyst
from tools import search_tool, read_data_tool, analyze_investment_tool, create_risk_assessment_tool

## Creating a task to analyze financial documents
analyze_financial_document = Task(
    description="""
    Analyze the financial document at {file_path} thoroughly to address the user's query: {query}
    
    Steps:
    1. Use the Financial Document Reader tool to read the document at {file_path}
    2. Identify key financial metrics (revenue, profit, cash flow, debt, etc.)
    3. Analyze trends and patterns in the data
    4. Provide actionable insights
    5. Highlight risks and opportunities
    """,
    expected_output="""
    Comprehensive financial analysis report including:
    - Executive summary of key findings
    - Analysis of important financial metrics and trends
    - Insights and strategic recommendations
    - Identified limitations or data gaps
    """,
    agent=financial_analyst,#Assigns a specific agent to perform this task
    async_execution=False,#Tasks run one after another (sequential), not in parallel
)

## Creating a document verification task
verification = Task(
    description="""
    Verify the financial document at {file_path} for accessibility, completeness, and data quality.
    
    Steps:
    1. Use the Financial Document Reader tool to access the document at {file_path}
    2. Check if the document can be read successfully
    3. Verify the document contains financial data
    4. Identify any data quality issues
    5. Confirm the document is suitable for analysis
    """,
    expected_output="""
    Verification report including:
    - Document accessibility status (pass/fail)
    - Data completeness assessment
    - List of any issues or concerns found
    - Recommendation on whether to proceed with analysis
    """,
    agent=verifier,
    async_execution=False,
)

## Creating an investment analysis task
investment_analysis = Task(
    description="""
    Provide investment insights based on the financial document at {file_path} for the query: {query}
    
    Steps:
    1. Use the Financial Document Reader tool to read the document at {file_path}
    2. Use the Investment Analysis Tool to evaluate investment potential
    3. Use web search if needed to gather market context
    4. Assess investment opportunities and risks
    5. Provide actionable investment recommendations
    """,
    expected_output="""
    Investment analysis report including:
    - Investment thesis and key opportunities
    - Risk-return profile assessment
    - Specific investment recommendations
    - Important disclaimers about investment risks
    - Recommendation to consult financial professionals
    """,
    agent=investment_advisor,
    async_execution=False,
)

## Creating a risk assessment task
risk_assessment = Task(
    description="""
    Conduct comprehensive risk assessment based on the financial document at {file_path} for the query: {query}
    
    Steps:
    1. Use the Financial Document Reader tool to read the document at {file_path}
    2. Use the Risk Assessment Tool to identify and categorize risks
    3. Use web search if needed for industry risk benchmarks
    4. Evaluate risk severity and likelihood
    5. Recommend risk mitigation strategies
    """,
    expected_output="""
    Risk assessment report including:
    - Comprehensive risk identification and categorization
    - Risk severity levels (High/Medium/Low)
    - Detailed risk analysis for each identified risk
    - Mitigation strategies and recommendations
    - Monitoring and control recommendations
    """,
    agent=risk_assessor,
    async_execution=False,
)

## Creating a tax analysis task
tax_analysis = Task(
    description="""
    Conduct comprehensive tax analysis based on the financial document at {file_path} for the query: {query}
    
    Steps:
    1. Use the Financial Document Reader tool to read the document at {file_path}
    2. Identify taxable income, deductions, and credits
    3. Use web search if needed to verify current tax rates and regulations
    4. Calculate estimated tax liabilities
    5. Provide tax optimization strategies and recommendations
    """,
    expected_output="""
    Tax analysis report including:
    - Summary of taxable income and tax liabilities
    - Identified deductions and tax credits
    - Current applicable tax rates (federal, state, international)
    - Tax optimization strategies
    - Compliance recommendations
    - Important disclaimers about consulting tax professionals
    """,
    #agent=tax_analyst,
    async_execution=False,
)