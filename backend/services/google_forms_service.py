import os
import json
import requests
import re
from urllib.parse import quote
from ..logger import log_error
from llama_index.llms.openrouter import OpenRouter

class GoogleFormsService:
    ALL_DATA_FIELDS = "FB_PUBLIC_LOAD_DATA_"
    
    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        # Ensure llm attribute exists even if API key missing
        self.llm = None
        self.form_data = None
        self.entries = None
        
        # Initialize OpenRouter LLM for field mapping
        if self.openrouter_key:
            self.llm = OpenRouter(
                api_key=self.openrouter_key,
                model="mistralai/mistral-7b-instruct:free",
                max_tokens=1000,
                temperature=0.1
            )
        

    
    def extract_form_id(self, form_url: str) -> str:
        """Extract form ID from Google Forms URL"""
        try:
            if '/forms/d/e/' in form_url:
                form_id = form_url.split('/forms/d/e/')[1].split('/')[0]
                return form_id
            elif '/forms/d/' in form_url:
                form_id = form_url.split('/forms/d/')[1].split('/')[0]
                return form_id
            else:
                raise ValueError("Invalid Google Forms URL")
        except Exception as e:
            log_error(f"Failed to extract form ID: {e}", "google-forms")
            return None
    
    async def get_form_structure(self, form_url: str) -> dict:
        """Get form structure"""
        form_id = self.extract_form_id(form_url)
        return {"fields": self._get_default_fields(), "form_id": form_id}
    

    
    def _get_default_fields(self) -> list:
        """Return default form fields"""
        return [
            {"type": "text", "label": "Name"},
            {"type": "email", "label": "Email"},
            {"type": "text", "label": "Phone"},
            {"type": "textarea", "label": "Skills"},
            {"type": "text", "label": "Education"}
        ]
    
    async def submit_form_response(self, form_url: str, resume_data: dict) -> dict:
        """Submit form response using reference repo approach"""
        try:
            # Parse form entries from the URL
            entries = self._parse_form_entries(form_url)
            if not entries:
                return {"success": False, "error": "Could not parse form entries"}
            
            # Fill entries with resume data
            filled_data = self._fill_entries_with_resume_data(entries, resume_data)
            
            # Submit the form
            submit_result = self._submit_form(form_url, filled_data)

            # If _submit_form returns a dict with details, merge it into response
            if isinstance(submit_result, dict):
                submit_ok = submit_result.get('ok', False)
            else:
                submit_ok = bool(submit_result)

            response = {
                "success": submit_ok,
                "filled_fields": [f"{k}: {str(v)[:200]}" for k, v in filled_data.items()],
                "filled_data": filled_data
            }

            if submit_ok:
                response["message"] = f"Form submitted successfully with {len(filled_data)} fields"
            else:
                # attach submit_result details for debugging
                response["error"] = "Form submission failed"
                if isinstance(submit_result, dict):
                    response.update({k: submit_result[k] for k in submit_result if k not in response})

            return response
                    
        except Exception as e:
            log_error(f"Form submission failed: {e}", "google-forms")
            return {"success": False, "error": str(e)}
    

    
    def _get_form_response_url(self, url: str) -> str:
        """Convert form URL to form response URL"""
        url = url.replace('/viewform', '/formResponse')
        if not url.endswith('/formResponse'):
            if not url.endswith('/'):
                url += '/'
            url += 'formResponse'
        return url
    
    def _extract_script_variables(self, name: str, html: str):
        """Extract a JavaScript variable (JSON) from page HTML.

        Handles both `var NAME = ...;` and more modern inline assignments where
        the JSON may be large and include nested arrays/objects. Attempts a
        regex first, then a bracket-matching fallback if needed.
        """
        # Try a simple regex first
        try:
            pattern = re.compile(r'var\s+' + re.escape(name) + r'\s*=\s*(\[.*?\]);', re.S)
            match = pattern.search(html)
            if match:
                value_str = match.group(1)
                return json.loads(value_str)
        except Exception:
            pass

        # Fallback: locate the name and extract the JSON starting at the first '['
        idx = html.find(name)
        if idx == -1:
            return None

        # Find the '=' after the name
        eq = html.find('=', idx)
        if eq == -1:
            return None

        # Find the first '[' after '=' and then extract balanced JSON until matching bracket
        start = html.find('[', eq)
        if start == -1:
            return None

        i = start
        depth = 0
        while i < len(html):
            ch = html[i]
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    # try to capture up to this index
                    candidate = html[start:i+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        # if parsing fails, continue scanning until we find a valid JSON
                        pass
            i += 1

        return None
    
    def _get_fb_public_load_data(self, url: str):
        """Get form data from a Google form URL"""
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log_error(f"Can't get form data: {response.status_code}", "google-forms")
            return None
        return self._extract_script_variables(self.ALL_DATA_FIELDS, response.text)
    
    def _parse_form_entries(self, url: str):
        """Parse the form entries and return a list of entries"""
        self.form_data = self._get_fb_public_load_data(url)
        
        if not self.form_data or not self.form_data[1] or not self.form_data[1][1]:
            log_error("Can't get form entries", "google-forms")
            return None
        
        parsed_entries = []
        for entry in self.form_data[1][1]:
            if entry[3] == 8:  # Skip session type entries
                continue
            
            entry_name = entry[1]
            for sub_entry in entry[4]:
                info = {
                    "id": sub_entry[0],
                    "name": entry_name,
                    "type": entry[3],
                    "required": sub_entry[2] == 1,
                    "options": [x[0] for x in sub_entry[1]] if sub_entry[1] else None,
                }
                parsed_entries.append(info)
        
        return parsed_entries
    
    def _fill_entries_with_resume_data(self, entries, resume_data):
        """Map resume fields to Google Form entry IDs using label heuristics.

        Tries multiple candidate keys and falls back to raw_text snippets when
        a direct mapping isn't found. Returns a dict suitable for posting to
        the Google Forms `formResponse` endpoint: keys like `entry.12345`.
        """
        def get_value(candidates):
            for k in candidates:
                if not k:
                    continue
                v = resume_data.get(k)
                if v:
                    return v
            return ''

        filled_data = {}
        raw_text = resume_data.get('raw_text', '') or ''

        for entry in entries:
            entry_id = f"entry.{entry['id']}"
            entry_name = (entry.get('name') or '').lower()
            value = ''

            if any(word in entry_name for word in ['name', 'full name']):
                value = get_value(['Full Name', 'name'])
            elif any(word in entry_name for word in ['email', 'mail']):
                value = get_value(['Email', 'email'])
            elif any(word in entry_name for word in ['phone', 'mobile', 'contact']):
                value = get_value(['Phone Number', 'Phone', 'phone'])
            elif any(word in entry_name for word in ['address', 'location']):
                value = get_value(['Address', 'address'])
            elif any(word in entry_name for word in ['skill', 'technology']):
                skills = get_value(['Skills', 'skills'])
                if isinstance(skills, list):
                    value = ', '.join(skills)
                else:
                    value = skills
            elif any(word in entry_name for word in ['education', 'degree', 'university', 'college']):
                edu = get_value(['Education', 'education'])
                if isinstance(edu, list):
                    value = '; '.join(edu)
                else:
                    value = edu
            elif any(word in entry_name for word in ['experience', 'work', 'job', 'company', 'role', 'position']):
                exp = get_value(['Work Experience', 'work_experience', 'experience'])
                if isinstance(exp, list):
                    value = '; '.join(exp)
                else:
                    value = exp
            else:
                # Try direct keys that match the label
                cand = resume_data.get(entry.get('name')) or resume_data.get(entry.get('name').title()) if entry.get('name') else None
                value = cand or ''

            # Final fallback: find a short line in raw_text containing a keyword from the label
            if not value and raw_text:
                import re as _re
                for word in _re.findall(r"[a-zA-Z]{3,}", entry_name):
                    m = _re.search(r"^.*?%s.*$" % _re.escape(word), raw_text, _re.I | _re.M)
                    if m:
                        snippet = m.group(0).strip()
                        if len(snippet) < 500:
                            value = snippet
                            break

            if isinstance(value, list):
                value = ', '.join(value)

            filled_data[entry_id] = str(value or '')

        return filled_data
    
    def _submit_form(self, url: str, data: dict) -> bool:
        """Submit the form with data"""
        submit_url = self._get_form_response_url(url)
        try:
            # Use a session and include a Referer header — some forms validate it
            session = requests.Session()
            headers = {"Referer": url, "User-Agent": "Mozilla/5.0 (compatible)"}
            response = session.post(submit_url, data=data, headers=headers, timeout=15, allow_redirects=True)

            # Treat 200 and 302 (redirect) as success; otherwise return details
            if response.status_code in (200, 302):
                return True

            # Not a success — log status and a snippet of the response for debugging
            snippet = ''
            try:
                snippet = response.text[:2000]
            except Exception:
                snippet = '<non-text response>'

            log_error(f"Form submission failed with status {response.status_code}: {snippet}", "google-forms")
            return {"ok": False, "status_code": response.status_code, "response_snippet": snippet}

        except Exception as e:
            log_error(f"Form submission error: {e}", "google-forms")
            return {"ok": False, "error": str(e)}
    
    def _map_question_to_resume(self, title: str, resume_data: dict) -> str:
        """Map form question to resume data"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['name', 'full name']):
            return resume_data.get('Full Name', '')
        elif any(word in title_lower for word in ['email', 'mail']):
            return resume_data.get('Email', '')
        elif any(word in title_lower for word in ['phone', 'mobile', 'contact']):
            return resume_data.get('Phone Number', '')
        elif any(word in title_lower for word in ['skill', 'technology']):
            return resume_data.get('Skills', '')
        elif any(word in title_lower for word in ['education', 'degree']):
            return resume_data.get('Education', '')
        elif any(word in title_lower for word in ['experience', 'work', 'job']):
            return resume_data.get('Work Experience', '')
        
        return ''
    
