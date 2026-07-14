import logging
from flask import request, jsonify, session, redirect, url_for, flash
from app.services.admin_service import AdminService
from app.utils.auth import verify_admin
from app.utils.correlation_id import generate_correlation_id

logger = logging.getLogger(__name__)

class AdminController:
    def __init__(self, service: AdminService) -> None:
        self.service = service
        
    def get_metadata(self):
        try:
            metadata = self.service.get_model_metadata()
            return jsonify({
                "model_name": metadata.model_name,
                "f1_weighted": metadata.f1_weighted,
                "serialization_timestamp": metadata.serialization_timestamp,
                "model_path": metadata.model_path,
                "scaler_path": metadata.scaler_path
            }), 200
        except Exception as e:
            correlation_id = generate_correlation_id()
            logger.error(f"Admin get_metadata error (Correlation ID: {correlation_id}): {e}")
            return jsonify({"error": "internal_error", "correlation_id": correlation_id}), 500
            
    def post_retrain(self):
        try:
            self.service.trigger_retraining()
            return jsonify({
                "status": "accepted", 
                "message": "Retraining started in background."
            }), 202
        except Exception as e:
            correlation_id = generate_correlation_id()
            logger.error(f"Admin post_retrain error (Correlation ID: {correlation_id}): {e}")
            return jsonify({"error": "internal_error", "correlation_id": correlation_id}), 500
            
    def get_retrain_status(self):
        try:
            status = self.service.get_retrain_status()
            return jsonify(status), 200
        except Exception as e:
            correlation_id = generate_correlation_id()
            logger.error(f"Admin get_retrain_status error (Correlation ID: {correlation_id}): {e}")
            return jsonify({"error": "internal_error", "correlation_id": correlation_id}), 500
            
    def admin_login_post(self):
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if verify_admin(username, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_bp.admin_dashboard'))
        else:
            flash("Invalid credentials.", "danger")
            # redirect with 302 back to login; session is NOT set
            return redirect(url_for('admin_bp.admin_login_get'))
            
    def admin_logout(self):
        session.pop('admin_logged_in', None)
        return redirect(url_for('main_bp.index'))
