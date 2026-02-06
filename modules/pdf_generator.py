"""
PDF Generator - Konvertiert Outline Markdown zu PDF
"""
import os
import re
import subprocess
import requests
import unicodedata
from urllib.parse import urlparse, parse_qs
from typing import Dict
from dotenv import load_dotenv

# Umlaute in ASCII umwandeln (ü -> ue, ä -> ae, etc.)
def sanitize_filename(title: str) -> str:
    # Entferne Akzente und normalisiere
    title = unicodedata.normalize('NFKD', title)
    title = title.encode('ascii', 'ignore').decode('ascii')
    # Erlaube nur Buchstaben, Zahlen, Leerzeichen und Bindestriche
    title = re.sub(r'[^\w\s-]', '', title)
    # Leerzeichen zu Unterstrichen
    title = title.strip().replace(' ', '_')
    # Falls leer, Fallback
    return title if title else "dokument"

load_dotenv()

class PDFGenerator:
    def __init__(self):
        self.outline_url = os.getenv("OUTLINE_URL", "").rstrip("/")
        self.api_token = os.getenv("OUTLINE_API_TOKEN", "")
        self.output_dir = os.getenv("OUTPUT_DIR", "output")
        self.images_dir = os.path.join(self.output_dir, "images")
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
    
    def make_absolute(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("/"):
            return self.outline_url + url
        return url
    
    def download_image(self, full_url: str) -> str:
        headers = {}
        if full_url.startswith(self.outline_url):
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        try:
            print(f"Lade Bild: {full_url}")
            r = requests.get(full_url, headers=headers, allow_redirects=True)
            r.raise_for_status()
        except Exception as e:
            print(f"Warnung: Konnte Bild {full_url} nicht laden: {e}")
            return full_url
        
        content_type = (r.headers.get("Content-Type", "") or "").lower()
        if "png" in content_type:
            ext = ".png"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "gif" in content_type:
            ext = ".gif"
        else:
            ext = ".bin"
        
        parsed = urlparse(full_url)
        qs = parse_qs(parsed.query)
        if "id" in qs and qs["id"]:
            base_name = qs["id"][0]
        else:
            base_name = os.path.basename(parsed.path) or "image"
        
        filename = base_name + ext
        local_path = os.path.join(self.images_dir, filename)
        
        with open(local_path, "wb") as f:
            f.write(r.content)
        
        return f"images/{filename}"
    
    def rewrite_markdown_images(self, md_text: str) -> str:
        pattern_md = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        def repl(match):
            alt_text = match.group(1)
            raw_target = match.group(2).strip()
            
            if '"' in raw_target:
                url_part = raw_target.split('"', 1)[0].strip()
            else:
                url_part = raw_target.split()[0].strip()
            
            url = url_part.strip()
            full_url = self.make_absolute(url)
            new_rel = self.download_image(full_url)
            return f"![{alt_text}]({new_rel})"
        
        return re.sub(pattern_md, repl, md_text)
    
    def rewrite_html_img_in_markdown(self, md_text: str) -> str:
        pattern_img = r'<img\s+[^>]*src="([^"]+)"([^>]*)>'
        
        def repl(match):
            url = match.group(1).strip()
            rest = match.group(2)
            full_url = self.make_absolute(url)
            new_rel = self.download_image(full_url)
            return f'<img src="{new_rel}"{rest}>'
        
        return re.sub(pattern_img, repl, md_text)
    
    def normalize_markdown(self, md_text: str) -> str:
        md_text = md_text.replace("\\n", " ")
        md_text = md_text.replace("\u00A0", " ")
        md_text = md_text.replace("\u200B", "")
        md_text = md_text.replace("\uFEFF", "")
        
        md_text = re.sub(r'^[ \t]+(?=#+\s)', '', md_text, flags=re.MULTILINE)
        md_text = re.sub(r'([^\n])\n(#+\s)', r'\1\n\n\2', md_text)
        
        md_text = re.sub(r'</div\s*>', '', md_text, flags=re.IGNORECASE)
        md_text = re.sub(r'<div[^>]*>', '', md_text, flags=re.IGNORECASE)
        
        return md_text
    
    def generate_pdf(self, markdown_text: str, title: str, style: Dict = None) -> str:
        if style is None:
            style = {}
        
        md_text = self.normalize_markdown(markdown_text)
        md_text = self.rewrite_markdown_images(md_text)
        md_text = self.rewrite_html_img_in_markdown(md_text)
        
        temp_md = os.path.join(self.output_dir, "temp.md")
        with open(temp_md, "w", encoding="utf-8") as f:
            f.write(md_text)
        safe_title = re.sub(r'[^\w\s-]', '', title, flags=re.ASCII).strip().replace(' ', '_')
        if not safe_title:
            safe_title = "dokument"

        pdf_filename = f"{safe_title}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)
        
        cmd = [
            "pandoc",
            os.path.basename(temp_md),
            "-o",
            pdf_filename,
            "--pdf-engine=xelatex",
            "--toc",
            "--toc-depth=3",
            "-N",
            "-V", "toc-title=Inhaltsverzeichnis",
            "-V", f"geometry:margin={style.get('margin', '2.5cm')}",
            "-V", f"fontsize={style.get('fontsize', '11pt')}",
            "-V", f"mainfont={style.get('font', 'Arial')}",
            "-V", f"title={title}",
        ]
        
        print(f"Führe Pandoc aus: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, cwd=self.output_dir)
        
        return pdf_path