import os
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

# Root directory for images
IMAGE_DIR = os.path.join(app.root_path, 'static')

@app.route('/')
def home():
    return "📁 Image API with subfolder support is running!"

@app.route('/images', methods=['GET'])
def get_images():
    """
    Scans /static and all subfolders for images.
    Optional query params:
    - folder: specify a subfolder (e.g. ?folder=components)
    - tag: filter by keyword in filename
    """
    folder = request.args.get('folder')
    tag = request.args.get('tag')

    # Determine directory path
    if folder:
        target_dir = os.path.join(IMAGE_DIR, folder)
    else:
        target_dir = IMAGE_DIR

    if not os.path.exists(target_dir):
        return jsonify({"error": f"Folder '{folder}' not found."}), 404

    images = []

    # Walk through all files and subdirectories
    for root, dirs, files in os.walk(target_dir):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                # Get the relative path of the image
                rel_path = os.path.relpath(os.path.join(root, filename), IMAGE_DIR)
                if tag and tag.lower() not in filename.lower():
                    continue
                images.append({
                    "name": filename,
                    "path": rel_path.replace("\\", "/"),
                    "url": f"/static/{rel_path.replace('\\', '/')}"
                })

    return jsonify(images)

@app.route('/static/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True)
