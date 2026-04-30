import re
import csv
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from urllib.parse import urlparse

# analyze the header issue for common crawl data (jsonl file)

@dataclass
class Finding:
    header: str
    severity: str
    issue: str
    recommendation: str
    url: Optional[str] = None
    domain: Optional[str] = None
    details: Optional[str] = None


def extract_domain_from_url(url: str) -> Optional[str]:
    """从URL中提取domain"""
    try:
        if not url:
            return None

        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        parsed = urlparse(url)
        domain = parsed.netloc

        # 移除端口号
        if ':' in domain:
            domain = domain.split(':')[0]

        # 移除用户名密码
        if '@' in domain:
            domain = domain.split('@')[1]

        return domain.lower()
    except Exception as e:
        print(f"Error extracting domain from URL {url}: {e}")
        return None

def _norm(h: str) -> str:
    return h.strip().lower()


def parse_directives(header_val: str) -> Dict[str, Optional[str]]:
    out = {}
    for part in re.split(r';\s*', header_val or ''):
        if not part:
            continue
        if '=' in part:
            k, v = part.split('=', 1)
            out[_norm(k)] = v.strip()
        else:
            out[_norm(part)] = None
    return out


def parse_csp(csp: str) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for seg in re.split(r';\s*', csp or ''):
        if not seg:
            continue
        parts = seg.strip().split()
        if not parts:
            continue
        d = _norm(parts[0])
        out[d] = parts[1:]
    return out


def parse_set_cookie(set_cookie_value: str) -> Tuple[str, Dict[str, Optional[str]]]:
    parts = [p.strip() for p in set_cookie_value.split(';')]
    if not parts:
        return "", {}
    name_val = parts[0]
    attrs: Dict[str, Optional[str]] = {}
    if '=' in name_val:
        name, value = name_val.split('=', 1)
        attrs['value'] = value
    else:
        name = name_val
        attrs['value'] = None
    for attr in parts[1:]:
        if '=' in attr:
            k, v = attr.split('=', 1)
            attrs[_norm(k)] = v.strip()
        else:
            attrs[_norm(attr)] = None
    return name.strip(), attrs


def parse_all_csp_policies(csp_values: List[str]) -> Dict[str, List[str]]:
    merged_csp: Dict[str, List[str]] = {}
    for csp_val in csp_values:
        csp = parse_csp(csp_val or '')
        for directive, sources in csp.items():
            if directive not in merged_csp:
                merged_csp[directive] = []
            for source in sources:
                if source not in merged_csp[directive]:
                    merged_csp[directive].append(source)
    return merged_csp


# ---------- 具体检查 ----------
def check_hsts(values: List[str]) -> List[Finding]:
    findings: List[Finding] = []
    if not values:
        findings.append(Finding("Strict-Transport-Security", "high",
                                "Missing HSTS.",
                                "HSTS, recommend max-age≥15552000 (180 days)"))
        return findings

    raw = "; ".join([v for v in values if v])
    if not raw:
        return findings

    d = parse_directives(raw)
    max_age_val = d.get('max-age')
    max_age = 0
    if isinstance(max_age_val, str):
        try:
            max_age = int(max_age_val)
        except ValueError:
            m = re.search(r'max-age\s*=\s*(\d+)', raw, flags=re.I)
            if m:
                max_age = int(m.group(1))

    if max_age < 15552000:
        findings.append(Finding("Strict-Transport-Security", "medium",
                                "HSTS max-age is too short.",
                                "Set max-age≥15552000 (at least 180 days)",
                                details=raw))

    has_isd = 'includesubdomains' in d or re.search(r'\bincludeSubDomains\b', raw, re.I)
    if not has_isd:
        findings.append(Finding("Strict-Transport-Security", "low",
                                "includeSubDomains is not enabled.",
                                "Add includeSubDomains.",
                                details=raw))
    return findings


def check_x_content_type_options(values: List[str]) -> List[Finding]:
    if not values:
        return [Finding("X-Content-Type-Options", "medium",
                        "X-Content-Type-Options Header Not Present",
                        "Add X-Content-Type-Options header with value 'nosniff'")]
    findings = []
    for val in values:
        if _norm(val or '') != 'nosniff':
            findings.append(Finding("X-Content-Type-Options", "medium",
                                    f"Invalid Value: '{val}'",
                                    "Set X-Content-Type-Options value to 'nosniff'"))
    return findings


def check_clickjacking(csp_values: List[str], xfo_values: List[str]) -> List[Finding]:
    findings: List[Finding] = []
    fa_present = False
    if csp_values:
        merged_csp = parse_all_csp_policies(csp_values)
        if merged_csp.get('frame-ancestors'):
            fa_present = True

    if csp_values and not fa_present:
        findings.append(Finding("Content-Security-Policy", "medium",
                                "Missing frame-ancestors Directive",
                                "Add frame-ancestors directive to CSP"))

    valid_xfo = False
    if xfo_values:
        for xfo in xfo_values:
            if _norm(xfo or '') in ('deny', 'sameorigin'):
                valid_xfo = True
                break
        if not valid_xfo:
            findings.append(Finding("X-Frame-Options", "medium",
                                    "Invalid Values",
                                    "Set X-Frame-Options to DENY or SAMEORIGIN"))
    else:
        findings.append(Finding("X-Frame-Options", "medium",
                                "X-Frame-Options Header Not Present",
                                "Add X-Frame-Options header with DENY or SAMEORIGIN"))

    if not fa_present and not valid_xfo and not csp_values:
        findings.append(Finding("Clickjacking Protection", "high",
                                "No Clickjacking Protection",
                                "Implement either CSP frame-ancestors or X-Frame-Options"))
    return findings


def check_csp(values: List[str]) -> List[Finding]:
    findings: List[Finding] = []
    if not values:
        findings.append(Finding("Content-Security-Policy", "high",
                                "Missing CSP.",
                                "Add strict CSP."))
        return findings

    merged_csp = parse_all_csp_policies(values)
    
    if 'script-src' not in merged_csp and 'default-src' not in merged_csp:
        findings.append(Finding("Content-Security-Policy", "medium",
                                "script-src and default-src directives are missing.",
                                "Add script-src to mitigate injection risks",
                                details=f"All CSP policies: {'; '.join(values)}"))

    if 'object-src' not in merged_csp or merged_csp.get('object-src') != ["'none'"]:
        findings.append(Finding("Content-Security-Policy", "medium",
                                "object-src is not set to 'none'.",
                                "Set object-src 'none'",
                                details=f"All CSP policies: {'; '.join(values)}"))

    base_uri_sources = merged_csp.get('base-uri', [])
    if not base_uri_sources:
        findings.append(Finding("Content-Security-Policy", "medium",
                                "base-uri directive is missing.",
                                "Set base-uri 'none'",
                                details=f"All CSP policies: {'; '.join(values)}"))

    for d in ('script-src', 'style-src'):
        sources = merged_csp.get(d, [])
        if "'unsafe-inline'" in (s.lower() for s in sources):
            findings.append(Finding("Content-Security-Policy", "high",
                                    f"{d} contains 'unsafe-inline'.",
                                    "Remove unsafe-inline",
                                    details=f"All CSP policies: {'; '.join(values)}"))

        if "'unsafe-eval'" in (s.lower() for s in sources) and d == 'script-src':
            findings.append(Finding("Content-Security-Policy", "medium",
                                    "script-src contains 'unsafe-eval'.",
                                    "Avoid eval-like functions.",
                                    details=f"All CSP policies: {'; '.join(values)}"))

        if '*' in sources:
            findings.append(Finding("Content-Security-Policy", "medium",
                                    f"{d} allows wildcard *.",
                                    "Tighten sources to trusted domain list.",
                                    details=f"All CSP policies: {'; '.join(values)}"))
    return findings


def check_cors(headers: Dict[str, List[str]]) -> List[Finding]:
    findings: List[Finding] = []
    aco_values = headers.get('access-control-allow-origin', [])
    acc_values = headers.get('access-control-allow-credentials', [])
    for aco in aco_values:
        if _norm(aco or '') == '*':
            for acc in acc_values:
                if _norm(acc or '') == 'true':
                    findings.append(Finding("CORS", "high",
                                            "Access-Control-Allow-Origin is * and allows credentials.",
                                            "Do not use * with credentials.",
                                            details=f"ACAO: {aco}, ACAC: {acc}"))
    return findings


def check_cookies(set_cookie_values: List[str]) -> List[Finding]:
    findings: List[Finding] = []
    if not set_cookie_values:
        return findings
    cookies = {}
    for raw in set_cookie_values:
        name, attrs = parse_set_cookie(raw)
        if name:
            cookies[name] = (raw, attrs)

    for name, (raw, attrs) in cookies.items():
        samesite = _norm((attrs.get('samesite') or '')).strip()
        secure = 'secure' in attrs
        httponly = 'httponly' in attrs
        is_sessiony = bool(re.search(r'(session|sess|token|auth|sid)', name, re.I))

        if not samesite:
            findings.append(Finding("Set-Cookie", "medium",
                                    "Cookie is missing SameSite.",
                                    "Recommend SameSite=Lax",
                                    details=raw))
        elif samesite == 'none' and not secure:
            findings.append(Finding("Set-Cookie", "high",
                                    "Cookie is SameSite=None but Secure is not set.",
                                    "SameSite=None must be paired with Secure.",
                                    details=raw))

        if not secure:
            findings.append(Finding("Set-Cookie", "medium",
                                    "Cookie is missing Secure.",
                                    "Use Secure",
                                    details=raw))
        if is_sessiony and not httponly:
            findings.append(Finding("Set-Cookie", "high",
                                    "Session Cookie is missing HttpOnly.",
                                    "Set HttpOnly to prevent JavaScript access (XSS risk).",
                                    details=raw))
    return findings


def check_content_type(headers: Dict[str, List[str]]) -> List[Finding]:
    findings: List[Finding] = []
    ctypes = headers.get('content-type', [])
    if not ctypes:
        findings.append(Finding("Content-Type", "medium",
                                "Missing Content-Type.",
                                "Return precise MIME and include charset"))
    return findings


def check_headers(headers: Dict[str, List[str]]) -> List[Finding]:
    findings = []
    
    # 归一化 headers 键
    norm_headers = {k.lower(): v if isinstance(v, list) else [v] for k, v in headers.items()}
    
    security_headers = [
        'strict-transport-security',
        'content-security-policy', 
        'x-content-type-options',
        'x-frame-options'
    ]
    
    has_any_security_header = any(norm_headers.get(h) for h in security_headers)
    
    if not has_any_security_header:
        findings.append(Finding("Security Headers", "critical",
                                "Missing Security Headers",
                                "Implement basic security headers",
                                details="No security headers detected"))
    else:
        findings += check_hsts(norm_headers.get('strict-transport-security', []))
        findings += check_x_content_type_options(norm_headers.get('x-content-type-options', []))
        findings += check_csp(norm_headers.get('content-security-policy', []))
        findings += check_clickjacking(norm_headers.get('content-security-policy', []),
                                       norm_headers.get('x-frame-options', []))
    
    findings += check_cors(norm_headers)
    findings += check_cookies(norm_headers.get('set-cookie', []))
    findings += check_content_type(norm_headers)
    
    return findings

def write_findings(csv_path: Path, findings: List[Finding]):
    write_header = not csv_path.exists()
    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(
            f,
            fieldnames=["url", "domain", "header", "severity", "issue", "details"]
        )
        if write_header:
            w.writeheader()
        for f in findings:
            w.writerow({
                "url": f.url or "",
                "domain": f.domain or "",
                "header": f.header,
                "severity": f.severity,
                "issue": f.issue,
                "details": f.details or ""
            })


def process_record(record: Dict, csv_path: Path):
    url = record.get('url')
    status = record.get('status')
    headers = record.get('headers', {})
    domain = extract_domain_from_url(url)

    findings = check_headers(headers)
    
    ignored_issues = {
        "object-src is not set to 'none'.",
        "X-Frame-Options Header Not Present",
        "Missing Security Headers",
        "Missing frame-ancestors Directive",
        "includeSubDomains is not enabled.",
        "Missing CSP."
    }
    
    filtered_findings = [f for f in findings if f.issue not in ignored_issues]
    
    # Fill in record details for each finding
    for f in filtered_findings:
        f.url = url
        f.domain = domain
    
    if filtered_findings:
        write_findings(csv_path, filtered_findings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Common Crawl data for header issues")
    parser.add_argument("--input", type=str, required=True, help="Input JSONL file path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file path")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if output_path.exists():
        print(f"Removing existing output file: {output_path}")
        output_path.unlink()
    
    print(f"Processing {input_path}...")
    t0 = time.perf_counter()
    count = 0
    
    try:
        with open(input_path, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    process_record(record, output_path)
                    count += 1
                    if count % 1000 == 0:
                        elapsed = time.perf_counter() - t0
                        print(f"Processed {count} records... ({count/elapsed:.1f} rec/s)")
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing record: {e}")
                    continue
    except FileNotFoundError:
        print(f"Error: Input file {input_path} not found.")
        exit(1)
        
    dt = time.perf_counter() - t0
    print(f"\nAll done in {dt:.1f}s | Total records processed: {count} | Findings saved to {output_path}")