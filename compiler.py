import sys
from pathlib import Path
import time

# Try to import WeasyPrint, handle error if missing
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

def compile_html_to_pdf(source_dir="output"):
    """
    Compiles all .html files in the source directory to .pdf
    """
    if not WEASYPRINT_AVAILABLE:
        print("❌ Error: 'weasyprint' library is not installed.")
        print("Please run: pip install weasyprint")
        return False

    base_path = Path(source_dir)
    if not base_path.exists():
        print(f"Directory '{source_dir}' does not exist!")
        return False
    
    # Find all .html files
    html_files = list(base_path.glob("*.html"))
    print(f"Found {len(html_files)} HTML profiles in '{source_dir}'")
    
    success_count = 0
    failed_files = []
    
    for html_file in html_files:
        try:
            # Define output filename (Company_profile.html -> Company_profile.pdf)
            pdf_file = base_path / f"{html_file.stem}.pdf"
            
            print(f"Compiling: {html_file.name}...", end=" ", flush=True)
            
            # Generate PDF
            # We pass base_url so WeasyPrint can find the local 'logo.png' images
            HTML(filename=str(html_file), base_url=str(base_path)).write_pdf(str(pdf_file))
            
            print("✓ Done")
            success_count += 1
            
        except Exception as e:
            print(f"✗ Failed")
            failed_files.append((html_file.name, str(e)))

    # Summary Report
    print(f"\n{'='*50}")
    print("COMPILATION REPORT")
    print(f"{'='*50}")
    print(f"Total files: {len(html_files)}")
    print(f"Successful:  {success_count}")
    print(f"Failed:      {len(failed_files)}")
    
    if failed_files:
        print("\nErrors:")
        for fname, error in failed_files:
            print(f"- {fname}: {error}")
            
    return success_count > 0