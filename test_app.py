import unittest
import sys
import os
from app import app, db, User, Course
from flask import session

# Ensure correct path if app.py is not in the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            # Add a test course
            course = Course(
                name="Test Course",
                duration="July 1-10, 2025",
                instructor="Test Instructor",
                category="Test"
            )
            db.session.add(course)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_register_login_logout(self):
        # Register a new user
        response = self.client.post('/register', data={
            'student_id': '123456',
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'password': 'testpass',
            'confirm_password': 'testpass'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful', response.data)

        # Login
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpass'
        }, follow_redirects=True)
        self.assertIn(b'Logged in successfully', response.data)

        # Access home page after login
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'You have been logged out', response.data)

    def test_enroll_and_cancel(self):
        # Register and login
        self.client.post('/register', data={
            'student_id': '234567',
            'full_name': 'Test Enroller',
            'email': 'enroller@example.com',
            'phone': '0987654321',
            'password': 'testpass',
            'confirm_password': 'testpass'
        }, follow_redirects=True)
        self.client.post('/login', data={
            'email': 'enroller@example.com',
            'password': 'testpass'
        }, follow_redirects=True)

        # Get course ID
        with app.app_context():
            course = Course.query.first()
            course_id = course.id

        # Enroll in course
        response = self.client.post(f'/submit_enrollment/{course_id}', follow_redirects=True)
        self.assertIn(b'Enrolled successfully', response.data)

        # Cancel enrollment
        response = self.client.post(f'/cancel_enrollment/{course_id}', follow_redirects=True)
        self.assertIn(b'Enrollment cancelled', response.data)

    def test_course_page_access(self):
        # Access course list page
        response = self.client.get('/courses')
        self.assertEqual(response.status_code, 200)

    def test_course_detail(self):
        # Access specific course detail
        with app.app_context():
            course = Course.query.first()
            response = self.client.get(f'/courses/{course.id}')
            self.assertEqual(response.status_code, 200)
            self.assertIn(course.name.encode(), response.data)

if __name__ == '__main__':
    unittest.main()
