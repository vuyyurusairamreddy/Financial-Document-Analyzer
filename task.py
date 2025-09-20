## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, FinancialDocumentTool, InvestmentTool, RiskTool

## Creating a task to analyze financial documents
analyze_financial_document = Task(
    description="""
    Analyze the financial document thoroughly to address the user's query: {query}
    
    Your analysis should include:
    1. Extract and read the financial document content
    2. Identify key financial metrics and indicators
    3. Analyze trends, patterns, and significant changes
    4. Provide insights relevant to the user's specific query
    5. Highlight any areas of concern or opportunity
    6. Ensure all analysis is based on actual document content
    
    Be precise, factual, and base all conclusions on evidence from the document.
    If certain information is not available in the document, clearly state this limitation.
    """,

    expected_output="""
    A comprehensive financial analysis report containing:
    - Executive Summary of key findings
    - Detailed analysis of financial metrics relevant to the query  
    - Identification of trends and patterns in the data
    - Specific insights addressing the user's question
    - Risk factors and opportunities identified
    - Clear conclusions based on document evidence
    - Any limitations or assumptions made in the analysis
    
    Format the output in clear sections with proper headers and bullet points where appropriate.
    """,

    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    async_execution=False,
)

## Creating a document verification task
verification = Task(
    description="""
    Verify the financial document for:
    1. Document accessibility and readability
    2. Presence of key financial information
    3. Data quality and completeness
    4. Standard financial reporting elements
    5. Any formatting or data extraction issues
    
    Provide a clear assessment of whether the document contains sufficient 
    financial information for meaningful analysis.
    """,

    expected_output="""
    Document verification report including:
    - File accessibility status
    - Content extraction success/issues
    - Financial information assessment
    - Data quality evaluation  
    - Recommendations for analysis feasibility
    - List of key financial elements found
    
    Clear pass/fail status for document verification.
    """,

    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False
)

## Creating an investment analysis task
investment_analysis = Task(
    description="""
    Based on the financial document analysis, provide investment insights for: {query}
    
    Your analysis should cover:
    1. Investment attractiveness based on financial performance
    2. Key financial ratios and their implications
    3. Growth prospects and market position
    4. Competitive advantages or disadvantages
    5. Investment risks and mitigation strategies
    6. Suitable investor profiles for this investment
    
    Provide balanced, evidence-based investment perspective with appropriate disclaimers.
    """,

    expected_output="""
    Investment analysis report containing:
    - Investment thesis summary
    - Key financial metrics analysis
    - Strengths and weaknesses assessment
    - Risk-return profile evaluation
    - Target investor considerations
    - Investment recommendation with rationale
    - Important disclaimers about investment risks
    
    Include specific data points from the document to support recommendations.
    """,

    agent=investment_advisor,
    tools=[FinancialDocumentTool.read_data_tool, InvestmentTool.analyze_investment_tool, search_tool],
    async_execution=False,
)

## Creating a risk assessment task
risk_assessment = Task(
    description="""
    Conduct comprehensive risk assessment based on the financial document for: {query}
    
    Analyze the following risk categories:
    1. Financial risks (liquidity, credit, market)
    2. Operational risks
    3. Strategic and competitive risks  
    4. Regulatory and compliance risks
    5. Industry and market risks
    6. Risk mitigation measures in place
    
    Provide quantitative analysis where possible and qualitative assessment for other factors.
    """,

    expected_output="""
    Risk assessment report including:
    - Executive risk summary
    - Detailed risk category analysis
    - Risk severity and probability assessment
    - Risk interdependencies and correlations
    - Existing risk mitigation strategies
    - Recommended additional risk controls
    - Risk monitoring recommendations
    
    Present risks in order of priority with supporting evidence from the document.
    """,

    agent=risk_assessor,  
    tools=[FinancialDocumentTool.read_data_tool, RiskTool.create_risk_assessment_tool, search_tool],
    async_execution=False,
)