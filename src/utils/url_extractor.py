import csv
import re
import socket
import ssl
from urllib.parse import urlparse
from datetime import datetime
import tldextract


try:
    import requests
    requests.packages.urllib3.disable_warnings()
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
    """Fetch URL content with proper timeout and error handling"""
    if not requests:
        return None, None
    try:
        r = requests.get(
            url, 
            timeout=10, 
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            verify=False
        )
        return r.status_code, r.text[:100000]
    except Exception as e:
        print(f"Warning: Could not fetch content - {str(e)}")
        return None, None

def get_domain_age(domain):
    """Get domain age in days, returns -1 if unknown (suspicious)"""
    if not whois or not domain:
        return -1  # Changed: Unknown age = suspicious
    try:
        w = whois.whois(domain)
        cd = w.creation_date
        if isinstance(cd, list):
            cd = cd[0]
        if cd and not isinstance(cd, str):
            return (datetime.now() - cd).days
    except Exception as e:
        print(f"Warning: WHOIS lookup failed - {str(e)}")
    return -1  # Changed: Default to suspicious

def check_ssl(url, host):
    """Check SSL certificate validity"""
    if not url.startswith('https'):
        return -1  # No HTTPS = suspicious
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                if cert.get('notAfter'):
                    exp = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                    days_valid = (exp - datetime.utcnow()).days
                    return 1 if days_valid > 365 else (0 if days_valid > 30 else -1)
        return 0
    except Exception as e:
        print(f"Warning: SSL check failed - {str(e)}")
        return -1  # SSL failure = suspicious

def check_dns(domain):
    """Check if domain has valid DNS record"""
    if not dns or not domain:
        return -1  # Changed: No DNS tool or domain = suspicious
    try:
        dns.resolver.resolve(domain, 'A')
        return 1
    except:
        return -1  # No DNS record = suspicious

def validate_url(url):
    """Validate URL format and structure"""
    if not url or len(url) < 4:
        return False, "URL is too short"
    
    parsed = urlparse(url)
    
    if not parsed.scheme:
        return False, "Missing protocol (http:// or https://)"
    
    if parsed.scheme not in ['http', 'https']:
        return False, f"Invalid protocol: {parsed.scheme}"
    
    if not parsed.netloc:
        return False, "Invalid URL format. Missing domain"
    
    host = parsed.netloc.split(':')[0]
    
    if not host or host.count('.') < 1:
        return False, "Invalid domain. Must have at least one dot"
    
    if host.startswith('.') or host.endswith('.') or '..' in host:
        return False, "Invalid domain format"
    
    if not re.match(r'^[a-zA-Z0-9\.\-]+$', host):
        return False, "Domain contains invalid characters"
    
    parts = host.split('.')
    if any(len(part) == 0 for part in parts):
        return False, "Invalid domain structure"
    
    tld = parts[-1]
    if not re.match(r'^[a-zA-Z]{2,}$', tld):
        return False, f"Invalid TLD: .{tld}"
    
    return True, "Valid URL"

def extract_features_from_url(url):
    """Extract all phishing detection features from URL"""
    is_valid, message = validate_url(url)
    if not is_valid:
        raise ValueError(f"Invalid URL: {message}")
    
    parsed = urlparse(url)
    host = parsed.netloc.split(':')[0] if parsed.netloc else ''
    ext = tldextract.extract(host)
    domain = ext.registered_domain
    subdomain = ext.subdomain
    
    status, html = fetch_content(url)
    html = html or ''
    
    features = {}
    
    # IP Address check
    features["having_IP_Address"] = -1 if re.match(r'^\d+\.\d+\.\d+\.\d+$', host) else 1
    
    # URL Length
    length = len(url)
    features["URL_Length"] = 1 if length < 54 else (0 if length <= 75 else -1)
    
    # URL shortener service
    features["Shortining_Service"] = -1 if any(s in host.lower() for s in SHORTENERS) else 1
    
    # @ symbol in URL
    features["having_At_Symbol"] = -1 if '@' in url else 1
    
    # Double slash redirecting
    features["double_slash_redirecting"] = -1 if '//' in parsed.path else 1
    
    # Prefix/Suffix with dash
    features["Prefix_Suffix"] = -1 if '-' in host else 1
    
    # Subdomain count
    sub_count = len(subdomain.split('.')) if subdomain else 0
    features["having_Sub_Domain"] = 1 if sub_count <= 1 else (0 if sub_count == 2 else -1)
    
    # SSL/HTTPS check
    features["SSLfinal_State"] = check_ssl(url, host)
    
    # Domain age
    age_days = get_domain_age(domain)
    if age_days == -1:  # Unknown age
        age_val = -1  # Changed: Unknown = suspicious
    elif age_days >= 365:
        age_val = 1
    elif age_days >= 180:
        age_val = 0
    else:
        age_val = -1
    
    features["Domain_registeration_length"] = age_val
    features["age_of_domain"] = age_val
    
    # Non-standard port
    features["port"] = -1 if (':' in parsed.netloc and parsed.netloc.split(':')[-1] not in ('80', '443')) else 1
    
    # HTTPS in domain name (phishing trick)
    features["HTTPS_token"] = -1 if 'https' in host.lower() else 1
    
    # DNS Record
    features["DNSRecord"] = check_dns(domain)
    
    # HTML-based features
    if html and status == 200:  # Changed: Only if successfully fetched
        # Favicon
        fav = re.search(r'<link[^>]+rel=["\']?(?:icon|shortcut icon)["\']?[^>]+href=[\'"]([^\'"]+)', html, re.I)
        if fav:
            fav_domain = tldextract.extract(urlparse(fav.group(1)).netloc).registered_domain
            features["Favicon"] = -1 if fav_domain and fav_domain != domain else 1
        else:
            features["Favicon"] = 0  # No favicon = neutral
        
        # External resources
        links = re.findall(r'(?:src|href)=["\']([^"\']+)', html, re.I)
        ext_count = sum(1 for l in links if urlparse(l).netloc and 
                       tldextract.extract(urlparse(l).netloc).registered_domain != domain)
        ext_pct = (ext_count / len(links) * 100) if links else 0
        features["Request_URL"] = 1 if ext_pct < 22 else (0 if ext_pct <= 61 else -1)
        
        # Anchor tags
        anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)', html, re.I)
        susp_anch = sum(1 for a in anchors if a.startswith(('#', 'javascript:', 'mailto:')) or
                       (urlparse(a).netloc and tldextract.extract(urlparse(a).netloc).registered_domain != domain))
        anch_pct = (susp_anch / len(anchors) * 100) if anchors else 0
        features["URL_of_Anchor"] = 1 if anch_pct < 31 else (0 if anch_pct <= 67 else -1)
        
        # Meta/script/link tags
        tags = re.findall(r'<(?:meta|script|link)[^>]+(?:src|href)=["\']([^"\']+)', html, re.I)
        ext_tags = sum(1 for t in tags if urlparse(t).netloc and 
                      tldextract.extract(urlparse(t).netloc).registered_domain != domain)
        tag_pct = (ext_tags / len(tags) * 100) if tags else 0
        features["Links_in_tags"] = 1 if tag_pct < 17 else (0 if tag_pct <= 81 else -1)
        
        # Server Form Handler
        forms = re.findall(r'<form[^>]+action=["\']([^"\']*)', html, re.I)
        features["SFH"] = -1 if any(not f or 'about:blank' in f.lower() for f in forms) else 1
        
        # Email submission
        features["Submitting_to_email"] = -1 if re.search(r'mailto:', html, re.I) else 1
        
        # JavaScript tricks
        features["on_mouseover"] = -1 if re.search(r'onmouseover\s*=', html, re.I) else 1
        features["RightClick"] = -1 if re.search(r'event\.button\s*==\s*2', html, re.I) else 1
        features["popUpWidnow"] = -1 if re.search(r'window\.open\s*\(', html, re.I) else 1
        features["Iframe"] = -1 if '<iframe' in html.lower() else 1
    else:
        # Changed: If HTML not available, mark as suspicious/neutral
        features["Favicon"] = -1
        features["Request_URL"] = -1
        features["URL_of_Anchor"] = -1
        features["Links_in_tags"] = -1
        features["SFH"] = -1
        features["Submitting_to_email"] = 0
        features["on_mouseover"] = 0
        features["RightClick"] = 0
        features["popUpWidnow"] = 0
        features["Iframe"] = 0
    
    # URL structure
    features["Abnormal_URL"] = 1 if domain and parsed.scheme else -1
    
    # Redirects
    features["Redirect"] = -1 if status and 300 <= status < 400 else 1
    
    # Placeholder features (you should implement these properly)
    features["web_traffic"] = 0  # Changed: Neutral instead of safe
    features["Page_Rank"] = 0
    features["Google_Index"] = 0
    features["Links_pointing_to_page"] = 0
    features["Statistical_report"] = 0
    
    features["Result"] = 1  # Placeholder for prediction
    
    return features

def save_features_to_csv(features, filename):
    """Save extracted features to CSV file"""
    row = [features.get(c, 0) for c in COLUMNS]  # Changed: Default to 0 (neutral)
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerow(row)