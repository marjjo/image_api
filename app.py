from flask import Flask, jsonify

app = Flask(__name__)

# External images grouped by subfolder
IMAGES = {
    "components": [
        "https://raw.githubusercontent.com/marjjo/image_api_images/refs/heads/main/components/bamboo1.jpg",
        "https://raw.githubusercontent.com/marjjo/image_api_images/refs/heads/main/components/bamboo2.jpg"
    ],
    "precedents": [
        "https://raw.githubusercontent.com/marjjo/image_api_images/refs/heads/main/precedents/pablo_luna1.JPG"

    ],
    # Add more subfolders and images as needed
}

@app.route("/")
def home():
    return "Hello! This is the Image API."

@app.route("/images")
def all_images():
    # Returns the whole dictionary of images
    return jsonify(IMAGES)

@app.route("/images/<subfolder>")
def images_by_subfolder(subfolder):
    # Returns all images from a specific subfolder
    if subfolder in IMAGES:
        return jsonify(IMAGES[subfolder])
    else:
        return jsonify({"error": "Subfolder not found"}), 404

@app.route("/images/<subfolder>/<int:image_id>")
def get_image(subfolder, image_id):
    # Returns a single image by subfolder and index
    if subfolder in IMAGES and 0 <= image_id < len(IMAGES[subfolder]):
        return jsonify({"url": IMAGES[subfolder][image_id]})
    else:
        return jsonify({"error": "Image not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)
