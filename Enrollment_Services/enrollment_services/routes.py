from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'usp_secret_key'

# Mock student data (already completed courses)
student_completed_courses = {'CS111'}

# Sample course data (prerequisites as sets)
courses = [
    {
        'code': 'CS111',
        'title': 'Introduction to Computing',
        'description': 'Fundamentals of computer science and programming.',
        'prerequisites': set()
    },
    {
        'code': 'CS112',
        'title': 'Data Structures and Algorithms',
        'description': 'Essential data structures and algorithm analysis.',
        'prerequisites': {'CS111'}
    },
    {
        'code': 'CS241',
        'title': 'Operating Systems',
        'description': 'Principles of modern operating systems.',
        'prerequisites': {'CS112'}
    },
    {
        'code': 'MA101',
        'title': 'Calculus I',
        'description': 'Introduction to differential and integral calculus.',
        'prerequisites': set()
    }
]

@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    if 'enrolled_courses' not in session:
        session['enrolled_courses'] = []

    if request.method == 'POST':
        selected_courses = request.form.getlist('courses')
        if len(selected_courses) > 4:
            flash('You can select a maximum of 4 courses.', 'error')
            return redirect(url_for('enroll'))
        
        # Check prerequisites
        unmet = []
        for course in courses:
            if course['code'] in selected_courses:
                if not course['prerequisites'].issubset(student_completed_courses.union(selected_courses)):
                    unmet.append(course['code'])
        
        if unmet:
            flash(f"Cannot enroll in: {', '.join(unmet)} due to unmet prerequisites.", 'error')
        else:
            # Add only the courses that meet prerequisites
            session['enrolled_courses'].extend([course for course in selected_courses if course not in unmet])
            flash('Enrollment successful! Please confirm your courses.', 'success')
            return redirect(url_for('display_courses'))

    # Determine met/unmet prerequisites for view
    for course in courses:
        course['prereq_met'] = course['prerequisites'].issubset(student_completed_courses)
    
    return render_template('enroll.html', courses=courses)

@app.route('/display_courses')
def display_courses():
    enrolled_courses = [course for course in courses if course['code'] in session.get('enrolled_courses', [])]
    return render_template('display_courses.html', enrolled_courses=enrolled_courses)

@app.route('/drop_course/<course_code>')
def drop_course(course_code):
    if 'enrolled_courses' in session:
        session['enrolled_courses'] = [code for code in session['enrolled_courses'] if code != course_code]
        flash(f'Course {course_code} dropped successfully.', 'success')
    return redirect(url_for('display_courses'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)