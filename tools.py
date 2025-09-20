## Importing libraries and files
import os
import asyncio
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from crewai_tools import BaseTool
from crewai_tools import SerperDevTool
from langchain_community.document_loaders import PyPDFLoader
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool
class FinancialDocumentTool(BaseTool):
    name: str = "Financial Document Reader"
    description: str = "Tool to read and extract text content from PDF financial documents"

    @staticmethod
    def read_data_tool(path: str = 'data/sample.pdf') -> str:
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
                content = content.replace('\n\n\n', '\n\n')  # Replace triple newlines
                content = content.replace('  ', ' ')  # Replace double spaces
                content = content.strip()  # Remove leading/trailing whitespace
                
                if content:  # Only add non-empty content
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
class InvestmentTool(BaseTool):
    name: str = "Investment Analysis Tool"
    description: str = "Tool to analyze financial documents for investment insights"
    
    @staticmethod
    def analyze_investment_tool(financial_document_data: str) -> str:
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
class RiskTool(BaseTool):
    name: str = "Risk Assessment Tool"  
    description: str = "Tool to assess financial risks from document data"
    
    @staticmethod
    def create_risk_assessment_tool(financial_document_data: str) -> str:
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