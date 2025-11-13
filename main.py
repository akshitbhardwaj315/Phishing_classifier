# main.py
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import BytesIO, StringIO
import os
import urllib3
import sys
import asyncio
from typing import List

from api_utils import (
    URLRequest, PredictionResponse, MultiURLRequest, clean_features, 
    classify_prediction, MODEL_FEATURE_ORDER
)
from src.exception import CustomException
from src.logger import logging as lg
from src.pipeline.predict_pipeline import PredictionPipeline
from src.utils.url_extractor import extract_features_from_url

urllib3.disable_warnings()

app = FastAPI(
    title="Phishing URL Detection API",
    description="A professional, stateless API for ML prediction.",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

pipeline = None

@app.on_event("startup")
def load_pipeline():
    global pipeline
    try:
        lg.info("Application startup: Loading ML pipeline...")
        pipeline = PredictionPipeline()
        lg.info("ML pipeline loaded successfully.")
    except Exception as e:
        lg.critical(f"Application startup failed: Could not load ML pipeline. Error: {e}")
        raise e

def get_prediction_pipeline():
    if pipeline is None:
        lg.error("ML pipeline is not available. It may have failed to load at startup.")
        raise HTTPException(
            status_code=503,
            detail="Service is unavailable: Model not loaded."
        )
    return pipeline

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ML Pipeline API"}

@app.post("/predict", response_class=StreamingResponse)
async def predict_batch(
    file: UploadFile = File(...),
    pipeline: PredictionPipeline = Depends(get_prediction_pipeline)
):
    try:
        content = await file.read()
        input_df = pd.read_csv(BytesIO(content))
        predictions_df = pipeline.predict(input_df) 
        
        output_stream = StringIO()
        predictions_df.to_csv(output_stream, index=False)
        output_stream.seek(0)
        
        filename = f"predictions_{file.filename or 'batch'}.csv"
        
        return StreamingResponse(
            iter([output_stream.getvalue()]),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        lg.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def process_url_features(url: str) -> dict:
    """
    Helper function to extract and clean features for a single URL.
    Returns a dictionary of features.
    """
    try:
        features = extract_features_from_url(url)
        features = clean_features(features)
        features['url'] = url  # Add the URL itself for reference
        return features
    except Exception as e:
        lg.warning(f"Failed to extract features for URL '{url}': {e}")
        return None # Return None on failure

@app.post("/predict-url", response_model=PredictionResponse)
async def predict_url(
    req: URLRequest,
    pipeline: PredictionPipeline = Depends(get_prediction_pipeline)
):
    try:
        url = req.url
        lg.info(f"Analyzing URL: {url}")
        
        features = process_url_features(url)
        if not features:
             raise ValueError("Failed to extract features from URL.")
        
        try:
            features_df = pd.DataFrame([features])
            features_df_ordered = features_df[MODEL_FEATURE_ORDER]
            prediction_df = pipeline.predict(features_df_ordered)
            
            result_label = prediction_df['Result'].iloc[0]
            result_value = prediction_df['Result_Value'].iloc[0]

        except Exception as e:
            lg.error(f"Prediction pipeline failed: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
        
        prediction, status, result_val_classified = classify_prediction(result_value)
        lg.info(f"URL classified as {prediction} (value: {result_value})")
        
        return PredictionResponse(
            url=url,
            prediction=prediction,
            status=status,
            result_value=float(result_value),
            message=f"URL is classified as {prediction}",
            features={k: features[k] for k in MODEL_FEATURE_ORDER}
        )
            
    except Exception as e:
        lg.error(f"URL prediction failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# --- NEW: Endpoint for Single URL Report Download ---
@app.post("/download-url-report", response_class=StreamingResponse)
async def download_url_report(
    req: URLRequest,
    pipeline: PredictionPipeline = Depends(get_prediction_pipeline)
):
    try:
        url = req.url
        lg.info(f"Generating report for URL: {url}")
        
        features = process_url_features(url)
        if not features:
             raise ValueError("Failed to extract features from URL.")
        
        features_df = pd.DataFrame([features])
        features_df_ordered = features_df[MODEL_FEATURE_ORDER]
        prediction_df = pipeline.predict(features_df_ordered)
        
        # Add the URL to the final prediction DataFrame
        prediction_df['URL'] = url
        
        output_stream = StringIO()
        prediction_df.to_csv(output_stream, index=False)
        output_stream.seek(0)
        
        filename = f"report_{url.replace('https://','').replace('http://','').split('/')[0]}.csv"
        
        return StreamingResponse(
            iter([output_stream.getvalue()]),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        lg.error(f"URL report download failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# --- NEW: Endpoint for Batch URL Processing (Fast & Concurrent) ---
@app.post("/predict-multi-url", response_class=StreamingResponse)
async def predict_multi_url(
    req: MultiURLRequest,
    pipeline: PredictionPipeline = Depends(get_prediction_pipeline)
):
    try:
        lg.info(f"Processing {len(req.urls)} URLs in batch.")
        
        # This runs all 'process_url_features' calls concurrently in a thread pool.
        # This is the "make it fast" part.
        tasks = [asyncio.to_thread(process_url_features, url) for url in req.urls]
        results = await asyncio.gather(*tasks)
        
        # Filter out any URLs that failed extraction
        valid_features = [f for f in results if f is not None]
        
        if not valid_features:
            raise ValueError("No valid features could be extracted from any of the URLs.")
        
        lg.info(f"Successfully extracted features for {len(valid_features)} URLs.")
        
        features_df = pd.DataFrame(valid_features)
        features_df_ordered = features_df[MODEL_FEATURE_ORDER]
        prediction_df = pipeline.predict(features_df_ordered)
        
        # Add the original URL column back for the final report
        prediction_df['URL'] = features_df['url']
        
        output_stream = StringIO()
        prediction_df.to_csv(output_stream, index=False)
        output_stream.seek(0)
        
        filename = f"batch_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output_stream.getvalue()]),
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        lg.error(f"Multi-URL prediction failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# --- Error Handlers ---
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    lg.error(f"An unhandled 500 error occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    lg.error(f"A custom exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal error occurred: {exc}"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 FastAPI App Starting on http://127.0.0.1:{port}/")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
    