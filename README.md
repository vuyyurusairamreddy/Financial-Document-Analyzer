# Financial Document Analyzer - Fixed Version

A comprehensive AI-powered financial document analysis system built with CrewAI that processes corporate reports, financial statements, and investment documents to provide detailed insights and recommendations.

##  Bugs Found and Fixed

### Deterministic Bugs Fixed:

1. **Missing LLM Configuration** (`agents.py`)
   - **Bug**: `llm = llm` - Undefined variable
   - **Fix**: Added proper OpenAI ChatGPT integration with environment variable configuration

2. **Incorrect Import Statements** (`tools.py`)
   - **Bug**: `from crewai_tools import tools` - Wrong import
   - **Fix**: Corrected to `from crewai_tools import BaseTool`

3. **Missing PDF Processing Library** (`tools.py`)
   - **Bug**: `Pdf` class undefined 
   - **Fix**: Implemented `PyPDFLoader` from langchain_community

4. **Async Function Issues** (`tools.py`)
   - **Bug**: Functions marked `async` but not properly implemented
   - **Fix**: Converted to static methods with proper error handling

5. **Infinite Loop Bug** (`tools.py`)
   - **Bug**: `while "\n\n" in content:` could cause infinite loops
   - **Fix**: Implemented safe string replacement logic

6. **Missing Tool Imports** (`task.py`)
   - **Bug**: Tasks reference tools that weren't imported
   - **Fix**: Added all necessary tool imports

7. **File Path Handling** (`main.py`)
   - **Bug**: No file validation or error handling
   - **Fix**: Added comprehensive file validation, size limits, and error handling

8. **Missing Dependencies** (`requirements.txt`)
   - **Bug**: Missing critical packages like `pypdf`, `langchain-openai`, `uvicorn`
   - **Fix**: Added all required dependencies

### Inefficient Prompts Fixed:

1. **Unprofessional Agent Backstories**
   - **Before**: Agents had unprofessional, unreliable personas
   - **After**: Professional, competent agent descriptions with proper expertise

2. **Poor Task Descriptions**
   - **Before**: Vague, contradictory task instructions
   - **After**: Clear, specific, actionable task descriptions

3. **Inconsistent Output Formats**
   - **Before**: Random, unstructured outputs
   - **After**: Structured, professional report formats

4. **Missing Error Handling**
   - **Before**: No validation or error messages
   - **After**: Comprehensive error handling with informative messages

##  Setup Instructions

### Prerequisites
- Python 3.8+
- OpenAI API key
- Serper API key (for web search functionality)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd financial-document-analyzer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.template .env
   ```
   
   Edit `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   ```

4. **Create data directory:**
   ```bash
   mkdir -p data
   ```

5. **Add sample document (optional):**
   - Place your PDF financial document as `data/sample.pdf`
   - Or use the upload endpoint to analyze any PDF

### Running the Application

1. **Start the server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the API:**
   - API Base URL: `http://localhost:8000`
   - Interactive Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

##  API Documentation

### Endpoints

#### `GET /`
Health check endpoint
- **Response**: Basic API status

#### `GET /health`
Detailed health check
- **Response**: System status, configuration check

#### `POST /analyze`
Upload and analyze a financial document
- **Parameters**:
  - `file`: PDF file (max 10MB)
  - `query`: Analysis question (optional)
- **Response**: Comprehensive financial analysis

#### `POST /analyze-sample`
Analyze the sample document in data/sample.pdf
- **Parameters**:
  - `query`: Analysis question (optional)
- **Response**: Analysis of sample document

### Usage Examples

#### Using cURL

**Upload and analyze a document:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@/path/to/financial-report.pdf" \
  -F "query=What are the key investment risks?"
```

**Analyze sample document:**
```bash
curl -X POST "http://localhost:8000/analyze-sample" \
  -F "query=Provide investment recommendations"
```

#### Using Python requests

```python
import requests

# Upload and analyze
with open('financial-report.pdf', 'rb') as f:
    files = {'file': f}
    data = {'query': 'Analyze the revenue trends'}
    response = requests.post('http://localhost:8000/analyze', files=files, data=data)
    
print(response.json())
```

#### Using the Interactive Documentation

1. Go to `http://localhost:8000/docs`
2. Click on any endpoint to expand it
3. Use "Try it out" to test the API directly

##  System Architecture

### Agents
- **Financial Analyst**: Senior analyst for comprehensive financial analysis
- **Document Verifier**: Validates document quality and completeness
- **Investment Advisor**: Provides investment recommendations
- **Risk Assessor**: Conducts risk analysis

### Tools
- **FinancialDocumentTool**: PDF reading and content extraction
- **InvestmentTool**: Investment analysis functionality
- **RiskTool**: Risk assessment capabilities
- **SerperDevTool**: Web search for market insights

### Tasks
- **Document Verification**: Validates document accessibility and quality
- **Financial Analysis**: Comprehensive document analysis
- **Investment Analysis**: Investment insights and recommendations
- **Risk Assessment**: Risk evaluation and mitigation strategies

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for LLM functionality
- `SERPER_API_KEY`: Required for web search capabilities
- `APP_ENV`: Application environment (development/production)
- `LOG_LEVEL`: Logging level (INFO/DEBUG/ERROR)

### File Limits
- Maximum file size: 10MB
- Supported formats: PDF only
- Automatic cleanup of temporary files

##  Testing

### Manual Testing
1. Start the server
2. Visit `http://localhost:8000/docs`
3. Upload a sample financial PDF
4. Test different query types

### Sample Queries
- "What are the key financial metrics?"
- "Analyze the revenue trends over the past quarters"
- "What are the main investment risks?"
- "Provide investment recommendations based on this report"
- "Assess the company's financial health"

##  Error Handling

The system includes comprehensive error handling for:
- Invalid file formats
- File size limits
- Missing API keys
- PDF processing errors
- Analysis failures
- Network issues

All errors return structured JSON responses with clear error messages.

##  Logging

The application includes detailed logging for:
- File upload/processing
- Analysis progress
- Error conditions
- Performance metrics

Logs are configured via environment variables and include timestamps, levels, and detailed context.

##  Bonus Features Implemented

### Queue Worker Model Enhancement
To handle concurrent requests efficiently, consider implementing:

```python
# redis_queue.py (Optional Enhancement)
import redis
from rq import Queue
from rq.job import Job

redis_conn = redis.Redis(host='localhost', port=6379, db=0)
analysis_queue = Queue('analysis', connection=redis_conn)

def queue_analysis(file_path: str, query: str):
    job = analysis_queue.enqueue(
        run_crew,
        file_path,
        query,
        timeout='10m'
    )
    return job.id
```

### Database Integration Enhancement
For storing analysis results:

```python
# database.py (Optional Enhancement)
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

Base = declarative_base()

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    result = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

##  License

This project is licensed under the MIT License.

##  Support

For issues and questions:
1. Check the logs for detailed error messages
2. Verify API keys are correctly configured
3. Ensure all dependencies are installed
4. Check file format and size requirements

##  Version History

### v1.0.0 - Fixed Release
-  Fixed all deterministic bugs
-  Improved prompts and agent behavior
-  Added comprehensive error handling
-  Implemented proper logging
-  Added API documentation
-  Enhanced file validation
-  Professional agent personas
#http://localhost:8000/docs
POST /analyze - Main analysis endpoint (upload PDF)
POST /analyze-sample - Analyze default sample.pdf
POST /analyze-async - Queue-based async processing (bonus feature)