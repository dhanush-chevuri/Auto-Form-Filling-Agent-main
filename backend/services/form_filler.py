from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import re
import json
import os
from ..logger import log_error
from llama_index.llms.openrouter import OpenRouter

class FormFiller:
    def __init__(self):
        self.driver = None
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        # Ensure llm attribute exists even if API key missing
        self.llm = None
        
        # Initialize OpenRouter LLM
        if self.openrouter_key:
            self.llm = OpenRouter(
                api_key=self.openrouter_key,
                model="mistralai/mistral-7b-instruct:free",
                max_tokens=1000,
                temperature=0.1
            )
    
    async def fill_form(self, form_url: str, resume_data: dict, form_fields: dict) -> dict:
        try:
            self._setup_driver()
            self.driver.get(form_url)
            
            filled_fields = []
            
            # Wait for form to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # Increased wait for Google Forms to fully load
            
            # Wait for form inputs to be ready
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input | //textarea"))
                )
            except:
                pass  # Continue even if no inputs found immediately
            
            # Handle case where resume_data might be a coroutine
            if hasattr(resume_data, 'keys'):
                print(f"Resume data keys: {list(resume_data.keys())}")
            else:
                print(f"Resume data type: {type(resume_data)}")
                print(f"Resume data: {resume_data}")
            print(f"Form fields count: {len(form_fields.get('fields', []))}")
            print(f"Page title: {self.driver.title}")
            
            # Debug resume data
            print(f"Resume data received: {resume_data}")
            print(f"Resume data type: {type(resume_data)}")
            
            # Use AI-powered form filling
            if isinstance(resume_data, dict) and resume_data:
                filled_fields = await self._fill_form_with_ai(resume_data, form_fields)
            else:
                log_error(f"Invalid or empty resume_data: {resume_data}", "form-filler")
                filled_fields = []
            
            # Submit the form after filling
            print(f"Form filling completed. Filled {len(filled_fields)} fields.")
            print(f"Filled fields: {filled_fields}")
            
            if filled_fields:  # Only submit if we filled something
                time.sleep(2)  # Wait before submission
                submission_success = self._attempt_form_submission()
                if submission_success:
                    print("Form submitted successfully!")
                else:
                    print("Form submission failed or no submit button found")
            
            return {
                "success": True,
                "filled_fields": filled_fields,
                "message": f"Successfully filled {len(filled_fields)} fields"
            }
            
        except Exception as e:
            log_error(f"Form filling failed: {e}", "form-filler")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if self.driver:
                self.driver.quit()
    
    def _setup_driver(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.set_window_size(1920, 1080)
    
    def _fill_field(self, field: dict, resume_data: dict) -> bool:
        try:
            label = field['label'].lower()
            field_type = field['type']
            
            # Determine what data to fill based on field label
            value = self._get_value_for_field(label, resume_data)
            
            if not value:
                print(f"No value found for field: {field['label']}")
                return False
            
            # Find the input element
            input_element = self._find_input_element(field)
            
            if not input_element:
                print(f"No input element found for field: {field['label']}")
                return False
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", input_element)
            time.sleep(0.5)
            
            # Fill based on field type
            if field_type in ['text', 'email', 'phone', 'textarea']:
                input_element.click()
                time.sleep(0.5)
                input_element.clear()
                time.sleep(0.5)
                input_element.send_keys(str(value))
                time.sleep(0.5)
                # Trigger events to ensure Google Forms registers the input
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", input_element)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", input_element)
                self.driver.execute_script("arguments[0].blur();", input_element)
                print(f"Filled field '{field['label']}' with: {value}")
            elif field_type == 'radio':
                self._select_radio_option(field, value)
            elif field_type == 'checkbox':
                self._select_checkbox_options(field, value)
            
            return True
            
        except Exception as e:
            print(f"Error filling field {field['label']}: {e}")
            return False
    
    def _get_value_for_field(self, label: str, resume_data: dict) -> str:
        label_lower = label.lower()
        
        # More comprehensive field matching
        if any(word in label_lower for word in ['name', 'full name', 'your name']):
            return resume_data.get('Full Name', '')
        elif any(word in label_lower for word in ['email', 'e-mail', 'mail']):
            return resume_data.get('Email', '')
        elif any(word in label_lower for word in ['phone', 'mobile', 'contact', 'number']):
            return resume_data.get('Phone Number', '')
        elif any(word in label_lower for word in ['address', 'location', 'city']):
            return resume_data.get('Address', '')
        elif any(word in label_lower for word in ['education', 'degree', 'school', 'university']):
            return self._format_education(resume_data.get('Education', []))
        elif any(word in label_lower for word in ['experience', 'work', 'job', 'employment']):
            return self._format_experience(resume_data.get('Work Experience', []))
        elif any(word in label_lower for word in ['skill', 'abilities', 'competencies']):
            return self._format_skills(resume_data.get('Skills', []))
        elif any(word in label_lower for word in ['certification', 'certificate', 'license']):
            certs = resume_data.get('Certifications', [])
            return ', '.join(certs) if isinstance(certs, list) else str(certs)
        
        # Fallback - return first available data
        for key, value in resume_data.items():
            if value and key != 'raw_content' and key != 'error':
                return str(value)
        
        return ''
    
    def _find_input_element(self, field: dict):
        try:
            label = field['label']
            
            # Updated selectors for current Google Forms structure
            selectors = [
                f"//span[contains(text(), '{label}')]/ancestor::div[contains(@class, 'Qr7Oae')]//input",
                f"//span[contains(text(), '{label}')]/ancestor::div[contains(@class, 'Qr7Oae')]//textarea",
                f"//div[contains(@class, 'M7eMe') and contains(text(), '{label}')]/following::input[1]",
                f"//div[contains(@class, 'M7eMe') and contains(text(), '{label}')]/following::textarea[1]",
                "//input[@type='text']",
                "//input[@type='email']",
                "//textarea"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            return element
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"Error finding element: {e}")
            return None
    
    def _select_radio_option(self, field: dict, value: str):
        # Implementation for radio button selection
        pass
    
    def _select_checkbox_options(self, field: dict, value: str):
        # Implementation for checkbox selection
        pass
    
    def _format_education(self, education: list) -> str:
        if isinstance(education, list) and education:
            return "; ".join([f"{edu.get('degree', '')} from {edu.get('institution', '')}" for edu in education])
        return str(education) if education else ''
    
    def _format_experience(self, experience: list) -> str:
        if isinstance(experience, list) and experience:
            return "; ".join([f"{exp.get('position', '')} at {exp.get('company', '')}" for exp in experience])
        return str(experience) if experience else ''
    
    def _format_skills(self, skills: list) -> str:
        if isinstance(skills, list):
            return ", ".join(skills)
        return str(skills) if skills else ''
    
    async def _fill_form_with_ai(self, resume_data: dict, form_fields: dict) -> list:
        """AI-powered form filling using LLM for field mapping"""
        filled_fields = []
        
        try:
            # Wait for form to be interactive
            time.sleep(3)
            
            # Find all form elements
            form_elements = self._find_all_form_elements()
            print(f"Found {len(form_elements)} form elements")
            
            # Get field contexts for AI analysis
            field_contexts = []
            for i, element in enumerate(form_elements):
                if element.is_displayed() and element.is_enabled():
                    context = self._get_field_context(element)
                    field_contexts.append({
                        'index': i,
                        'context': context,
                        'element': element
                    })
            
            # Use AI to map fields to resume data
            field_mappings = await self._get_ai_field_mappings(field_contexts, resume_data, form_fields)
            
            # Fill fields based on AI mappings
            for mapping in field_mappings:
                try:
                    element = mapping['element']
                    value = mapping['value']
                    field_name = mapping['field_name']
                    
                    if value and value.strip():
                        success = self._fill_element_safely(element, value)
                        if success:
                            filled_fields.append(f"{field_name}: {value[:50]}...")
                            print(f"AI-filled '{field_name}' with: {value[:50]}...")
                            
                except Exception as e:
                    print(f"Error filling AI-mapped field: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in AI form filling: {e}")
            
        return filled_fields
    
    def _find_all_form_elements(self):
        """Find all fillable form elements in Google Forms"""
        selectors = [
            "//input[@type='text']",
            "//input[@type='email']", 
            "//input[@type='tel']",
            "//input[@type='url']",
            "//input[not(@type) or @type='']",
            "//textarea",
            "//div[@role='textbox']",
            "//div[@contenteditable='true']",
            "//input[contains(@class, 'whsOnd')]",  # Google Forms input class
            "//textarea[contains(@class, 'KHxj8b')]",  # Google Forms textarea class
            "//div[contains(@class, 'quantumWizTextinputPaperinputInput')]"
        ]
        
        elements = []
        for selector in selectors:
            try:
                found = self.driver.find_elements(By.XPATH, selector)
                elements.extend(found)
            except:
                continue
                
        return elements
    
    def _get_field_context(self, element):
        """Get context about the field for smart filling"""
        try:
            label_text = ""
            
            # Method 1: aria-label
            if element.get_attribute("aria-label"):
                label_text = element.get_attribute("aria-label")
            
            # Method 2: aria-describedby
            elif element.get_attribute("aria-describedby"):
                desc_id = element.get_attribute("aria-describedby")
                try:
                    desc_element = self.driver.find_element(By.ID, desc_id)
                    label_text = desc_element.text
                except:
                    pass
            
            # Method 3: Google Forms specific - find question text
            if not label_text:
                try:
                    # Look for question container
                    question_container = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'Qr7Oae')]")
                    question_text = question_container.find_element(By.XPATH, ".//span[contains(@class, 'M7eMe')]").text
                    label_text = question_text
                except:
                    pass
            
            # Method 4: placeholder
            if not label_text and element.get_attribute("placeholder"):
                label_text = element.get_attribute("placeholder")
            
            # Method 5: nearby text in parent
            if not label_text:
                try:
                    parent = element.find_element(By.XPATH, "./ancestor::div[2]")
                    label_text = parent.text.strip().split('\n')[0]  # Get first line
                except:
                    label_text = "unknown"
            
            return label_text.lower() if label_text else "unknown"
            
        except:
            return "unknown"
    
    def _fallback_field_mapping(self, field_contexts: list, resume_data: dict) -> list:
        """Fallback mapping when AI fails"""
        mappings = []
        data_map = {
            'name': resume_data.get('Full Name', ''),
            'email': resume_data.get('Email', ''),
            'phone': resume_data.get('Phone Number', ''),
            'address': resume_data.get('Address', ''),
            'education': str(resume_data.get('Education', '')),
            'experience': str(resume_data.get('Work Experience', '')),
            'skills': str(resume_data.get('Skills', ''))
        }
        
        for field in field_contexts:
            context = field['context'].lower()
            value = ''
            field_name = context
            
            # Simple pattern matching as fallback
            if any(word in context for word in ['name', 'full name']):
                value = data_map['name']
                field_name = 'Name'
            elif any(word in context for word in ['email', 'mail']):
                value = data_map['email']
                field_name = 'Email'
            elif any(word in context for word in ['phone', 'mobile', 'contact']):
                value = data_map['phone']
                field_name = 'Phone'
            elif any(word in context for word in ['skill', 'technology']):
                value = data_map['skills']
                field_name = 'Skills'
            elif any(word in context for word in ['education', 'degree']):
                value = data_map['education']
                field_name = 'Education'
            elif any(word in context for word in ['experience', 'work', 'job']):
                value = data_map['experience']
                field_name = 'Experience'
            
            if value and str(value).strip():
                mappings.append({
                    'element': field['element'],
                    'field_name': field_name,
                    'value': str(value),
                    'confidence': 0.8
                })
        
        return mappings
    
    async def _get_ai_field_mappings(self, field_contexts: list, resume_data: dict, form_fields: dict) -> list:
        """Use AI to intelligently map form fields to resume data"""
        try:
            # Prepare context for AI
            fields_info = []
            for field in field_contexts:
                fields_info.append({
                    'index': field['index'],
                    'context': field['context'],
                    'type': 'text'  # Default type
                })
            
            # Add form field information if available
            if form_fields.get('fields'):
                for i, form_field in enumerate(form_fields['fields']):
                    if i < len(fields_info):
                        fields_info[i]['label'] = form_field.get('label', '')
                        fields_info[i]['type'] = form_field.get('type', 'text')
            
            prompt = f"""
You are an AI assistant that maps form fields to resume data. 

Resume Data:
{json.dumps(resume_data, indent=2)}

Form Fields:
{json.dumps(fields_info, indent=2)}

For each form field, determine the best matching resume data value. Return a JSON array with mappings:

[
  {{
    "field_index": 0,
    "field_name": "Name",
    "resume_key": "Full Name",
    "value": "extracted value",
    "confidence": 0.9
  }}
]

Rules:
- Only include mappings with confidence > 0.7
- Use exact values from resume data
- Match field context/label to appropriate resume data
- Return valid JSON only
"""
            
            # Use OpenRouter LLM
            if not self.llm:
                print("OpenRouter LLM not initialized")
                return self._fallback_field_mapping(field_contexts, resume_data)
            
            try:
                response = await self.llm.acomplete(prompt)
                content = str(response)
                
                # Clean and parse JSON
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                
                ai_mappings = json.loads(content.strip())
                print(f"AI generated {len(ai_mappings)} field mappings")
                
                # Convert AI mappings to element mappings
                element_mappings = []
                for mapping in ai_mappings:
                    field_index = mapping.get('field_index', -1)
                    if 0 <= field_index < len(field_contexts):
                        element_mappings.append({
                            'element': field_contexts[field_index]['element'],
                            'field_name': mapping.get('field_name', f'Field {field_index}'),
                            'value': mapping.get('value', ''),
                            'confidence': mapping.get('confidence', 0.0)
                        })
                
                return element_mappings
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse AI response: {e}")
                print(f"Raw content: {content}")
            except Exception as e:
                print(f"OpenRouter LLM error: {e}")
        except Exception as e:
            print(f"Error in AI field mapping: {e}")
        
        # Fallback to simple mapping if AI fails
        return self._fallback_field_mapping(field_contexts, resume_data)
    
    def _fill_element_safely(self, element, value):
        """Safely fill element with proper events"""
        try:
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # Focus on element with multiple methods
            try:
                element.click()
            except:
                self.driver.execute_script("arguments[0].focus();", element)
            time.sleep(0.3)
            
            # Clear existing content with multiple methods
            try:
                element.clear()
            except:
                pass
            
            # Select all and delete
            try:
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.DELETE)
            except:
                pass
            
            time.sleep(0.2)
            
            # Type the value character by character for better compatibility
            for char in str(value):
                element.send_keys(char)
                time.sleep(0.01)  # Small delay between characters
            
            time.sleep(0.3)
            
            # Trigger comprehensive events for Google Forms
            self.driver.execute_script("""
                var element = arguments[0];
                element.dispatchEvent(new Event('focus', {bubbles: true}));
                element.dispatchEvent(new Event('input', {bubbles: true}));
                element.dispatchEvent(new Event('change', {bubbles: true}));
                element.dispatchEvent(new Event('blur', {bubbles: true}));
                
                // Google Forms specific events
                element.dispatchEvent(new Event('keyup', {bubbles: true}));
                element.dispatchEvent(new Event('keydown', {bubbles: true}));
            """, element)
            
            time.sleep(0.3)
            
            # Verify the value was set
            current_value = element.get_attribute('value') or element.text
            if current_value and str(value) in current_value:
                print(f"Successfully filled field with: {value[:50]}...")
                return True
            else:
                print(f"Value verification failed. Expected: {value[:50]}, Got: {current_value}")
                return False
            
        except Exception as e:
            print(f"Error filling element: {e}")
            return False
    
    def _attempt_form_submission(self):
        """Attempt to submit the form automatically"""
        try:
            # Look for submit button with Google Forms specific selectors
            submit_selectors = [
                "//span[contains(text(), 'Submit')]/ancestor::div[@role='button']",
                "//div[@role='button']//span[contains(text(), 'Submit')]",
                "//div[contains(@class, 'freebirdFormviewerViewNavigationSubmitButton')]",
                "//div[contains(@class, 'uArJ5e UQuaGc Y5sE8d VkkpIf NqnGTe')]",  # Google Forms submit button class
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Send')]"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, selector)
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                        time.sleep(1)
                        
                        # Try clicking with JavaScript first
                        self.driver.execute_script("arguments[0].click();", submit_btn)
                        print("Form submitted successfully with JavaScript")
                        time.sleep(3)
                        return True
                except:
                    continue
            
            print("No submit button found")
            return False
            
        except Exception as e:
            print(f"Error submitting form: {e}")
            return False