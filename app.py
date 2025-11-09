from flask import Flask, jsonify, send_from_directory
import os

# Create the Flask app and define where static files are stored
app = Flask(__name__, static_folder="static")

@app.route("/")
def home():
    return "Hello! This is the Image API serving from /static folders."

@app.route("/images")
def all_images():
    """
    Returns all categories and their image URLs dynamically.
    Example: { "components": [...], "precedents": [...] }
    """
    base_url = request.host_url.rstrip('/')
    data = {}

    # Loop through subfolders inside /static
    for category in os.listdir(app.static_folder):
        folder_path = os.path.join(app.static_folder, category)
        if os.path.isdir(folder_path):
            data[category] = [
                f"{base_url}/static/{category}/{f}"
                for f in os.listdir(folder_path)
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
            ]

    return jsonify(data)

@app.route("/images/<category>")
def images_by_category(category):
    """
    Returns all images from a specific subfolder (category).
    Example: /images/components
    """
    folder_path = os.path.join(app.static_folder, category)
    if not os.path.exists(folder_path):
        return jsonify({"error": "Category not found"}), 404

    base_url = request.host_url.rstrip('/')
    images = [
        f"{base_url}/static/{category}/{f}"
        for f in os.listdir(folder_path)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]
    return jsonify(images)

@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve individual image files from the static directory."""
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    app.run(debug=True)
