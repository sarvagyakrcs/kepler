from controllers.light_curve.dip_array import get_lightcurve_deviation_array

array = get_lightcurve_deviation_array(
    file_path="/Users/sarvagyakumar/coding/kepler/data/Kepler 001160789 lightcurve.fits",
    start_day=0,
    duration_days=3,
)

print(array)