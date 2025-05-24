from flask import Flask, render_template, request, url_for, session, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for Flask-WTF

# Set the session lifetime to 30 minutes
app.permanent_session_lifetime = timedelta(minutes=30)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for('register'))
        user = User(
            student_id=form.student_id.data,
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session.permanent = True
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            session['student_id'] = user.student_id
            session['user_name'] = user.full_name
            flash("Logged in successfully.", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.", "danger")
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('student_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Course model
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    instructor = db.Column(db.String(100), nullable=False)
    enrolled = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Course {self.name}>'

# Enrollment model
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)  # Match with User primary key
    course_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Inject current year into templates
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# Home page: display featured courses
@app.route('/')
def home():
    science_courses = Course.query.filter(Course.id.in_([1, 2, 3])).all()
    business_courses = Course.query.filter(Course.id.in_([4, 5, 6])).all()
    tech_courses = Course.query.filter(Course.id.in_([7, 8, 9])).all()
    return render_template("home.html",
                           science_courses=science_courses,
                           business_courses=business_courses,
                           tech_courses=tech_courses)

@app.route('/courses')
def courses():
    query = request.args.get('query', '').lower()
    category = request.args.get('category')
    time = request.args.get('time')
    instructor = request.args.get('instructor')

    courses = Course.query
    if query:
        courses = courses.filter(Course.name.ilike(f"%{query}%"))
    if category:
        courses = courses.filter_by(category=category)
    if instructor:
        courses = courses.filter_by(instructor=instructor)
    if time == "july":
        courses = courses.filter(Course.duration.ilike("%July%"))
    elif time == "august":
        courses = courses.filter(Course.duration.ilike("%Aug%"))

    courses = courses.all()

    # Get all filter options
    all_categories = db.session.query(Course.category).distinct().all()
    all_instructors = db.session.query(Course.instructor).distinct().all()
    categories = [c[0] for c in all_categories]
    instructors = [i[0] for i in all_instructors]

    return render_template('courses.html',
                           courses=courses,
                           selected_category=category,
                           selected_instructor=instructor,
                           selected_time=time,
                           categories=categories,
                           instructors=instructors)

# Course detail page
@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template("course_detail.html", course=course)

# Enroll in a course
@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('enroll.html', course=course)

@app.route('/submit_enrollment/<int:course_id>', methods=['POST'])
def submit_enrollment(course_id):
    student_id = session.get('student_id')
    if not student_id:
        flash("You must be logged in.", "warning")
        return redirect(url_for('login'))

    # Prevent duplicate enrollment
    existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if not existing:
        new_enroll = Enrollment(student_id=student_id, course_id=course_id)
        db.session.add(new_enroll)
        db.session.commit()

    flash("Enrolled successfully!", "success")
    return redirect(url_for('my_enrolments'))

# View my enrollments
@app.route('/my_enrolments')
def my_enrolments():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))

    enrolled_courses = (
        db.session.query(Course)
        .join(Enrollment, Course.id == Enrollment.course_id)
        .filter(Enrollment.student_id == student_id)
        .all()
    )
    return render_template("my_enrolments.html", courses=enrolled_courses)

# Cancel enrollment
@app.route('/cancel_enrollment/<int:course_id>', methods=['POST'])
def cancel_enrollment(course_id):
    student_id = session.get('student_id')
    if student_id:
        enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
        if enrollment:
            db.session.delete(enrollment)
            db.session.commit()
            flash("Enrollment cancelled.", "info")
    return redirect(url_for('my_enrolments'))

# Instructor list
@app.route('/teachers')
def teachers():
    instructors = db.session.query(Course.instructor).distinct().all()
    instructors = [i[0] for i in instructors]
    return render_template('teachers.html', instructors=instructors)

# Courses by instructor
@app.route('/courses/instructor/<instructor>')
def courses_by_instructor(instructor):
    courses = Course.query.filter_by(instructor=instructor).all()
    return render_template('courses.html', courses=courses, selected_instructor=instructor)

# Create tables (run once)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
