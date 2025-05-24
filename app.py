from flask import Flask, render_template, request, url_for, session, flash, redirect

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, flash
from forms import RegistrationForm, LoginForm


app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Flask-WTF 

# Set the session lifecycle to 30 minutes
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


# Route for handling user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():    # Check if form submission is valid
        session.permanent = True  # Make the session follow the set expiration time
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Store user info in session for login persistence
            session['student_id'] = user.student_id  
            session['user_name'] = user.full_name   
            flash("Logged in successfully.", "success")  # Success feedback
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.", "danger")  # Error feedback
    return render_template('login.html', form=form)

# Route for handling user logout
@app.route('/logout')
def logout():
    session.pop('student_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))



# SQLite database setting
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database objects
db = SQLAlchemy(app)


# user model

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


# courses model
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    instructor = db.Column(db.String(100), nullable=False)
    enrolled = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)  # add new field

    def __repr__(self):
        return f'<Course {self.name}>'

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)  # Ensure consistency with the User primary key
    course_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)



# Current year template injection
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# homepage

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

    # Provide all options for constructing the dropdown list
    all_categories = db.session.query(Course.category).distinct().all()
    all_instructors = db.session.query(Course.instructor).distinct().all()

  # Flatten into a list
    categories = [c[0] for c in all_categories]
    instructors = [i[0] for i in all_instructors]

    return render_template('courses.html', 
                       courses=courses,
                       selected_category=category,
                       selected_instructor=instructor,
                       selected_time=time,
                       categories=categories,
                       instructors=instructors)



# single course details show
@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template("course_detail.html", course=course)

# Initialize the database (required only for the first run)
# with app.app_context():
#     db.create_all()



# ======= Initialize course data (run only once)）=======
# def insert_initial_data():
#     with app.app_context():
#         courses = [
#             Course(name='The Wonders of the Universe', duration='July 4 to July 20, 2025',
#                    instructor='Dr. Emily', enrolled=42, image_url='/static/images/universe.jpg',
#                    category='Science & Engineering'),
#             Course(name='Genetics & DNA: Code of Life', duration='July 10 to July 25, 2025',
#                    instructor='Prof. Alan', enrolled=58, image_url='/static/images/DNA.png',
#                    category='Science & Engineering'),
#             Course(name='Climate Science and Earth Systems', duration='Aug 1 to Aug 14, 2025',
#                    instructor='Ms. Li', enrolled=30, image_url='/static/images/climate_science.png',
#                    category='Science & Engineering'),

#             Course(name='Learn to Think Like a CEO', duration='July 10 to July 24, 2025',
#                    instructor='Dr. Linda', enrolled=33, image_url='/static/images/ceo.jpg',
#                    category='Business & Management'),
#             Course(name='Marketing Strategies for the Digital Era', duration='Aug 5 to Aug 20, 2025',
#                    instructor='Ms. Nora', enrolled=41, image_url='/static/images/marketing.jpg',
#                    category='Business & Management'),
#             Course(name='Financial Planning & Analysis', duration='July 15 to Aug 1, 2025',
#                    instructor='Mr. Kevin', enrolled=29, image_url='/static/images/finance.jpg',
#                    category='Business & Management'),

#             Course(name='Python for Beginners', duration='July 10 to July 24, 2025',
#                    instructor='Dr. Jordan', enrolled=121, image_url='/static/images/python.jpg',
#                    category='Technology & Computing'),
#             Course(name='AI and Society', duration='Aug 1 to Aug 14, 2025',
#                    instructor='Prof. Alan', enrolled=98, image_url='/static/images/ai.jpg',
#                    category='Technology & Computing'),
#             Course(name='Introduction to Cybersecurity', duration='Aug 5 to Aug 19, 2025',
#                    instructor='Ms. Eva', enrolled=74, image_url='/static/images/cybersecurity.jpg',
#                    category='Technology & Computing'),
#         ]

#         db.session.bulk_save_objects(courses)
#         db.session.commit()
#         print("Courses inserted successfully.")

# Call the insertion function (only for the first run)
#insert_initial_data()

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

    # Avoid duplicate enrollment
    existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if not existing:
        new_enroll = Enrollment(student_id=student_id, course_id=course_id)
        db.session.add(new_enroll)
        db.session.commit()

    flash("Enrolled successfully!", "success")
    return redirect(url_for('my_enrolments'))


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

# cancel enrolment 
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

@app.route('/teachers')
def teachers():
    instructors = db.session.query(Course.instructor).distinct().all()
    instructors = [i[0] for i in instructors]  # Extract pure string
    return render_template('teachers.html', instructors=instructors)


@app.route('/courses/instructor/<instructor>')
def courses_by_instructor(instructor):
    courses = Course.query.filter_by(instructor=instructor).all()
    return render_template('courses.html', courses=courses, selected_instructor=instructor)

if __name__ == '__main__':
    app.run(debug=True)
