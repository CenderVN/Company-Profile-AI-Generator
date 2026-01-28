import os
import json
import time
from pathlib import Path

# Import your modules
from companies_profile import CorporateProfileGenerator
from html_generator import HtmlProfileGenerator
import logo_finder
import compiler

# --- Configuration ---
OUTPUT_DIR = "output"
TEMPLATE_FILE = "profile_template.html"

# List of companies to process
TARGET_COMPANIES = [
    "Nokia",
    "Rovio Entertainment",
    "Kone",
    "Supercell"
]

def main():
    # 0. Setup
    print("🚀 STARTING CORPORATE INTELLIGENCE PIPELINE")
    print(f"📂 Output Directory: {OUTPUT_DIR}")
    
    # Check API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set.")
        return

    # Create output dir
    base_path = Path(OUTPUT_DIR)
    base_path.mkdir(exist_ok=True)

    # --- STEP 1: Generate Intelligence (JSON) ---
    print("\n[1/4] 🧠 Generating Intelligence Profiles (Gemini AI)...")
    ai_gen = CorporateProfileGenerator(api_key=api_key)
    ai_gen.process_companies_from_list(TARGET_COMPANIES, OUTPUT_DIR)

    # --- STEP 2: Acquire Assets (Logos) ---
    print("\n[2/4] 🖼️ Acquiring Target Assets (Logos)...")
    json_files = list(base_path.glob("*_data.json"))
    
    if not json_files:
        print("❌ No data files found. Skipping remaining steps.")
        return

    for json_file in json_files:
        # derive names
        safe_name = json_file.stem.replace('_data', '')
        company_name = safe_name.replace('_', ' ')
        logo_filename = f"{safe_name}_logo.png"
        logo_path = base_path / logo_filename

        # Skip if exists
        if logo_path.exists():
            print(f"  ✓ Logo exists for {company_name}")
            continue

        # Search and Download
        print(f"  🔍 Searching logo for: {company_name}...")
        img_url = logo_finder._google_images_search(f"{company_name} logo")
        
        if img_url:
            success = logo_finder._download_image(img_url, base_path, filename=logo_filename)
            if success:
                print(f"  ✓ Downloaded {logo_filename}")
            else:
                print(f"  ✗ Failed download for {company_name}")
        else:
            print(f"  ✗ No logo URL found for {company_name}")
        
        # Be polite to Google
        time.sleep(1.0)

    # --- STEP 3: Generate Dossiers (HTML) ---
    print("\n[3/4] 📝 Compiling HTML Dossiers...")
    html_gen = HtmlProfileGenerator(TEMPLATE_FILE)
    
    for json_file in json_files:
        safe_name = json_file.stem.replace('_data', '')
        logo_filename = f"{safe_name}_logo.png"
        
        try:
            # Load the existing JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # INJECT the specific logo filename into the data context
            # This allows the HTML template to use ${logo_filename}
            data['logo_filename'] = logo_filename
            
            # Generate HTML
            html_content = html_gen.generate_html_content(data)
            
            # Save HTML
            html_path = base_path / f"{safe_name}_profile.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"  ✓ Created {html_path.name}")
            
        except Exception as e:
            print(f"  ✗ Error processing {json_file.name}: {e}")

    # --- STEP 4: Finalize Reports (PDF) ---
    print("\n[4/4] 🖨️  Rendering Final PDFs...")
    success = compiler.compile_html_to_pdf(OUTPUT_DIR)

    print("\n" + "="*40)
    print("✅ PIPELINE COMPLETE")
    if success:
        print(f"📂 Files available in: {os.path.abspath(OUTPUT_DIR)}")
    else:
        print("⚠️  Completed with some errors.")

if __name__ == "__main__":
    main()