from flask import Flask, request, jsonify, send_from_directory
import qrcode
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from flask_mail import Mail, Message

app = Flask(__name__)

# Setup konfigurasi email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'your_email@example.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# Tempat penyimpanan peserta dan tiket
participants_file = 'participants.xlsx'
tickets_folder = 'tickets'

# Pastikan folder tiket ada
if not os.path.exists(tickets_folder):
    os.makedirs(tickets_folder)

# Fungsi untuk menyimpan data peserta ke Excel
def save_to_excel(name, email, qr_code_path):
    # Membaca data peserta yang sudah ada
    if os.path.exists(participants_file):
        df = pd.read_excel(participants_file)
    else:
        df = pd.DataFrame(columns=["Nama", "Email", "QR Code"])

    # Menambah data baru
    new_data = {"Nama": name, "Email": email, "QR Code": qr_code_path}
    df = df.append(new_data, ignore_index=True)

    # Menyimpan ke file Excel
    df.to_excel(participants_file, index=False)

# Fungsi untuk menghasilkan QR Code
def generate_qr_code(data):
    qr = qrcode.make(data)
    img = BytesIO()
    qr.save(img)
    img.seek(0)
    return img

# Fungsi untuk mengirim email dengan QR Code
def send_ticket_email(email, qr_code_img, filename):
    msg = Message('Tiket Acara Anda', sender='your_email@example.com', recipients=[email])
    msg.body = 'Terima kasih telah memesan tiket. QR Code Anda terlampir.'

    # Menambahkan QR code sebagai lampiran
    msg.attach(filename, 'image/png', qr_code_img.getvalue())

    # Mengirim email
    with app.app_context():
        mail.send(msg)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    data = request.get_json()
    name = data['name']
    email = data['email']
    
    # Membuat QR code dengan data nama
    qr_code_img = generate_qr_code(f"{name} | {email}")

    # Menyimpan QR code sebagai gambar
    qr_code_filename = f"{name}_{email}.png"
    qr_code_path = os.path.join(tickets_folder, qr_code_filename)
    with open(qr_code_path, 'wb') as f:
        f.write(qr_code_img.getvalue())

    # Menyimpan data peserta ke Excel
    save_to_excel(name, email, qr_code_path)

    # Mengirim email dengan QR Code
    send_ticket_email(email, qr_code_img, qr_code_filename)

    return jsonify({"status": "success", "message": "Tiket berhasil dipesan!"})

if __name__ == '__main__':
    app.run(debug=True)
