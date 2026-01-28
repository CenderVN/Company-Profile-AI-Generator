import sys
import os
import time
import json
from pathlib import Path

# UI Imports
from qtpy.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QProgressBar, QFileDialog, QSplitter,
                            QMessageBox, QGroupBox, QComboBox)
from qtpy.QtCore import Qt, QThread, Signal, QObject, QSettings
from qtpy.QtGui import QIcon, QFont

# Import your pipeline modules
import companies_profile
import html_generator
import logo_finder
import compiler

# --- Worker Thread (Handles the heavy lifting) ---
class WorkerSignals(QObject):
    log = Signal(str)
    progress = Signal(int)
    finished = Signal()
    error = Signal(str)

class PipelineWorker(QThread):
    def __init__(self, api_key, companies, output_dir, template_name):
        super().__init__()
        self.api_key = api_key
        self.companies = [c.strip() for c in companies if c.strip()]
        self.output_dir = output_dir
        self.template_name = template_name
        self.signals = WorkerSignals()
        self.is_running = True

    def run(self):
        try:
            total_steps = len(self.companies) * 3 + 1 
            current_step = 0
            
            base_path = Path(self.output_dir)
            base_path.mkdir(exist_ok=True)

            # --- PHASE 0: TEMPLATE ANALYSIS ---
            self.signals.log.emit(f"<b>[PHASE 0] Analyzing Template...</b>")
            template_path = Path("templates") / self.template_name
            if not template_path.exists():
                self.signals.error.emit(f"Template not found: {template_path}")
                return

            # Initialize HTML generator to scan for variables
            html_gen = html_generator.HtmlProfileGenerator(str(template_path))
            required_fields = html_gen.get_template_variables()
            
            if not required_fields:
                self.signals.log.emit("<span style='color:orange'>⚠️ No variables found in template. AI will use default profile.</span>")
            else:
                self.signals.log.emit(f"📝 Found {len(required_fields)} fields to collect: <i>{', '.join(required_fields[:5])}...</i>")

            # --- PHASE 1: AI GENERATION ---
            self.signals.log.emit(f"<br><b>[PHASE 1] Connecting to Gemini API...</b>")
            
            try:
                ai_gen = companies_profile.CorporateProfileGenerator(api_key=self.api_key)
            except Exception as e:
                self.signals.error.emit(str(e))
                return

            for i, company in enumerate(self.companies):
                if not self.is_running: return
                
                self.signals.log.emit(f"🧠 AI searching for data: {company}...")
                
                # We pass the REQUIRED_FIELDS scanned from the HTML here
                success, json_path = ai_gen.process_company(company, required_fields, self.output_dir)
                
                if success:
                    self.signals.log.emit(f"<span style='color:green'>  ✓ Data Collected & Saved</span>")
                else:
                    self.signals.log.emit(f"<span style='color:red'>  ✗ AI Generation Failed</span>")
                
                current_step += 1
                self.signals.progress.emit(int((current_step / total_steps) * 100))
                
                if i < len(self.companies) - 1:
                    self.signals.log.emit("  ⏳ Safety cooldown (10s)...")
                    for _ in range(10): 
                        if not self.is_running: return
                        time.sleep(1)

            # --- PHASE 2: LOGO ACQUISITION ---
            self.signals.log.emit(f"<br><b>[PHASE 2] Downloading Logos...</b>")
            json_files = list(base_path.glob("*_data.json"))
            
            for json_file in json_files:
                if not self.is_running: return
                
                safe_name = json_file.stem.replace('_data', '')
                company_name = safe_name.replace('_', ' ')
                logo_filename = f"{safe_name}_logo.png"
                logo_path = base_path / logo_filename

                if logo_path.exists():
                    self.signals.log.emit(f"  ✓ Logo exists for {company_name}")
                else:
                    self.signals.log.emit(f"🔍 Searching logo: {company_name}")
                    img_url = logo_finder._google_images_search(f"{company_name} logo")
                    
                    if img_url:
                        success = logo_finder._download_image(img_url, base_path, filename=logo_filename)
                        if success:
                            self.signals.log.emit(f"<span style='color:green'>  ✓ Downloaded logo</span>")
                        else:
                            self.signals.log.emit(f"<span style='color:orange'>  ✗ Download failed</span>")
                    else:
                        self.signals.log.emit(f"<span style='color:orange'>  ✗ No image found</span>")
                
                current_step += 1
                self.signals.progress.emit(int((current_step / total_steps) * 100))

            # --- PHASE 3: HTML COMPILATION ---
            self.signals.log.emit(f"<br><b>[PHASE 3] Building HTML Dossiers...</b>")
            
            for json_file in json_files:
                if not self.is_running: return
                
                safe_name = json_file.stem.replace('_data', '')
                logo_filename = f"{safe_name}_logo.png"
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Inject local path for logo
                    data['logo_filename'] = logo_filename
                    
                    # Generate HTML using the scanned template
                    html_content = html_gen.generate_html_content(data)
                    html_path = base_path / f"{safe_name}_profile.html"
                    
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    self.signals.log.emit(f"  ✓ Built HTML: {safe_name}")
                    
                except Exception as e:
                    self.signals.log.emit(f"<span style='color:red'>  ✗ Error: {e}</span>")

                current_step += 1
                self.signals.progress.emit(int((current_step / total_steps) * 100))

            # --- PHASE 4: PDF RENDERING ---
            self.signals.log.emit(f"<br><b>[PHASE 4] Rendering PDFs (WeasyPrint)...</b>")
            success = compiler.compile_html_to_pdf(self.output_dir)
            
            if success:
                self.signals.log.emit(f"<br><b style='color:green'>✅ PIPELINE COMPLETE!</b>")
            else:
                self.signals.log.emit(f"<br><b style='color:orange'>⚠️ Finished with PDF errors.</b>")

            self.signals.progress.emit(100)
            self.signals.finished.emit()

        except Exception as e:
            self.signals.error.emit(f"Critical Pipeline Error: {str(e)}")

    def stop(self):
        self.is_running = False

# --- Main Window ---
class CorporateProfileApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Corporate Profile Generator")
        self.resize(950, 800)
        self.settings = QSettings("MyCompany", "ProfileGen")
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 1. Configuration Section
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # Template Selection Row
        tpl_layout = QHBoxLayout()
        tpl_layout.addWidget(QLabel("HTML Template:"))
        self.template_dropdown = QComboBox()
        self.refresh_templates()
        
        self.refresh_tpl_btn = QPushButton("Refresh List")
        self.refresh_tpl_btn.clicked.connect(self.refresh_templates)
        
        tpl_layout.addWidget(self.template_dropdown, 1)
        tpl_layout.addWidget(self.refresh_tpl_btn)
        config_layout.addLayout(tpl_layout)

        # API Key Row
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("Gemini API Key:"))
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.Password)
        self.api_input.setText(self.settings.value("api_key", ""))
        api_layout.addWidget(self.api_input)
        config_layout.addLayout(api_layout)

        # Output Dir Row
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Output Folder:"))
        self.dir_input = QLineEdit()
        self.dir_input.setText(self.settings.value("output_dir", "output"))
        self.dir_btn = QPushButton("Browse...")
        self.dir_btn.clicked.connect(self.browse_folder)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_btn)
        config_layout.addLayout(dir_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 2. Main Content Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Side: Company List
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.addWidget(QLabel("<b>Target Companies (One per line):</b>"))
        self.companies_input = QTextEdit()
        self.companies_input.setPlaceholderText("Nokia\nMicrosoft\nTesla")
        self.companies_input.setText(self.settings.value("companies", ""))
        left_layout.addWidget(self.companies_input)
        splitter.addWidget(left_widget)

        # Right Side: Logs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.addWidget(QLabel("<b>Operation Log:</b>"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas; font-size: 12px;")
        right_layout.addWidget(self.log_output)
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        # 3. Controls
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("🚀 Start Generation Pipeline")
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #2c3e50; color: white;")
        self.start_btn.clicked.connect(self.start_process)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_process)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

    def refresh_templates(self):
        """Scans the 'templates' folder for HTML files"""
        self.template_dropdown.clear()
        template_dir = Path("templates")
        
        if not template_dir.exists():
            template_dir.mkdir(exist_ok=True)
            return

        html_files = list(template_dir.glob("*.html"))
        if not html_files:
            self.template_dropdown.addItem("No .html templates found!")
        else:
            for f in html_files:
                self.template_dropdown.addItem(f.name)
            
            last_tpl = self.settings.value("last_template", "")
            index = self.template_dropdown.findText(last_tpl)
            if index >= 0:
                self.template_dropdown.setCurrentIndex(index)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.dir_input.setText(folder)

    def start_process(self):
        api_key = self.api_input.text().strip()
        companies_text = self.companies_input.toPlainText().strip()
        output_dir = self.dir_input.text().strip()
        selected_template = self.template_dropdown.currentText()

        if not api_key:
            QMessageBox.warning(self, "Error", "Please enter a Gemini API Key.")
            return
        if not companies_text:
            QMessageBox.warning(self, "Error", "Please list at least one company.")
            return
        if "No .html" in selected_template or not selected_template:
            QMessageBox.warning(self, "Error", "Please select a template.")
            return

        self.settings.setValue("api_key", api_key)
        self.settings.setValue("output_dir", output_dir)
        self.settings.setValue("companies", companies_text)
        self.settings.setValue("last_template", selected_template)

        companies_list = companies_text.split('\n')

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.companies_input.setEnabled(False)
        self.log_output.clear()
        self.progress_bar.setValue(0)

        # Start Thread
        self.worker = PipelineWorker(api_key, companies_list, output_dir, selected_template)
        self.worker.signals.log.connect(self.append_log)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.finished.connect(self.process_finished)
        self.worker.signals.error.connect(self.process_error)
        self.worker.start()

    def stop_process(self):
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.append_log("<br>🛑 <b>Stopping...</b>")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.companies_input.setEnabled(True)

    def append_log(self, text):
        self.log_output.append(text)
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def process_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.companies_input.setEnabled(True)
        QMessageBox.information(self, "Done", "Processing Complete!")

    def process_error(self, err_msg):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.companies_input.setEnabled(True)
        self.append_log(f"<br><span style='color:red'><b>CRITICAL ERROR:</b> {err_msg}</span>")
        QMessageBox.critical(self, "Error", err_msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CorporateProfileApp()
    window.show()
    sys.exit(app.exec_())