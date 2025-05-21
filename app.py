import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CONVERTED_FOLDER'] = 'converted'
app.config['ALLOWED_EXTENSIONS'] = {'mov', 'MOV', 'mp4', 'MP4'}
app.config['MAX_CONTENT_LENGTH'] = 800 * 1024 * 1024  # 800MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CONVERTED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def convert_mov_to_wav(input_path, output_path):
    try:
        # Using FFmpeg to convert MOV to WAV
        command = [
            'ffmpeg',
            '-i', input_path,          # Input file
            '-acodec', 'pcm_s16le',   # PCM 16-bit little-endian
            '-ar', '44100',           # Sample rate 44.1kHz
            '-ac', '2',               # Stereo audio
            '-vn',                    # No video
            '-y',                     # Overwrite output file if exists
            output_path
        ]
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed: {e}")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        # Generate output filename
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}.wav"
        output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)
        
        # Convert the file
        if convert_mov_to_wav(input_path, output_path):
            # Clean up the uploaded file
            os.remove(input_path)
            return redirect(url_for('download_file', filename=output_filename))
        else:
            return "Conversion failed", 500
    
    return "Invalid file type", 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(
        app.config['CONVERTED_FOLDER'],
        filename,
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)