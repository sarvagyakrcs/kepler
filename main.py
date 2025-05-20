from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Path
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os
from pathlib import Path as FilePath
import tempfile
import uuid
from typing import Optional, List
from pydantic import BaseModel, Field

from scripts.process_kic_target import process_kic_target
from utils.plot_deviation import plot_deviation, plot_multiple_deviations

# Define response models for better Swagger documentation
class StatusResponse(BaseModel):
    status: str = Field(..., example="success", description="Status of the operation")
    message: str = Field(..., example="Operation completed successfully", description="Detailed message about the operation")

class ProcessKICResponse(StatusResponse):
    results_path: Optional[str] = Field(None, example="results/deviation_array/kic_12345", description="Path to the results directory")

class KICListResponse(BaseModel):
    kic_numbers: List[int] = Field(..., example=[12345, 67890], description="List of available KIC numbers")

app = FastAPI(
    title="Kepler Data Analysis API", 
    description="API for processing and analyzing Kepler light curve data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Create necessary directories
FilePath("results/deviation_array").mkdir(parents=True, exist_ok=True)
FilePath("temp_plots").mkdir(exist_ok=True)

@app.get("/", response_model=StatusResponse, tags=["General"])
def read_root():
    """
    Root endpoint that returns a welcome message.
    
    Returns:
        dict: A welcome message
    """
    return {"status": "success", "message": "Welcome to Kepler Data Analysis API"}

@app.post("/process-kic", response_model=ProcessKICResponse, tags=["KIC Processing"])
def process_kic(
    kic_number: int = Query(..., description="KIC catalogue number to process", example=12345),
    timeout: int = Query(120, description="Timeout in seconds for each download", example=120),
    max_files: Optional[int] = Query(None, description="Maximum number of files to process", example=5)
):
    """
    Process a KIC target by downloading and analyzing its light curve data.
    
    This endpoint will:
    1. Download light curve data for the specified KIC number
    2. Process the data to generate deviation arrays
    3. Save the results to the results directory
    
    Args:
        kic_number: KIC catalogue number to process
        timeout: Timeout in seconds for each download
        max_files: Maximum number of files to process (optional)
    
    Returns:
        ProcessKICResponse: Status of the operation and path to results
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        process_kic_target(kic_number, timeout, max_files)
        results_dir = FilePath(f"results/deviation_array/kic_{kic_number}")
        
        if not (results_dir / "deviation.txt").exists():
            return {"status": "error", "message": "No files were successfully processed"}
            
        return {
            "status": "success", 
            "message": f"Successfully processed KIC {kic_number}",
            "results_path": str(results_dir)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plot-deviation/{kic_number}", tags=["Visualization"])
def get_deviation_plot(
    kic_number: int = Path(..., description="KIC catalogue number", example=12345),
    save_plot: bool = Query(False, description="Whether to save the plot to disk")
):
    """
    Generate and return a deviation plot for the specified KIC number.
    
    Args:
        kic_number: KIC catalogue number
        save_plot: Whether to save the plot to disk (optional, default: False)
    
    Returns:
        FileResponse: PNG image of the deviation plot
        
    Raises:
        HTTPException: If no deviation data is found for the specified KIC number
    """
    file_path = FilePath(f"results/deviation_array/kic_{kic_number}/deviation.txt")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"No deviation data found for KIC {kic_number}")
    
    # Generate a unique filename for the plot
    plot_filename = f"kic_{kic_number}_{uuid.uuid4().hex[:8]}.png"
    plot_path = FilePath("temp_plots") / plot_filename
    
    # Create the plot
    plot_deviation(
        file_path=str(file_path),
        save_path=str(plot_path),
        show_plot=False,
        title=f"Deviation for KIC {kic_number}"
    )
    
    # Return the plot as a file response
    return FileResponse(
        path=plot_path,
        media_type="image/png",
        filename=f"kic_{kic_number}_deviation.png"
    )

@app.get("/compare-deviations", tags=["Visualization"])
def compare_deviations(
    kic_numbers: List[int] = Query(..., description="List of KIC numbers to compare", example=[12345, 67890])
):
    """
    Compare deviations across multiple KIC targets and return a plot.
    
    Args:
        kic_numbers: List of KIC numbers to compare
    
    Returns:
        FileResponse: PNG image of the comparison plot
        
    Raises:
        HTTPException: If no deviation data is found for any of the specified KIC numbers
    """
    file_paths = []
    
    for kic_number in kic_numbers:
        file_path = FilePath(f"results/deviation_array/kic_{kic_number}/deviation.txt")
        if not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"No deviation data found for KIC {kic_number}"
            )
        file_paths.append(str(file_path))
    
    # Generate a unique filename for the plot
    plot_filename = f"comparison_{uuid.uuid4().hex[:8]}.png"
    plot_path = FilePath("temp_plots") / plot_filename
    
    # Create the comparison plot
    plot_multiple_deviations(
        file_paths=file_paths,
        save_path=str(plot_path),
        show_plot=False
    )
    
    # Return the plot as a file response
    return FileResponse(
        path=plot_path,
        media_type="image/png",
        filename="deviation_comparison.png"
    )

@app.get("/available-kics", response_model=KICListResponse, tags=["KIC Management"])
def get_available_kics():
    """
    List all available processed KIC targets.
    
    Returns:
        KICListResponse: List of available KIC numbers
    """
    results_dir = FilePath("results/deviation_array")
    
    if not results_dir.exists():
        return {"kic_numbers": []}
    
    kic_dirs = [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("kic_")]
    kic_numbers = [int(d.name.split("_")[1]) for d in kic_dirs]
    
    return {"kic_numbers": kic_numbers}

@app.delete("/delete-kic/{kic_number}", response_model=StatusResponse, tags=["KIC Management"])
def delete_kic(
    kic_number: int = Path(..., description="KIC catalogue number to delete", example=12345)
):
    """
    Delete processed data for a specific KIC target.
    
    Args:
        kic_number: KIC catalogue number to delete
    
    Returns:
        StatusResponse: Status of the operation
        
    Raises:
        HTTPException: If no data is found for the specified KIC number
    """
    results_dir = FilePath(f"results/deviation_array/kic_{kic_number}")
    
    if not results_dir.exists():
        raise HTTPException(status_code=404, detail=f"No data found for KIC {kic_number}")
    
    import shutil
    shutil.rmtree(results_dir)
    
    return {"status": "success", "message": f"Data for KIC {kic_number} deleted successfully"}

@app.on_event("shutdown")
def cleanup():
    """Clean up temporary plot files when the application shuts down."""
    import shutil
    shutil.rmtree("temp_plots", ignore_errors=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
