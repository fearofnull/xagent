"""
Cron API Routes Module

This module defines RESTful API endpoints for managing cron jobs.
"""

import logging
from flask import Flask, request, jsonify
from typing import Dict, Any

from ...core.crons.manager import CronManager
from ...core.crons.models import CronJobSpec, CronJobView
from ..auth import AuthManager

logger = logging.getLogger(__name__)

def register_cron_api_routes(
    app: Flask, 
    cron_manager: CronManager,
    auth_manager: AuthManager,
    rate_limits: dict = None
):
    """Register cron API routes with the Flask app
    
    Args:
        app: Flask application instance
        cron_manager: CronManager instance
        auth_manager: Authentication manager instance
        rate_limits: Dictionary of rate limit decorators (optional)
    """
    
    # Helper function to apply rate limit if available
    def apply_rate_limit(route_func, limit_type):
        """Apply rate limit decorator if available"""
        if rate_limits and limit_type in rate_limits:
            return rate_limits[limit_type](route_func)
        return route_func
    
    # ==================== Cron Job Routes ====================
    
    @app.route('/api/cron/jobs', methods=['GET'])
    @auth_manager.require_auth
    def list_jobs():
        """List all cron jobs
        
        Response:
            {
                "success": true,
                "data": [
                    {
                        "id": "job-123",
                        "name": "Daily Reminder",
                        "enabled": true,
                        "schedule": {...},
                        "task_type": "text",
                        "text": "Good morning!",
                        "dispatch": {...},
                        "runtime": {...},
                        "meta": {}
                    }
                ]
            }
        """
        try:
            jobs = cron_manager.list_jobs_sync()
            return jsonify({
                'success': True,
                'data': [job.model_dump() for job in jobs]
            }), 200
        except Exception as e:
            logger.error(f"Error listing jobs: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list cron jobs'
                }
            }), 500
    
    @app.route('/api/cron/jobs', methods=['POST'])
    @auth_manager.require_auth
    def create_job():
        """Create a new cron job
        
        Request body:
            {
                "id": "job-123",
                "name": "Daily Reminder",
                "enabled": true,
                "schedule": {
                    "type": "cron",
                    "cron": "0 9 * * *",
                    "timezone": "UTC"
                },
                "task_type": "text",
                "text": "Good morning!",
                "dispatch": {
                    "type": "channel",
                    "channel": "feishu",
                    "target": {
                        "chat_id": "oc_xxx",
                        "user_id": "ou_xxx"
                    },
                    "mode": "final",
                    "meta": {}
                },
                "runtime": {
                    "max_concurrency": 1,
                    "timeout_seconds": 120,
                    "misfire_grace_seconds": 60
                },
                "meta": {}
            }
        
        Response:
            {
                "success": true,
                "data": {
                    "id": "job-123",
                    "name": "Daily Reminder",
                    "enabled": true,
                    "schedule": {...},
                    "task_type": "text",
                    "text": "Good morning!",
                    "dispatch": {...},
                    "runtime": {...},
                    "meta": {}
                }
            }
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'BAD_REQUEST',
                        'message': 'Request body is required'
                    }
                }), 400
            
            spec = CronJobSpec(**data)
            cron_manager.create_or_replace_job_sync(spec)
            return jsonify({
                'success': True,
                'data': spec.model_dump()
            }), 200
        except ValueError as e:
            # Cron表达式验证错误
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_CRON',
                    'message': str(e)
                }
            }), 400
        except Exception as e:
            # Pydantic验证错误或其他错误
            error_msg = str(e)
            if 'validation error' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': error_msg
                    }
                }), 400
            
            logger.error(f"Error creating job: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create cron job'
                }
            }), 500
    
    @app.route('/api/cron/jobs/<job_id>', methods=['GET'])
    @auth_manager.require_auth
    def get_job(job_id: str):
        """Get a specific cron job
        
        Response:
            {
                "success": true,
                "data": {
                    "spec": {...},
                    "state": {
                        "last_run_at": "2024-01-01T12:00:00Z",
                        "next_run_at": "2024-01-02T12:00:00Z",
                        "last_status": "success",
                        "last_error": null
                    }
                }
            }
        """
        try:
            job = cron_manager.get_job_sync(job_id)
            if not job:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Job not found'
                    }
                }), 404
            state = cron_manager.get_state_sync(job_id)
            job_view = {
                'spec': job.model_dump(),
                'state': state.model_dump() if state else None
            }
            return jsonify({
                'success': True,
                'data': job_view
            }), 200
        except Exception as e:
            logger.error(f"Error getting job: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get cron job'
                }
            }), 500
    
    @app.route('/api/cron/jobs/<job_id>', methods=['PUT'])
    @auth_manager.require_auth
    def update_job(job_id: str):
        """Update a cron job
        
        Request body:
            {
                "id": "job-123",
                "name": "Daily Reminder Updated",
                "enabled": true,
                "schedule": {
                    "type": "cron",
                    "cron": "0 10 * * *",
                    "timezone": "UTC"
                },
                "task_type": "text",
                "text": "Good morning!",
                "dispatch": {
                    "type": "channel",
                    "channel": "feishu",
                    "target": {
                        "chat_id": "oc_xxx",
                        "user_id": "ou_xxx"
                    },
                    "mode": "final",
                    "meta": {}
                },
                "runtime": {
                    "max_concurrency": 1,
                    "timeout_seconds": 120,
                    "misfire_grace_seconds": 60
                },
                "meta": {}
            }
        
        Response:
            {
                "success": true,
                "data": {
                    "id": "job-123",
                    "name": "Daily Reminder Updated",
                    "enabled": true,
                    "schedule": {...},
                    "task_type": "text",
                    "text": "Good morning!",
                    "dispatch": {...},
                    "runtime": {...},
                    "meta": {}
                }
            }
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'BAD_REQUEST',
                        'message': 'Request body is required'
                    }
                }), 400
            
            if data.get('id') != job_id:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'BAD_REQUEST',
                        'message': 'Job id in path and body must match'
                    }
                }), 400
            
            spec = CronJobSpec(**data)
            cron_manager.create_or_replace_job_sync(spec)
            return jsonify({
                'success': True,
                'data': spec.model_dump()
            }), 200
        except ValueError as e:
            # Cron表达式验证错误
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_CRON',
                    'message': str(e)
                }
            }), 400
        except Exception as e:
            # Pydantic验证错误或其他错误
            error_msg = str(e)
            if 'validation error' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': error_msg
                    }
                }), 400
            
            logger.error(f"Error updating job: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update cron job'
                }
            }), 500
    
    @app.route('/api/cron/jobs/<job_id>', methods=['DELETE'])
    @auth_manager.require_auth
    def delete_job(job_id: str):
        """Delete a cron job
        
        Response:
            {
                "success": true,
                "message": "Job deleted successfully"
            }
        """
        try:
            deleted = cron_manager.delete_job_sync(job_id)
            if not deleted:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Job not found'
                    }
                }), 404
            return jsonify({
                'success': True,
                'message': 'Job deleted successfully'
            }), 200
        except Exception as e:
            logger.error(f"Error deleting job: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete cron job'
                }
            }), 500
    
    @app.route('/api/cron/jobs/<job_id>/pause', methods=['POST'])
    @auth_manager.require_auth
    def pause_job(job_id: str):
        """Pause a cron job
        
        Response:
            {
                "success": true,
                "message": "Job paused successfully"
            }
        """
        try:
            cron_manager.pause_job_sync(job_id)
            return jsonify({
                'success': True,
                'message': 'Job paused successfully'
            }), 200
        except Exception as e:
            logger.error(f"Error pausing job: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Job not found'
                }
            }), 404
    
    @app.route('/api/cron/jobs/<job_id>/resume', methods=['POST'])
    @auth_manager.require_auth
    def resume_job(job_id: str):
        """Resume a cron job
        
        Response:
            {
                "success": true,
                "message": "Job resumed successfully"
            }
        """
        try:
            cron_manager.resume_job_sync(job_id)
            return jsonify({
                'success': True,
                'message': 'Job resumed successfully'
            }), 200
        except Exception as e:
            logger.error(f"Error resuming job: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Job not found'
                }
            }), 404
    
    @app.route('/api/cron/jobs/<job_id>/run', methods=['POST'])
    @auth_manager.require_auth
    def run_job(job_id: str):
        """Run a cron job immediately
        
        Response:
            {
                "success": true,
                "message": "Job started successfully"
            }
        """
        try:
            cron_manager.run_job_sync(job_id)
            return jsonify({
                'success': True,
                'message': 'Job started successfully'
            }), 200
        except KeyError as e:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Job not found'
                }
            }), 404
        except Exception as e:
            logger.error(f"Error running job: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to run cron job'
                }
            }), 500
    
    logger.info("Cron API routes registered successfully")
