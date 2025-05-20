# Kepler

Part - 1 : A FastAPI application for processing and analyzing Kepler light curve data.

## Features

- Process Kepler Input Catalog (KIC) targets
- Generate deviation plots for light curves
- Compare deviations across multiple KIC targets
- List available processed KIC targets
- Delete processed KIC data

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Start the API server

```bash
python main.py
```

The API will be available at http://localhost:8000

### API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Process a KIC Target

```
POST /process-kic?kic_number={kic_number}&timeout={timeout}&max_files={max_files}
```

- `kic_number`: KIC catalog number to process
- `timeout`: (Optional) Timeout in seconds for each download (default: 120)
- `max_files`: (Optional) Maximum number of files to process

### Get Deviation Plot

```
GET /plot-deviation/{kic_number}?save_plot={save_plot}
```

- `kic_number`: KIC catalog number
- `save_plot`: (Optional) Whether to save the plot to disk (default: false)

### Compare Deviations

```
GET /compare-deviations?kic_numbers={kic_number1}&kic_numbers={kic_number2}
```

- `kic_numbers`: List of KIC numbers to compare (can be specified multiple times)

### List Available KIC Targets

```
GET /available-kics
```

Returns a list of all processed KIC targets available in the system.

### Delete KIC Data

```
DELETE /delete-kic/{kic_number}
```

- `kic_number`: KIC catalog number to delete

## Example Usage

1. Process a KIC target:
```bash
curl -X POST "http://localhost:8000/process-kic?kic_number=12345&timeout=180"
```

2. Get a deviation plot:
```bash
curl -X GET "http://localhost:8000/plot-deviation/12345" --output deviation.png
```

3. Compare multiple targets:
```bash
curl -X GET "http://localhost:8000/compare-deviations?kic_numbers=12345&kic_numbers=67890" --output comparison.png
```
