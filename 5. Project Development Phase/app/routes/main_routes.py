import time
import os
import pandas as pd
from flask import Blueprint, render_template, jsonify, current_app

main_bp = Blueprint('main_bp', __name__)

START_TIME = time.time()


@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@main_bp.route('/about', methods=['GET'])
def about():
    return render_template('about.html')


@main_bp.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')


@main_bp.route('/research', methods=['GET'])
def research():
    stats = {"total_rows": "N/A", "total_cols": "N/A", "classes": {}}
    try:
        dataset_path = current_app.config.get('DATASET_PATH', 'datasets/crop_recommendation.csv')
        if os.path.exists(dataset_path):
            df = pd.read_csv(dataset_path)
            class_counts = df['label'].value_counts().to_dict() if 'label' in df.columns else {}
            stats = {
                "total_rows": len(df),
                "total_cols": len(df.columns),
                "classes": class_counts,
            }
    except Exception:
        pass  # Fall through to N/A defaults — never crash the page
    return render_template('research.html', dataset_stats=stats)


@main_bp.route('/api/health', methods=['GET'])
def health_check():
    uptime = int(time.time() - START_TIME)
    return jsonify({"status": "ok", "uptime_seconds": uptime}), 200
