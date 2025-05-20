import lightkurve as lk
import numpy as np

def get_lightcurve_deviation_array(
    file_path,
    start_day=None,
    duration_days=None,
    time_bin_size=0.5,
):
    """
    Load a light curve FITS file and return time and flux deviation arrays.

    Args:
        file_path (str or Path): Path to the light curve FITS file.
        start_day (float or None): Start time in days. If None, uses earliest data time.
        duration_days (float or None): Duration in days to analyze. If None, uses all data from start_day.
        time_bin_size (float): Bin size in days for smoothing (default 0.5).

    Returns:
        tuple: (time_array, deviation_array)
            - time_array: numpy array of binned time values (days)
            - deviation_array: numpy array of flux deviations in percentage (%)
    """
    lc = lk.read(file_path)

    time_min = lc.time.value.min()
    time_max = lc.time.value.max()

    if start_day is None or start_day < time_min:
        start_day = time_min

    if duration_days is not None:
        end_day = start_day + duration_days
        if end_day > time_max:
            end_day = time_max
    else:
        end_day = time_max

    mask = (lc.time.value >= start_day) & (lc.time.value <= end_day)
    if not np.any(mask):
        raise ValueError(f"No data available between {start_day} and {end_day} days")

    lc = lc[mask]

    lc = lc.remove_nans()
    lc = lc.remove_outliers()
    lc = lc.flatten()
    lc = lc.normalize()
    lc = lc.bin(time_bin_size=time_bin_size)

    deviation = (lc.flux.value - 1.0) * 100  # percentage deviation

    return deviation
