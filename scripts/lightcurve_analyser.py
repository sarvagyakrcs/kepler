import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def get_data_time_range(file_path):
    """Get the time range of the data in the FITS file."""
    lc = lk.read(file_path)
    return lc.time.value.min(), lc.time.value.max()

def analyze_lightcurve(file_path, start_day=0, duration_days=None, time_bin_size=0.5, return_array=False):
    """Analyze a single light curve file and return key statistics.
    
    Args:
        file_path: Path to the FITS file
        start_day: Starting day of observation (default: 0)
        duration_days: Number of days to observe (default: None, meaning all available data)
        time_bin_size: Size of time bins in days (default: 0.5)
        return_array: If True, return the deviation array instead of plotting (default: False)
    """
    # Read the light curve
    lc = lk.read(file_path)
    
    # Get the time range of the data
    time_min = lc.time.value.min()
    time_max = lc.time.value.max()
    
    # Adjust start_day if it's before the data starts
    if start_day < time_min:
        print(f"Warning: Start day {start_day} is before data begins ({time_min:.2f}). Using {time_min:.2f} as start.")
        start_day = time_min
    
    # Calculate end day
    if duration_days is not None:
        end_day = start_day + duration_days
        if end_day > time_max:
            print(f"Warning: End day {end_day:.2f} is after data ends ({time_max:.2f}). Using {time_max:.2f} as end.")
            end_day = time_max
    else:
        end_day = time_max
    
    # Select the time range
    mask = (lc.time.value >= start_day) & (lc.time.value <= end_day)
    if not np.any(mask):
        raise ValueError(f"No data available in the specified time range ({start_day} to {end_day} days)")
    
    lc = lc[mask]
    
    # Remove systematic trends and normalize
    lc = lc.remove_nans()  # Remove any NaN values
    lc = lc.remove_outliers()  # Remove outliers
    lc = lc.flatten()  # Remove systematic trends
    lc = lc.normalize()  # Normalize to relative brightness
    
    # Apply smoothing to reduce noise
    lc = lc.bin(time_bin_size=time_bin_size)  # Bin the data to reduce noise
    
    # Calculate deviation from 1.0 and convert to percentage
    deviation = (lc.flux.value - 1.0) * 100  # Convert to percentage
    
    # Basic statistics
    actual_duration = (lc.time[-1] - lc.time[0]).value
    stats = {
        'duration': actual_duration,
        'mean_flux': np.mean(lc.flux),
        'std_flux': np.std(lc.flux),
        'min_flux': np.min(lc.flux),
        'max_flux': np.max(lc.flux),
        'n_points': len(lc.time)
    }
    
    if return_array:
        return {
            'time': lc.time.value,
            'deviation': deviation,
            'stats': stats
        }
    else:
        return lc, stats

def plot_lightcurve(lc, title):
    """Plot the normalized and smoothed light curve with basic styling."""
    plt.figure(figsize=(12, 6))
    lc.plot()
    plt.title(title)
    plt.ylabel('Relative Brightness')
    plt.ylim(0.997, 1.003)  # Tighter y-axis limits to better show variations
    plt.grid(True)
    plt.show()

def list_available_files():
    """List all available FITS files in the data directory."""
    data_dir = Path("data")
    fits_files = list(data_dir.glob("*.fits"))
    print("\nAvailable FITS files:")
    for i, file in enumerate(fits_files, 1):
        print(f"{i}. {file.name}")
    return fits_files

def main():
    # List available files
    fits_files = list_available_files()
    
    # Get user input for file selection
    while True:
        try:
            file_choice = input("\nEnter file number or path to FITS file (default: 1): ").strip()
            if not file_choice:
                file_choice = "1"
            
            if file_choice.isdigit() and 1 <= int(file_choice) <= len(fits_files):
                file_path = fits_files[int(file_choice) - 1]
            else:
                # Try to use the input as a direct path
                file_path = Path(file_choice)
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                if not file_path.suffix.lower() == '.fits':
                    raise ValueError(f"Not a FITS file: {file_path}")
            
            break
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {str(e)}")
            print("Please try again.")
    
    # Get and display the time range of the data
    time_min, time_max = get_data_time_range(file_path)
    print(f"\nData time range: {time_min:.2f} to {time_max:.2f} days")
    print(f"Note: Entering 0 as start day will use {time_min:.2f} (the actual start of the data)")
    
    # Get user input for time range
    try:
        start_day = float(input(f"Enter start day (default: {time_min:.2f}): ") or str(time_min))
        duration_input = input("Enter number of days to observe (default: all available data): ")
        duration_days = float(duration_input) if duration_input else None
    except ValueError:
        print("Invalid input. Using default values.")
        start_day = time_min
        duration_days = None
    
    # Get user input for time bin size
    try:
        time_bin_size = float(input("Enter time bin size in days (default: 0.5): ") or "0.5")
    except ValueError:
        print("Invalid input. Using default value of 0.5 days.")
        time_bin_size = 0.5
    
    # Get user input for output type
    output_type = input("Choose output type (1: Plot, 2: Array) [default: 1]: ").strip() or "1"
    return_array = output_type == "2"
    
    print(f"\nAnalyzing file: {file_path.name}")
    print(f"Time range: {start_day} to {start_day + duration_days if duration_days else time_max:.2f} days")
    print(f"Time bin size: {time_bin_size} days")
    print(f"Output type: {'Array' if return_array else 'Plot'}\n")
    
    try:
        if return_array:
            result = analyze_lightcurve(file_path, start_day, duration_days, time_bin_size, return_array=True)
            
            # Print statistics
            stats = result['stats']
            print(f"Duration: {stats['duration']:.2f} days")
            print(f"Number of data points: {stats['n_points']}")
            print(f"Mean deviation: {np.mean(result['deviation']):.4f}%")
            print(f"Deviation std: {np.std(result['deviation']):.4f}%")
            print(f"Deviation range: [{np.min(result['deviation']):.4f}%, {np.max(result['deviation']):.4f}%]")
            
            # Print the array data
            print("\nTime (days) | Deviation (%)")
            print("-" * 35)
            for t, d in zip(result['time'], result['deviation']):
                print(f"{t:10.2f} | {d:+.4f}%")
        else:
            lc, stats = analyze_lightcurve(file_path, start_day, duration_days, time_bin_size)
            
            # Print statistics
            print(f"Duration: {stats['duration']:.2f} days")
            print(f"Number of data points: {stats['n_points']}")
            print(f"Mean relative brightness: {stats['mean_flux']:.6f}")
            print(f"Brightness variation (std): {stats['std_flux']:.6f}")
            print(f"Brightness range: [{stats['min_flux']:.6f}, {stats['max_flux']:.6f}]")
            
            # Plot the light curve
            plot_lightcurve(lc, f"Relative Brightness (Smoothed): {file_path.name}\nDays {start_day:.1f} to {start_day + stats['duration']:.1f}")
        
    except Exception as e:
        print(f"Error analyzing {file_path.name}: {str(e)}")

if __name__ == "__main__":
    main()
