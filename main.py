import os
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, render_template, send_from_directory, url_for, jsonify
import whisper
import datetime
import uuid 
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Folder to store uploaded videos
UPLOAD_FOLDER = 'video_uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#  directory exists for render
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Route that handles video upload
@app.route('/upload', methods=['POST'])
def upload_video():
    if not request.files:
        return "No file part"
    
    video_file = request.files['video']
    if video_file.filename == '':
        return "No selected file"
    
    if video_file:
        # Generate a unique identifier (e.g., UUID) for the video
        unique_id = str(uuid.uuid4())
        
        # Use the unique identifier to create unique filenames for the video and transcription
        video_filename = f"{unique_id}.mp4"
        transcription_filename = f"{unique_id}.vtt"
        
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        video_file.save(video_path)
        
        # Use Whisper to transcribe the video
        model = whisper.load_model('base.en')
        option = whisper.DecodingOptions(language='en', fp16=False)
        result = model.transcribe(video_path)
        
        # Save the WebVTT file in the same directory as the video
        transcription_path = os.path.join(app.config['UPLOAD_FOLDER'], transcription_filename)
        
        with open(transcription_path, 'w') as file:
            for indx, segment in enumerate(result['segments']):
                file.write(str(indx + 1) + '\n')
                file.write(str(datetime.timedelta(seconds=segment['start'])) + '--> ' + str(datetime.timedelta(seconds=segment['end'])) + '\n')
                file.write(segment['text'].strip() + '\n')
                file.write('\n')
        
        # Return the URLs of the video and the transcription files
        return redirect(url_for('display_video', video=video_filename, subtitle=transcription_filename))

# Route for playing the video
@app.route('/display/<video>/<subtitle>')
def display_video(video, subtitle):
    # Get the full paths of the video and the subtitle files
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video)
    subtitle_path = os.path.join(app.config['UPLOAD_FOLDER'], subtitle)
    
    # Generate URLs with the unique identifiers
    video_url = url_for('uploaded_file', filename=video)
    subtitle_url = url_for('uploaded_file', filename=subtitle)
    
    # Render the template with the URLs of the files
    return render_template('play_video.html', video_url=video_url, subtitle_url=subtitle_url)

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Serve the file from the UPLOAD_FOLDER
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
