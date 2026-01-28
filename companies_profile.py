import os
import requests
import json
import time
from pathlib import Path

class CorporateProfileGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Priority list of models. 
        # 1.5 Flash is fast and stable. 2.0 Flash is the latest experimental.
        self.models = [
            "gemini-2.5-flash"
        ]
        self.working_model = None

    def find_working_model(self):
        """Test which model works with the current API key"""
        print("🔍 Testing API connection and models...")
        
        headers = {'Content-Type': 'application/json'}
        test_data = {
            "contents": [{"parts": [{"text": "Return the word 'OK'"}]}],
            "generationConfig": {"maxOutputTokens": 10}
        }

        for model in self.models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                print(f"  ... Testing {model} ...", end=" ")
                response = requests.post(f"{url}?key={self.api_key}", headers=headers, json=test_data)
                
                if response.status_code == 200:
                    print("✅ WORKS!")
                    self.working_model = model
                    return url
                elif response.status_code == 404:
                    print("❌ Not Found (404)")
                elif response.status_code == 429:
                    print("⚠️ Rate Limited (429)")
                else:
                    print(f"❌ Error {response.status_code}")
            except Exception as e:
                print(f"Error: {e}")

        return None

    def query_gemini(self, prompt):
        """Query the Gemini API with automatic model selection and retry logic."""
        if not self.working_model:
            base_url = self.find_working_model()
            if not base_url:
                return None
        else:
            base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.working_model}:generateContent"

        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.8, # Slightly higher for more creative/realistic fiction
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 4096,
                "response_mime_type": "application/json" # Forces JSON mode where supported
            }
        }
        
        for attempt in range(3):
            try:
                response = requests.post(f"{base_url}?key={self.api_key}", headers=headers, json=data)
                
                if response.status_code == 200:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                elif response.status_code == 429:
                    print(f"  ⚠️ Rate limit. Waiting 20s (Attempt {attempt+1}/3)...")
                    time.sleep(20)
                else:
                    print(f"  ❌ API Error {response.status_code}: {response.text}")
                    return None
            except Exception as e:
                print(f"  ❌ Exception: {e}")
                return None
        
        return None
    
    def generate_company_info(self, company_name, required_fields):
        """
        Generates company data specifically for the fields requested by the HTML template.
        """
        fields_list_str = "\n".join([f"- {f}" for f in required_fields])
        
        prompt = f"""
        Generate a comprehensive, realistic but fictional corporate profile for a company named '{company_name}'.
        The output must be a single JSON object.
        
        Include exactly these JSON keys:
        {fields_list_str}
        
        Guidelines:
        - Information must be realistic enough for training scenarios.
        - For address fields, provide full plausible addresses.
        - For lists (like key_technologies or aliases), provide 3-5 items.
        - If you cannot find real data, invent realistic details consistent with the company's industry.
        - Return ONLY the JSON object.
        """
        
        result = self.query_gemini(prompt)
        if result:
            try:
                # Basic cleaning in case model returns markdown code blocks
                clean_json = result.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                
                start_idx = clean_json.find('{')
                end_idx = clean_json.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    return json.loads(clean_json[start_idx:end_idx])
            except Exception as e:
                print(f"  ❌ JSON Parsing Error: {e}")
                print(f"  Raw Result: {result[:100]}...")
        return None
    
    def process_company(self, company_name, required_fields, output_dir="output"):
        """
        Handles the end-to-end generation for a single company and saves to disk.
        """
        print(f"Processing {company_name}...")
        Path(output_dir).mkdir(exist_ok=True)
        
        info = self.generate_company_info(company_name, required_fields)
        if info:
            # Create a filename-safe version of the company name
            safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            fname = Path(output_dir) / f"{safe_name}_data.json"
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2)
            
            return True, fname
        else:
            return False, None