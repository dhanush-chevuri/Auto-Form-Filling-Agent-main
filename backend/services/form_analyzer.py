import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
from ..logger import log_form_fields, log_error
from llama_index.llms.openrouter import OpenRouter

class FormAnalyzer:
    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        # Ensure llm attribute exists even if API key missing
        self.llm = None
        
        # Initialize OpenRouter LLM
        if self.openrouter_key:
            self.llm = OpenRouter(
                api_key=self.openrouter_key,
                model="mistralai/mistral-7b-instruct:free",
                max_tokens=500,
                temperature=0.1
            )
    
    async def analyze_google_form(self, form_url: str) -> dict:
        try:
            html_content = await self._get_form_html(form_url)
            form_fields = self._extract_form_fields(html_content)
            
            # Use AI to analyze and enhance field mappings
            if form_fields and self.llm:
                ai_analysis = await self._analyze_fields_with_ai(form_fields)
                result = {"fields": form_fields, "mappings": ai_analysis.get('mappings', {})}
            else:
                result = {"fields": form_fields, "mappings": {}}
            
            log_form_fields(result)
            return result
        except Exception as e:
            log_error(f"Form analysis failed: {e}", "form-analyzer")
            return {"fields": [], "mappings": {}}
    
    async def _get_form_html(self, url: str) -> str:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.get(url)
            
            # Wait for dynamic content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # Additional wait for Google Forms to fully load
            
            return driver.page_source
        finally:
            driver.quit()
    
    def _extract_form_fields(self, html: str) -> list:
        soup = BeautifulSoup(html, 'html.parser')
        fields = []
        
        # Updated Google Forms selectors
        selectors = [
            {'class': lambda x: x and 'Qr7Oae' in x},  # Current Google Forms question container
            {'class': lambda x: x and 'freebirdFormviewerViewItemsItemItem' in x},  # Legacy selector
        ]
        
        questions = []
        for selector in selectors:
            questions.extend(soup.find_all(['div'], class_=selector['class']))
        
        # If no questions found, try generic approach
        if not questions:
            # Look for any input fields
            inputs = soup.find_all(['input', 'textarea'])
            for i, inp in enumerate(inputs):
                if inp.get('type') not in ['hidden', 'submit', 'button']:
                    field_info = {
                        'type': inp.get('type', 'text'),
                        'label': f'Field {i+1}',
                        'required': False,
                        'options': []
                    }
                    fields.append(field_info)
            return fields
        
        for question in questions:
            field_info = {
                'type': 'text',
                'label': '',
                'required': False,
                'options': []
            }
            
            # Extract question text - try multiple selectors
            label_selectors = [
                lambda x: x and 'M7eMe' in x,  # Current title class
                lambda x: x and 'freebirdFormviewerViewItemsItemItemTitle' in x,  # Legacy
            ]
            
            label_elem = None
            for selector in label_selectors:
                label_elem = question.find(['span', 'div'], class_=selector)
                if label_elem:
                    break
            
            if label_elem:
                field_info['label'] = label_elem.get_text(strip=True)
            
            # Check if required
            required_elem = question.find(['span'], class_=lambda x: x and 'required' in str(x).lower())
            field_info['required'] = required_elem is not None
            
            # Determine field type
            if question.find(['input'], type='email'):
                field_info['type'] = 'email'
            elif question.find(['input'], type='tel'):
                field_info['type'] = 'phone'
            elif question.find(['textarea']):
                field_info['type'] = 'textarea'
            elif question.find(['input'], type='radio'):
                field_info['type'] = 'radio'
            elif question.find(['input'], type='checkbox'):
                field_info['type'] = 'checkbox'
            
            if field_info['label'] or field_info['type'] != 'text':
                fields.append(field_info)
        
        return fields
    
    async def _analyze_fields_with_ai(self, fields: list) -> dict:
        """Analyze form fields using OpenRouter LLM"""
        prompt = f"""
Analyze these form fields and map them to resume data categories:
{json.dumps(fields, indent=2)}

Map each field to one of these categories:
- name, email, phone, address, education, experience, skills, certifications, other

Return JSON with field mappings.
"""
        
        try:
            response = await self.llm.acomplete(prompt)
            content = str(response)
            
            # Clean and parse JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            return json.loads(content.strip())
            
        except Exception as e:
            log_error(f"AI field analysis failed: {e}", "form-analyzer")
            return {"fields": fields, "mappings": {}}