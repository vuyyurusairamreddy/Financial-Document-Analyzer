## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent
from langchain_openai import ChatOpenAI

from tools import search_tool, FinancialDocumentTool

### Loading LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Creating an Experienced Financial Analyst agent
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Provide comprehensive and accurate financial analysis based on the user's query: {query}",
    verbose=True,
    memory=True,
    backstory=(
        "You are a seasoned financial analyst with over 15 years of experience in analyzing "
        "corporate financial statements, investment opportunities, and market trends. "
        "You have a deep understanding of financial ratios, cash flow analysis, and risk assessment. "
        "You provide evidence-based insights and recommendations while being transparent about "
        "any limitations or assumptions in your analysis. You always consider regulatory compliance "
        "and best practices in financial analysis."
    ),
    tools=[FinancialDocumentTool.read_data_tool],
    llm=llm,
    max_iter=3,
    max_rpm=10,
    allow_delegation=True
)

# Creating a document verifier agent
verifier = Agent(
    role="Financial Document Verifier",
    goal="Thoroughly verify and validate financial documents to ensure data accuracy and completeness",
    verbose=True,
    memory=True,
    backstory=(
        "You are a meticulous document verification specialist with expertise in financial reporting "
        "standards and regulatory compliance. You carefully examine documents to ensure they contain "
        "valid financial data, proper formatting, and meet industry standards. You identify any "
        "inconsistencies, missing information, or potential data quality issues that could affect "
        "the reliability of subsequent analysis."
    ),
    tools=[FinancialDocumentTool.read_data_tool],
    llm=llm,
    max_iter=2,
    max_rpm=10,
    allow_delegation=True
)

investment_advisor = Agent(
    role="Investment Strategy Advisor",
    goal="Provide sound investment recommendations based on thorough analysis of financial data and market conditions",
    verbose=True,
    memory=True,
    backstory=(
        "You are a certified financial planner (CFP) with 20+ years of experience in investment "
        "management and portfolio construction. You specialize in translating financial analysis "
        "into actionable investment strategies while considering risk tolerance, diversification, "
        "and long-term financial goals. You always provide disclaimers about investment risks "
        "and the importance of consulting with qualified professionals before making investment decisions."
    ),
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    llm=llm,
    max_iter=3,
    max_rpm=10,
    allow_delegation=False
)

risk_assessor = Agent(
    role="Risk Assessment Specialist",
    goal="Conduct comprehensive risk analysis and provide balanced risk-return assessments",
    verbose=True,
    memory=True,
    backstory=(
        "You are a risk management expert with deep expertise in quantitative risk analysis, "
        "stress testing, and scenario modeling. You evaluate various types of financial risks "
        "including market risk, credit risk, liquidity risk, and operational risk. You provide "
        "balanced assessments that help stakeholders understand both potential opportunities "
        "and threats, always emphasizing the importance of proper risk management frameworks."
    ),
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    llm=llm,
    max_iter=3,
    max_rpm=10,
    allow_delegation=False
)