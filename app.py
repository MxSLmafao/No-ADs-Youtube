from dotenv import load_dotenv
import os
import yt_dlp
from flask import Flask, request, jsonify, render_template

# Load environment variables from .env file if available
load_dotenv()

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract_video_url():
    data = request.get_json()
    youtube_url = data.get('url')
    if not youtube_url:
        return jsonify({'error': 'No URL provided'}), 400

    # Path to your exported cookies file (in Netscape cookie file format)
    cookie_file_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
    
    # Set yt-dlp options to use cookies and force the web (desktop) client
    ydl_opts = {
        "cookiefile": cookie_file_path,
        "extractor_args": {
            "youtube": "player_client=web"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
        
        # Filter for progressive formats (formats that have both audio and video)
        progressive_formats = [
            f for f in info.get('formats', [])
            if f.get('acodec') != 'none' and f.get('vcodec') != 'none'
        ]
        
        chosen_format = None
        if progressive_formats:
            # First, try to find a format exactly at 1080p
            formats_1080 = [f for f in progressive_formats if f.get('height') == 1080]
            if formats_1080:
                # Optionally, choose the one with the highest bitrate among 1080p formats
                chosen_format = max(formats_1080, key=lambda f: f.get('tbr') or 0)
            else:
                # Find all formats with height <= 1080
                formats_below_1080 = [f for f in progressive_formats if f.get('height') and f.get('height') <= 1080]
                if formats_below_1080:
                    chosen_format = max(formats_below_1080, key=lambda f: f.get('height') or 0)
                else:
                    # Fallback: use the highest quality progressive format available
                    chosen_format = max(progressive_formats, key=lambda f: f.get('height') or 0)
        else:
            # If no progressive format exists, fall back to selecting the best overall format
            chosen_format = max(info.get('formats', []), key=lambda f: f.get('height') or 0)

        stream_url = chosen_format.get('url')
        if not stream_url:
            return jsonify({'error': 'No stream URL available'}), 500

        return jsonify({'video_url': stream_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Run on port 6789 instead of 5000
    port = int(os.environ.get('PORT', 6789))
    app.run(debug=True, port=port)
