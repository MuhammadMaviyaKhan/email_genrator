import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header, make_header
from typing import Tuple, Optional, Dict, Any, List
import re
import quopri
import base64
from datetime import datetime
from email.utils import parsedate_to_datetime, parseaddr


class EmailParser:
    @staticmethod
    def parse_email(raw_bytes: bytes) -> Dict[str, Any]:
        msg = email.message_from_bytes(raw_bytes)
        
        result = {
            "subject": EmailParser._decode_header(msg.get("Subject")),
            "from": EmailParser._parse_address(msg.get("From")),
            "to": EmailParser._parse_addresses(msg.get_all("To")),
            "cc": EmailParser._parse_addresses(msg.get_all("Cc")),
            "bcc": EmailParser._parse_addresses(msg.get_all("Bcc")),
            "reply_to": EmailParser._parse_address(msg.get("Reply-To")),
            "date": EmailParser._parse_date(msg.get("Date")),
            "message_id": msg.get("Message-ID"),
            "headers": EmailParser._extract_headers(msg),
            "text_body": "",
            "html_body": "",
            "attachments": [],
        }
        
        text_parts = []
        html_parts = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition") or "")
                
                if "attachment" in disposition:
                    result["attachments"].append(
                        EmailParser._parse_attachment(part)
                    )
                elif content_type == "text/plain":
                    text_parts.append(EmailParser._decode_content(part))
                elif content_type == "text/html":
                    html_parts.append(EmailParser._decode_content(part))
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                text_parts.append(EmailParser._decode_content(msg))
            elif content_type == "text/html":
                html_parts.append(EmailParser._decode_content(msg))
        
        result["text_body"] = "\n".join(text_parts)
        result["html_body"] = "\n".join(html_parts)
        
        return result
    
    @staticmethod
    def _decode_header(header_value: Optional[str]) -> str:
        if not header_value:
            return ""
        try:
            return str(make_header(decode_header(header_value)))
        except Exception:
            return str(header_value)
    
    @staticmethod
    def _parse_address(header_value: Optional[str]) -> Dict[str, str]:
        if not header_value:
            return {"name": "", "email": ""}
        
        name, addr = parseaddr(header_value)
        return {
            "name": EmailParser._decode_header(name),
            "email": addr,
        }
    
    @staticmethod
    def _parse_addresses(header_values: Optional[List[str]]) -> List[Dict[str, str]]:
        if not header_values:
            return []
        
        addresses = []
        for header in header_values:
            for addr in header.split(","):
                parsed = EmailParser._parse_address(addr.strip())
                if parsed["email"]:
                    addresses.append(parsed)
        
        return addresses
    
    @staticmethod
    def _parse_date(header_value: Optional[str]) -> Optional[datetime]:
        if not header_value:
            return None
        try:
            return parsedate_to_datetime(header_value)
        except Exception:
            return None
    
    @staticmethod
    def _extract_headers(msg: email.message.Message) -> Dict[str, str]:
        headers = {}
        for key, value in msg.items():
            headers[key] = EmailParser._decode_header(value)
        return headers
    
    @staticmethod
    def _decode_content(part: email.message.Message) -> str:
        try:
            payload = part.get_payload(decode=True)
            if not payload:
                return ""
            
            charset = part.get_content_charset() or "utf-8"
            try:
                return payload.decode(charset, errors="replace")
            except (UnicodeDecodeError, LookupError):
                return payload.decode("utf-8", errors="replace")
        except Exception:
            return ""
    
    @staticmethod
    def _parse_attachment(part: email.message.Message) -> Dict[str, Any]:
        filename = part.get_filename()
        if not filename:
            filename = f"attachment_{datetime.utcnow().timestamp()}"
        
        content_type = part.get_content_type()
        payload = part.get_payload(decode=True) or b""
        
        return {
            "filename": EmailParser._decode_header(filename),
            "content_type": content_type,
            "size": len(payload),
            "content_id": part.get("Content-ID"),
            "is_inline": "inline" in str(part.get("Content-Disposition") or "").lower(),
            "data": base64.b64encode(payload).decode("utf-8") if payload else "",
        }
    
    @staticmethod
    def create_email_message(
        from_addr: str,
        to_addr: str,
        subject: str,
        text_body: str = "",
        html_body: str = "",
        attachments: Optional[List[Dict]] = None,
    ) -> bytes:
        msg = MIMEMultipart("mixed")
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid()
        
        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        if attachments:
            for att in attachments:
                part = email.mime.base.MIMEBase(
                    att.get("content_type", "application/octet-stream").split("/")[0],
                    att.get("content_type", "application/octet-stream").split("/")[-1],
                )
                part.set_payload(base64.b64decode(att["data"]))
                email.encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=att["filename"],
                )
                msg.attach(part)
        
        return msg.as_bytes()
    
    @staticmethod
    def extract_otp(text: str) -> Optional[str]:
        patterns = [
            r'(?:verification|otp|code|pin)[\s:]*?(\d{4,8})',
            r'\b(\d{6})\b',
            r'\b(\d{4})\b',
            r'\b(\d{5})\b',
            r'\b(\d{8})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def sanitize_html(html: str) -> str:
        if not html:
            return ""
        
        allowed_tags = {
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div',
            'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
            'li', 'ol', 'p', 'pre', 'span', 'strong', 'table', 'tbody',
            'td', 'tfoot', 'th', 'thead', 'tr', 'ul', 'font', 'small',
            'big', 'sub', 'sup', 'u', 'strike', 'center',
        }
        
        allowed_attrs = {
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'width', 'height', 'style'],
            'table': ['border', 'cellpadding', 'cellspacing', 'width', 'style'],
            'td': ['width', 'height', 'style', 'align', 'valign'],
            'th': ['width', 'height', 'style', 'align', 'valign'],
            'p': ['style', 'align'],
            'div': ['style', 'align'],
            'span': ['style'],
            'font': ['color', 'size', 'face'],
            '*': ['style'],
        }
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            for tag in soup.find_all(True):
                if tag.name not in allowed_tags:
                    tag.unwrap()
                    continue
                
                allowed = allowed_attrs.get(tag.name, allowed_attrs.get('*', []))
                for attr in list(tag.attrs):
                    if attr not in allowed:
                        del tag[attr]
                
                if tag.name == 'a':
                    tag['rel'] = 'noopener noreferrer'
                    tag['target'] = '_blank'
                    href = tag.get('href', '')
                    if not href.startswith(('http://', 'https://', 'mailto:')):
                        del tag['href']
            
            return str(soup)
        except ImportError:
            import re
            cleaned = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r'<style.*?</style>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
            return cleaned
    
    @staticmethod
    def extract_images(html: str) -> List[Dict[str, str]]:
        import re
        images = []
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        
        for match in re.finditer(img_pattern, html, re.IGNORECASE):
            src = match.group(1)
            if src.startswith(('http://', 'https://', 'cid:', 'data:')):                
                images.append({
                    "src": src,
                    "tag": match.group(0),
                })
        
        return images