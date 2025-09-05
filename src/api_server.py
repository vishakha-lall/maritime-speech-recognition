from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import subprocess
import logging
import os
import json
from pathlib import Path
import uuid
from datetime import datetime

app = FastAPI(title="Maritime Speech Processing API", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store for tracking job status
job_status = {}

class ProcessAudioRequest(BaseModel):
    video_path: str
    session_id: int
    loglevel: Optional[str] = "INFO"
    results_path: Optional[str] = "temp"

class JobStatus(BaseModel):
    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    message: str
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

def run_process_audio_script(job_id: str, video_path: str, session_id: int, loglevel: str, results_path: str):
    """Run the process_audio_v2.py script as a subprocess"""
    try:
        # Update job status to running
        job_status[job_id]["status"] = "running"
        job_status[job_id]["message"] = "Processing audio..."
        
        # Construct the command
        script_path = Path(__file__).parent / "process_audio_v2.py"
        cmd = [
            "python",
            str(script_path),
            "--video_path", video_path,
            "--session_id", str(session_id),
            "--loglevel", loglevel,
            "--results_path", results_path
        ]
        
        logger.info(f"Job {job_id} - Running command: {' '.join(cmd)}")
        logger.info(f"Job {job_id} - Working directory: {Path(__file__).parent}")
        
        # Run the subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent),
            timeout=3600  # 1 hour timeout
        )
        
        # Log the output
        logger.info(f"Job {job_id} - Return code: {result.returncode}")
        logger.info(f"Job {job_id} - STDOUT: {result.stdout[:500] if result.stdout else 'No stdout'}...")
        if result.stderr:
            logger.error(f"Job {job_id} - STDERR: {result.stderr}")
        
        if result.returncode == 0:
            job_status[job_id]["status"] = "completed"
            job_status[job_id]["message"] = "Audio processing completed successfully"
            job_status[job_id]["completed_at"] = datetime.now().isoformat()
            job_status[job_id]["stdout"] = result.stdout
            job_status[job_id]["stderr"] = result.stderr
            logger.info(f"Job {job_id} completed successfully")
        else:
            job_status[job_id]["status"] = "failed"
            job_status[job_id]["message"] = f"Audio processing failed with return code {result.returncode}"
            job_status[job_id]["error"] = result.stderr or "No error output available"
            job_status[job_id]["stdout"] = result.stdout
            job_status[job_id]["stderr"] = result.stderr
            job_status[job_id]["completed_at"] = datetime.now().isoformat()
            logger.error(f"Job {job_id} failed: {result.stderr or 'No stderr output'}")
            
    except subprocess.TimeoutExpired as e:
        error_msg = f"Process timed out after {e.timeout} seconds"
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = "Audio processing timed out"
        job_status[job_id]["error"] = error_msg
        job_status[job_id]["completed_at"] = datetime.now().isoformat()
        logger.error(f"Job {job_id} timed out: {error_msg}")
        
    except FileNotFoundError as e:
        error_msg = f"Python or script file not found: {str(e)}"
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = "Script file not found"
        job_status[job_id]["error"] = error_msg
        job_status[job_id]["completed_at"] = datetime.now().isoformat()
        logger.error(f"Job {job_id} file not found: {error_msg}")
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = "Audio processing failed with exception"
        job_status[job_id]["error"] = error_msg
        job_status[job_id]["completed_at"] = datetime.now().isoformat()
        logger.error(f"Job {job_id} failed with exception: {error_msg}")

@app.post("/process-audio", response_model=dict)
async def process_audio(request: ProcessAudioRequest, background_tasks: BackgroundTasks):
    """
    Start audio processing job asynchronously
    """
    # Validate video path exists
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=400, detail=f"Video file not found: {request.video_path}")
    
    # Validate loglevel
    if request.loglevel not in ["DEBUG", "INFO"]:
        raise HTTPException(status_code=400, detail="loglevel must be 'DEBUG' or 'INFO'")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_status[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Job queued for processing",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None,
        "stdout": None,
        "stderr": None
    }
    
    # Add background task
    background_tasks.add_task(
        run_process_audio_script,
        job_id,
        request.video_path,
        request.session_id,
        request.loglevel,
        request.results_path
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Audio processing job started",
        "check_status_url": f"/job-status/{job_id}"
    }

@app.post("/process-audio-sync", response_model=dict)
async def process_audio_sync(request: ProcessAudioRequest):
    """
    Process audio synchronously (blocking)
    """
    # Validate video path exists
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=400, detail=f"Video file not found: {request.video_path}")
    
    # Validate loglevel
    if request.loglevel not in ["DEBUG", "INFO"]:
        raise HTTPException(status_code=400, detail="loglevel must be 'DEBUG' or 'INFO'")
    
    try:
        # Construct the command
        script_path = Path(__file__).parent / "process_audio_v2.py"
        cmd = [
            "python",
            str(script_path),
            "--video_path", request.video_path,
            "--session_id", str(request.session_id),
            "--loglevel", request.loglevel,
            "--results_path", request.results_path
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info(f"Working directory: {Path(__file__).parent}")
        
        # Run the subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent),
            timeout=3600  # 1 hour timeout
        )
        
        # Log the output regardless of success/failure
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"STDOUT: {result.stdout[:500] if result.stdout else 'No stdout'}...")
        if result.stderr:
            logger.error(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Audio processing completed successfully",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "results_path": request.results_path
            }
        else:
            error_detail = {
                "message": "Audio processing failed",
                "return_code": result.returncode,
                "stderr": result.stderr or "No stderr output",
                "stdout": result.stdout or "No stdout output",
                "command": " ".join(cmd)
            }
            logger.error(f"Process failed with details: {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)
            
    except subprocess.TimeoutExpired as e:
        error_detail = {
            "message": "Audio processing timed out",
            "error": f"Process timed out after {e.timeout} seconds",
            "command": " ".join(cmd)
        }
        logger.error(f"Process timeout: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)
        
    except FileNotFoundError as e:
        error_detail = {
            "message": "Python or script file not found",
            "error": str(e),
            "script_path": str(script_path),
            "command": " ".join(cmd)
        }
        logger.error(f"File not found: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)
        
    except Exception as e:
        error_detail = {
            "message": "Audio processing failed with exception",
            "error": str(e),
            "error_type": type(e).__name__,
            "command": " ".join(cmd)
        }
        logger.error(f"Unexpected exception: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/job-status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get the status of a processing job
    """
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**job_status[job_id])

@app.get("/jobs", response_model=list)
async def list_jobs():
    """
    List all jobs and their statuses
    """
    return list(job_status.values())

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job from the status tracking
    """
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del job_status[job_id]
    return {"message": f"Job {job_id} deleted"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Maritime Speech Processing API",
        "version": "1.0.0",
        "endpoints": {
            "POST /process-audio": "Start audio processing (async)",
            "POST /process-audio-sync": "Process audio (sync)",
            "GET /job-status/{job_id}": "Get job status",
            "GET /jobs": "List all jobs",
            "DELETE /job/{job_id}": "Delete job",
            "GET /health": "Health check"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
