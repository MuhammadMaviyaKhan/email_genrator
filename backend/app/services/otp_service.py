import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib
import secrets
import string


class OTPService:
    OTP_PATTERNS = [
        (r'(?:verification code|otp|code|pin)[\s:]*?([0-9]{4,8})', 4, 8),
        (r'([0-9]{6})\s*(?:is your|is the|is)', 6, 6),
        (r'(?:your|the)\s*(?:code|otp|pin)[\s:]*?([0-9]{4,8})', 4, 8),
        (r'\b([0-9]{4})\b', 4, 4),
        (r'\b([0-9]{5})\b', 5, 5),
        (r'\b([0-9]{6})\b', 6, 6),
        (r'\b([0-9]{8})\b', 8, 8),
    ]
    
    VERIFICATION_PATTERNS = [
        r'https?://[^\s<>"]+(?:verify|verification|confirm|activate|validate|complete|finish|approve)[^\s<>"]*',
        r'https?://[^\s<>"]+(?:account|email|signup|register|registration|login|auth)[^\s<>"]*',
        r'https?://[^\s<>"]+(?:\?|&)(?:token|code|otp|key|id)=[^\s<>"]+',
    ]
    
    def extract_otp_codes(
        self, 
        text: str, 
        html: str = "", 
        subject: str = ""
    ) -> List[Dict]:
        combined_text = f"{subject}\n{text}\n{html}"
        found_codes = []
        seen = set()
        
        for pattern, min_len, max_len in self.OTP_PATTERNS:
            matches = re.findall(pattern, combined_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                code = match if isinstance(match, str) else match[0]
                if code and code.isdigit() and min_len <= len(code) <= max_len:
                    if code not in seen:
                        seen.add(code)
                        found_codes.append({
                            "code": code,
                            "length": len(code),
                            "context": self._extract_context(combined_text, code),
                            "position": combined_text.find(code),
                        })
        
        return found_codes
    
    def extract_verification_links(
        self, 
        text: str, 
        html: str = ""
    ) -> List[Dict]:
        combined_text = f"{text}\n{html}"
        links = []
        seen = set()
        
        for pattern in self.VERIFICATION_PATTERNS:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                url = match if isinstance(match, str) else match[0]
                if url and url not in seen:
                    seen.add(url)
                    links.append({
                        "url": url,
                        "text": self._extract_link_text(combined_text, url),
                    })
        
        return links
    
    def _extract_context(self, text: str, code: str, context_length: int = 80) -> str:
        idx = text.find(code)
        if idx == -1:
            return ""
        
        start = max(0, idx - context_length // 2)
        end = min(len(text), idx + len(code) + context_length // 2)
        context = text[start:end].strip()
        return context.replace("\n", " ").replace("\r", " ")
    
    def _extract_link_text(self, text: str, url: str) -> str:
        idx = text.find(url)
        if idx == -1:
            return "Verification Link"
        
        before = text[:idx].rstrip()
        last_newline = before.rfind("\n")
        if last_newline != -1:
            candidate = before[last_newline + 1:].strip()
            if candidate and len(candidate) < 100:
                return candidate
        
        return "Verification Link"
    
    def filter_valid_otps(self, codes: List[Dict]) -> List[Dict]:
        valid_lengths = {4, 5, 6, 8}
        return [c for c in codes if c["length"] in valid_lengths]
    
    def get_primary_otp(self, codes: List[Dict]) -> Optional[Dict]:
        if not codes:
            return None
        
        valid = self.filter_valid_otps(codes)
        if not valid:
            return None
        
        priority = {6: 0, 4: 1, 5: 2, 8: 3}
        return sorted(valid, key=lambda x: priority.get(x["length"], 10))[0]
    
    def validate_otp_format(self, code: str) -> bool:
        return bool(re.match(r'^\d{4,8}$', code))
    
    def generate_test_otp(self, length: int = 6) -> str:
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def clean_otp(self, code: str) -> str:
        return re.sub(r'\D', '', code)[:8]
    
    def extract_otp_with_keywords(self, text: str, keywords: List[str]) -> List[Dict]:
        results = []
        seen = set()
        
        for keyword in keywords:
            pattern = rf'{keyword}[\s:]*?([0-9]{{4,8}})'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and match.isdigit() and match not in seen:
                    seen.add(match)
                    results.append({
                        "code": match,
                        "length": len(match),
                        "keyword": keyword,
                        "context": self._extract_context(text, match),
                    })
        
        return results