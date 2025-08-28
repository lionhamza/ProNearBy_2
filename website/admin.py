from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from .models import ProRegistrationRequest, User, Post, ServiceRequest, Message, Like
from . import db
from datetime import datetime

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route('/dashboard')
def dashboard():
    return render_template('admin/dashboard.html')


@admin.route('/applications')
def view_applications():
    applications = ProRegistrationRequest.query.all()
    return render_template('admin/applications.html', applications=applications)

@admin.route('/application/<int:application_id>')
def view_application_detail(application_id):
    application = ProRegistrationRequest.query.get_or_404(application_id)
    return render_template('admin/view_application.html', application=application)


@admin.route('/application/<int:application_id>', methods=['POST'])
def process_application(application_id):
    application = ProRegistrationRequest.query.get_or_404(application_id)
    action = request.form.get('action')

    if action == 'approve':
        # Determine user_type based on is_certified flag
        user_type = "certifiedPro" if application.is_certified else "experiencedPro"

        # Check if user already exists
        existing_user = User.query.filter_by(Email=application.email).first()

        if existing_user:
            # Update existing user
            existing_user.Service = application.service
            existing_user.Experience = application.experience
            existing_user.availability = application.availability
            existing_user.Location = application.location
            existing_user.Rating = 0.0
            existing_user.Reviews = 0
            existing_user.Bio = application.bio or ""
            existing_user.Image = None
            existing_user.CoverImage = None
            existing_user.user_type = user_type

            message = 'Application approved and existing user updated.'
        else:
            # Create a new user
            new_user = User(
                Name=application.name,
                Surname=application.surname,
                Email=application.email,
                CellPhone=application.contact,
                Password=application.password,  # Already hashed
                Service=application.service,
                Experience=application.experience,
                availability=application.availability,
                Location=application.location,
                Rating=0.0,
                Reviews=0,
                Bio=application.bio or "",
                Image=None,
                CoverImage=None,
                user_type=user_type
            )
            db.session.add(new_user)
            message = 'Application approved and new user created.'

        try:
            application.status = 'Approved'
            db.session.commit()
            flash(message, 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error while processing application: {e}")
            flash('Failed to process application. Try again.', 'error')

    elif action == 'reject':
        db.session.delete(application)
        db.session.commit()
        flash('Application has been rejected and deleted.', 'success')

    return redirect(url_for('admin.view_applications'))





@admin.route('/analytics')
def analytics():
    return render_template('admin/data_analytics.html')


@admin.route('/signup-admin')
def signup_admin():
    return render_template('admin/signup_admin.html')


@admin.route('/complaints')
def view_complaints():
    return render_template('admin/admin_complaints.html')

from sqlalchemy import func

@admin.route("/analytics/data/total-users")
def total_users_data():
    total = db.session.query(func.count(User.ID)).scalar()
    return jsonify({"total_users": total or 0})

@admin.route("/analytics/data/user-breakdown")
def user_breakdown_data():
    certified = db.session.query(func.count(User.ID)).filter(User.user_type == "certifiedPro").scalar()
    experienced = db.session.query(func.count(User.ID)).filter(User.user_type == "experiencedPro").scalar()
    regular = db.session.query(func.count(User.ID)).filter(User.user_type == "regular").scalar()

    return jsonify({
        "certified": certified or 0,
        "experienced": experienced or 0,
        "regular": regular or 0
    })

@admin.route("/analytics/data/service-requests")
def service_requests_data():
    total = db.session.query(func.count(ServiceRequest.id)).scalar()
    accepted = db.session.query(func.count(ServiceRequest.id)).filter(ServiceRequest.status == 'accepted').scalar()
    declined = db.session.query(func.count(ServiceRequest.id)).filter(ServiceRequest.status == 'declined').scalar()

    return jsonify({
        "total_requests": total or 0,
        "accepted": accepted or 0,
        "declined": declined or 0
    })
