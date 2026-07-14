from flask import Blueprint, render_template, current_app, redirect, url_for
from app.utils.auth import login_required
from app.controllers.admin_controller import AdminController
from app.services.admin_service import AdminService

admin_bp = Blueprint('admin_bp', __name__)


def get_controller():
    repo = current_app.extensions['prediction_repository']
    service = AdminService(repo, current_app.config)
    return AdminController(service)


@admin_bp.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    repo = current_app.extensions['prediction_repository']
    # Fetch all records for the admin table (server-rendered, not paginated via API)
    records = repo.get_paginated(1, 500)
    return render_template('admin/dashboard.html', predictions=records)


@admin_bp.route('/admin/login', methods=['GET'])
def admin_login_get():
    return render_template('admin/login.html')


@admin_bp.route('/admin/login', methods=['POST'])
def admin_login_post():
    return get_controller().admin_login_post()


@admin_bp.route('/admin/logout', methods=['GET'])
def admin_logout():
    return get_controller().admin_logout()


@admin_bp.route('/api/admin/metadata', methods=['GET'])
@login_required
def api_admin_metadata():
    return get_controller().get_metadata()


@admin_bp.route('/api/admin/retrain', methods=['POST'])
@login_required
def api_admin_retrain():
    return get_controller().post_retrain()


@admin_bp.route('/api/admin/retrain/status', methods=['GET'])
@login_required
def api_admin_retrain_status():
    return get_controller().get_retrain_status()


@admin_bp.route('/admin/records/<int:record_id>/delete', methods=['POST'])
@login_required
def admin_delete_record(record_id: int):
    repo = current_app.extensions['prediction_repository']
    repo.delete(record_id)
    return redirect(url_for('admin_bp.admin_dashboard'))


@admin_bp.route('/admin/records/clear', methods=['POST'])
@login_required
def admin_clear_history():
    repo = current_app.extensions['prediction_repository']
    repo.delete_all()
    return redirect(url_for('admin_bp.admin_dashboard'))
