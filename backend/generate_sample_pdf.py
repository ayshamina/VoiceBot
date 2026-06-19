from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Page 1: Introduction and Course Information
    c.drawString(100, 750, "Bridgeon Skillversity Company Information Brochure")
    c.drawString(100, 720, "About Bridgeon:")
    c.drawString(100, 700, "Bridgeon Skillversity is an industry-simulation training academy providing job-oriented bootcamps.")
    c.drawString(100, 680, "We specialize in software development tracks designed to get students hired within 8 to 10 months.")
    c.drawString(100, 650, "Courses Offered:")
    c.drawString(100, 630, "1. MERN Stack Web Development (React, Node.js, Express, MongoDB)")
    c.drawString(100, 610, "2. Python Full Stack Web Development (Django, Flask, Python)")
    c.drawString(100, 590, "3. Flutter Mobile App Development (Dart, Flutter Android/iOS)")
    c.drawString(100, 570, "4. Data Science and Analytics (Machine Learning, Python, SQL)")
    c.drawString(100, 550, "5. UI/UX Design (Figma, Adobe XD, Wireframing, User Research)")
    
    c.drawString(100, 500, "Placement Records:")
    c.drawString(100, 480, "Bridgeon provides 100% placement support. Our graduates start with packages between 2.5 LPA and 4.9+ LPA.")
    c.drawString(100, 460, "We have partnerships with over 50 technology companies across India.")
    
    # Page 2: Admissions, Fees and Refund Policies
    c.showPage()
    c.drawString(100, 750, "Bridgeon Admissions and Refund Policy Guide")
    c.drawString(100, 720, "Admissions Process:")
    c.drawString(100, 700, "1. Schedule a call with our admissions counselor.")
    c.drawString(100, 680, "2. Complete the coding aptitude assessment (no prior programming required).")
    c.drawString(100, 660, "3. Reserve your seat with an admission fee of ₹5,000.")
    
    c.drawString(100, 620, "Course Fees and Payment Plans:")
    c.drawString(100, 600, "The standard course fee is ₹35,000 for all developer bootcamps.")
    c.drawString(100, 580, "We support installment plans: ₹10,000 monthly or zero-cost EMIs via partner financial services.")
    
    c.drawString(100, 540, "Refund Policy:")
    c.drawString(100, 520, "1. A full refund of the reservation fee (₹5,000) is given if cancelled within 7 days of payment.")
    c.drawString(100, 500, "2. If a student withdraws within the first 14 days of batch startup, 75% of the tuition is refundable.")
    c.drawString(100, 480, "3. No refunds are provided after 30 days of joining the batch.")
    
    c.drawString(100, 420, "Contact Details:")
    c.drawString(100, 400, "For general inquiries, email: admissions@bridgeon.in or call +91 95138 86363.")
    c.drawString(100, 380, "Office hours are Monday to Saturday, 9:00 AM to 6:00 PM IST.")
    
    c.save()

if __name__ == "__main__":
    create_pdf("bridgeon_info.pdf")
    print("Sample PDF generated successfully as bridgeon_info.pdf")
