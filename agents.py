## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, LLM

# Try multiple API providers
openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")
perplexity_key = os.getenv("PERPLEXITY_API_KEY")

if perplexity_key:
    # Perplexity configuration
    llm = LLM(
        model="perplexity/sonar-pro",  # or "perplexity/sonar" for faster/cheaper
        temperature=0.1,
        api_key=perplexity_key
    )
    print(" Using Perplexity Sonar Pro")
elif openai_key:
    llm = LLM(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=openai_key
    )
    print(" Using OpenAI GPT-4o-mini")
elif gemini_key:
    llm = LLM(
        model="gemini/gemini-1.5-flash",
        temperature=0.1,
        api_key=gemini_key
    )
    print(" Using Google Gemini")
else:
    raise ValueError("No valid API key found. Please set PERPLEXITY_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY in .env")

# Import tool instances (not classes)
from tools import search_tool, read_data_tool, analyze_investment_tool, create_risk_assessment_tool

# Creating an Experienced Financial Analyst agent
financial_analyst = Agent (
    role="Senior Financial Analyst",
    goal="Provide comprehensive and accurate financial analysis based on the user's query: {query}",
    verbose=True,#Show detailed logs (agent's thinking process) 
    # False: only final output is shown
    memory=True,
    #True: Agent remembers previous interactions
    #False: Each interaction is independent
    backstory=(
        "You are a seasoned financial analyst with over 15 years of experience in analyzing "
        "corporate financial statements, investment opportunities, and market trends. "
        "You have a deep understanding of financial ratios, cash flow analysis, and risk assessment. "
        "You provide evidence-based insights and recommendations while being transparent about "
        "any limitations or assumptions in your analysis. You always consider regulatory compliance "
        "and best practices in financial analysis."
    ),
    tools=[read_data_tool],  # List of tools this agent can use
    llm=llm,
    max_iter=3,  # Agent can think → act → think → act → think → act (3 cycles), preventing infinite loops
    max_rpm=10,
    allow_delegation=True  # True: Can ask other agents for help | False: Works independently
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
    tools=[read_data_tool],
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
    tools=[read_data_tool, analyze_investment_tool, search_tool],
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
    tools=[read_data_tool, create_risk_assessment_tool, search_tool],
    llm=llm,
    max_iter=3,
    max_rpm=10,
    allow_delegation=False
)

"""# Creating a Tax Analyst agent
tax_analyst = Agent(
    role="Senior Tax Analyst",
    goal="Analyze tax implications and provide tax optimization strategies based on financial data from: {query}",
    verbose=True,
    memory=True,
    backstory=(
        "You are a certified public accountant (CPA) with 18+ years of experience in corporate taxation, "
        "tax planning, and compliance. You specialize in identifying tax liabilities, deductions, credits, "
        "and optimization strategies. You stay current with tax code changes and provide actionable "
        "recommendations while ensuring compliance with IRS regulations and international tax laws. "
        "You always emphasize the importance of consulting with qualified tax professionals for specific tax advice."
    ),
    tools=[read_data_tool, search_tool],  # Can read documents and search for tax law updates
    llm=llm,
    max_iter=3,
    max_rpm=10,
    allow_delegation=False  # Tax analysis is specialized, works independently
)"""