from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, make_response
import logging
from io import BytesIO  # Import BytesIO for in-memory PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = 'usp_secret_key'

# Set up logging
logging.basicConfig(level=logging.ERROR)  # Log errors and above

# Mock student data (already completed courses)
student_completed_courses = {'CS111'}

# Sample course data (prerequisites as sets)
courses = [
    {
        'code': 'CS111',
        'title': 'Introduction to Computing',
        'description': 'Fundamentals of computer science and programming.',
        'prerequisites': set(),
        'credits': 3,
        'fee_per_credit': 50.00
    },
    {
        'code': 'CS112',
        'title': 'Data Structures and Algorithms',
        'description': 'Essential data structures and algorithm analysis.',
        'prerequisites': {'CS111'},
        'credits': 3,
        'fee_per_credit': 50.00
    },
    {
        'code': 'CS241',
        'title': 'Operating Systems',
        'description': 'Principles of modern operating systems.',
        'prerequisites': {'CS112'},
        'credits': 3,
        'fee_per_credit': 50.00
    },
    {
        'code': 'MA101',
        'title': 'Calculus I',
        'description': 'Introduction to differential and integral calculus.',
        'prerequisites': set(),
        'credits': 4,
        'fee_per_credit': 50.00
    }
]

# Mock student details and invoice data
student_details = {
    'name': 'Ratu Epeli Nailatikau',
    'id': 's11223344'
}
invoice_details = {
    'number': 'INV-2025-1234',
    'date': 'October 26, 2025',
    'semester': 'Semester 2, 2025',
    'payment_status': 'Paid'  # Could be 'Paid', 'Pending', 'Hold'
}


def calculate_invoice(enrolled_courses):
    """Calculates the invoice details for the given courses."""
    invoice_items = []
    total_amount = 0
    for course_code in enrolled_courses:
        course = next((c for c in courses if c['code'] == course_code), None)
        if course:
            subtotal = course['credits'] * course['fee_per_credit']
            invoice_items.append({
                'code': course['code'],
                'title': course['title'],
                'credits': course['credits'],
                'fee_per_credit': course['fee_per_credit'],
                'subtotal': subtotal
            })
            total_amount += subtotal
    return invoice_items, total_amount


@app.route('/')  # Add a route for the root URL
@app.route('/dashboard')  # Add a route for /dashboard
def dashboard():
    """Renders the dashboard page."""
    return render_template('dashboard.html')  # You'll need a dashboard.html template


@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    try:
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
                    if not course['prerequisites'].issubset(student_completed_courses.union(session['enrolled_courses'])):
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
    except Exception as e:
        logging.error(f"Error in /enroll: {e}")
        # Instead of a generic message, render the 500.html template
        return render_template('500.html'), 500


@app.route('/display_courses')
def display_courses():
    try:
        enrolled_courses = [course for course in courses if course['code'] in session.get('enrolled_courses', [])]
        return render_template('display_courses.html', enrolled_courses=enrolled_courses)
    except Exception as e:
        logging.error(f"Error in /display_courses: {e}")
        # Instead of a generic message, render the 500.html template
        return render_template('500.html'), 500


@app.route('/drop_course/<course_code>')
def drop_course(course_code):
    try:
        if 'enrolled_courses' in session:
            session['enrolled_courses'] = [code for code in session['enrolled_courses'] if code != course_code]
            flash(f'Course {course_code} dropped successfully.', 'success')
        return redirect(url_for('display_courses'))
    except Exception as e:
        logging.error(f"Error in /drop_course/{course_code}: {e}")
        # Instead of a generic message, render the 500.html template
        return render_template('500.html'), 500


@app.route('/fees')
def fees():
    try:
        enrolled_courses_codes = session.get('enrolled_courses', [])
        invoice_items, total_amount = calculate_invoice(enrolled_courses_codes)
        return render_template(
            'fees.html',
            student=student_details,
            invoice=invoice_details,
            items=invoice_items,
            total=total_amount
        )
    except Exception as e:
        logging.error(f"Error in /fees: {e}")
        return render_template('500.html'), 500


@app.route('/download_invoice_pdf')
def download_invoice_pdf():
    try:
        enrolled_courses_codes = session.get('enrolled_courses', [])
        invoice_items, total_amount = calculate_invoice(enrolled_courses_codes)

        buffer = BytesIO()  # Create an in-memory buffer
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Invoice Header
        elements.append(Paragraph("Invoice", styles['h1']))
        elements.append(Paragraph("University of the South Pacific", styles['h2']))
        elements.append(Paragraph(f"Invoice Number: {invoice_details['number']}", styles['Normal']))
        elements.append(Paragraph(f"Date: {invoice_details['date']}", styles['Normal']))
        elements.append(Paragraph(f"Semester: {invoice_details['semester']}", styles['Normal']))

        # Student Details
        elements.append(Paragraph("Student Details", styles['h3']))
        elements.append(Paragraph(f"Name: {student_details['name']}", styles['Normal']))
        elements.append(Paragraph(f"ID: {student_details['id']}", styles['Normal']))

        # Invoice Items Table
        data = [['Course Code', 'Course Title', 'Credits', 'Fee per Credit', 'Subtotal']]
        for item in invoice_items:
            data.append([item['code'], item['title'], item['credits'], f"${item['fee_per_credit']:.2f}",
                         f"${item['subtotal']:.2f}"])
        data.append(['', '', '', 'Total:', f"${total_amount:.2f}"])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        # Payment Status
        elements.append(Paragraph(f"Payment Status: {invoice_details['payment_status']}", styles['Normal']))

        doc.build(elements)

        # Prepare response
        buffer.seek(0)  # Go to the beginning of the buffer
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment;filename=invoice.pdf'

        return response

    except Exception as e:
        logging.error(f"Error in /download_invoice_pdf: {e}")
        return render_template('500.html'), 500


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error handler."""
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)