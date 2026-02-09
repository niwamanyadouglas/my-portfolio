import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import pandas as pd

# 1. Load Environment Variables from .env file
load_dotenv(override=True) # Add override=True here

app = Flask(__name__)

# 2. Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET')
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USER')

# Initialize Mail and Ensure Uploads Directory exists
mail = Mail(app)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 3. Context Processor for Dynamic Footer Year
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# 4. Helper Functions
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
    """Render Portfolio with Demo links enabled where applicable."""
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
            "description": "Comprehensive analysis of retail sales data using Pivot Tables and Power Query to drive business decisions.",
            "image": "sales-analysis.jpg",
            "link": url_for('sales_analysis_project'),
            "demo_link": None
        },
        {
            "title": "Remote Work Trends Research",
            "description": "A research project investigating the socio-economic impacts of the shift to remote work in 2024-2025.",
            "image": "research-project.jpg",
            "link": url_for('research_project'),
            "demo_link": None
        }
    ]
    return render_template('portfolio.html', projects=projects)

# Project Detail Pages
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
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # pandas cleaning logic
                df = pd.read_csv(filepath)
                
                # Standardize columns: lowercase and underscores
                df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_")
                
                # Remove duplicates
                df = df.drop_duplicates()
                
                # Fill missing numeric values with the mean
                numeric_cols = df.select_dtypes(include=['number']).columns
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                
                # Drop columns that are mostly empty (more than 50% null)
                df = df.dropna(axis=1, thresh=len(df)*0.5)
                
                cleaned_filename = 'cleaned_' + filename
                cleaned_filepath = os.path.join(app.config['UPLOAD_FOLDER'], cleaned_filename)
                df.to_csv(cleaned_filepath, index=False)
                
                flash("Cleaning complete! Download your file below.", "success")
                return redirect(url_for('data_cleaning_demo', filename=cleaned_filename))
            
            except Exception as e:
                flash(f"Error processing CSV: {str(e)}", "danger")
                return redirect(request.url)
                
    return render_template('data-cleaning-demo.html')

@app.route('/downloads/<filename>')
def download_cleaned_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# 6. CONTACT FORM: Sending Emails
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
        
        return redirect(url_for('home'))

    return render_template('contact.html')

@app.route('/resume')
def resume():
    return render_template('resume.html')

# 7. ERROR HANDLERS
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Run with debug=True for development only
    app.run(debug=True)