import os
import shutil
import argparse
import numpy as np
from pathlib import Path
import lightkurve as lk
from controllers.light_curve.dip_array import get_lightcurve_deviation_array
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError

class DownloadTimeoutError(Exception):
    pass

def download_with_timeout(lc_file, timeout):
    """Download a light curve file with timeout handling using threads."""
    result = {"success": False, "lc": None, "error": None}
    
    def _download():
        try:
            result["lc"] = lc_file.download()
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
    
    # Start download in a separate thread
    thread = threading.Thread(target=_download)
    thread.daemon = True
    thread.start()
    
    # Wait for the thread to complete or timeout
    thread.join(timeout)
    
    if thread.is_alive():
        # If thread is still alive after timeout, it's still downloading
        return False, None, "Download timed out"
    
    if result["success"]:
        return True, result["lc"], None
    else:
        return False, None, result["error"]

def process_kic_target(kic_number, timeout=120, max_files=None):
    """
    Process a KIC target by:
    1. Downloading all available FITS files
    2. Processing them to get deviation arrays
    3. Saving results to organized directories
    4. Cleaning up temporary files
    
    Args:
        kic_number (int): KIC catalogue number
        timeout (int): Timeout in seconds for each download
        max_files (int, optional): Maximum number of files to process
    """
    print(f"Processing KIC {kic_number}...")
    
    # Create necessary directories
    data_dir = Path(f"data/kic_{kic_number}")
    results_dir = Path(f"results/deviation_array/kic_{kic_number}")
    
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Download light curve data
    print(f"Searching for light curves for KIC {kic_number}...")
    search_result = lk.search_lightcurve(f"KIC {kic_number}", mission="Kepler")
    
    if len(search_result) == 0:
        print(f"No light curves found for KIC {kic_number}")
        return
    
    # Limit the number of files if specified
    if max_files and max_files < len(search_result):
        print(f"Limiting to {max_files} files out of {len(search_result)} available")
        search_result = search_result[:max_files]
    else:
        print(f"Found {len(search_result)} light curve files")
    
    # Download all FITS files
    all_deviations = []
    metadata = {
        "kic_number": kic_number,
        "total_files": len(search_result),
        "processed_files": 0,
        "skipped_files": 0,
        "time_bin_size": 0.5
    }
    
    for i, lc_file in enumerate(search_result):
        try:
            print(f"Downloading file {i+1}/{len(search_result)}")
            
            # Download the file with timeout using threads
            start_time = time.time()
            success, lc, error = download_with_timeout(lc_file, timeout)
            
            if not success:
                print(f"Download error: {error}, skipping file")
                metadata["skipped_files"] += 1
                continue
                
            download_time = time.time() - start_time
            print(f"Download completed in {download_time:.1f} seconds")
            
            # The actual file path is stored in lc.filename
            fits_path = Path(lc.filename)
            
            if not fits_path.exists():
                print(f"Downloaded file not found at {fits_path}, skipping")
                metadata["skipped_files"] += 1
                continue
            
            # Process the file
            print("Processing file...")
            start_time = time.time()
            deviation = get_lightcurve_deviation_array(fits_path)
            process_time = time.time() - start_time
            print(f"Processing completed in {process_time:.1f} seconds")
            
            all_deviations.extend(deviation)
            
            # Don't need to delete the file as we'll clean up the whole directory later
            
            metadata["processed_files"] += 1
            print(f"Successfully processed file {i+1}/{len(search_result)}")
        except Exception as e:
            print(f"Error processing file {i+1}: {e}")
            metadata["skipped_files"] += 1
    
    # Save results
    if metadata["processed_files"] > 0:
        # Save deviation array
        print(f"Saving {len(all_deviations)} deviation points to file...")
        np.savetxt(results_dir / "deviation.txt", np.array(all_deviations))
        
        # Save metadata
        with open(results_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Successfully processed {metadata['processed_files']} files for KIC {kic_number}")
        print(f"Results saved to {results_dir}")
    else:
        print(f"No files were successfully processed for KIC {kic_number}")
        # Remove empty directories
        shutil.rmtree(results_dir, ignore_errors=True)
    
    # Clean up data directory
    shutil.rmtree(data_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Process KIC targets and generate deviation arrays")
    parser.add_argument("kic_number", type=int, help="KIC catalogue number to process")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds for each download (default: 120)")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process")
    args = parser.parse_args()
    
    process_kic_target(args.kic_number, args.timeout, args.max_files)

if __name__ == "__main__":
    main()
