import numpy as np
import matplotlib.pyplot as plt
import os

def plot_deviation(file_path, save_path=None, show_plot=True, title=None, figsize=(10, 6)):
    """
    Plot deviation data from a text file.
    
    Parameters:
    -----------
    file_path : str
        Path to the deviation data file
    save_path : str, optional
        Path to save the plot. If None, plot is not saved
    show_plot : bool, default=True
        Whether to display the plot
    title : str, optional
        Title for the plot. If None, uses filename as title
    figsize : tuple, default=(10, 6)
        Figure size (width, height) in inches
    
    Returns:
    --------
    fig, ax : tuple
        Matplotlib figure and axes objects
    """
    # Extract filename for default title
    if title is None:
        filename = os.path.basename(file_path)
        parent_dir = os.path.basename(os.path.dirname(file_path))
        title = f"Deviation for {parent_dir}"
    
    # Load data, handling NaN values
    try:
        data = np.loadtxt(file_path)
    except ValueError:
        # Handle case with NaN values
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.lower() == 'nan':
                    data.append(np.nan)
                elif line:
                    try:
                        data.append(float(line))
                    except ValueError:
                        data.append(np.nan)
        data = np.array(data)
    
    # Create figure and plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Get indices for x-axis (point number)
    x = np.arange(len(data))
    
    # Plot the data, skipping NaN values
    mask = ~np.isnan(data)
    ax.plot(x[mask], data[mask], 'b-', linewidth=1)
    
    # Mark NaN positions if any
    if np.any(~mask):
        nan_indices = np.where(~mask)[0]
        if len(nan_indices) < 100:  # Only mark if not too many
            ax.plot(nan_indices, np.zeros_like(nan_indices), 'rx', label='NaN values')
            ax.legend()
    
    # Set labels and title
    ax.set_xlabel('Point Number')
    ax.set_ylabel('Deviation')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    # Save plot if requested
    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
    
    # Show plot if requested
    if show_plot:
        plt.tight_layout()
        plt.show()
    else:
        plt.close()
    
    return fig, ax

def plot_multiple_deviations(file_paths, save_path=None, show_plot=True, figsize=(12, 8)):
    """
    Plot multiple deviation files on the same figure for comparison.
    
    Parameters:
    -----------
    file_paths : list
        List of paths to deviation data files
    save_path : str, optional
        Path to save the plot. If None, plot is not saved
    show_plot : bool, default=True
        Whether to display the plot
    figsize : tuple, default=(12, 8)
        Figure size (width, height) in inches
    
    Returns:
    --------
    fig, ax : tuple
        Matplotlib figure and axes objects
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    for file_path in file_paths:
        # Extract filename for legend
        filename = os.path.basename(os.path.dirname(file_path))
        
        # Load data
        try:
            data = np.loadtxt(file_path)
        except ValueError:
            # Handle case with NaN values
            data = []
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.lower() == 'nan':
                        data.append(np.nan)
                    elif line:
                        try:
                            data.append(float(line))
                        except ValueError:
                            data.append(np.nan)
            data = np.array(data)
        
        # Get indices for x-axis (point number)
        x = np.arange(len(data))
        
        # Plot the data, skipping NaN values
        mask = ~np.isnan(data)
        ax.plot(x[mask], data[mask], linewidth=1, label=filename)
    
    # Set labels and title
    ax.set_xlabel('Point Number')
    ax.set_ylabel('Deviation')
    ax.set_title('Comparison of Deviations')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Save plot if requested
    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
    
    # Show plot if requested
    if show_plot:
        plt.tight_layout()
        plt.show()
    else:
        plt.close()
    
    return fig, ax

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        save_path = sys.argv[2] if len(sys.argv) > 2 else None
        plot_deviation(file_path, save_path)
    else:
        print("Usage: python plot_deviation.py <file_path> [save_path]")