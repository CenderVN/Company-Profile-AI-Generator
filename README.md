# 🏢 Company Profile AI Generator

An automated pipeline that generates professional corporate dossiers. By scanning custom HTML templates for variables, the app uses **Google Gemini AI** to gather company data, scrapes logos from the web, and renders high-quality, print-ready PDFs.

### 🌟 Key Feature: "Template-Agnostic"
Unlike other generators, this tool doesn't have a fixed list of fields. 
1. It **scans your HTML template** for placeholders like `${ceo_name}` or `${sustainability_score}`.
2. It automatically **tells the AI** to find information for exactly those fields.
3. No code changes are required to add new data points—just edit your HTML.

---

## 🛠 Prerequisites

1.  **Python 3.10+** installed on your system.
2.  **Gemini API Key:** Obtain a free key from [Google AI Studio](https://aistudio.google.com/).
3.  **System Dependencies (Required for PDF Rendering):**
    The app uses **WeasyPrint**, which requires certain system libraries to handle fonts and layouts.
    *   **Windows:** Install the [GTK3 Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases).
    *   **macOS:** `brew install pango libffi`
    *   **Linux:** `sudo apt install shared-mime-info`

---

## 🚀 Guide to Run

### 1. Clone the Repository
```bash
git clone https://github.com/CenderVN/Company-Profile-AI-Generator.git
cd Company-Profile-AI-Generator
```

### 2. Install Python Dependencies
It is recommended to use a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install qtpy requests beautifulsoup4 weasyprint
```

### 3. Setup Templates
The app looks for HTML files in a folder named `templates`.
*   Ensure a folder named `templates/` exists in the root directory.
*   Place your `.html` files (like the provided `profile_template.html`) inside that folder.

### 4. Launch the Application
```bash
python app_ui.py
```

---

## 📖 How to Use

1.  **Select Template:** Use the dropdown menu to choose which HTML design you want to use.
2.  **API Key:** Paste your Google Gemini API Key into the configuration box.
3.  **Target Companies:** List the companies you want to research (one per line).
4.  **Output Folder:** Choose where you want the final JSON, HTML, and PDF files to be saved.
5.  **Start:** Click **"🚀 Start Generation Pipeline"**.

### What happens behind the scenes?
*   **Phase 0:** The app "reads" your HTML to see what variables you used.
*   **Phase 1:** Gemini AI generates a realistic corporate profile based on those variables.
*   **Phase 2:** The app searches Google for the company logo.
*   **Phase 3:** Data is injected into the HTML template.
*   **Phase 4:** WeasyPrint renders the final document as a professional A4 PDF.

---

## 📁 File Structure

*   `app_ui.py`: The Graphical User Interface (PyQt/PySide).
*   `html_generator.py`: Scans HTML for `${variables}` and handles data merging.
*   `companies_profile.py`: Interfaces with the Gemini API.
*   `logo_finder.py`: Scrapes the web for company logos.
*   `compiler.py`: Handles the HTML-to-PDF conversion.
*   `/templates`: Storage for your custom HTML designs.

---

## ⚖️ Disclaimer
This tool is intended for creating fictional training materials and educational props. Ensure you comply with the Google Gemini API Terms of Service. All scraped logos remain the property of their respective trademark holders.

---

## 🤝 Contributing
Feel free to fork this project, open issues, or submit pull requests to improve the AI prompting or the PDF layout engine!
## 📸 Preview

### Application Interface
<img width="956" height="831" alt="image" src="https://github.com/user-attachments/assets/fd9e69b9-a1b4-40d9-a311-3ac75ca5f2c1" />



### Sample Output (PDF)
<img width="1275" height="1650" alt="1_PDFsam_Texas_Intstruments-1" src="https://github.com/user-attachments/assets/e93644be-9565-4ec4-98dd-dd64010984b2" />
