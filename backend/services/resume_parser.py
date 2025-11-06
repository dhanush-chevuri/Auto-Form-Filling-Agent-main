import os
import asyncio
import json
from PyPDF2 import PdfReader
from docx import Document
import io
from ..logger import log_resume_data, log_error

# OCR libraries
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Official LlamaIndex libraries
from llama_index.llms.openrouter import OpenRouter
from llama_parse import LlamaParse
from llama_index.core import Document as LlamaDocument

class ResumeParser:
    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.llama_key = os.getenv("LLAMA_CLOUD_API_KEY")
        # Ensure attributes exist even if API keys are missing
        self.llm = None
        self.parser = None
        
        # Initialize OpenRouter LLM
        if self.openrouter_key:
            self.llm = OpenRouter(
                api_key=self.openrouter_key,
                model="mistralai/mistral-7b-instruct:free",
                max_tokens=1500,
                temperature=0.0
            )
        
        # Initialize LlamaParse
        if self.llama_key:
            self.parser = LlamaParse(
                api_key=self.llama_key,
                result_type="text",
                parsing_instruction="Extract structured information including name, email, phone, address, education, work experience, and skills from this resume document."
            )
    
    async def extract_data(self, content: bytes, filename: str) -> dict:
        # Try Llama Cloud first with original file
        llama_result = await self._try_llama_cloud(content, filename)
        if llama_result:
            return llama_result

        # Fallback to text extraction + heuristic parser
        text = self._extract_text(content, filename)

        # Check if we got any text at all - PDF must be ATS-friendly
        if not text or not text.strip():
            log_error("PDF is not ATS-friendly - no text extracted", "resume-parser")
            return {
                "success": False,
                "ats_friendly": False,
                "error": "This PDF is NOT ATS-friendly",
                "message": "Your resume appears to be a scanned image or uses formatting that prevents text extraction. ATS (Applicant Tracking Systems) cannot read this type of PDF.",
                "suggestions": [
                    "Export your resume as a 'text-based PDF' from your word processor",
                    "Use File > Save As > PDF (not Print to PDF)",
                    "Upload a DOCX file instead",
                    "Avoid using images or special fonts",
                    "Test your PDF: Can you select and copy text from it? If not, it's not ATS-friendly"
                ],
                "Full Name": "",
                "Email": "",
                "Phone Number": "",
                "Address": "",
                "Education": [],
                "Work Experience": [],
                "Skills": [],
                "raw_text": ""
            }

        # First try a deterministic extractor on the text — prefer exact matches
        basic = self._extract_basic_fields(text)
        
        # Mark as ATS-friendly since we extracted text
        basic['ats_friendly'] = True
        basic['success'] = True
        
        # If we found a name or email, prefer deterministic result (avoids AI overwriting)
        if basic.get('Full Name') or basic.get('Email'):
            log_resume_data(basic)
            return basic

        # Try AI parsing if deterministic extractor didn't find enough
        if self.llm:
            try:
                ai_result = await self._parse_with_ai(text)
                # If AI produced a valid dict with meaningful fields, return it
                if isinstance(ai_result, dict) and ai_result.get('Full Name'):
                    return ai_result
            except Exception:
                # fall through to deterministic extractor
                pass

        # As a robust fallback, return what the deterministic extractor produced
        basic['ats_friendly'] = True
        basic['success'] = True
        log_resume_data(basic)
        return basic
    
    def _extract_text(self, content: bytes, filename: str) -> str:
        if filename.endswith('.pdf'):
            return self._extract_pdf_text(content)
        elif filename.endswith('.docx'):
            return self._extract_docx_text(content)
        else:
            return content.decode('utf-8')
    
    def _extract_pdf_text(self, content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            # If no text was extracted, try OCR as fallback
            if not text.strip():
                log_error("PDF text extraction returned empty - attempting OCR", "resume-parser")
                text = self._extract_pdf_text_with_ocr(content)
            
            return text
        except Exception as e:
            log_error(f"PDF extraction error: {e}", "resume-parser")
            # Try OCR as last resort
            try:
                return self._extract_pdf_text_with_ocr(content)
            except Exception:
                return ""
    
    def _extract_pdf_text_with_ocr(self, content: bytes) -> str:
        """Extract text from PDF using OCR (for image-based/scanned PDFs)"""
        if not OCR_AVAILABLE:
            log_error("OCR libraries not available - install pdf2image and pytesseract", "resume-parser")
            return ""
        
        try:
            # Set Tesseract path for Windows
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # Convert PDF pages to images
            images = convert_from_bytes(content, dpi=300)
            
            # OCR each page
            text = ""
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang='eng')
                if page_text:
                    text += page_text + "\n"
                log_error(f"OCR page {i+1}: extracted {len(page_text)} characters", "resume-parser")
            
            if text.strip():
                log_error(f"OCR successful: extracted {len(text)} total characters", "resume-parser")
            else:
                log_error("OCR completed but no text found", "resume-parser")
            
            return text
        except Exception as e:
            log_error(f"OCR extraction error: {e}", "resume-parser")
            return ""
    
    def _extract_docx_text(self, content: bytes) -> str:
        doc = Document(io.BytesIO(content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    async def _parse_with_ai(self, text: str) -> dict:
        """Parse resume text using OpenRouter LLM"""
        if not self.llm:
            log_error("OpenRouter LLM not initialized", "resume-parser")
            return self._get_fallback_data()
        
        prompt = f"""
Extract and structure the following resume information into JSON format:

{{
    "Full Name": "extracted full name",
    "Email": "extracted email address", 
    "Phone Number": "extracted phone number",
    "Address": "extracted address",
    "Education": "education background",
    "Work Experience": "work experience summary",
    "Skills": "technical and professional skills"
}}

Resume text:
{text[:2000]}

Return only valid JSON, no additional text.
"""
        
        try:
            response = await self.llm.acomplete(prompt)
            content = str(response).strip()
            
            # Clean and parse JSON response
            cleaned_content = self._clean_json_response(content)
            
            # Handle empty response
            if not cleaned_content or cleaned_content.isspace():
                log_error("Empty response from OpenRouter", "resume-parser")
                return self._get_fallback_data()
            
            parsed = json.loads(cleaned_content)
            
            # Validate required fields
            if self._validate_parsed_data(parsed):
                log_resume_data(parsed)
                return parsed
            else:
                log_error("Invalid data structure from OpenRouter", "resume-parser")
                return self._get_fallback_data()
                
        except Exception as e:
            log_error(f"OpenRouter parsing failed: {e}", "resume-parser")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> dict:
        """Return fallback data when AI parsing fails"""
        # Keep a conservative, minimal fallback if nothing can be parsed
        fallback_data = {
            "Full Name": "",
            "Email": "",
            "Phone Number": "",
            "Address": "",
            "Education": [],
            "Work Experience": [],
            "Skills": []
        }
        log_resume_data(fallback_data)
        return fallback_data

    def _extract_basic_fields(self, text: str) -> dict:
        """Extract common resume fields from plain text using regex heuristics.

        This does not rely on external AI and provides deterministic results for
        name, email, phone, education, work experience and skills.
        """
        import re

        # Normalize
        t = text.replace('\r', '\n')

        # Email
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", t)
        email = email_match.group(0) if email_match else ''

        # Phone (simple patterns)
        phone_match = re.search(r"(\+?\d[\d\-(). ]{6,}\d)", t)
        phone = phone_match.group(0).strip() if phone_match else ''

        # Name: try the first non-empty line that contains letters and a space and is not 'resume' or 'curriculum'
        name = ''
        for line in [l.strip() for l in t.split('\n') if l.strip()]:
            low = line.lower()
            if 'name' in low and ':' in line:
                # handle lines like 'Full Name: Alice Example'
                parts = line.split(':', 1)
                candidate = parts[1].strip()
                if candidate:
                    name = candidate
                    break

            if len(line) > 2 and 'resume' not in low and 'curriculum' not in low and any(c.isalpha() for c in line) and 'email' not in low:
                # Heuristic: a name usually has 2 words; accept lines with ':' too if they look like a name
                words = [w for w in line.split() if w]
                if len(words) >= 2 and len(words) <= 5:
                    # remove trailing ':' if present
                    candidate = line.strip().rstrip(':')
                    name = candidate
                    break

        # Skills: look for a 'skills' section
        skills = []
        skills_section = re.search(r"skills[:\n\s]*(.+?)(?:\n\n|education|experience|$)", t, re.I | re.S)
        if skills_section:
            raw = skills_section.group(1)
            # split by commas or newlines
            parts = re.split(r'[;,\n]', raw)
            skills = [p.strip() for p in parts if p.strip()]

        # Education: capture lines under education heading
        education = []
        edu_section = re.search(r"education[:\n\s]*(.+?)(?:\n\n|experience|skills|$)", t, re.I | re.S)
        if edu_section:
            raw = edu_section.group(1).strip()
            edu_lines = [l.strip() for l in raw.split('\n') if l.strip()]
            education = edu_lines

        # Work experience: capture paragraphs under experience heading
        experience = []
        exp_section = re.search(r"(experience|work experience|professional experience)[:\n\s]*(.+?)(?:\n\n|education|skills|$)", t, re.I | re.S)
        if exp_section:
            raw = exp_section.group(2).strip()
            exp_lines = [l.strip() for l in raw.split('\n') if l.strip()]
            experience = exp_lines

        return {
            "Full Name": name,
            "Email": email,
            "Phone Number": phone,
            "Address": '',
            "Education": education,
            "Work Experience": experience,
            "Skills": skills,
            "raw_text": text
        }
    
    async def _try_llama_cloud(self, content: bytes, filename: str) -> dict:
        """Try LlamaParse for document parsing"""
        if not self.parser:
            log_error("LlamaParse not initialized", "resume-parser")
            return None
        
        try:
            # Save content to temporary file for LlamaParse
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Parse document with LlamaParse
            documents = await self.parser.aload_data(tmp_file_path)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            if documents:
                # Extract text from parsed documents
                full_text = '\n'.join([doc.text for doc in documents])
                
                # Use OpenRouter to structure the extracted text
                structured_result = await self._parse_with_ai(full_text)
                return structured_result
            else:
                log_error("No documents parsed by LlamaParse", "resume-parser")
                return None
                
        except Exception as e:
            log_error(f"LlamaParse error: {e}", "resume-parser")
            return None
    

    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type for file"""
        if filename.endswith('.pdf'):
            return 'application/pdf'
        elif filename.endswith('.docx'):
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            return 'text/plain'
    
    def _extract_field(self, text: str, keywords: list) -> str:
        """Simple field extraction from text"""
        lines = text.lower().split('\n')
        for line in lines:
            for keyword in keywords:
                if keyword in line:
                    # Extract content after the keyword
                    parts = line.split(keyword)
                    if len(parts) > 1:
                        return parts[1].strip(' :').strip()
        return ''
    
    def _clean_json_response(self, content: str) -> str:
        """Clean JSON response from AI models"""
        # Remove markdown code blocks
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        
        # Remove extra whitespace and newlines
        content = content.strip()
        
        # Fix common JSON issues
        content = content.replace('\n', ' ').replace('\r', ' ')
        content = ' '.join(content.split())  # Normalize whitespace
        
        return content
    
    def _validate_parsed_data(self, data: dict) -> bool:
        """Validate that parsed data has required structure"""
        required_fields = ['Full Name', 'Email', 'Phone Number']
        
        if not isinstance(data, dict):
            return False
            
        # Check if at least one required field has data
        for field in required_fields:
            if field in data and data[field] and str(data[field]).strip():
                return True
                
        return False