"""
Interactive URL Feature Extractor for Phishing Detection
Usage: python url_feature_extractor.py
"""

import csv
import re
import socket
import ssl
from urllib.parse import urlparse
from datetime import datetime
import tldextract

try:
    import requests
except:
    requests = None

try:
    import whois
except:
    whois = None

try:
    import dns.resolver
except:
    dns = None

SHORTENERS = {"bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co", "is.gd", "buff.ly", "adf.ly"}

COLUMNS = [
    "having_IP_Address", "URL_Length", "Shortining_Service", "having_At_Symbol",
    "double_slash_redirecting", "Prefix_Suffix", "having_Sub_Domain", "SSLfinal_State",
    "Domain_registeration_length", "Favicon", "port", "HTTPS_token", "Request_URL",
    "URL_of_Anchor", "Links_in_tags", "SFH", "Submitting_to_email", "Abnormal_URL",
    "Redirect", "on_mouseover", "RightClick", "popUpWidnow", "Iframe", "age_of_domain",
    "DNSRecord", "web_traffic", "Page_Rank", "Google_Index", "Links_pointing_to_page",
    "Statistical_report", "Result"
]

def fetch_content(url):
    """Fetch URL content"""
    if not requests:
        return None, None
    try:
        r = requests.get(url, timeout=10, allow_redirects=True, 
                        headers={"User-Agent": "Mozilla/5.0"}, verify=False)
        return r.status_code, r.text[:100000]
    except:
        return None, None

def get_domain_age(domain):
    """Get domain age in days"""
    if not whois or not domain:
        return None
    try:
        w = whois.whois(domain)
        cd = w.creation_date
        if isinstance(cd, list):
            cd = cd[0]
        if cd and not isinstance(cd, str):
            return (datetime.now() - cd).days
    except:
        pass
    return None

def check_ssl(url, host):
    """Check SSL certificate validity"""
    if not url.startswith('https'):
        return -1
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                if cert.get('notAfter'):
                    exp = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                    return 1 if (exp - datetime.utcnow()).days > 30 else 0
        return 1
    except:
        return -1

def check_dns(domain):
    """Check DNS record"""
    if not dns or not domain:
        return 1
    try:
        dns.resolver.resolve(domain, 'A')
        return 1
    except:
        return -1

def extract_features(url):
    """Extract all features from URL"""
    print(f"\n[*] Analyzing: {url}\n")
    
    parsed = urlparse(url)
    host = parsed.netloc.split(':')[0] if parsed.netloc else ''
    ext = tldextract.extract(host)
    domain = ext.registered_domain
    subdomain = ext.subdomain
    
    status, html = fetch_content(url)
    html = html or ''
    
    features = {}
    
    # URL-based features (no HTML needed)
    features["having_IP_Address"] = -1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else 1
    
    length = len(url)
    features["URL_Length"] = 1 if length < 54 else (0 if length <= 75 else -1)
    
    features["Shortining_Service"] = -1 if any(s in host.lower() for s in SHORTENERS) else 1
    features["having_At_Symbol"] = -1 if '@' in url else 1
    features["double_slash_redirecting"] = -1 if '//' in parsed.path else 1
    features["Prefix_Suffix"] = -1 if '-' in host else 1
    
    sub_count = len(subdomain.split('.')) if subdomain else 0
    features["having_Sub_Domain"] = 1 if sub_count <= 1 else (0 if sub_count == 2 else -1)
    
    features["SSLfinal_State"] = check_ssl(url, host)
    
    # Domain age
    age_days = get_domain_age(domain)
    age_val = 1 if age_days is None else (1 if age_days >= 365 else (0 if age_days >= 180 else -1))
    features["Domain_registeration_length"] = age_val
    features["age_of_domain"] = age_val
    
    features["port"] = -1 if (':' in parsed.netloc and parsed.netloc.split(':')[-1] not in ('80', '443')) else 1
    features["HTTPS_token"] = -1 if 'https' in host.lower() else 1
    
    # HTML-based features
    if html:
        # Favicon
        fav = re.search(r'<link[^>]+rel=["\']?(?:icon|shortcut icon)["\']?[^>]+href=[\'"]([^\'"]+)', html, re.I)
        if fav:
            fav_domain = tldextract.extract(urlparse(fav.group(1)).netloc).registered_domain
            features["Favicon"] = -1 if fav_domain and fav_domain != domain else 1
        else:
            features["Favicon"] = 1
        
        # External resources
        links = re.findall(r'(?:src|href)=["\']([^"\']+)', html, re.I)
        ext_count = sum(1 for l in links if urlparse(l).netloc and 
                       tldextract.extract(urlparse(l).netloc).registered_domain != domain)
        ext_pct = (ext_count / len(links) * 100) if links else 0
        features["Request_URL"] = 1 if ext_pct < 22 else (0 if ext_pct <= 61 else -1)
        
        # Anchors
        anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)', html, re.I)
        susp_anch = sum(1 for a in anchors if a.startswith(('#', 'javascript:', 'mailto:')) or
                       (urlparse(a).netloc and tldextract.extract(urlparse(a).netloc).registered_domain != domain))
        anch_pct = (susp_anch / len(anchors) * 100) if anchors else 0
        features["URL_of_Anchor"] = 1 if anch_pct < 31 else (0 if anch_pct <= 67 else -1)
        
        # Meta/Script/Link tags
        tags = re.findall(r'<(?:meta|script|link)[^>]+(?:src|href)=["\']([^"\']+)', html, re.I)
        ext_tags = sum(1 for t in tags if urlparse(t).netloc and 
                      tldextract.extract(urlparse(t).netloc).registered_domain != domain)
        tag_pct = (ext_tags / len(tags) * 100) if tags else 0
        features["Links_in_tags"] = 1 if tag_pct < 17 else (0 if tag_pct <= 81 else -1)
        
        # Form handlers
        forms = re.findall(r'<form[^>]+action=["\']([^"\']*)', html, re.I)
        features["SFH"] = -1 if any(not f or 'about:blank' in f.lower() for f in forms) else 1
        
        features["Submitting_to_email"] = -1 if re.search(r'mailto:', html, re.I) else 1
        features["on_mouseover"] = -1 if re.search(r'onmouseover\s*=', html, re.I) else 1
        features["RightClick"] = -1 if re.search(r'event\.button\s*==\s*2', html, re.I) else 1
        features["popUpWidnow"] = -1 if re.search(r'window\.open\s*\(', html, re.I) else 1
        features["Iframe"] = -1 if '<iframe' in html.lower() else 1
    else:
        # No HTML - set defaults
        for feat in ["Favicon", "Request_URL", "URL_of_Anchor", "Links_in_tags", "SFH", 
                    "Submitting_to_email", "on_mouseover", "RightClick", "popUpWidnow", "Iframe"]:
            features[feat] = 1
    
    features["Abnormal_URL"] = -1 if not domain or not parsed.scheme else 1
    features["Redirect"] = -1 if status and 300 <= status < 400 else 1
    features["DNSRecord"] = check_dns(domain)
    
    # Network features (unknown)
    for feat in ["web_traffic", "Page_Rank", "Google_Index", "Links_pointing_to_page", "Statistical_report"]:
        features[feat] = 1
    
    features["Result"] = 1
    
    return features

def save_csv(features, filename="url_features.csv"):
    """Save features to CSV"""
    row = [features.get(c, 1) for c in COLUMNS]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerow(row)
    
    print(f"\n{'='*60}")
    print(f"Features saved to: {filename}")
    print(f"{'='*60}")
    
    susp = sum(1 for v in row if v == -1)
    neut = sum(1 for v in row if v == 0)
    legit = sum(1 for v in row if v == 1)
    
    print(f"\n(-1=Suspicious, 0=Neutral, 1=Legitimate)")
    for c, v in zip(COLUMNS, row):
        icon = "🔴" if v == -1 else ("🟡" if v == 0 else "🟢")
        print(f"{icon} {c:30s}: {v:2d}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {susp} suspicious | {neut} neutral | {legit} legitimate")
    print(f"{'='*60}\n")

def main():
    try:
        import urllib3
        urllib3.disable_warnings()
    except:
        pass
    
    print("\n" + "="*60)
    print("URL FEATURE EXTRACTOR FOR PHISHING DETECTION")
    print("="*60)
    
    url = input("\nEnter URL: ").strip()
    if not url:
        print("Error: No URL provided")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    try:
        features = extract_features(url)
        save_csv(features)
        print("✅ CSV ready! Feed 'url_features.csv' to your model.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()