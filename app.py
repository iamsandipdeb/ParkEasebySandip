from flask import Flask, render_template, request, redirect, url_for, g, session
import sqlite3
import random
import string
import qrcode
from PIL import Image


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong secret key

# SQLite database setup
DATABASE = 'new_parking_app.db'  # New database file name

def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Drop the existing 'bookings' table if it exists
    cursor.execute("DROP TABLE IF EXISTS bookings")
    # Create a new 'bookings' table with the updated schema
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL,
                      password TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      unique_id TEXT NOT NULL,
                      username TEXT NOT NULL,
                      date TEXT NOT NULL,
                      start_time TEXT NOT NULL,
                      end_time TEXT NOT NULL,
                      location TEXT NOT NULL,
                      section TEXT NOT NULL,
                      parking_number INTEGER NOT NULL)''')
    conn.commit()
    conn.close()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and user[2] == password:
            session['username'] = username
            return redirect(url_for('select_slot'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/select_slot', methods=['GET', 'POST'])
def select_slot():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        location = request.form['location']  # Capture location from the form
        section = request.form['section']    # Capture section from the form
        unique_id = generate_unique_id()
        parking_number = random.randint(1, 100)
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO bookings (unique_id, username, date, start_time, end_time, location, section, parking_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (unique_id, session['username'], date, start_time, end_time, location, section, parking_number))
        db.commit()
        return redirect(url_for('confirmation', unique_id=unique_id))
    return render_template('select_slot.html')



@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # Process the form data and send email notifications (add your code here)

        # Return a response, for example, a thank you message
        return "Thank you for contacting us. We will get back to you soon."



@app.route('/confirmation/<unique_id>')
def confirmation(unique_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT date, start_time, end_time, location, section, parking_number FROM bookings WHERE unique_id = ?", (unique_id,))
    booking = cursor.fetchone()

    if booking:
        date, start_time, end_time, location, section, parking_number = booking

        # Generate the content for the QR code (include the booking information, location, and section)
        qr_content = f"Booking ID: {unique_id}\nDate: {date}\nStart Time: {start_time}\nEnd Time: {end_time}\nLocation: {location}\nSection: {section}\nParking Number: {parking_number}"

        # Create a QR code with a larger box size (adjust the value as needed)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=7,  # Adjust this value to change the size
            border=5,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        # Generate the QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Create a larger canvas to center the QR code
        canvas_size = (300, 300)  # Adjust this size as needed
        canvas = Image.new('RGB', canvas_size, 'white')

        # Calculate the position to center the QR code on the canvas
        x = (canvas_size[0] - qr_img.size[0]) // 2
        y = (canvas_size[1] - qr_img.size[1]) // 2

        # Paste the QR code onto the canvas
        canvas.paste(qr_img, (x, y))

        # Define the path to save the QR code image (use a unique filename)
        qr_img_path = f"static/qr_codes/{unique_id}.png"

        # Save the QR code image (including the centered QR code) to a file
        canvas.save(qr_img_path)

        return render_template('confirmation.html', username=session['username'], unique_id=unique_id, date=date, start_time=start_time, end_time=end_time, location=location, section=section, parking_number=parking_number, qr_img_path=qr_img_path)
    else:
        return "Booking not found."




def generate_unique_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

if __name__ == '__main__':
    create_table()
    app.run(port=8000)
