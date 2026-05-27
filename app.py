from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
import os
import uuid
import base64
import zipfile
import tempfile
from io import BytesIO
from converters.pdf_converter import PDFConverter

app = Flask(__name__)
CORS(app)

# Folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =============================================
# HOME - Test Page
# =============================================
@app.route('/', methods=['GET'])
def home():
    return '''
    <h2 style="font-family: Arial;">Bhai Ka Converter Tester 🚀</h2>
    <form action="/convert/pdf-to-jpg" method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept=".pdf" style="margin-bottom: 10px;"><br>
      <input type="submit" value="Convert to JPG" 
       style="padding: 10px; background: blue; color: white; border: none; border-radius: 5px;">
    </form>
    '''

# =============================================
# PDF TO JPG - MAIN ROUTE
# =============================================
@app.route('/convert/pdf-to-jpg', methods=['POST'])
def convert_pdf_to_jpg():
    
    # Step 1: File check karo
    if 'file' not in request.files:
        return jsonify({"error": "Koi file nahi mili"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "File select nahi ki"}), 400

    # Step 2: File save karo
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.pdf")
    file.save(input_path)

    try:
        # Step 3: Converter call karo
        result = PDFConverter.to_image(input_path, OUTPUT_FOLDER, unique_id)

        # Step 4: Result check karo
        if not result['success']:
            return jsonify({
                "error": f"Conversion mein dikkat: {result['error']}"
            }), 500

        # =============================================
        # CASE 1: Kam pages - JSON mein images bhejo
        # =============================================
        if result['type'] == 'images':
            return jsonify({
                "status": "success",
                "type": "images",
                "total_pages": len(result['data']),
                "images": result['data']  # Base64 list
            })

        # =============================================
        # CASE 2: Zyada pages - ZIP file bhejo
        # =============================================
        elif result['type'] == 'zip':
            zip_path = result['file_path']

            # ZIP file ko bytes mein padho
            with open(zip_path, 'rb') as f:
                zip_bytes = f.read()

            # Total pages count karo ZIP se
            with zipfile.ZipFile(zip_path, 'r') as zf:
                total_pages = len(zf.namelist())

            # Response banao - Content-Type clearly ZIP set karo
            response = Response(
                zip_bytes,
                status=200,
                mimetype='application/zip'
            )
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = \
                'attachment; filename=Converted_Pages.zip'
            response.headers['X-Total-Pages'] = str(total_pages)
            response.headers['X-Response-Type'] = 'zip'

            return response

        else:
            return jsonify({"error": "Unknown result type"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

    finally:
        # Input file delete karo (cleanup)
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except:
            pass


# =============================================
# HEALTH CHECK - Server chal raha hai ya nahi
# =============================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "Server chal raha hai! ✅",
        "version": "1.0"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)