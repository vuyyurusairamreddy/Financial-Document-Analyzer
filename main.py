# === Import Required Libraries ===
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid
import asyncio  #Run CPU-intensive tasks in background threads
from datetime import datetime #Timestamp for output files

# CrewAI imports
from crewai import Crew, Process 
#Crew	Orchestrates multiple agents working together
#Process	Defines how agents execute (sequential/parallel)
from agents import financial_analyst, verifier, investment_advisor, risk_assessor #tax_analyst
from task import analyze_financial_document, verification, investment_analysis, risk_assessment #tax_analysis

# === Initialize FastAPI App ===
app = FastAPI(title="Financial Document Analyzer")


# === Function: Run the Complete Multi-Agent Crew ===
# This function runs all four agents sequentially to analyze the financial document.
#This is the heart of the application - it orchestrates all 4 AI agents.

def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """
    Runs all financial agents sequentially (Verifier → Analyst → Investment → Risk).
    
    Args:
        query (str): User's question or focus area.
        file_path (str): Path of the financial document (uploaded or default).
    
    Returns:
        result: The combined CrewAI result after all tasks are executed.
    """
    # Create the multi-agent workflow
    financial_crew = Crew(
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],#tax_analyst
        tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],#tax_analysis,
        process=Process.sequential, 
        # Agents will execute one after another # Investment & Risk analysis can run in parallel
        #process=Process.hierarchical
    )

    # Start the analysis process
    result = financial_crew.kickoff({"query": query, "file_path": file_path})
    return result


# === Function: Save Output to "output/" Folder ===
def save_output_report(query: str, file_path: str, analysis_text: str) -> str:
    """
    Saves the analysis output report to an 'output/' folder as a .txt file.
    
    Args:
        query (str): The analysis query used.
        file_path (str): Path of the financial document analyzed.
        analysis_text (str): The generated analysis content.
    
    Returns:
        str: Full path to the saved output file.
    """
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    # Generate unique filename using timestamp
    """Prevents overwriting previous reports
       Allows tracking analysis history
       Each analysis gets a unique file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"financial_analysis_{timestamp}.txt"
    output_path = os.path.join("output", filename)

    try:
        # Write analysis details into the file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=== Financial Document Analysis Report ===\n\n")
            f.write(f"Query: {query}\n")
            f.write(f"Analyzed File: {file_path}\n")
            f.write(f"Generated On: {datetime.now()}\n\n")
            f.write("=== Full Analysis Output ===\n\n")
            f.write(str(analysis_text))
            f.write("\n\n=== End of Report ===\n")

        return output_path
    except Exception as e:
        print(f" Error saving report: {e}")
        return None


# === Health Check Endpoint ===
@app.get("/")
async def root():
    """
    Simple health check endpoint to verify the API is running.
    purpose: check that server is running
    use: Before uploading files, to verify server is alive
    """
    return {"message": " Financial Document Analyzer API is running"}


# === Favicon Endpoint (to prevent 404 errors in browser) ===
@app.get("/favicon.ico")
async def favicon():
    """
    Return 204 No Content for favicon requests to avoid 404 logs.
    """
    from fastapi.responses import Response
    return Response(status_code=204)


# === Main Endpoint: Analyze Financial Document ===
@app.post("/analyze")
async def analyze_financial_doc(
    file: UploadFile = File(None),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """
    Endpoint to analyze a financial document.
    
    - Accepts an optional uploaded PDF file.
    - Uses a default sample file if no upload is provided.
    - Runs all four analysis agents sequentially.
    - Saves the result in the output folder.
    """
    file_path = "data/sample.pdf"  # Default fallback file
    file_id = None  # For cleanup tracking

    try:
        # Ensure data directory exists for temporary files
        os.makedirs("data", exist_ok=True)

        # If a user uploaded a file, save it temporarily
        if file:
            file_id = str(uuid.uuid4())
            file_path = f"data/financial_document_{file_id}.pdf"
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

        # Clean and validate query text
        query = query.strip() or "Analyze this financial document for investment insights"

        # Run the full analysis in a non-blocking thread
        """Why asyncio.to_thread()?

            CrewAI's run_crew() is CPU-intensive and blocking:

            Takes 30-60 seconds to complete
            Would freeze the entire server if run directly
        Solution:

            asyncio.to_thread(): Runs run_crew() in a separate thread
            await: Waits for result without blocking other requests
            Other users can still access the API while one analysis runs"""
        response = await asyncio.to_thread(run_crew, query, file_path)

        # Save analysis report to output folder
        output_path = save_output_report(query, file_path, str(response))

        # Return API response
        return {
            "status": "success",
            "query": query,
            "file_used": os.path.basename(file_path),
            "output_report": output_path if output_path else "Failed to save report",
        }

    except Exception as e:
        # Handle any errors gracefully
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    finally:
        # Clean up uploaded files (keep default file intact)
        if file_id and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors silently


# === Run the API Locally ===
# === Run the API Locally ===
if __name__ == "__main__":
    import uvicorn
    # Launch FastAPI app with proper configuration
    """"main:app" :Load app object from main.py file
        host="127.0.0.1" :Localhost	Only accessible from this computer
        port=8000	:8000	Server listens on port 8000
        reload=True	:Auto-reload	Restarts server when code changes
        log_level="info"	:Info logs	Show request logs (GET, POST, etc.)
"""
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )