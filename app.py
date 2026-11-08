import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import pandas as pd

# 1. Load Environment Variables
if os.path.exists('.env'):
    load_dotenv(override=True)

# Initialize Flask App (FIXED: __name__)
app = Flask(__name__)

# 2. Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'default-secret-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')

mail = Mail(app)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/portfolio')
def portfolio():
    projects = [
        {
            "title": "Automated Data Cleaning with Python",
            "description": "A Python-based tool that automates data preprocessing by handling missing values, duplicates, and column normalization.",
            "image": "data-cleaning.jpg",
            "link": url_for('data_cleaning_project'),
            "demo_link": url_for('data_cleaning_demo')
        },
        {
            "title": "Sales Data Analysis in Excel",
            "description": "Comprehensive analysis of retail sales data using Pivot Tables and Power Query.",
            "image": "sales-analysis.jpg",
            "link": url_for('sales_analysis_project'),
            "demo_link": None
        },
        {
            "title": "Remote Work Trends Research",
            "description": "A research project investigating the socio-economic impacts of the shift to remote work.",
            "image": "research-project.jpg",
            "link": url_for('research_project'),
            "demo_link": None
        }
    ]
    return render_template('portfolio.html', projects=projects)

@app.route('/projects/data-cleaning')
def data_cleaning_project():
    return render_template('data-cleaning.html')

@app.route('/projects/sales-analysis')
def sales_analysis_project():
    return render_template('sales-analysis.html')

@app.route('/projects/research')
def research_project():
    return render_template('research-project.html')

# 5. LIVE DEMO: Data Cleaning Tool
@app.route('/projects/data-cleaning/demo', methods=['GET', 'POST'])
def data_cleaning_demo():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part found.", "danger")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("No file selected.", "danger")
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            try:
                if file_extension == 'csv':
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath, engine='openpyxl')
                
                # --- CALCULATE "BEFORE" STATS ---
                initial_duplicates = int(df.duplicated().sum())
                initial_missing = int(df.isna().sum().sum())
                
                # --- CORRECT CLEANING ORDER ---
                # 1. Standardize columns
                df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_")
                # 2. Remove duplicates
                df = df.drop_duplicates()
                # 3. Drop sparse columns FIRST (more than 50% null)
                df = df.dropna(axis=1, thresh=len(df)*0.5)
                # 4. Fill missing numeric values AFTER dropping sparse columns
                numeric_cols = df.select_dtypes(include=['number']).columns
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                
                # --- CALCULATE "AFTER" STATS FOR DASHBOARD ---
                final_duplicates = int(df.duplicated().sum())
                final_missing = int(df.isna().sum().sum())
                
                duplicates_removed = initial_duplicates - final_duplicates
                missing_values_filled = initial_missing - final_missing
                
                report = (
                    "=== DATA CLEANING REPORT ===\n"
                    f"1. Standardized column names to lowercase with underscores.\n"
                    f"2. Removed {duplicates_removed} duplicate rows.\n"
                    f"3. Dropped columns with >50% missing values.\n"
                    f"4. Filled {missing_values_filled} missing numeric values with mean.\n"
                    f"\nFinal dataset: {len(df)} rows, {len(df.columns)} columns"
                )
                
                total_cells = df.size
                quality_score = 100.0
                if total_cells > 0:
                    missing_penalty = (final_missing / total_cells) * 40
                    duplicate_penalty = (final_duplicates / len(df)) * 30 if len(df) > 0 else 0
                    quality_score = round(max(0, min(100, 100 - missing_penalty - duplicate_penalty)), 2)

                stats = {
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'duplicate_rows': final_duplicates,
                    'missing_values': {'total': final_missing}
                }

                # Save cleaned file
                cleaned_filename = f"cleaned_{uuid.uuid4().hex}.{file_extension}"
                cleaned_filepath = os.path.join(app.config['UPLOAD_FOLDER'], cleaned_filename)
                
                if file_extension == 'csv':
                    df.to_csv(cleaned_filepath, index=False)
                else:
                    df.to_excel(cleaned_filepath, index=False, engine='openpyxl')
                
                flash("Cleaning complete! Download your file below.", "success")
                
                return render_template(
                    'data-cleaning-demo.html',
                    filename=cleaned_filename,
                    original_name=original_filename,
                    stats=stats,
                    quality_score=quality_score,
                    duplicates_removed=duplicates_removed,
                    missing_values_filled=missing_values_filled,
                    report=report,
                    file_extension=file_extension
                )
            
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "danger")
                return redirect(request.url)
    
    return render_template('data-cleaning-demo.html')

@app.route('/downloads/<filename>')
def download_cleaned_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not name or not email or not message:
            flash("Please fill out all fields.", "warning")
            return redirect(url_for('contact'))
        
        try:
            msg = Message(
                subject=f"Portfolio Contact: {name}",
                recipients=[os.getenv('EMAIL_USER')],
                body=f"From: {name} <{email}>\n\nMessage:\n{message}"
            )
            mail.send(msg)
            flash("Thank you! Your message has been sent.", "success")
        except Exception as e:
            print(f"Mail Error: {e}")
            flash("Email service failed. Please try again later.", "danger")
        
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/resume')
def resume():
    return render_template('resume.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# FIXED: __name__ == '__main__'
if __name__ == '__main__':
    app.run(debug=True)