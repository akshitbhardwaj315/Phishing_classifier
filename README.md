# Phishing URL Detection System

A machine learning web application for detecting phishing URLs through comprehensive feature analysis. The system examines 30 distinct URL characteristics to classify links as legitimate or potentially malicious.

## Overview

This project provides both single-URL and batch analysis capabilities with a focus on speed and accuracy. Built on FastAPI, the application offers real-time classification with detailed feature reporting.

## Key Capabilities

**Single URL Analysis**
- Real-time classification results displayed in the browser
- Detailed view of all 30 extracted features
- Exportable CSV reports for documentation

**Batch Processing**
- Multi-URL analysis from pasted lists
- Concurrent processing for improved throughput
- Progress estimation during processing
- Single consolidated CSV output

**CSV File Upload**
- Bulk processing of URL lists from CSV files
- Drag-and-drop file handling
- Results appended to original data structure

**Detection Features**
- 30-feature extraction pipeline
- Pre-trained ML model loaded at startup
- SSL/TLS certificate validation
- Domain registration and age verification
- Content-based threat indicators

## Technology Stack

**Backend Components**
- Python 3.8+
- FastAPI (async web framework)
- Uvicorn (ASGI server)
- Pandas & NumPy (data processing)
- Scikit-learn (ML inference)

**Frontend**
- HTML5/CSS3 with responsive design
- Vanilla JavaScript with Fetch API

**ML Architecture**
- Stateless prediction pipeline
- Dependency injection for model management
- Custom feature engineering
- Structured logging and error handling

## Architecture

```
┌──────────────────┐
│   Web Interface  │
└─────────┬────────┘
          │
          ▼
┌──────────────────┐
│   FastAPI Layer  │
└─────────┬────────┘
          │
          ├─────► Feature Extraction (30 features)
          │
          ├─────► ML Pipeline (Inference)
          │
          └─────► CSV Generation
```

## Installation

**Requirements**
- Python 3.8 or higher
- pip package manager
- Git

**Setup Steps**

1. Clone the repository:
```bash
git clone https://github.com/yourusername/phishing-detection.git
cd phishing-detection
```

2. Create a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Verify installation:
```bash
python -c "import fastapi; import uvicorn; import pandas; print('Dependencies loaded successfully')"
```

## Running the Application

**Development Mode**
```bash
python main.py
```
Application starts at `http://127.0.0.1:8080/` with auto-reload enabled.

**Production Deployment**
```bash
export PORT=8080
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app
```

## Using the Interface

**Single URL Check**
1. Navigate to the home page
2. Select the "Check URL" tab
3. Enter the URL to analyze
4. Choose "Analyze (Quick Look)" for in-browser results or "Analyze & Download Report" for CSV export

**Batch Analysis**
1. Select the "Batch URLs" tab
2. Paste URLs (one per line)
3. Click "Analyze & Download CSV"
4. Processing time estimate shown based on URL count

**CSV Upload**
1. Select the "Upload CSV" tab
2. Upload your file via drag-and-drop or file browser
3. Click "Analyze File" to download results

## API Documentation

**Health Check**
```
GET /health
```
Returns service status information.

**Single URL Analysis (JSON)**
```
POST /predict-url
Content-Type: application/json

{
  "url": "https://example.com"
}
```
Returns classification result with all extracted features.

**Single URL Report (CSV)**
```
POST /download-url-report
Content-Type: application/json

{
  "url": "https://example.com"
}
```
Downloads CSV report for the specified URL.

**Batch URL Analysis**
```
POST /predict-multi-url
Content-Type: application/json

{
  "urls": [
    "https://example.com",
    "http://suspicious-site.net"
  ]
}
```
Returns CSV file with results for all URLs.

**CSV File Analysis**
```
POST /predict
Content-Type: multipart/form-data

file: <csv_file>
```
Processes uploaded CSV and returns enhanced file with predictions.

## Feature Extraction

The system analyzes 30 distinct characteristics organized into four categories:

**URL Structure (Features 1-11)**
- IP address usage detection
- URL length analysis
- URL shortening service identification
- Special character presence (@ symbol)
- Redirect patterns
- Subdomain analysis
- SSL/TLS validation
- Domain registration duration
- Favicon source verification
- Non-standard port detection

**Content Analysis (Features 12-19)**
- HTTPS token in domain
- External resource loading patterns
- Anchor tag analysis
- Meta/script/link tag inspection
- Form handler verification
- Email submission detection
- WHOIS correlation
- Redirect chain analysis

**JavaScript Behavior (Features 20-22)**
- Status bar manipulation detection
- Right-click functionality checks
- Popup window patterns

**Domain Reputation (Features 23-30)**
- Iframe analysis
- Domain age calculation
- DNS record verification
- Traffic ranking
- PageRank metrics
- Search engine indexing status
- Backlink analysis
- Phishing database cross-reference

## Project Structure

```
phishing-detection/
├── main.py                     # FastAPI application entry point
├── api_utils.py                # Pydantic models and helpers
├── setup.py                    # Package configuration
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
├── templates/
│   └── index.html              # Web interface
├── src/
│   ├── components/             # ML components
│   │   ├── data_ingestion.py
│   │   ├── data_transformation.py
│   │   └── model_trainer.py
│   ├── pipeline/               # Inference and training pipelines
│   │   ├── train_pipeline.py
│   │   └── predict_pipeline.py
│   ├── utils/                  # Utility modules
│   │   ├── url_extractor.py    # Feature extraction
│   │   └── main_utils.py       # File operations
│   ├── exception.py            # Error handling
│   └── logger.py               # Logging configuration
├── model.pkl                   # Trained model (generated)
└── logs/                       # Application logs
```

## Model Training

Training occurs offline and is not exposed through the API for security reasons.

**Training a New Model**

1. Prepare your labeled dataset (e.g., `phising.csv`)
2. Update the data path in `src/components/data_ingestion.py` if needed
3. Run the training pipeline:

```bash
python -c "from src.pipeline.train_pipeline import TrainingPipeline; pipeline = TrainingPipeline(); pipeline.run_pipeline()"
```

This generates a new `model.pkl` file. Restart the FastAPI application to load the updated model.

## Troubleshooting

**Import Errors**
```bash
pip install -r requirements.txt --force-reinstall
```

**Missing Model File**
Train the model first:
```bash
python -c "from src.pipeline.train_pipeline import TrainingPipeline; TrainingPipeline().run_pipeline()"
```

**Port Conflicts**
```bash
export PORT=8081
python main.py
```

**Feature Extraction Failures**
- Verify internet connectivity (required for WHOIS, DNS queries)
- Ensure target URLs are accessible
- Check application logs in the `logs/` directory

## Example Usage

**Python Script**
```python
import requests

BASE_URL = "http://127.0.0.1:8080"

# Single URL analysis
response = requests.post(
    f"{BASE_URL}/predict-url",
    json={'url': 'https://example.com'}
)
result = response.json()
print(f"Classification: {result['prediction']}")
print(f"Status: {result['status']}")

# Download detailed report
response = requests.post(
    f"{BASE_URL}/download-url-report",
    json={'url': 'https://example.com'}
)
with open('report.csv', 'wb') as f:
    f.write(response.content)

# Batch analysis
urls = ["https://google.com", "http://suspicious-site.com"]
response = requests.post(
    f"{BASE_URL}/predict-multi-url",
    json={'urls': urls}
)
with open('batch_results.csv', 'wb') as f:
    f.write(response.content)
```

**cURL Commands**
```bash
# Quick analysis
curl -X POST "http://127.0.0.1:8080/predict-url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Batch processing
curl -X POST "http://127.0.0.1:8080/predict-multi-url" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://google.com", "https://example.com"]}' \
  -o results.csv
```

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes with clear messages
4. Push to your fork (`git push origin feature/improvement`)
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Contact

**Author:** Akshit Bhardwaj  
**Email:** akshitbhardwaj315@gmail.com

## Acknowledgments

This project builds on established research in phishing detection and URL analysis. Feature extraction techniques are derived from academic security research and industry best practices.

## Version History

**v2.0.0** - FastAPI Migration
- Migrated from Flask to FastAPI for improved performance
- Implemented stateless API architecture
- Added concurrent batch processing
- Removed training endpoint (moved to offline process)
- Implemented model loading via dependency injection
- Separated JSON and CSV response endpoints

**v1.0.0** - Initial Release
- Single URL analysis
- Basic batch processing
- 30-feature extraction pipeline
- CSV report generation
