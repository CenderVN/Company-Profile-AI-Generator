import json
import re
from pathlib import Path
from string import Template
from datetime import datetime

class HtmlProfileGenerator:
    # Variables that the Python script handles automatically. 
    # The AI does NOT need to provide these.
    SYSTEM_VARIABLES = {
        'timestamp', 
        'case_number', 
        'logo_filename'
    }

    def __init__(self, template_path="templates/profile_template.html"):
        self.template_path = Path(template_path)
        self.set_template(template_path)

    def set_template(self, template_path):
        """Allows switching templates dynamically and verifies existence."""
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            print(f"⚠️ Warning: Template file {template_path} not found.")

    def get_template_variables(self):
        """
        Scans the HTML template for placeholders like ${variable_name}.
        Returns a list of unique keys that the AI should generate.
        """
        if not self.template_path.exists():
            return []

        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all patterns matching ${identifier}
            pattern = r'\$\{([a-zA-Z0-9_]+)\}'
            found_vars = re.findall(pattern, content)

            # Convert to set to remove duplicates, then subtract system variables
            ai_required_vars = set(found_vars) - self.SYSTEM_VARIABLES
            
            return sorted(list(ai_required_vars))
        except Exception as e:
            print(f"❌ Error scanning template for variables: {e}")
            return []

    def _format_value(self, value):
        """Helper to clean up AI data (lists, dicts) for clean HTML display."""
        if isinstance(value, list):
            return ", ".join(self._format_value(i) for i in value)
        elif isinstance(value, dict):
            return ", ".join(str(v) for v in value.values() if v)
        elif value is None:
            return "N/A"
        return str(value)

    def generate_html_content(self, company_info):
        """
        Merges company data into the HTML template.
        'company_info' should be a dictionary of key-value pairs.
        """
        # 1. Prepare system-calculated values
        context = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'case_number': f"OP-D-V-{datetime.now().strftime('%H%M')}",
        }

        # 2. Add AI-generated values and format them
        if isinstance(company_info, dict):
            for key, value in company_info.items():
                context[key] = self._format_value(value)

        # 3. Perform the substitution
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_str = f.read()
            
            src = Template(template_str)
            # safe_substitute prevents crashing if a variable is missing
            return src.safe_substitute(context)
            
        except Exception as e:
            return f"<h1>Error generating profile</h1><p>Template: {self.template_path}<br>Error: {e}</p>"