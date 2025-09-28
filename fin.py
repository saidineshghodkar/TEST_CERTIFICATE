from flask import Flask, render_template_string, request, redirect, url_for, send_file, jsonify
import json, os, uuid
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'skd_university_2025_secret_key'

APPLICATIONS_FILE = 'applications.json'
COMPUTER_SESSION_FILE = 'computer_session.json'
REBLOCK_QUEUE_FILE = 'reblock_queue.json'
AR_SESSION_FILE = 'ar_session.json'
VR_SESSION_FILE = 'vr_session.json'
VERIFIED_CERTIFICATES_FILE = 'verified_certificates.json'
POST_SESSION_FILE = 'post_session.json'

def init_json_files():
    for f in [APPLICATIONS_FILE, COMPUTER_SESSION_FILE, REBLOCK_QUEUE_FILE, AR_SESSION_FILE, VR_SESSION_FILE, VERIFIED_CERTIFICATES_FILE, POST_SESSION_FILE]:
        if not os.path.exists(f):
            with open(f, 'w') as fp:
                json.dump([], fp)

def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as fp:
            return json.load(fp)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)

def gen_app_number():
    return f"SKD{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"

def format_datetime(dt_string):
    """Format datetime string to readable format"""
    if not dt_string or dt_string == 'Waiting for previous steps':
        return 'Waiting for previous steps'
    try:
        if isinstance(dt_string, str):
            dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        else:
            dt = dt_string
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return str(dt_string) if dt_string else 'Waiting for previous steps'

def check_duplicate_application(roll_number, certificate_type):
    """Check if application with same hall ticket and certificate type already exists"""
    apps = load_json(APPLICATIONS_FILE)
    verified = load_json(VERIFIED_CERTIFICATES_FILE)
    
    # Check in pending applications
    for app in apps:
        if (app.get('roll_number') == roll_number and 
            app.get('certificate_type') == certificate_type):
            return True
    
    # Check in verified certificates
    for cert in verified:
        if (cert.get('roll_number') == roll_number and 
            cert.get('certificate_type') == certificate_type):
            return True
    
    return False

def build_timeline(app):
    """Build enhanced modern timeline with proper formatting and status indicators"""
    timeline = []
    
    # Application Submitted
    submission_time = app.get('submission_time', '')
    timeline.append({
        'stage': 'Application Submitted', 
        'status': 'Completed', 
        'timestamp': format_datetime(submission_time),
        'css_class': 'completed',
        'icon': 'fa-paper-plane',
        'description': f"{app.get('certificate_type', 'Certificate')} application submitted successfully",
        'step': 1
    })
    
    # Block Office
    verification_time = app.get('verification_time')
    verification_status = app.get('verification_status')
    if verification_time and verification_status:
        status_text = 'Approved' if verification_status == 'approve' else verification_status.title()
        timeline.append({
            'stage': 'Block Office', 
            'status': status_text, 
            'timestamp': format_datetime(verification_time),
            'css_class': 'completed' if verification_status == 'approve' else 'pending',
            'icon': 'fa-building',
            'description': 'Document verification completed',
            'step': 2
        })
    else:
        timeline.append({
            'stage': 'Block Office', 
            'status': 'Pending', 
            'timestamp': 'Waiting for previous steps',
            'css_class': 'pending',
            'icon': 'fa-building',
            'description': 'Waiting for document verification',
            'step': 2
        })
    
    # Computer Session
    computer_session_time = app.get('computer_session_time')
    computer_session_status = app.get('computer_session_status')
    if computer_session_time and computer_session_status:
        status_text = 'Approved' if computer_session_status == 'approved' else computer_session_status.title()
        timeline.append({
            'stage': 'Computer Session', 
            'status': status_text, 
            'timestamp': format_datetime(computer_session_time),
            'css_class': 'completed' if computer_session_status == 'approved' else 'pending',
            'icon': 'fa-laptop',
            'description': 'Digital processing completed',
            'step': 3
        })
    else:
        timeline.append({
            'stage': 'Computer Session', 
            'status': 'Pending', 
            'timestamp': 'Waiting for previous steps',
            'css_class': 'pending',
            'icon': 'fa-laptop',
            'description': 'Waiting for computer processing',
            'step': 3
        })
    
    # Re-Block Queue
    reblock_time = app.get('reblock_time')
    reblock_status = app.get('reblock_status')
    if reblock_time and reblock_status:
        status_text = 'Completed' if reblock_status == 'approved' else reblock_status.title()
        timeline.append({
            'stage': 'Re-Block Queue', 
            'status': status_text, 
            'timestamp': format_datetime(reblock_time),
            'css_class': 'completed' if reblock_status == 'approved' else 'pending',
            'icon': 'fa-redo',
            'description': 'Re-blocking process completed',
            'step': 4
        })
    else:
        timeline.append({
            'stage': 'Re-Block Queue', 
            'status': 'Pending', 
            'timestamp': 'Waiting for previous steps',
            'css_class': 'pending',
            'icon': 'fa-redo',
            'description': 'Waiting for previous steps',
            'step': 4
        })
    
    # AR Session
    ar_time = app.get('ar_time')
    ar_status = app.get('ar_status')
    if ar_time and ar_status:
        status_text = 'Approved' if ar_status == 'approved' else ar_status.title()
        timeline.append({
            'stage': 'AR Session', 
            'status': status_text, 
            'timestamp': format_datetime(ar_time),
            'css_class': 'completed' if ar_status == 'approved' else 'pending',
            'icon': 'fa-cube',
            'description': 'Augmented reality verification',
            'step': 5
        })
    else:
        timeline.append({
            'stage': 'AR Session', 
            'status': 'Pending', 
            'timestamp': 'Waiting for previous steps',
            'css_class': 'pending',
            'icon': 'fa-cube',
            'description': 'Waiting for previous steps',
            'step': 5
        })
    
    # VR Session
    vr_time = app.get('vr_time')
    vr_status = app.get('vr_status')
    if vr_time and vr_status:
        status_text = 'Approved' if vr_status == 'approved' else vr_status.title()
        timeline.append({
            'stage': 'VR Session', 
            'status': status_text, 
            'timestamp': format_datetime(vr_time),
            'css_class': 'completed' if vr_status == 'approved' else 'pending',
            'icon': 'fa-vr-cardboard',
            'description': 'Virtual reality processing',
            'step': 6
        })
    else:
        timeline.append({
            'stage': 'VR Session', 
            'status': 'Pending', 
            'timestamp': 'Waiting for previous steps',
            'css_class': 'pending',
            'icon': 'fa-vr-cardboard',
            'description': 'Waiting for previous steps',
            'step': 6
        })
    
    # Post Session
    post_time = app.get('post_time')
    post_status = app.get('post_status')
    if post_time and post_status:
        post_status_text = 'Approved' if post_status == 'approved' else post_status.title()
        timeline.append({
            'stage': 'Post Session', 
            'status': post_status_text, 
            'timestamp': format_datetime(post_time),
            'css_class': 'completed' if post_status == 'approved' else 'pending',
            'icon': 'fa-mail-bulk',
            'description': 'Final processing completed',
            'step': 7
        })
    else:
        timeline.append({
            'stage': 'Post Session', 
            'status': 'Pending', 
            'timestamp': 'Waiting for previous steps',
            'css_class': 'pending',
            'icon': 'fa-mail-bulk',
            'description': 'Waiting for previous steps',
            'step': 7
        })
    
    # Verified Certificates
    verified_time = app.get('verified_time')
    if verified_time:
        timeline.append({
            'stage': 'Verified Certificate', 
            'status': 'Approved', 
            'timestamp': format_datetime(verified_time),
            'css_class': 'completed',
            'icon': 'fa-certificate',
            'description': 'Certificate has been verified and is available for viewing',
            'step': 8
        })
    else:
        timeline.append({
            'stage': 'Verified Certificate', 
            'status': 'Pending', 
            'timestamp': 'Waiting for previous steps',
            'css_class': 'pending',
            'icon': 'fa-certificate',
            'description': 'Certificate is not yet verified',
            'step': 8
        })

    return timeline

def get_progress_percentage(timeline):
    """Calculate progress percentage based on completed steps"""
    completed_steps = sum(1 for event in timeline if event['status'] in ['Completed', 'Approved'])
    total_steps = len(timeline)
    return (completed_steps / total_steps) * 100 if total_steps > 0 else 0

def get_current_stage(app):
    if app.get('verified_time'): return 'Verified Certificates'
    if app.get('post_status'): return 'Post Session'
    if app.get('vr_status'): return 'VR Session'
    if app.get('ar_status'): return 'AR Session'
    if app.get('reblock_status'): return 'Re-Block Queue'
    if app.get('computer_session_status'): return 'Computer Session'
    if app.get('verification_status'): return 'Block Office'
    return 'Application Submitted'

def filter_apps(apps, search, date_filter):
    filtered = apps
    if search:
        filtered = [a for a in filtered if search.lower() in a.get('student_name', '').lower() or search.lower() in a.get('roll_number', '').lower()]
    if date_filter:
        filtered = [a for a in filtered if a.get('submission_time', '').startswith(date_filter)]
    return sorted(filtered, key=lambda x: x.get('submission_time', ''), reverse=True)

def get_pending_apps(apps):
    """Get only pending applications (not verified)"""
    return [a for a in apps if not a.get('verified_time')]

BASE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SKU Certificate System</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
  <style>
    :root {
      --primary-color: #2563eb;
      --secondary-color: #1e40af;
      --success-color: #10b981;
      --warning-color: #f59e0b;
      --danger-color: #ef4444;
      --info-color: #06b6d4;
      --light-bg: #f8fafc;
      --dark-bg: #0f172a;
      --card-bg: #ffffff;
      --text-color: #1e293b;
      --border-color: #e2e8f0;
      --timeline-bg: #1e40af;
      --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      --gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      --gradient-success: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }

    [data-theme="dark"] {
      --light-bg: #0f172a;
      --card-bg: #1e293b;
      --text-color: #f1f5f9;
      --border-color: #334155;
      --timeline-bg: #3b82f6;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: 'Poppins', sans-serif;
      background: var(--light-bg);
      color: var(--text-color);
      transition: all 0.3s ease;
      min-height: 100vh;
      -webkit-tap-highlight-color: transparent;
    }

    .navbar {
      background: var(--gradient-primary);
      backdrop-filter: blur(20px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    .navbar-brand {
      font-weight: 700;
      font-size: 1.3rem;
      color: white !important;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .navbar-brand img {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: 2px solid rgba(255,255,255,0.2);
    }

    .nav-link {
      color: rgba(255,255,255,0.9) !important;
      font-weight: 500;
      transition: all 0.3s ease;
      position: relative;
      font-size: 0.9rem;
      padding: 8px 12px !important;
    }

    .nav-link:hover {
      color: white !important;
      transform: translateY(-1px);
    }

    .nav-link::after {
      content: '';
      position: absolute;
      bottom: -5px;
      left: 0;
      width: 0;
      height: 2px;
      background: white;
      transition: width 0.3s ease;
    }

    .nav-link:hover::after {
      width: 100%;
    }

    .container {
      max-width: 1200px;
      margin: 2rem auto;
      padding: 0 1rem;
    }

    .card {
      background: var(--card-bg);
      border-radius: 20px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.1);
      border: 1px solid var(--border-color);
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      overflow: hidden;
      backdrop-filter: blur(10px);
    }

    .card:hover {
      transform: translateY(-8px);
      box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    }

    .btn-primary {
      background: var(--gradient-primary);
      border: none;
      font-weight: 600;
      padding: 14px 28px;
      border-radius: 15px;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
      font-size: 1rem;
    }

    .btn-primary:hover {
      transform: translateY(-3px);
      box-shadow: 0 12px 25px rgba(102, 126, 234, 0.4);
    }

    .btn-primary:disabled {
      background: #9ca3af;
      transform: none;
      box-shadow: none;
      cursor: not-allowed;
    }

    .badge {
      padding: 8px 16px;
      border-radius: 25px;
      font-weight: 600;
      font-size: 0.85rem;
    }

    .badge.bg-warning { background: var(--warning-color) !important; color: white; }
    .badge.bg-info { background: var(--info-color) !important; }
    .badge.bg-danger { background: var(--danger-color) !important; }
    .badge.bg-primary { background: var(--primary-color) !important; }
    .badge.bg-secondary { background: #6b7280 !important; }
    .badge.bg-success { background: var(--success-color) !important; }

    /* Modern Timeline Styles */
    .modern-timeline {
      position: relative;
      padding: 40px 0;
    }
    
    .modern-timeline::before {
      content: '';
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      top: 0;
      bottom: 0;
      width: 4px;
      background: var(--gradient-primary);
      border-radius: 10px;
    }
    
    .timeline-item-modern {
      position: relative;
      margin-bottom: 60px;
      width: 100%;
      display: flex;
      justify-content: flex-start;
    }
    
    .timeline-item-modern:nth-child(even) {
      justify-content: flex-end;
    }
    
    .timeline-content-modern {
      background: var(--card-bg);
      border-radius: 20px;
      padding: 25px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.1);
      border: 1px solid var(--border-color);
      width: 45%;
      position: relative;
      transition: all 0.3s ease;
    }
    
    .timeline-content-modern:hover {
      transform: translateY(-5px);
      box-shadow: 0 15px 40px rgba(0,0,0,0.15);
    }
    
    .timeline-content-modern::before {
      content: '';
      position: absolute;
      top: 30px;
      width: 20px;
      height: 20px;
      background: var(--card-bg);
      transform: rotate(45deg);
      border-right: 1px solid var(--border-color);
      border-bottom: 1px solid var(--border-color);
    }
    
    .timeline-item-modern:nth-child(odd) .timeline-content-modern::before {
      right: -10px;
    }
    
    .timeline-item-modern:nth-child(even) .timeline-content-modern::before {
      left: -10px;
      border-right: none;
      border-left: 1px solid var(--border-color);
      border-bottom: 1px solid var(--border-color);
    }
    
    .timeline-icon-modern {
      position: absolute;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      width: 60px;
      height: 60px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.5rem;
      box-shadow: 0 5px 20px rgba(0,0,0,0.2);
      z-index: 2;
    }
    
    .timeline-item-modern.completed .timeline-icon-modern {
      background: var(--gradient-success);
    }
    
    .timeline-item-modern.approved .timeline-icon-modern {
      background: var(--gradient-success);
    }
    
    .timeline-item-modern.pending .timeline-icon-modern {
      background: var(--gradient-secondary);
    }
    
    .timeline-item-modern.in-progress .timeline-icon-modern {
      background: var(--gradient-primary);
      animation: pulse 2s infinite;
    }
    
    .timeline-step {
      position: absolute;
      top: -10px;
      left: 20px;
      background: var(--primary-color);
      color: white;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 0.9rem;
    }
    
    .timeline-content-modern h6 {
      color: var(--text-color);
      font-weight: 700;
      margin-bottom: 10px;
      font-size: 1.1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    
    .timeline-content-modern .time-info {
      color: var(--text-color);
      font-size: 0.9rem;
      margin-bottom: 10px;
      opacity: 0.8;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .timeline-content-modern .description {
      color: var(--text-color);
      font-size: 0.9rem;
      line-height: 1.5;
      opacity: 0.8;
      padding: 10px 15px;
      background: rgba(0,0,0,0.03);
      border-radius: 10px;
      border-left: 3px solid var(--primary-color);
    }
    
    [data-theme="dark"] .timeline-content-modern .description {
      background: rgba(255,255,255,0.05);
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.8; transform: scale(1.1); }
    }

    /* Theme toggle button - Bottom right for mobile */
    .theme-toggle {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: var(--card-bg);
      border: 2px solid var(--border-color);
      border-radius: 50%;
      width: 55px;
      height: 55px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 8px 25px rgba(0,0,0,0.15);
      transition: all 0.3s ease;
      z-index: 1000;
      color: var(--text-color);
    }

    .theme-toggle:hover {
      transform: scale(1.1) rotate(15deg);
      box-shadow: 0 12px 30px rgba(0,0,0,0.2);
    }

    .form-control, .form-select {
      border: 2px solid var(--border-color);
      border-radius: 15px;
      padding: 14px 18px;
      font-weight: 500;
      transition: all 0.3s ease;
      background: var(--card-bg);
      color: var(--text-color);
      font-size: 1rem;
    }

    .form-control:focus, .form-select:focus {
      border-color: var(--primary-color);
      box-shadow: 0 0 0 0.3rem rgba(37,99,235,0.15);
      transform: translateY(-2px);
    }

    .footer {
      background: var(--gradient-primary);
      color: white;
      text-align: center;
      padding: 25px 0;
      margin-top: 60px;
      font-weight: 600;
      font-size: 1rem;
    }

    /* Search form improvements */
    .search-form {
      background: var(--card-bg);
      padding: 25px;
      border-radius: 20px;
      margin-bottom: 30px;
      border: 1px solid var(--border-color);
      box-shadow: 0 5px 25px rgba(0,0,0,0.08);
    }

    .search-form .form-control {
      background: var(--card-bg);
      color: var(--text-color);
    }

    .search-form .input-group-text {
      background: var(--card-bg);
      color: var(--text-color);
      border-color: var(--border-color);
      border-radius: 15px 0 0 15px;
    }

    .table {
      color: var(--text-color);
      border-radius: 15px;
      overflow: hidden;
    }

    .table th {
      background: var(--gradient-primary);
      color: white;
      font-weight: 600;
      padding: 15px;
      border: none;
    }

    .table td {
      background: var(--card-bg);
      color: var(--text-color);
      padding: 15px;
      border-color: var(--border-color);
    }

    .table-hover tbody tr:hover {
      background: rgba(0,0,0,0.03);
      transform: translateX(5px);
      transition: all 0.3s ease;
    }

    [data-theme="dark"] .table-hover tbody tr:hover {
      background: rgba(255,255,255,0.05);
    }

    @media (max-width: 768px) {
      .container { 
        margin: 1rem auto; 
        padding: 0 0.5rem; 
      }
      
      .modern-timeline::before { 
        left: 30px; 
      }
      
      .timeline-item-modern { 
        justify-content: flex-start !important; 
        margin-bottom: 40px;
      }
      
      .timeline-content-modern { 
        width: calc(100% - 80px); 
        margin-left: 80px; 
        padding: 20px;
      }
      
      .timeline-content-modern::before { 
        left: -10px !important; 
        border-right: none; 
        border-left: 1px solid var(--border-color); 
        border-bottom: 1px solid var(--border-color); 
      }
      
      .timeline-icon-modern { 
        left: 30px; 
        transform: translateX(0); 
        width: 50px;
        height: 50px;
        font-size: 1.2rem;
      }
      
      .navbar-brand { 
        font-size: 1.1rem; 
      }
      
      .nav-link { 
        padding: 6px 8px !important; 
        font-size: 0.8rem; 
      }
      
      .btn-primary { 
        padding: 12px 20px; 
        font-size: 0.9rem; 
      }
      
      .card {
        border-radius: 15px;
      }
      
      .theme-toggle {
        bottom: 20px;
        right: 15px;
        width: 50px;
        height: 50px;
      }
      
      .stats-container {
        grid-template-columns: 1fr;
        gap: 15px;
      }
      
      .stat-card {
        padding: 20px;
      }
      
      .stat-number {
        font-size: 2rem;
      }
      
      .search-form {
        padding: 20px;
      }
      
      .table-responsive {
        font-size: 0.85rem;
      }
      
      .table th, .table td {
        padding: 10px 8px;
      }
      
      .btn-primary {
        padding: 12px 20px;
        font-size: 0.9rem;
      }
      
      /* Mobile navbar improvements */
      .navbar-collapse {
        background: var(--gradient-primary);
        border-radius: 0 0 15px 15px;
        padding: 15px;
        margin-top: 10px;
      }
      
      .navbar-nav {
        text-align: center;
      }
      
      .nav-link {
        padding: 10px 15px !important;
        border-radius: 10px;
        margin: 2px 0;
      }
      
      .nav-link:hover {
        background: rgba(255,255,255,0.1);
      }
    }

    @media (min-width: 769px) {
      .theme-toggle {
        top: 20px;
        right: 20px;
        bottom: auto;
      }
    }

    .fade-in {
      animation: fadeInUp 0.8s ease-out;
    }

    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(40px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .admin-card-container {
        display: flex;
        flex-wrap: wrap;
        gap: 25px;
        justify-content: center;
    }
    
    .status-card {
        background: var(--card-bg);
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        padding: 25px;
        border: 1px solid var(--border-color);
        text-align: center;
        transition: all 0.3s ease;
        min-width: 200px;
    }
    
    .status-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
    }
    
    .status-card h5 {
        font-weight: 700;
        margin-top: 15px;
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .modal-backdrop {
      background-color: rgba(0, 0, 0, 0.6);
    }
    
    .modal-content {
      border-radius: 25px;
      border: none;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      background: var(--card-bg);
      color: var(--text-color);
    }
    
    .modal-header {
      background: var(--gradient-primary);
      color: white;
      border-radius: 25px 25px 0 0;
      border: none;
      padding: 25px;
    }
    
    .modal-body {
      padding: 30px;
    }
    
    .modal-footer {
      border-top: 1px solid var(--border-color);
      padding: 25px;
      border-radius: 0 0 25px 25px;
    }

    .certificate-options {
      background: var(--card-bg);
      border-radius: 15px;
      padding: 25px;
      margin-top: 20px;
      border: 1px solid var(--border-color);
      box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    }

    .certificate-options h6 {
      color: var(--primary-color);
      margin-bottom: 20px;
      font-weight: 700;
      font-size: 1.1rem;
    }

    .form-check-label {
      color: var(--text-color);
      font-weight: 500;
    }

    .text-muted {
      color: var(--text-color) !important;
      opacity: 0.7;
    }

    /* Application Stats */
    .stats-container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .stat-card {
      background: var(--card-bg);
      border-radius: 20px;
      padding: 25px;
      text-align: center;
      box-shadow: 0 8px 25px rgba(0,0,0,0.1);
      border: 1px solid var(--border-color);
      transition: all 0.3s ease;
    }

    .stat-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }

    .stat-number {
      font-size: 2.5rem;
      font-weight: 700;
      margin-bottom: 10px;
      background: var(--gradient-primary);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .stat-label {
      color: var(--text-color);
      font-weight: 600;
      opacity: 0.8;
    }

    /* Touch improvements for mobile */
    .btn, .form-control, .form-select, .nav-link {
      -webkit-tap-highlight-color: transparent;
    }

    .btn:active, .nav-link:active {
      transform: scale(0.98);
    }
    
    /* Admin Search Results */
    .admin-search-results {
      margin-top: 30px;
    }
    
    .search-result-card {
      background: var(--card-bg);
      border-radius: 20px;
      padding: 25px;
      margin-bottom: 20px;
      border: 1px solid var(--border-color);
      box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    }
    
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
    }

    .status-badge.completed {
      background: rgba(16, 185, 129, 0.15);
      color: #047857;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-badge.approved {
      background: rgba(16, 185, 129, 0.15);
      color: #047857;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-badge.pending {
      background: rgba(245, 158, 11, 0.15);
      color: #92400e;
      border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .status-badge.in-progress {
      background: rgba(6, 182, 212, 0.15);
      color: #155e75;
      border: 1px solid rgba(6, 182, 212, 0.3);
    }
    
    /* Loading Spinner */
    .loading-spinner {
      display: none;
      text-align: center;
      padding: 20px;
    }
    
    .spinner-border {
      width: 3rem;
      height: 3rem;
    }
  </style>
</head>
<body>
  <div class="theme-toggle" onclick="toggleTheme()">
    <i class="fas fa-moon" id="theme-icon"></i>
  </div>
  
  <nav class="navbar navbar-expand-lg navbar-dark">
    <div class="container">
      <a class="navbar-brand" href="/">
        <img src="https://upload.wikimedia.org/wikipedia/en/thumb/b/b4/Sri_Krishnadevaraya_University_logo.png/220px-Sri_Krishnadevaraya_University_logo.png" alt="SKU Logo">
        <span class="d-none d-md-inline">Sri Krishnadevaraya University</span>
        <span class="d-md-none">SK University</span>
      </a>
      
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">
          <li class="nav-item"><a class="nav-link" href="/"><i class="fas fa-file-alt me-1"></i>Application</a></li>
          <li class="nav-item"><a class="nav-link" href="/student_portal"><i class="fas fa-user-graduate me-1"></i>Student Portal</a></li>
          <li class="nav-item"><a class="nav-link" href="/block"><i class="fas fa-building me-1"></i>Block Office</a></li>
          <li class="nav-item"><a class="nav-link" href="/computer_session"><i class="fas fa-laptop me-1"></i>Computer Session</a></li>
          <li class="nav-item"><a class="nav-link" href="/reblock"><i class="fas fa-redo me-1"></i>Re-Block</a></li>
          <li class="nav-item"><a class="nav-link" href="/ar_session"><i class="fas fa-cube me-1"></i>AR Session</a></li>
          <li class="nav-item"><a class="nav-link" href="/vr_session"><i class="fas fa-vr-cardboard me-1"></i>VR Session</a></li>
          <li class="nav-item"><a class="nav-link" href="/post_session"><i class="fas fa-mail-bulk me-1"></i>Post Session</a></li>
          <li class="nav-item"><a class="nav-link" href="/verified_certificates"><i class="fas fa-certificate me-1"></i>Verified</a></li>
          <li class="nav-item"><a class="nav-link" href="/admin"><i class="fas fa-user-shield me-1"></i>Admin</a></li>
        </ul>
      </div>
    </div>
  </nav>

  <main class="container">
    {{content}}
  </main>

  <footer class="footer">
    <p>&copy; 2025 Sri Krishnadevaraya University. All rights reserved.</p>
  </footer>

  <!-- Download Modal -->
  <div class="modal fade" id="downloadModal" tabindex="-1" aria-labelledby="downloadModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="downloadModalLabel"><i class="fas fa-download me-2"></i>Download Data</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <form id="downloadForm" action="/admin/download_excel" method="post">
            <div class="mb-3">
              <label for="fromDate" class="form-label">From Date</label>
              <input type="date" class="form-control" id="fromDate" name="from_date" required>
            </div>
            <div class="mb-3">
              <label for="toDate" class="form-label">To Date</label>
              <input type="date" class="form-control" id="toDate" name="to_date" required>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" form="downloadForm" class="btn btn-primary">Download Excel</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Duplicate Application Modal -->
  <div class="modal fade" id="duplicateModal" tabindex="-1" aria-labelledby="duplicateModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="duplicateModalLabel"><i class="fas fa-exclamation-triangle me-2"></i>Duplicate Application Detected</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p>This hall ticket number <strong id="duplicateHallTicket"></strong> has already been issued for <strong id="duplicateCertificate"></strong> certificate.</p>
          <p>Please check the student portal for the status of your application.</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal">OK</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Loading Spinner -->
  <div class="loading-spinner" id="loadingSpinner">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
    <p class="mt-2">Processing your request...</p>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    function toggleTheme() {
      const body = document.body;
      const icon = document.getElementById('theme-icon');
      
      if (body.getAttribute('data-theme') === 'dark') {
        body.removeAttribute('data-theme');
        icon.className = 'fas fa-moon';
        localStorage.setItem('theme', 'light');
      } else {
        body.setAttribute('data-theme', 'dark');
        icon.className = 'fas fa-sun';
        localStorage.setItem('theme', 'dark');
      }
    }

    function showLoading() {
      document.getElementById('loadingSpinner').style.display = 'block';
    }

    function hideLoading() {
      document.getElementById('loadingSpinner').style.display = 'none';
    }

    // Load saved theme
    document.addEventListener('DOMContentLoaded', function() {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        document.getElementById('theme-icon').className = 'fas fa-sun';
      }
      
      // Add touch effects for mobile
      document.querySelectorAll('.btn, .nav-link').forEach(element => {
        element.addEventListener('touchstart', function() {
          this.style.transform = 'scale(0.98)';
        });
        
        element.addEventListener('touchend', function() {
          this.style.transform = '';
        });
      });
      
      // Check for duplicate application on form submission
      const applicationForm = document.getElementById('applicationForm');
      if (applicationForm) {
        applicationForm.addEventListener('submit', function(e) {
          const rollNumber = document.getElementById('roll_number').value;
          const certificateType = document.getElementById('certificate_type').value;
          
          if (rollNumber && certificateType) {
            showLoading();
            fetch('/check_duplicate', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
              body: `roll_number=${encodeURIComponent(rollNumber)}&certificate_type=${encodeURIComponent(certificateType)}`
            })
            .then(response => response.json())
            .then(data => {
              hideLoading();
              if (data.duplicate) {
                e.preventDefault();
                document.getElementById('duplicateHallTicket').textContent = rollNumber;
                document.getElementById('duplicateCertificate').textContent = certificateType;
                const duplicateModal = new bootstrap.Modal(document.getElementById('duplicateModal'));
                duplicateModal.show();
              }
            })
            .catch(error => {
              console.error('Error checking duplicate:', error);
              hideLoading();
            });
          }
        });
      }
      
      // Add loading to form submissions
      document.querySelectorAll('form').forEach(form => {
        if (form.id !== 'applicationForm') {
          form.addEventListener('submit', function() {
            showLoading();
          });
        }
      });
    });
    
    // Admin search function
    function adminSearch() {
      const hallTicket = document.getElementById('adminSearchInput').value;
      if (!hallTicket) {
        alert('Please enter a hall ticket number');
        return;
      }
      
      showLoading();
      window.location.href = `/admin/search?hall_ticket=${encodeURIComponent(hallTicket)}`;
    }
    
    // Handle page load completion
    window.addEventListener('load', function() {
      hideLoading();
    });
  </script>
</body>
</html>"""

INDEX = """<div class="card p-4 fade-in">
  <div class="text-center mb-4">
    <i class="fas fa-graduation-cap fa-3x mb-3" style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;"></i>
    <h3 class="mb-3">Certificate Application</h3>
    <p class="text-muted">Apply for your academic certificates online with our streamlined process</p>
  </div>
  
  <form method="post" action="/submit_application" onsubmit="return validateForm()" id="applicationForm">
    <div class="row">
      <div class="col-md-6 mb-3">
        <label class="form-label fw-semibold"><i class="fas fa-user me-2"></i>Student Name *</label>
        <input class="form-control" name="student_name" id="student_name" required>
      </div>
      
      <div class="col-md-6 mb-3">
        <label class="form-label fw-semibold"><i class="fas fa-id-card me-2"></i>Hall Ticket No *</label>
        <input class="form-control" name="roll_number" id="roll_number" required>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6 mb-3">
        <label class="form-label fw-semibold"><i class="fas fa-graduation-cap me-2"></i>Degree Type *</label>
        <select class="form-select" name="degree_type" id="degree" required>
          <option value="">Select Degree Type</option>
          <option value="UG">Under Graduate (UG)</option>
          <option value="PG">Post Graduate (PG)</option>
          <option value="Master of Philosophy">Master of Philosophy</option>
          <option value="Doctor of Philosophy">Doctor of Philosophy</option>
        </select>
      </div>
      
      <div class="col-md-6 mb-3" id="methodDiv" style="display:none;">
        <label class="form-label fw-semibold"><i class="fas fa-list me-2"></i>Program *</label>
        <select class="form-select" name="sub_category" id="method" required>
          <option value="">Select Program</option>
        </select>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6 mb-3" id="certificateTypeDiv" style="display:none;">
        <label class="form-label fw-semibold"><i class="fas fa-certificate me-2"></i>Certificate Type *</label>
        <select class="form-select" name="certificate_type" id="certificate_type" required onchange="showCertificateOptions()">
          <option value="">Select Certificate Type</option>
          <option value="Provisional Certificate">Provisional Certificate</option>
          <option value="Migration Certificate">Migration Certificate</option>
          <option value="Convocation Certificate">Convocation Certificate</option>
          <option value="Transcripts Certificate">Transcripts Certificate</option>
        </select>
      </div>
    </div>

    <!-- Certificate Specific Options -->
    <div id="certificateOptions" style="display: none;">
      <!-- This will be populated dynamically based on certificate type -->
    </div>

    <div class="text-center mt-4">
      <button type="submit" id="submitBtn" class="btn btn-primary btn-lg px-5" disabled>
        <i class="fas fa-paper-plane me-2"></i>Submit Application
      </button>
      <div id="formStatus" class="mt-3 text-muted small">
        Please fill all required fields to enable submission
      </div>
    </div>
  </form>
</div>

<script>
const degreeOptions = {
  'UG': ['B.Tech', 'B.Pharmacy', 'B.A', 'B.Sc', 'B.Com', 'BBA', 'B.Ed', 'B.P.Ed'],
  'PG': ['M.Tech', 'M.Pharmacy', 'MBA', 'M.A', 'M.Sc', 'M.Com', 'M.P.Ed', 'MSW', 'M.Lib.I.Sc'],
  'Master of Philosophy': ['M.Phil'],
  'Doctor of Philosophy': ['Ph.D']
};

const certificateOptions = {
  'Provisional Certificate': {
    documents: [
      'SBI Challan',
      'Application Form',
      'Lower Degree Convocation',
      'All Years Marks Memo',
      'Other University Original Migration',
      'Inter Memo',
      '10th Memo',
      'Aadhaar Card',
      'A4 Size Cloth Cover'
    ],
    feeOptions: [
      { value: 'within_state_50', label: 'Within State - Rs 50', price: '50' },
      { value: 'other_state_60', label: 'Other State - Rs 60', price: '60' }
    ],
    additional: 'Attach Postal Stamp'
  },
  'Migration Certificate': {
    documents: [
      'SBI Challan',
      'Application Form',
      'Inter Memo',
      '10th Memo',
      'Aadhaar Card',
      'A4 Size Cloth Cover',
      'Transfer Certificate',
      'CCM and Provisional/Old Provisional'
    ],
    feeOptions: [
      { value: 'within_state_50', label: 'Within State - Rs 50', price: '50' },
      { value: 'other_state_60', label: 'Other State - Rs 60', price: '60' }
    ],
    additional: 'Attach Postal Stamp'
  },
  'Convocation Certificate': {
    documents: [
      'SBI Challan',
      'Application Form',
      'Inter Memo',
      '10th Memo',
      'Aadhaar Card',
      'A4 Size Cloth Cover',
      'Transfer Certificate',
      'CCM and Provisional/Old Provisional'
    ],
    feeOptions: [
      { value: 'within_state_50', label: 'Within State - Rs 50', price: '50' },
      { value: 'other_state_60', label: 'Other State - Rs 60', price: '60' }
    ],
    additional: 'Attach Postal Stamp, Application - 2 Photos, Gazetted - 1 Photo above Gazetted Attestation'
  },
  'Transcripts Certificate': {
    documents: [
      'SBI Challan',
      'Application Form',
      'Inter Memo',
      '10th Memo',
      'Aadhaar Card',
      'A4 Size Cloth Cover',
      'Transfer Certificate',
      'CCM and Provisional/Old Provisional',
      'Convocation'
    ],
    feeOptions: [
      { value: 'within_state_80', label: 'Within State - Rs 80', price: '80' },
      { value: 'other_state_100', label: 'Other State - Rs 100', price: '100' }
    ],
    additional: 'Attach Postal Stamp'
  }
};

function updateFormStatus() {
  const statusElement = document.getElementById('formStatus');
  const submitBtn = document.getElementById('submitBtn');
  
  if (submitBtn.disabled) {
    statusElement.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Please complete all required fields to enable submission';
    statusElement.style.color = '#ef4444';
  } else {
    statusElement.innerHTML = '<i class="fas fa-check-circle me-2"></i>All requirements completed. Ready to submit!';
    statusElement.style.color = '#10b981';
  }
}

function showCertificateOptions() {
  const certificateType = document.getElementById('certificate_type').value;
  const optionsContainer = document.getElementById('certificateOptions');
  
  if (certificateType && certificateOptions[certificateType]) {
    const options = certificateOptions[certificateType];
    let html = `
      <div class="certificate-options">
        <h6><i class="fas fa-file-alt me-2"></i>Required Documents for ${certificateType}</h6>
        <div class="row">
    `;
    
    // Split documents into two columns for better layout
    const midIndex = Math.ceil(options.documents.length / 2);
    const firstColumn = options.documents.slice(0, midIndex);
    const secondColumn = options.documents.slice(midIndex);
    
    html += `
      <div class="col-md-6">
        ${firstColumn.map(doc => `
          <div class="form-check mb-2">
            <input class="form-check-input" type="checkbox" name="certificate_documents" value="${doc}" id="doc_${doc.replace(/\s+/g, '_')}" required>
            <label class="form-check-label" for="doc_${doc.replace(/\s+/g, '_')}">
              <i class="fas fa-check-circle me-2"></i>${doc}
            </label>
          </div>
        `).join('')}
      </div>
      <div class="col-md-6">
        ${secondColumn.map(doc => `
          <div class="form-check mb-2">
            <input class="form-check-input" type="checkbox" name="certificate_documents" value="${doc}" id="doc_${doc.replace(/\s+/g, '_')}" required>
            <label class="form-check-label" for="doc_${doc.replace(/\s+/g, '_')}">
              <i class="fas fa-check-circle me-2"></i>${doc}
            </label>
          </div>
        `).join('')}
      </div>
    </div>
    
    <div class="mt-4">
      <h6><i class="fas fa-money-bill-wave me-2"></i>Fee Options</h6>
      <div class="row">
        <div class="col-md-6">
          ${options.feeOptions.map(fee => `
            <div class="form-check mb-2">
              <input class="form-check-input" type="radio" name="fee_option" value="${fee.value}" id="fee_${fee.value}" required>
              <label class="form-check-label" for="fee_${fee.value}">
                <i class="fas fa-rupee-sign me-2"></i>${fee.label}
              </label>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
    
    <div class="mt-3">
      <h6><i class="fas fa-info-circle me-2"></i>Additional Requirements</h6>
      <p class="text-muted">${options.additional}</p>
    </div>
    `;
    
    optionsContainer.innerHTML = html;
    optionsContainer.style.display = 'block';
  } else {
    optionsContainer.style.display = 'none';
    optionsContainer.innerHTML = '';
  }
  checkFormValidity();
}

document.getElementById('degree').addEventListener('change', function() {
  const selectedDegree = this.value;
  const methodSelect = document.getElementById('method');
  const methodDiv = document.getElementById('methodDiv');
  const certificateTypeDiv = document.getElementById('certificateTypeDiv');
  
  if (selectedDegree && degreeOptions[selectedDegree]) {
    methodSelect.innerHTML = '<option value="">Select Program</option>';
    degreeOptions[selectedDegree].forEach(program => {
      methodSelect.innerHTML += `<option value="${program}">${program}</option>`;
    });
    methodDiv.style.display = 'block';
    certificateTypeDiv.style.display = 'none';
    document.getElementById('certificateOptions').style.display = 'none';
    document.getElementById('certificateOptions').innerHTML = '';
  } else {
    methodDiv.style.display = 'none';
    certificateTypeDiv.style.display = 'none';
    document.getElementById('certificateOptions').style.display = 'none';
    document.getElementById('certificateOptions').innerHTML = '';
  }
  checkFormValidity();
});

document.getElementById('method').addEventListener('change', function() {
  const selectedProgram = this.value;
  const certificateTypeDiv = document.getElementById('certificateTypeDiv');
  
  if (selectedProgram) {
    certificateTypeDiv.style.display = 'block';
  } else {
    certificateTypeDiv.style.display = 'none';
    document.getElementById('certificateOptions').style.display = 'none';
    document.getElementById('certificateOptions').innerHTML = '';
  }
  checkFormValidity();
});

// Track all form elements for validation
const formElements = ['student_name', 'roll_number', 'degree_type', 'sub_category', 'certificate_type'];
formElements.forEach(elementName => {
  const element = document.getElementById(elementName);
  if (element) {
    element.addEventListener('input', checkFormValidity);
    element.addEventListener('change', checkFormValidity);
  }
});

// Also track certificate documents and fee options
document.addEventListener('change', function(e) {
  if (e.target.name === 'certificate_documents' || e.target.name === 'fee_option') {
    checkFormValidity();
  }
});

function checkFormValidity() {
  const name = document.getElementById('student_name').value.trim();
  const rollNumber = document.getElementById('roll_number').value.trim();
  const degreeType = document.getElementById('degree').value;
  const subCategory = document.getElementById('method').value;
  const certificateType = document.getElementById('certificate_type').value;
  
  // Check if all required fields are filled
  const basicFieldsValid = name && rollNumber && degreeType && 
    (degreeOptions[degreeType] ? subCategory : true) && certificateType;
  
  if (!basicFieldsValid) {
    document.getElementById('submitBtn').disabled = true;
    updateFormStatus();
    return;
  }
  
  // Check certificate-specific requirements
  const certificateDocs = document.querySelectorAll('input[name="certificate_documents"]:checked');
  const feeOption = document.querySelector('input[name="fee_option"]:checked');
  
  const certificateValid = certificateDocs.length > 0 && feeOption;
  
  document.getElementById('submitBtn').disabled = !certificateValid;
  updateFormStatus();
}

function validateForm() {
  const submitBtn = document.getElementById('submitBtn');
  if (submitBtn.disabled) {
    alert('Please complete all required fields and select all required documents and fee option.');
    return false;
  }
  
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';
  submitBtn.disabled = true;
  
  return true;
}

// Initialize form status
updateFormStatus();
</script>"""

STUDENT_PORTAL = """<div class="fade-in">
  <div class="card p-4 mb-4">
    <div class="text-center mb-4">
      <i class="fas fa-search fa-3x mb-3" style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;"></i>
      <h3>Student Portal - Track Your Application</h3>
      <p class="text-muted">Enter your hall ticket number to track your application status</p>
    </div>
    
    <form method="post" class="search-form">
      <div class="row g-3">
        <div class="col-md-9">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-ticket-alt"></i></span>
            <input name="hall_ticket" class="form-control" placeholder="Enter Hall Ticket Number" required>
          </div>
        </div>
        <div class="col-md-3">
          <button class="btn btn-primary w-100">
            <i class="fas fa-search me-2"></i>Track Application
          </button>
        </div>
      </div>
    </form>
  </div>

  {% if app_data %}
  <div class="card mb-4">
    <div class="card-header" style="background: var(--gradient-primary); color: white;">
      <h5 class="mb-0"><i class="fas fa-user-graduate me-2"></i>Application Details</h5>
    </div>
    <div class="card-body">
      <div class="row">
        <div class="col-md-6">
          <p><strong><i class="fas fa-user me-2"></i>Name:</strong> {{app_data.student_name}}</p>
          <p><strong><i class="fas fa-id-badge me-2"></i>Application No:</strong> {{app_data.app_number}}</p>
          <p><strong><i class="fas fa-certificate me-2"></i>Certificate Type:</strong> {{app_data.certificate_type}}</p>
        </div>
        <div class="col-md-6">
          <p><strong><i class="fas fa-graduation-cap me-2"></i>Degree:</strong> {{app_data.degree_type}} - {{app_data.sub_category}}</p>
          <p><strong><i class="fas fa-map-marker-alt me-2"></i>Current Stage:</strong> <span class="badge bg-info">{{current_stage}}</span></p>
          <p><strong><i class="fas fa-money-bill-wave me-2"></i>Fee Option:</strong> {{app_data.fee_option_label}}</p>
        </div>
      </div>
      {% if app_data.certificate_documents %}
      <div class="mt-3">
        <strong><i class="fas fa-file-alt me-2"></i>Submitted Documents:</strong>
        <div class="mt-2">
          {% for doc in app_data.certificate_documents %}
          <span class="badge bg-success me-2 mb-2">{{ doc }}</span>
          {% endfor %}
        </div>
      </div>
      {% endif %}
    </div>
  </div>

  <div class="card mb-4">
    <div class="card-header" style="background: var(--gradient-primary); color: white;">
      <h5 class="mb-0"><i class="fas fa-history me-2"></i>Application Timeline</h5>
    </div>
    <div class="card-body">
      <div class="progress mb-4" style="height: 12px;">
        <div class="progress-bar bg-success" role="progressbar" style="width: {{progress_percentage}}%" aria-valuenow="{{progress_percentage}}" aria-valuemin="0" aria-valuemax="100"></div>
      </div>
      
      <div class="modern-timeline">
        {% for event in timeline %}
        <div class="timeline-item-modern {{event.css_class}}">
          <div class="timeline-icon-modern">
            <i class="fas {{event.icon}}"></i>
          </div>
          <div class="timeline-content-modern">
            <div class="timeline-step">{{event.step}}</div>
            <h6>
              {{event.stage}}
              <span class="status-badge {{event.css_class}}">{{event.status}}</span>
            </h6>
            <div class="time-info"><i class="far fa-clock me-1"></i>{{event.timestamp}}</div>
            {% if event.description %}
            <div class="description">{{event.description}}</div>
            {% endif %}
          </div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
  {% endif %}
</div>"""

ADMIN_SUMMARY_TEMPLATE = """
<div class="fade-in">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h3><i class="fas fa-user-shield me-2"></i>Admin Dashboard</h3>
    <div class="d-flex gap-2">
      <div class="badge bg-info fs-6">
        <i class="fas fa-file-alt me-1"></i>{{apps|length}} Pending Applications
      </div>
      <button type="button" class="btn btn-success" data-bs-toggle="modal" data-bs-target="#downloadModal">
        <i class="fas fa-download me-2"></i>Download
      </button>
    </div>
  </div>
  
  <!-- Admin Search Form -->
  <div class="card p-4 mb-4">
    <div class="text-center mb-4">
      <i class="fas fa-search fa-3x mb-3" style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;"></i>
      <h4>Search Application by Hall Ticket Number</h4>
      <p class="text-muted">Enter hall ticket number to search for specific application</p>
    </div>
    
    <div class="row g-3">
      <div class="col-md-9">
        <div class="input-group">
          <span class="input-group-text"><i class="fas fa-ticket-alt"></i></span>
          <input id="adminSearchInput" class="form-control" placeholder="Enter Hall Ticket Number">
        </div>
      </div>
      <div class="col-md-3">
        <button class="btn btn-primary w-100" onclick="adminSearch()">
          <i class="fas fa-search me-2"></i>Search
        </button>
      </div>
    </div>
  </div>
  
  <!-- Statistics Cards -->
  <div class="stats-container mb-4">
    <div class="stat-card">
      <div class="stat-number">{{ total_applications }}</div>
      <div class="stat-label">Total Applications</div>
    </div>
    <div class="stat-card">
      <div class="stat-number">{{ pending_applications }}</div>
      <div class="stat-label">Pending Applications</div>
    </div>
    <div class="stat-card">
      <div class="stat-number">{{ verified_applications }}</div>
      <div class="stat-label">Verified Certificates</div>
    </div>
  </div>
  
  <form method="get" class="search-form mb-4">
    <div class="row g-3">
      <div class="col-md-4">
        <div class="input-group">
          <span class="input-group-text"><i class="fas fa-search"></i></span>
          <input name="search" class="form-control" placeholder="Search by name or hall ticket" 
                 value="{{request.args.get('search', '')}}">
        </div>
      </div>
      <div class="col-md-3">
        <div class="input-group">
          <span class="input-group-text"><i class="fas fa-calendar"></i></span>
          <input name="date" type="date" class="form-control" value="{{request.args.get('date', '')}}">
        </div>
      </div>
      <div class="col-md-2">
        <button class="btn btn-primary w-100">
          <i class="fas fa-search me-2"></i>Search
        </button>
      </div>
      <div class="col-md-3">
        <a href="/admin" class="btn btn-secondary w-100">
          <i class="fas fa-refresh me-2"></i>Clear
        </a>
      </div>
    </div>
  </form>

  <div class="row">
    {% for a in apps %}
    <div class="col-lg-6 col-xl-4 mb-4">
      <div class="card h-100">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start mb-3">
            <div class="flex-grow-1">
              <h6 class="card-title mb-1">
                <i class="fas fa-user me-2"></i>{{a.student_name}}
              </h6>
              <small class="text-muted d-block mb-1">
                <i class="fas fa-id-badge me-1"></i>{{a.app_number}}
              </small>
              <small class="text-muted">
                <i class="fas fa-certificate me-1"></i>{{a.certificate_type}}
              </small>
              <small class="text-muted d-block">
                <i class="far fa-clock me-1"></i>{{a.submission_time}}
              </small>
            </div>
            <span class="badge bg-info">
              <i class="fas fa-map-marker-alt me-1"></i>{{get_current_stage(a)}}
            </span>
          </div>
          
          <div class="d-flex justify-content-between align-items-center">
            <small class="text-info">
              <i class="fas fa-graduation-cap me-1"></i>{{a.degree_type}} - {{a.sub_category}}
            </small>
          </div>
        </div>
        <div class="card-footer bg-transparent">
          <a href="/admin/details/{{a.app_number}}" class="btn btn-primary btn-sm w-100">
            <i class="fas fa-eye me-2"></i>View Details
          </a>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
</div>
"""

ADMIN_SEARCH_TEMPLATE = """
<div class="fade-in">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h3><i class="fas fa-search me-2"></i>Admin Search Results</h3>
    <a href="/admin" class="btn btn-secondary">
      <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
    </a>
  </div>
  
  <div class="card p-4 mb-4">
    <div class="text-center mb-4">
      <i class="fas fa-search fa-3x mb-3" style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;"></i>
      <h4>Search Results for Hall Ticket: {{hall_ticket}}</h4>
    </div>
    
    {% if search_results %}
    <div class="admin-search-results">
      {% for app in search_results %}
      <div class="search-result-card">
        <div class="row">
          <div class="col-md-6">
            <h6><i class="fas fa-user me-2"></i>{{app.student_name}}</h6>
            <p><strong>Application No:</strong> {{app.app_number}}</p>
            <p><strong>Certificate Type:</strong> {{app.certificate_type}}</p>
            <p><strong>Degree:</strong> {{app.degree_type}} - {{app.sub_category}}</p>
          </div>
          <div class="col-md-6">
            <p><strong>Hall Ticket No:</strong> {{app.roll_number}}</p>
            <p><strong>Current Stage:</strong> <span class="badge bg-info">{{get_current_stage(app)}}</span></p>
            <p><strong>Submission Date:</strong> {{app.submission_time}}</p>
            <p><strong>Status:</strong> 
              {% if app.verified_time %}
                <span class="badge bg-success">Verified</span>
              {% else %}
                <span class="badge bg-warning">Pending</span>
              {% endif %}
            </p>
          </div>
        </div>
        <div class="mt-3">
          <a href="/admin/details/{{app.app_number}}" class="btn btn-primary btn-sm">
            <i class="fas fa-eye me-2"></i>View Full Details
          </a>
        </div>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="text-center py-4">
      <i class="fas fa-search fa-3x mb-3 text-muted"></i>
      <h5 class="text-muted">No applications found for this hall ticket number</h5>
      <p class="text-muted">Please check the hall ticket number and try again</p>
    </div>
    {% endif %}
  </div>
</div>
"""

ADMIN_DETAIL_TEMPLATE = """
<div class="fade-in">
    <div class="card p-4 mb-4">
        <a href="/admin" class="btn btn-secondary mb-3" style="width: fit-content;">
            <i class="fas fa-arrow-left me-2"></i>Back to Admin Dashboard
        </a>
        <div class="text-center mb-4">
            <i class="fas fa-file-alt fa-3x mb-3" style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;"></i>
            <h3>Application Details for {{app_data.student_name}}</h3>
            <p class="text-muted">Application Number: {{app_data.app_number}}</p>
        </div>
        <div class="row mb-4">
            <div class="col-md-6">
                <p><strong><i class="fas fa-user me-2"></i>Name:</strong> {{app_data.student_name}}</p>
                <p><strong><i class="fas fa-id-card me-2"></i>Hall Ticket No:</strong> {{app_data.roll_number}}</p>
                <p><strong><i class="fas fa-certificate me-2"></i>Certificate Type:</strong> {{app_data.certificate_type}}</p>
            </div>
            <div class="col-md-6">
                <p><strong><i class="fas fa-graduation-cap me-2"></i>Degree:</strong> {{app_data.degree_type}} - {{app_data.sub_category}}</p>
                <p><strong><i class="fas fa-map-marker-alt me-2"></i>Current Stage:</strong> <span class="badge bg-info">{{current_stage}}</span></p>
                <p><strong><i class="fas fa-money-bill-wave me-2"></i>Fee Option:</strong> {{app_data.fee_option_label}}</p>
            </div>
        </div>
        
        {% if app_data.certificate_documents %}
        <div class="mb-4">
            <strong><i class="fas fa-file-alt me-2"></i>Submitted Documents:</strong>
            <div class="mt-2">
                {% for doc in app_data.certificate_documents %}
                <span class="badge bg-success me-2 mb-2">{{ doc }}</span>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
    
    <div class="card mb-4">
        <div class="card-header" style="background: var(--gradient-primary); color: white;">
            <h5 class="mb-0"><i class="fas fa-history me-2"></i>Application Timeline</h5>
        </div>
        <div class="card-body">
            <div class="progress mb-4" style="height: 12px;">
                <div class="progress-bar bg-success" role="progressbar" style="width: {{progress_percentage}}%" aria-valuenow="{{progress_percentage}}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
            
            <div class="modern-timeline">
                {% for event in timeline %}
                <div class="timeline-item-modern {{event.css_class}}">
                    <div class="timeline-icon-modern">
                        <i class="fas {{event.icon}}"></i>
                    </div>
                    <div class="timeline-content-modern">
                        <div class="timeline-step">{{event.step}}</div>
                        <h6>
                            {{event.stage}}
                            <span class="status-badge {{event.css_class}}">{{event.status}}</span>
                        </h6>
                        <div class="time-info"><i class="far fa-clock me-1"></i>{{event.timestamp}}</div>
                        {% if event.description %}
                        <div class="description">{{event.description}}</div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
"""

# Missing templates that were referenced but not defined
BLOCK = """
<div class="fade-in">
  <div class="card p-4">
    <h3 class="mb-4"><i class="fas fa-building me-2"></i>Block Office - Pending Applications</h3>
    
    <form method="get" class="search-form mb-4">
      <div class="row g-3">
        <div class="col-md-4">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input name="search" class="form-control" placeholder="Search by name or hall ticket" 
                   value="{{request.args.get('search', '')}}">
          </div>
        </div>
        <div class="col-md-3">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-calendar"></i></span>
            <input name="date" type="date" class="form-control" value="{{request.args.get('date', '')}}">
          </div>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100">
            <i class="fas fa-search me-2"></i>Search
          </button>
        </div>
        <div class="col-md-3">
          <a href="/block" class="btn btn-secondary w-100">
            <i class="fas fa-refresh me-2"></i>Clear
          </a>
        </div>
      </div>
    </form>

    {% if apps %}
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Application No</th>
            <th>Student Name</th>
            <th>Hall Ticket</th>
            <th>Certificate Type</th>
            <th>Submission Time</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for app in apps %}
          <tr>
            <td>{{ app.app_number }}</td>
            <td>{{ app.student_name }}</td>
            <td>{{ app.roll_number }}</td>
            <td>{{ app.certificate_type }}</td>
            <td>{{ app.submission_time }}</td>
            <td>
              <a href="/review_block/{{ app.app_number }}" class="btn btn-primary btn-sm">
                <i class="fas fa-eye me-1"></i>Review
              </a>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="text-center py-5">
      <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
      <h5 class="text-muted">No pending applications</h5>
      <p class="text-muted">All applications have been processed</p>
    </div>
    {% endif %}
  </div>
</div>
"""

COMPUTER_SESSION = """
<div class="fade-in">
  <div class="card p-4">
    <h3 class="mb-4"><i class="fas fa-laptop me-2"></i>Computer Session - Pending Applications</h3>
    
    <form method="get" class="search-form mb-4">
      <div class="row g-3">
        <div class="col-md-4">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input name="search" class="form-control" placeholder="Search by name or hall ticket" 
                   value="{{request.args.get('search', '')}}">
          </div>
        </div>
        <div class="col-md-3">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-calendar"></i></span>
            <input name="date" type="date" class="form-control" value="{{request.args.get('date', '')}}">
          </div>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100">
            <i class="fas fa-search me-2"></i>Search
          </button>
        </div>
        <div class="col-md-3">
          <a href="/computer_session" class="btn btn-secondary w-100">
            <i class="fas fa-refresh me-2"></i>Clear
          </a>
        </div>
      </div>
    </form>

    {% if apps %}
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Application No</th>
            <th>Student Name</th>
            <th>Hall Ticket</th>
            <th>Certificate Type</th>
            <th>Submission Time</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for app in apps %}
          <tr>
            <td>{{ app.app_number }}</td>
            <td>{{ app.student_name }}</td>
            <td>{{ app.roll_number }}</td>
            <td>{{ app.certificate_type }}</td>
            <td>{{ app.submission_time }}</td>
            <td>
              <form action="/computer_session/submit/{{ app.app_number }}" method="post" style="display:inline;">
                <button type="submit" class="btn btn-success btn-sm">
                  <i class="fas fa-check me-1"></i>Approve
                </button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="text-center py-5">
      <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
      <h5 class="text-muted">No pending applications</h5>
      <p class="text-muted">All applications have been processed</p>
    </div>
    {% endif %}
  </div>
</div>
"""

REBLOCK_QUEUE_TEMPLATE = """
<div class="fade-in">
  <div class="card p-4">
    <h3 class="mb-4"><i class="fas fa-redo me-2"></i>Re-Block Queue - Pending Applications</h3>
    
    <form method="get" class="search-form mb-4">
      <div class="row g-3">
        <div class="col-md-4">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input name="search" class="form-control" placeholder="Search by name or hall ticket" 
                   value="{{request.args.get('search', '')}}">
          </div>
        </div>
        <div class="col-md-3">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-calendar"></i></span>
            <input name="date" type="date" class="form-control" value="{{request.args.get('date', '')}}">
          </div>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100">
            <i class="fas fa-search me-2"></i>Search
          </button>
        </div>
        <div class="col-md-3">
          <a href="/reblock" class="btn btn-secondary w-100">
            <i class="fas fa-refresh me-2"></i>Clear
          </a>
        </div>
      </div>
    </form>

    {% if apps %}
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Application No</th>
            <th>Student Name</th>
            <th>Hall Ticket</th>
            <th>Certificate Type</th>
            <th>Submission Time</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for app in apps %}
          <tr>
            <td>{{ app.app_number }}</td>
            <td>{{ app.student_name }}</td>
            <td>{{ app.roll_number }}</td>
            <td>{{ app.certificate_type }}</td>
            <td>{{ app.submission_time }}</td>
            <td>
              <form action="/reblock/submit/{{ app.app_number }}" method="post" style="display:inline;">
                <button type="submit" class="btn btn-success btn-sm">
                  <i class="fas fa-check me-1"></i>Approve
                </button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="text-center py-5">
      <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
      <h5 class="text-muted">No pending applications</h5>
      <p class="text-muted">All applications have been processed</p>
    </div>
    {% endif %}
  </div>
</div>
"""

AR_SESSION = """
<div class="fade-in">
  <div class="card p-4">
    <h3 class="mb-4"><i class="fas fa-cube me-2"></i>AR Session - Pending Applications</h3>
    
    <form method="get" class="search-form mb-4">
      <div class="row g-3">
        <div class="col-md-4">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input name="search" class="form-control" placeholder="Search by name or hall ticket" 
                   value="{{request.args.get('search', '')}}">
          </div>
        </div>
        <div class="col-md-3">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-calendar"></i></span>
            <input name="date" type="date" class="form-control" value="{{request.args.get('date', '')}}">
          </div>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100">
            <i class="fas fa-search me-2"></i>Search
          </button>
        </div>
        <div class="col-md-3">
          <a href="/ar_session" class="btn btn-secondary w-100">
            <i class="fas fa-refresh me-2"></i>Clear
          </a>
        </div>
      </div>
    </form>

    {% if apps %}
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Application No</th>
            <th>Student Name</th>
            <th>Hall Ticket</th>
            <th>Certificate Type</th>
            <th>Submission Time</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for app in apps %}
          <tr>
            <td>{{ app.app_number }}</td>
            <td>{{ app.student_name }}</td>
            <td>{{ app.roll_number }}</td>
            <td>{{ app.certificate_type }}</td>
            <td>{{ app.submission_time }}</td>
            <td>
              <form action="/ar_session/submit/{{ app.app_number }}" method="post" style="display:inline;">
                <button type="submit" class="btn btn-success btn-sm">
                  <i class="fas fa-check me-1"></i>Approve
                </button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="text-center py-5">
      <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
      <h5 class="text-muted">No pending applications</h5>
      <p class="text-muted">All applications have been processed</p>
    </div>
    {% endif %}
  </div>
</div>
"""

VR_SESSION = """
<div class="fade-in">
  <div class="card p-4">
    <h3 class="mb-4"><i class="fas fa-vr-cardboard me-2"></i>VR Session - Pending Applications</h3>
    
    <form method="get" class="search-form mb-4">
      <div class="row g-3">
        <div class="col-md-4">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input name="search" class="form-control" placeholder="Search by name or hall ticket" 
                   value="{{request.args.get('search', '')}}">
          </div>
        </div>
        <div class="col-md-3">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-calendar"></i></span>
            <input name="date" type="date" class="form-control" value="{{request.args.get('date', '')}}">
          </div>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100">
            <i class="fas fa-search me-2"></i>Search
          </button>
        </div>
        <div class="col-md-3">
          <a href="/vr_session" class="btn btn-secondary w-100">
            <i class="fas fa-refresh me-2"></i>Clear
          </a>
        </div>
      </div>
    </form>

    {% if apps %}
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Application No</th>
            <th>Student Name</th>
            <th>Hall Ticket</th>
            <th>Certificate Type</th>
            <th>Submission Time</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for app in apps %}
          <tr>
            <td>{{ app.app_number }}</td>
            <td>{{ app.student_name }}</td>
            <td>{{ app.roll_number }}</td>
            <td>{{ app.certificate_type }}</td>
            <td>{{ app.submission_time }}</td>
            <td>
              <form action="/vr_session/submit/{{ app.app_number }}" method="post" style="display:inline;">
                <button type="submit" class="btn btn-success btn-sm">
                  <i class="fas fa-check me-1"></i>Approve
                </button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="text-center py-5">
      <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
      <h5 class="text-muted">No pending applications</h5>
      <p class="text-muted">All applications have been processed</p>
    </div>
    {% endif %}
  </div>
</div>
"""

POST_SESSION = """
<div class="fade-in">
  <div class="card p-4">
    <h3 class="mb-4"><i class="fas fa-mail-bulk me-2"></i>Post Session - Pending Applications</h3>
    
    <form method="get" class="search-form mb-4">
      <div class="row g-3">
        <div class="col-md-4">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input name="search" class="form-control" placeholder="Search by name or hall ticket" 
                   value="{{request.args.get('search', '')}}">
          </div>
        </div>
        <div class="col-md-3">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-calendar"></i></span>
            <input name="date" type="date" class="form-control" value="{{request.args.get('date', '')}}">
          </div>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100">
            <i class="fas fa-search me-2"></i>Search
          </button>
        </div>
        <div class="col-md-3">
          <a href="/post_session" class="btn btn-secondary w-100">
            <i class="fas fa-refresh me-2"></i>Clear
          </a>
        </div>
      </div>
    </form>

    {% if apps %}
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Application No</th>
            <th>Student Name</th>
            <th>Hall Ticket</th>
            <th>Certificate Type</th>
            <th>Submission Time</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for app in apps %}
          <tr>
            <td>{{ app.app_number }}</td>
            <td>{{ app.student_name }}</td>
            <td>{{ app.roll_number }}</td>
            <td>{{ app.certificate_type }}</td>
            <td>{{ app.submission_time }}</td>
            <td>
              <form action="/post_session/submit/{{ app.app_number }}" method="post" style="display:inline;">
                <button type="submit" class="btn btn-success btn-sm">
                  <i class="fas fa-check me-1"></i>Approve
                </button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="text-center py-5">
      <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
      <h5 class="text-muted">No pending applications</h5>
      <p class="text-muted">All applications have been processed</p>
    </div>
    {% endif %}
  </div>
</div>
"""

VERIFIED_CERTIFICATES = """
<div class="fade-in">
  <div class="card p-4">
    <h3 class="mb-4"><i class="fas fa-certificate me-2"></i>Verified Certificates</h3>
    
    <form method="get" class="search-form mb-4">
      <div class="row g-3">
        <div class="col-md-4">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-search"></i></span>
            <input name="search" class="form-control" placeholder="Search by name or hall ticket" 
                   value="{{request.args.get('search', '')}}">
          </div>
        </div>
        <div class="col-md-3">
          <div class="input-group">
            <span class="input-group-text"><i class="fas fa-calendar"></i></span>
            <input name="date" type="date" class="form-control" value="{{request.args.get('date', '')}}">
          </div>
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary w-100">
            <i class="fas fa-search me-2"></i>Search
          </button>
        </div>
        <div class="col-md-3">
          <a href="/verified_certificates" class="btn btn-secondary w-100">
            <i class="fas fa-refresh me-2"></i>Clear
          </a>
        </div>
      </div>
    </form>

    {% if verified %}
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Application No</th>
            <th>Student Name</th>
            <th>Hall Ticket</th>
            <th>Certificate Type</th>
            <th>Verification Date</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for cert in verified %}
          <tr>
            <td>{{ cert.app_number }}</td>
            <td>{{ cert.student_name }}</td>
            <td>{{ cert.roll_number }}</td>
            <td>{{ cert.certificate_type }}</td>
            <td>{{ cert.verified_time }}</td>
            <td>
              <a href="/view_certificate/{{ cert.app_number }}" class="btn btn-primary btn-sm">
                <i class="fas fa-eye me-1"></i>View Certificate
              </a>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="text-center py-5">
      <i class="fas fa-certificate fa-3x mb-3 text-muted"></i>
      <h5 class="text-muted">No verified certificates</h5>
      <p class="text-muted">No certificates have been verified yet</p>
    </div>
    {% endif %}
  </div>
</div>
"""

VIEW_CERTIFICATE = """
<div class="fade-in">
  <div class="card p-4">
    <div class="text-center mb-4">
      <i class="fas fa-certificate fa-3x mb-3" style="background: var(--gradient-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;"></i>
      <h3>Certificate Details</h3>
      <p class="text-muted">Certificate for {{cert.student_name}}</p>
    </div>
    
    <div class="row">
      <div class="col-md-6">
        <div class="certificate-info mb-4">
          <h5 class="mb-3"><i class="fas fa-user-graduate me-2"></i>Student Information</h5>
          <p><strong>Name:</strong> {{cert.student_name}}</p>
          <p><strong>Hall Ticket No:</strong> {{cert.roll_number}}</p>
          <p><strong>Application No:</strong> {{cert.app_number}}</p>
        </div>
      </div>
      <div class="col-md-6">
        <div class="certificate-details mb-4">
          <h5 class="mb-3"><i class="fas fa-certificate me-2"></i>Certificate Details</h5>
          <p><strong>Certificate Type:</strong> {{cert.certificate_type}}</p>
          <p><strong>Degree:</strong> {{cert.degree_type}} - {{cert.sub_category}}</p>
          <p><strong>Verification Date:</strong> {{cert.verified_time}}</p>
        </div>
      </div>
    </div>
    
    <div class="certificate-preview mt-4 p-4 text-center" style="border: 2px solid var(--primary-color); border-radius: 15px; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);">
      <h4 class="mb-3">Sri Krishnadevaraya University</h4>
      <h5 class="mb-4">Certificate of {{cert.certificate_type}}</h5>
      <p class="mb-4">This is to certify that</p>
      <h3 class="mb-4" style="color: var(--primary-color);">{{cert.student_name}}</h3>
      <p class="mb-4">has successfully completed the requirements for</p>
      <p class="mb-4"><strong>{{cert.degree_type}} - {{cert.sub_category}}</strong></p>
      <p class="mb-4">Hall Ticket Number: {{cert.roll_number}}</p>
      <div class="mt-5 pt-4">
        <p>Date of Issue: {{cert.verified_time}}</p>
        <p>Application Reference: {{cert.app_number}}</p>
      </div>
    </div>
    
    <div class="text-center mt-4">
      <a href="/verified_certificates" class="btn btn-secondary">
        <i class="fas fa-arrow-left me-2"></i>Back to Verified Certificates
      </a>
    </div>
  </div>
</div>
"""

# Routes
@app.route('/')
def application():
    return render_template_string(BASE.replace('{{content}}', INDEX))

@app.route('/student_portal', methods=['GET','POST'])
def student_portal():
    app_data = None
    timeline = []
    current_stage = None
    progress_percentage = 0
    if request.method == 'POST':
        hall_ticket = request.form['hall_ticket']
        apps = load_json(APPLICATIONS_FILE)
        verified_apps = load_json(VERIFIED_CERTIFICATES_FILE)
        
        # Search in both applications and verified certificates
        app_data = next((x for x in apps if x.get('roll_number') == hall_ticket), None)
        if not app_data:
            app_data = next((x for x in verified_apps if x.get('roll_number') == hall_ticket), None)
            
        if app_data:
            current_stage = get_current_stage(app_data)
            timeline = build_timeline(app_data)
            progress_percentage = get_progress_percentage(timeline)
            
            # Add fee option label for display
            fee_labels = {
                'within_state_50': 'Within State - Rs 50',
                'other_state_60': 'Other State - Rs 60',
                'within_state_80': 'Within State - Rs 80',
                'other_state_100': 'Other State - Rs 100'
            }
            app_data['fee_option_label'] = fee_labels.get(app_data.get('fee_option'), app_data.get('fee_option', 'N/A'))
            
    return render_template_string(BASE.replace('{{content}}', STUDENT_PORTAL), 
                                app_data=app_data, timeline=timeline, 
                                current_stage=current_stage, progress_percentage=progress_percentage)

@app.route('/check_duplicate', methods=['POST'])
def check_duplicate():
    roll_number = request.form.get('roll_number')
    certificate_type = request.form.get('certificate_type')
    
    if not roll_number or not certificate_type:
        return jsonify({'duplicate': False})
    
    duplicate = check_duplicate_application(roll_number, certificate_type)
    return jsonify({'duplicate': duplicate})

@app.route('/submit_application', methods=['POST'])
def submit_application():
    form = request.form
    certificate_documents = request.form.getlist('certificate_documents')
    fee_option = request.form.get('fee_option')
    
    # Check for duplicate application
    if check_duplicate_application(form['roll_number'], form['certificate_type']):
        return redirect(url_for('application'))
    
    # Map fee option values to readable labels
    fee_labels = {
        'within_state_50': 'Within State - Rs 50',
        'other_state_60': 'Other State - Rs 60',
        'within_state_80': 'Within State - Rs 80',
        'other_state_100': 'Other State - Rs 100'
    }
    
    a = {
        'app_number': gen_app_number(),
        'student_name': form['student_name'],
        'roll_number': form['roll_number'],
        'degree_type': form['degree_type'],
        'sub_category': form['sub_category'],
        'certificate_type': form['certificate_type'],
        'certificate_documents': certificate_documents,
        'fee_option': fee_option,
        'fee_option_label': fee_labels.get(fee_option, fee_option),
        'status': 'Pending Verification',
        'submission_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'verification_time': None,
        'verification_status': None,
        'computer_session_status': None,
        'computer_session_time': None,
        'reblock_status': None,
        'reblock_time': None,
        'ar_status': None,
        'ar_time': None,
        'vr_status': None,
        'vr_time': None,
        'post_status': None,
        'post_time': None,
        'verified_time': None
    }
    apps = load_json(APPLICATIONS_FILE)
    apps.append(a)
    save_json(APPLICATIONS_FILE, apps)
    return redirect(url_for('student_portal'))

@app.route('/block')
def block_office():
    apps = load_json(APPLICATIONS_FILE)
    search = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    pending_apps = [a for a in apps if not a.get('verification_status')]
    filtered_apps = filter_apps(pending_apps, search, date_filter)
    return render_template_string(BASE.replace('{{content}}', BLOCK), apps=filtered_apps)

@app.route('/review_block/<app_no>')
def review_block(app_no):
    apps = load_json(APPLICATIONS_FILE)
    app_data = next((x for x in apps if x.get('app_number') == app_no), None)
    if not app_data:
        return redirect(url_for('block_office'))
    
    content = f"""
    <div class="card p-4 fade-in">
        <h3 class="card-title mb-4">Review Application for {app_data.get('student_name', 'N/A')}</h3>
        <p><strong>Application Number:</strong> {app_data.get('app_number', 'N/A')}</p>
        <p><strong>Hall Ticket No:</strong> {app_data.get('roll_number', 'N/A')}</p>
        <p><strong>Certificate Type:</strong> {app_data.get('certificate_type', 'N/A')}</p>
        <p><strong>Degree:</strong> {app_data.get('degree_type', 'N/A')} - {app_data.get('sub_category', 'N/A')}</p>
        <p><strong>Fee Option:</strong> {app_data.get('fee_option_label', 'N/A')}</p>
        <p><strong>Submitted Documents:</strong></p>
        <ul>
            {"".join(f"<li>{doc}</li>" for doc in app_data.get('certificate_documents', []))}
        </ul>
        <div class="mt-4">
            <form action="/block/approve/{app_no}" method="post" style="display:inline;">
                <button type="submit" class="btn btn-success me-2">Approve</button>
            </form>
            <a href="/block" class="btn btn-secondary">Back to Dashboard</a>
        </div>
    </div>
    """
    return render_template_string(BASE.replace('{{content}}', content))

@app.route('/block/approve/<app_no>', methods=['POST'])
def approve_block(app_no):
    apps = load_json(APPLICATIONS_FILE)
    for a in apps:
        if a.get('app_number') == app_no:
            a['verification_status'] = 'approve'
            a['verification_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            a['status'] = 'Approved by Block Office'
            save_json(APPLICATIONS_FILE, apps)
            return redirect(url_for('block_office'))
    return redirect(url_for('block_office'))

@app.route('/computer_session')
def computer_session():
    apps = load_json(APPLICATIONS_FILE)
    search = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    pending_apps = [a for a in apps if a.get('verification_status') == 'approve' and not a.get('computer_session_status')]
    filtered_apps = filter_apps(pending_apps, search, date_filter)
    return render_template_string(BASE.replace('{{content}}', COMPUTER_SESSION), apps=filtered_apps)

@app.route('/computer_session/submit/<app_no>', methods=['POST'])
def submit_computer_session(app_no):
    apps = load_json(APPLICATIONS_FILE)
    for a in apps:
        if a.get('app_number') == app_no:
            a['computer_session_status'] = 'approved'
            a['computer_session_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            a['status'] = 'Approved by Computer Session'
            save_json(APPLICATIONS_FILE, apps)
            return redirect(url_for('computer_session'))
    return redirect(url_for('computer_session'))

@app.route('/reblock')
def reblock_queue():
    apps = load_json(APPLICATIONS_FILE)
    search = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    pending_apps = [a for a in apps if a.get('computer_session_status') == 'approved' and not a.get('reblock_status')]
    filtered_apps = filter_apps(pending_apps, search, date_filter)
    return render_template_string(BASE.replace('{{content}}', REBLOCK_QUEUE_TEMPLATE), apps=filtered_apps)

@app.route('/reblock/submit/<app_no>', methods=['POST'])
def submit_reblock(app_no):
    apps = load_json(APPLICATIONS_FILE)
    for a in apps:
        if a.get('app_number') == app_no:
            a['reblock_status'] = 'approved'
            a['reblock_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            a['status'] = 'Approved by Re-Block'
            save_json(APPLICATIONS_FILE, apps)
            return redirect(url_for('reblock_queue'))
    return redirect(url_for('reblock_queue'))

@app.route('/ar_session')
def ar_session():
    apps = load_json(APPLICATIONS_FILE)
    search = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    pending_apps = [a for a in apps if a.get('reblock_status') == 'approved' and not a.get('ar_status')]
    filtered_apps = filter_apps(pending_apps, search, date_filter)
    return render_template_string(BASE.replace('{{content}}', AR_SESSION), apps=filtered_apps)

@app.route('/ar_session/submit/<app_no>', methods=['POST'])
def submit_ar_session(app_no):
    apps = load_json(APPLICATIONS_FILE)
    for a in apps:
        if a.get('app_number') == app_no:
            a['ar_status'] = 'approved'
            a['ar_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            a['status'] = 'Approved by AR Session'
            save_json(APPLICATIONS_FILE, apps)
            return redirect(url_for('ar_session'))
    return redirect(url_for('ar_session'))

@app.route('/vr_session')
def vr_session():
    apps = load_json(APPLICATIONS_FILE)
    search = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    pending_apps = [a for a in apps if a.get('ar_status') == 'approved' and not a.get('vr_status')]
    filtered_apps = filter_apps(pending_apps, search, date_filter)
    return render_template_string(BASE.replace('{{content}}', VR_SESSION), apps=filtered_apps)

@app.route('/vr_session/submit/<app_no>', methods=['POST'])
def submit_vr_session(app_no):
    apps = load_json(APPLICATIONS_FILE)
    for a in apps:
        if a.get('app_number') == app_no:
            a['vr_status'] = 'approved'
            a['vr_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            a['status'] = 'Approved by VR Session'
            save_json(APPLICATIONS_FILE, apps)
            return redirect(url_for('vr_session'))
    return redirect(url_for('vr_session'))

@app.route('/post_session')
def post_session():
    apps = load_json(APPLICATIONS_FILE)
    search = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    pending_apps = [a for a in apps if a.get('vr_status') == 'approved' and not a.get('post_status')]
    filtered_apps = filter_apps(pending_apps, search, date_filter)
    return render_template_string(BASE.replace('{{content}}', POST_SESSION), apps=filtered_apps)

@app.route('/post_session/submit/<app_no>', methods=['POST'])
def submit_post_session(app_no):
    apps = load_json(APPLICATIONS_FILE)
    verified = load_json(VERIFIED_CERTIFICATES_FILE)
    for a in apps:
        if a.get('app_number') == app_no:
            a['post_status'] = 'approved'
            a['post_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            a['status'] = 'Approved by Post Session'
            a['verified_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_json(APPLICATIONS_FILE, apps)
            verified.append(a)
            save_json(VERIFIED_CERTIFICATES_FILE, verified)
            return redirect(url_for('post_session'))
    return redirect(url_for('post_session'))

@app.route('/verified_certificates')
def verified_certificates():
    vc = load_json(VERIFIED_CERTIFICATES_FILE)
    # Remove duplicates
    seen = set()
    unique_vc = []
    for v in vc:
        if v.get('app_number') and v.get('app_number') not in seen:
            unique_vc.append(v)
            seen.add(v['app_number'])
    
    search = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    filtered_vc = filter_apps(unique_vc, search, date_filter)
    
    return render_template_string(BASE.replace('{{content}}', VERIFIED_CERTIFICATES), verified=filtered_vc)

@app.route('/view_certificate/<app_no>')
def view_certificate(app_no):
    vc = load_json(VERIFIED_CERTIFICATES_FILE)
    cert = next((x for x in vc if x.get('app_number')==app_no), None)
    if not cert:
        return redirect(url_for('verified_certificates'))
    return render_template_string(BASE.replace('{{content}}', VIEW_CERTIFICATE), cert=cert)

@app.route('/admin')
def admin_dashboard():
    apps = load_json(APPLICATIONS_FILE)
    all_apps = apps
    verified_apps = load_json(VERIFIED_CERTIFICATES_FILE)
    
    # Get only pending applications
    pending_apps = get_pending_apps(apps)
    
    search = request.args.get('search', '')
    date_filter = request.args.get('date', '')
    filtered_apps = filter_apps(pending_apps, search, date_filter)
    
    # Calculate statistics
    total_applications = len(all_apps)
    pending_applications_count = len(pending_apps)
    verified_applications_count = len(verified_apps)
    
    return render_template_string(BASE.replace('{{content}}', ADMIN_SUMMARY_TEMPLATE), 
                                  apps=filtered_apps, 
                                  get_current_stage=get_current_stage,
                                  total_applications=total_applications,
                                  pending_applications=pending_applications_count,
                                  verified_applications=verified_applications_count)

@app.route('/admin/search')
def admin_search():
    hall_ticket = request.args.get('hall_ticket', '')
    apps = load_json(APPLICATIONS_FILE)
    verified_apps = load_json(VERIFIED_CERTIFICATES_FILE)
    
    # Search in both applications and verified certificates
    search_results = []
    
    # Search in pending applications
    for app in apps:
        if app.get('roll_number') == hall_ticket:
            search_results.append(app)
    
    # Search in verified certificates
    for cert in verified_apps:
        if cert.get('roll_number') == hall_ticket:
            search_results.append(cert)
    
    return render_template_string(BASE.replace('{{content}}', ADMIN_SEARCH_TEMPLATE), 
                                  hall_ticket=hall_ticket,
                                  search_results=search_results,
                                  get_current_stage=get_current_stage)

@app.route('/admin/details/<app_no>')
def admin_view_details(app_no):
    apps = load_json(APPLICATIONS_FILE)
    verified_apps = load_json(VERIFIED_CERTIFICATES_FILE)
    
    # Search in both applications and verified certificates
    app_data = next((a for a in apps if a.get('app_number') == app_no), None)
    if not app_data:
        app_data = next((a for a in verified_apps if a.get('app_number') == app_no), None)
        
    if not app_data:
        return redirect(url_for('admin_dashboard'))

    current_stage = get_current_stage(app_data)
    timeline = build_timeline(app_data)
    progress_percentage = get_progress_percentage(timeline)
    
    return render_template_string(BASE.replace('{{content}}', ADMIN_DETAIL_TEMPLATE), 
                                  app_data=app_data, 
                                  current_stage=current_stage,
                                  timeline=timeline, 
                                  progress_percentage=progress_percentage)

@app.route('/admin/download_excel', methods=['POST'])
def download_excel():
    from_date = request.form.get('from_date')
    to_date = request.form.get('to_date')
    
    if not from_date or not to_date:
        return "Please select both from and to dates", 400
    
    apps = load_json(APPLICATIONS_FILE)
    
    # Filter applications by date range
    filtered_apps = []
    for app in apps:
        submission_date = app.get('submission_time', '')[:10]  # Get YYYY-MM-DD part
        if from_date <= submission_date <= to_date:
            filtered_apps.append(app)
    
    if not filtered_apps:
        return "No data found for the selected date range", 404
    
    # Create DataFrame
    data = []
    for app in filtered_apps:
        row = {
            'Application Number': app.get('app_number', ''),
            'Student Name': app.get('student_name', ''),
            'Hall Ticket No': app.get('roll_number', ''),
            'Certificate Type': app.get('certificate_type', ''),
            'Degree Type': app.get('degree_type', ''),
            'Program': app.get('sub_category', ''),
            'Fee Option': app.get('fee_option_label', ''),
            'Submitted Documents': ', '.join(app.get('certificate_documents', [])),
            'Submission Time': app.get('submission_time', ''),
            'Current Stage': get_current_stage(app),
            'Block Office Status': app.get('verification_status', 'Pending'),
            'Computer Session Status': app.get('computer_session_status', 'Pending'),
            'Re-Block Status': app.get('reblock_status', 'Pending'),
            'AR Session Status': app.get('ar_status', 'Pending'),
            'VR Session Status': app.get('vr_status', 'Pending'),
            'Post Session Status': app.get('post_status', 'Pending'),
            'Verified': 'Yes' if app.get('verified_time') else 'No'
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Applications', index=False)
    
    output.seek(0)
    
    # Send file
    filename = f"applications_{from_date}_to_{to_date}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__=='__main__':
    init_json_files()
    app.run(debug=True, host='0.0.0.0', port=5000)