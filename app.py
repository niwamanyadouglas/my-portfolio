import os
import time
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

app = Flask(__name__)

# 2. Configuration
# If FLASK_SECRET is not set, use a random key so the app still starts
# (sessions/flash messages simply reset on restart). Set FLASK_SECRET on Render.
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET') or os.urandom(32).hex()
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB upload limit
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
FILE_MAX_AGE_SECONDS = 60 * 60  # uploaded/cleaned files are deleted after 1 hour

# Email Configuration (Gmail needs an app password; port 587 + TLS, or 465 + SSL)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USER')

mail = Mail(app)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


@app.context_processor
def inject_globals():
    # Social/contact links come from environment variables so no placeholder
    # links are shown. Set LINKEDIN_URL, GITHUB_URL and CONTACT_EMAIL on Render.
    return {
        'now': datetime.utcnow(),
        'linkedin_url': os.getenv('LINKEDIN_URL'),
        'github_url': os.getenv('GITHUB_URL'),
        'contact_email': os.getenv('CONTACT_EMAIL'),
    }


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_uploads():
    """Delete files in the upload folder older than FILE_MAX_AGE_SECONDS."""
    folder = app.config['UPLOAD_FOLDER']
    cutoff = time.time() - FILE_MAX_AGE_SECONDS
    try:
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
    except OSError as e:
        print(f"Cleanup error: {e}")


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
            "title": "Sales Data Analysis",
            "description": "Analysis of sales data using Excel and Python to uncover trends and pricing opportunities.",
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
    cleanup_old_uploads()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part found.", "danger")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("No file selected.", "danger")
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash("Unsupported file type. Please upload a .csv or .xlsx file.", "warning")
            return redirect(request.url)

        original_filename = secure_filename(file.filename) or "uploaded_file"
        # Take the extension from the validated filename (secure_filename can strip it)
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        try:
            if file_extension == 'csv':
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath, engine='openpyxl')

            if df.empty:
                flash("The uploaded file has no data.", "warning")
                return redirect(request.url)
            
            rows_before = len(df)
            
            # --- CLEANING ---
            # 1. Standardize columns
            df.columns = (df.columns.astype(str).str.strip().str.lower()
                          .str.replace(" ", "_").str.replace("-", "_"))
            # 2. Remove duplicates
            df = df.drop_duplicates()
            duplicates_removed = rows_before - len(df)
            # 3. Drop sparse columns FIRST (more than 50% null)
            df = df.dropna(axis=1, thresh=int(len(df) * 0.5))
            # 4. Fill missing numeric values AFTER dropping sparse columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            missing_values_filled = int(df[numeric_cols].isna().sum().sum())
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            
            # --- STATS FOR DASHBOARD ---
            final_duplicates = int(df.duplicated().sum())
            final_missing = int(df.isna().sum().sum())
            
            report = (
                "=== DATA CLEANING REPORT ===\n"
                f"1. Standardized column names to lowercase with underscores.\n"
                f"2. Removed {duplicates_removed} duplicate rows.\n"
                f"3. Dropped columns with >50% missing values.\n"
                f"4. Filled {missing_values_filled} missing numeric values with the column mean.\n"
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
            print(f"Cleaning error: {e}")
            flash("Sorry, that file could not be processed. Please check it is a valid CSV or Excel (.xlsx) file.", "danger")
            return redirect(request.url)
        
        finally:
            # Never keep the raw upload on the server
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return render_template('data-cleaning-demo.html')

@app.route('/downloads/<filename>')
def download_cleaned_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Honeypot: real visitors never see or fill this field; bots do
        if request.form.get('website'):
            flash("Thank you! Your message has been sent.", "success")
            return redirect(url_for('contact'))

        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip()
        message = (request.form.get('message') or '').strip()
        
        if not name or not email or not message:
            flash("Please fill out all fields.", "warning")
            return redirect(url_for('contact'))

        if len(name) > 100 or len(email) > 200 or len(message) > 5000:
            flash("Your message is too long. Please shorten it and try again.", "warning")
            return redirect(url_for('contact'))
        
        recipient = os.getenv('EMAIL_USER')
        if not recipient:
            print("Mail Error: EMAIL_USER is not set")
            flash("Email service is not configured. Please try again later.", "danger")
            return redirect(url_for('contact'))

        try:
            msg = Message(
                subject=f"Portfolio Contact: {name}",
                recipients=[recipient],
                reply_to=email,
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

@app.errorhandler(413)
def file_too_large(e):
    flash("File too large. The maximum size is 10MB.", "danger")
    return redirect(url_for('data_cleaning_demo'))

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Debug mode only when explicitly enabled (FLASK_DEBUG=1); never on Render
    app.run(debug=os.getenv('FLASK_DEBUG') == '1')
