from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os
from pathlib import Path
import tempfile
import uuid
from typing import Optional, List

from scripts.process_kic_target import process_kic_target
from utils.plot_deviation import plot_deviation, plot_multiple_deviations

app = FastAPI(title="Kepler Data Analysis API", description="API for processing Kepler light curves")

# Create necessary directories
Path("results/deviation_array").mkdir(parents=True, exist_ok=True)
Path("temp_plots").mkdir(exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to Kepler Data Analysis API"}

@app.post("/process-kic")
def process_kic(
    kic_number: int = Query(..., description="KIC catalogue number to process"),
    timeout: int = Query(120, description="Timeout in seconds for each download"),
    max_files: Optional[int] = Query(None, description="Maximum number of files to process")
):
    try:
        process_kic_target(kic_number, timeout, max_files)
        results_dir = Path(f"results/deviation_array/kic_{kic_number}")
        
        if not (results_dir / "deviation.txt").exists():
            return {"status": "error", "message": "No files were successfully processed"}
            
        return {
            "status": "success", 
            "message": f"Successfully processed KIC {kic_number}",
            "results_path": str(results_dir)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plot-deviation/{kic_number}")
def get_deviation_plot(
    kic_number: int,
    save_plot: bool = Query(False, description="Whether to save the plot to disk")
):
    file_path = Path(f"results/deviation_array/kic_{kic_number}/deviation.txt")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"No deviation data found for KIC {kic_number}")
    
    # Generate a unique filename for the plot
    plot_filename = f"kic_{kic_number}_{uuid.uuid4().hex[:8]}.png"
    plot_path = Path("temp_plots") / plot_filename
    
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

@app.get("/compare-deviations")
def compare_deviations(
    kic_numbers: List[int] = Query(..., description="List of KIC numbers to compare")
):
    file_paths = []
    
    for kic_number in kic_numbers:
        file_path = Path(f"results/deviation_array/kic_{kic_number}/deviation.txt")
        if not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"No deviation data found for KIC {kic_number}"
            )
        file_paths.append(str(file_path))
    
    # Generate a unique filename for the plot
    plot_filename = f"comparison_{uuid.uuid4().hex[:8]}.png"
    plot_path = Path("temp_plots") / plot_filename
    
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

@app.get("/available-kics")
def get_available_kics():
    results_dir = Path("results/deviation_array")
    
    if not results_dir.exists():
        return {"kic_numbers": []}
    
    kic_dirs = [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("kic_")]
    kic_numbers = [int(d.name.split("_")[1]) for d in kic_dirs]
    
    return {"kic_numbers": kic_numbers}

@app.delete("/delete-kic/{kic_number}")
def delete_kic(kic_number: int):
    results_dir = Path(f"results/deviation_array/kic_{kic_number}")
    
    if not results_dir.exists():
        raise HTTPException(status_code=404, detail=f"No data found for KIC {kic_number}")
    
    import shutil
    shutil.rmtree(results_dir)
    
    return {"status": "success", "message": f"Data for KIC {kic_number} deleted successfully"}

@app.on_event("shutdown")
def cleanup():
    # Clean up temporary plot files
    import shutil
    shutil.rmtree("temp_plots", ignore_errors=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
