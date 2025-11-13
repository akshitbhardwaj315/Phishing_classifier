# api_utils.py

import numpy as np
from pydantic import BaseModel, validator, Field
from typing import Dict, Any, List
from urllib.parse import urlparse
from src.logger import logging as lg

# --- NEW: Model Feature Order Constant ---
# This is the exact order of features the model was trained on.
# We use this to fix the "feature names" error.
MODEL_FEATURE_ORDER = [
    'having_IP_Address', 'URL_Length', 'Shortining_Service', 'having_At_Symbol',
    'double_slash_redirecting', 'Prefix_Suffix', 'having_Sub_Domain', 'SSLfinal_State',
    'Domain_registeration_length', 'Favicon', 'port', 'HTTPS_token', 'Request_URL',
    'URL_of_Anchor', 'Links_in_tags', 'SFH', 'Submitting_to_email', 'Abnormal_URL',
    'Redirect', 'on_mouseover', 'RightClick', 'popUpWidnow', 'Iframe', 'age_of_domain',
    'DNSRecord', 'web_traffic', 'Page_Rank', 'Google_Index', 'Links_pointing_to_page',
    'Statistical_report'
]

# --- Pydantic Models ---

class URLRequest(BaseModel):
    url: str

    @validator('url')
    def validate_url(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty")
        if '//' not in v and '.' in v:
            v = 'http://' + v
        return v

# --- NEW: Pydantic Model for Batch URL Feature ---
class MultiURLRequest(BaseModel):
    urls: List[str]

    @validator('urls')
    def validate_urls(cls, v):
        if not v:
            raise ValueError("URL list cannot be empty")
        validated_urls = []
        for url in v:
            url = url.strip()
            if not url:
                continue
            if '//' not in url and '.' in url:
                url = 'http://' + url
            validated_urls.append(url)
        if not validated_urls:
            raise ValueError("No valid URLs provided")
        return validated_urls

class PredictionResponse(BaseModel):
    success: bool = True
    url: str
    prediction: str
    status: str
    result_value: float
    message: str
    features: Dict[str, Any] = Field(..., example={"having_IP_Address": 0, "URL_Length": 1})


# --- Utility Functions ---

def clean_features(features: dict) -> dict:
    for key in features:
        if isinstance(features[key], str):
            try:
                features[key] = float(features[key])
            except (ValueError, TypeError):
                lg.warning(f"Non-numeric value for '{key}', setting to 0")
                features[key] = 0
        elif isinstance(features[key], (int, float)):
            if np.isnan(features[key]) or np.isinf(features[key]):
                features[key] = 0
    return features

def classify_prediction(result_value) -> tuple:
    try:
        result_value = int(result_value)
    except (ValueError, TypeError):
        lg.warning(f"Cannot convert result: {result_value}, defaulting to 0")
        result_value = 0
    
    if result_value == 1:
        return "SAFE", "safe", 1
    else:
        return "PHISHING", "danger", 0