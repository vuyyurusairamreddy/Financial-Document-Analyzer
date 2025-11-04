## Importing libraries and files
import os                                    # File system operations
import asyncio                               # Async operations (imported but not used)
from typing import Optional, Type            # Type hints
from dotenv import load_dotenv               # Load environment variables
load_dotenv()                                # Loads .env file

from crewai.tools import BaseTool            # Base class for custom tools
from pydantic import BaseModel, Field        # Input validation schemas
from crewai_tools import SerperDevTool       # Pre-built web search tool
from langchain_community.document_loaders import PyPDFLoader  # PDF reader
import logging                               # Error logging

logging.basicConfig(level=logging.INFO)      # Configure logging
logger = logging.getLogger(__name__)         # Create logger instance



# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) #Tracks errors and info messages

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool
class FinancialDocumentToolInput(BaseModel):
    """Input schema for FinancialDocumentTool."""
    path: str = Field(default='data/sample.pdf', description="Path to the PDF file")

class FinancialDocumentTool(BaseTool):
    #Tool name shown to the agent
    name: str = "Financial Document Reader"
    #Tells the agent what this tool does
    description: str = "Tool to read and extract text content from PDF financial documents"
    #Defines expected input format
    args_schema: Type[BaseModel] = FinancialDocumentToolInput

    def _run(self, path: str = 'data/sample.pdf') -> str:
        """Tool to read data from a PDF file from a path

        Args:
            path (str): Path of the PDF file. Defaults to 'data/sample.pdf'.

        Returns:
            str: Full Financial Document content
        """
        try:
            # Check if file exists
            if not os.path.exists(path):
                logger.error(f"File not found: {path}")
                return f"Error: File not found at path {path}. Please ensure the file exists."
            
            # Check if it's a PDF file
            if not path.lower().endswith('.pdf'):
                logger.error(f"Invalid file type: {path}")
                return f"Error: File must be a PDF. Received: {path}"
            
            # Load the PDF using PyPDFLoader
            loader = PyPDFLoader(path)
            docs = loader.load()
            
            if not docs:
                logger.warning(f"No content extracted from: {path}")
                return "Error: No content could be extracted from the PDF file."

            full_report = ""
            for i, page in enumerate(docs):
                # Clean and format the financial document data
                content = page.page_content
                
                # Remove excessive whitespaces and format properly
                content = content.replace('\n\n\n', '\n\n')
                content = content.replace('  ', ' ')
                content = content.strip()
                
                if content:
                    full_report += f"\n--- Page {i+1} ---\n"
                    full_report += content + "\n"
            
            if not full_report.strip():
                return "Error: No readable content found in the PDF file."
                
            logger.info(f"Successfully extracted {len(full_report)} characters from {path}")
            return full_report.strip()
            
        except Exception as e:
            logger.error(f"Error reading PDF file {path}: {str(e)}")
            return f"Error reading PDF file: {str(e)}. Please ensure the file is a valid PDF and not corrupted."

## Creating Investment Analysis Tool
class InvestmentToolInput(BaseModel):
    """Input schema for InvestmentTool."""
    financial_document_data: str = Field(..., description="The financial document content to analyze")

class InvestmentTool(BaseTool):
    name: str = "Investment Analysis Tool"
    description: str = "Tool to analyze financial documents for investment insights"
    args_schema: Type[BaseModel] = InvestmentToolInput
    
    def _run(self, financial_document_data: str) -> str:
        """Analyze financial document data for investment opportunities
        
        Args:
            financial_document_data (str): The financial document content
            
        Returns:
            str: Investment analysis results
        """
        try:
            if not financial_document_data or not financial_document_data.strip():
                return "Error: No financial document data provided for analysis."
            
            # Clean up the data format
            processed_data = financial_document_data.strip()
            
            # Remove excessive whitespaces
            while '  ' in processed_data:
                processed_data = processed_data.replace('  ', ' ')
                
            # Basic validation for financial content
            financial_keywords = [
                'revenue', 'profit', 'loss', 'assets', 'liabilities', 'cash flow',
                'earnings', 'balance sheet', 'income statement', 'financial',
                'investment', 'roi', 'margin', 'debt', 'equity'
            ]
            
            content_lower = processed_data.lower()
            found_keywords = [kw for kw in financial_keywords if kw in content_lower]
            
            if len(found_keywords) < 3:
                return ("Warning: This document may not contain sufficient financial information "
                       "for comprehensive investment analysis. Found financial terms: " + 
                       ", ".join(found_keywords))
            
            analysis_result = {
                "document_length": len(processed_data),
                "financial_keywords_found": found_keywords,
                "status": "Ready for detailed investment analysis",
                "recommendation": "Document contains sufficient financial data for analysis"
            }
            
            return f"Investment Analysis Summary:\n{analysis_result}"
            
        except Exception as e:
            logger.error(f"Error in investment analysis: {str(e)}")
            return f"Error during investment analysis: {str(e)}"

## Creating Risk Assessment Tool
class RiskToolInput(BaseModel):
    """Input schema for RiskTool."""
    financial_document_data: str = Field(..., description="The financial document content to assess")

class RiskTool(BaseTool):
    name: str = "Risk Assessment Tool"  
    description: str = "Tool to assess financial risks from document data"
    args_schema: Type[BaseModel] = RiskToolInput
    
    def _run(self, financial_document_data: str) -> str:
        """Create risk assessment from financial document data
        
        Args:
            financial_document_data (str): The financial document content
            
        Returns:
            str: Risk assessment results
        """
        try:
            if not financial_document_data or not financial_document_data.strip():
                return "Error: No financial document data provided for risk assessment."
            
            # Risk-related keywords to look for
            risk_keywords = [
                'debt', 'liability', 'risk', 'uncertainty', 'volatility',
                'loss', 'decline', 'decrease', 'challenge', 'threat',
                'exposure', 'contingency', 'default', 'bankruptcy'
            ]
            
            content_lower = financial_document_data.lower()
            found_risks = [kw for kw in risk_keywords if kw in content_lower]
            
            # Count risk mentions
            risk_mentions = sum(content_lower.count(kw) for kw in risk_keywords)
            
            # Basic risk categorization
            if risk_mentions > 20:
                risk_level = "High"
            elif risk_mentions > 10:
                risk_level = "Medium"  
            elif risk_mentions > 5:
                risk_level = "Low-Medium"
            else:
                risk_level = "Low"
            
            risk_assessment = {
                "overall_risk_level": risk_level,
                "risk_indicators_found": found_risks,
                "total_risk_mentions": risk_mentions,
                "document_length": len(financial_document_data),
                "assessment_status": "Completed"
            }
            
            return f"Risk Assessment Summary:\n{risk_assessment}"
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {str(e)}")
            return f"Error during risk assessment: {str(e)}"

# Create tool instances
read_data_tool = FinancialDocumentTool()
analyze_investment_tool = InvestmentTool()
create_risk_assessment_tool = RiskTool()
"""def _run(self, path: str = 'data/sample.pdf') -> str:
    loader = PyPDFLoader(path)
    docs = loader.load()
    
    # Group pages into chunks of 10
    PAGES_PER_CHUNK = 10
    chunks = []
    
    for i in range(0, len(docs), PAGES_PER_CHUNK):
        chunk_pages = docs[i:i + PAGES_PER_CHUNK]
        chunk_text = "\n".join([page.page_content for page in chunk_pages])
        chunks.append(f"--- Pages {i+1} to {i+len(chunk_pages)} ---\n{chunk_text}")
    
    # Return first chunk or summarized version
    return chunks[0]  # Or combine chunks intelligently"""
"""
from langchain.text_splitter import RecursiveCharacterTextSplitter

def _run(self, path: str = 'data/sample.pdf') -> str:
    loader = PyPDFLoader(path)
    docs = loader.load()
    
    # Combine all pages
    full_text = "\n".join([page.page_content for page in docs])
    
    # Split into chunks that fit token limits
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,      # ~1000 tokens (4 chars ≈ 1 token)
        chunk_overlap=200,    # Overlap to maintain context
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_text(full_text)
    
    # Process first chunk or combine summaries
    return chunks[0]  # Or use map-reduce pattern"""    