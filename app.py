# app.py
# Flask Image API that serves images from ./images/<category>/... and loads tags from tags.json

from flask import Flask, jsonify, request, send_from_directory, abort
import os
import json
from typing import Dict, List

# ---- App & Config ------------------------------------------------------------

app = Flask(__name__, static_folder="images")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TAGS_PATH = os.path.join(BASE_DIR, "tags.json")


# ---- Tags loader -------------------------------------------------------------

def load_tags() -> Dict[str, Dict[str, List[str]]]:
    """
    Load tags from tags.json if it exists.
    Expected shape:
    {
      "components": { "bamboo_joint1.jpg": ["joint","scissor"] },
      "precedents": { "kinetic_gate1.jpg": ["deployable","kinetic"] }
    }
    """
    if os.path.exists(TAGS_PATH):
        with open(TAGS_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Normalize tags into lists of strings
                for cat, files in list(data.items()):
                    if not isinstance(files, dict):
                        data.pop(cat, None)
                        continue
                    for fname, tags in list(files.items()):
                        if isinstance(tags, list):
                            data[cat][fname] = [str(t) for t in tags]
                        else:
                            data[cat][fname] = [str(tags)]
                return data
            except Exception:
                return {}
    return {}


# ---- Helpers ----------------------------------------------------------------

def base_url() -> str:
    return request.host_url.rstrip("/")

def categories() -> List[str]:
    """List category folders inside ./images"""
    cats = []
    if os.path.isdir(app.static_folder):
        for name in os.listdir(app.static_folder):
            path = os.path.join(app.static_folder, name)
            if os.path.isdir(path) and not name.startswith("."):
                cats.append(name)
    return sorted(cats)

def image_files_in(category: str) -> List[str]:
    """List image filenames inside a category folder."""
    folder = os.path.join(app.static_folder, category)
    if not os.path.isdir(folder):
        return []
    return sorted(
        [
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
            and f.lower().endswith(IMAGE_EXTS)
        ]
    )

def parse_multi_param(values: List[str]) -> List[str]:
    """
    Accept repeated params (?tag=a&tag=b) and comma lists (?tag=a,b).
    Returns a flattened list of non-empty strings.
    """
    out = []
    for v in values:
        if v is None:
            continue
        parts = [p.strip() for p in v.split(",")]
        out.extend([p for p in parts if p])
    return out


# ---- Routes -----------------------------------------------------------------

@app.route("/")
def home():
    return "Hello! This is the Image API (serving /images folders with tag support)."

@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serve actual image files from ./images"""
    return send_from_directory(app.static_folder, filename)

@app.route("/images", methods=["GET"])
def list_all_images():
    """
    List images across categories with optional filtering:
      - categories: repeated or comma-separated (?categories=components&categories=precedents)
      - tag: repeated or comma-separated (?tag=hypar,tensegrity)
      - limit: integer (total items across all categories)
    Response shape:
      {
        "components": [{"url": "...", "filename": "...", "tags": ["..."], "category":"components"}, ...],
        "precedents": [...]
      }
    """
    TAGS = load_tags()

    # Parse filters
    cat_filter = parse_multi_param(request.args.getlist("categories"))
    tag_filter = [t.lower() for t in parse_multi_param(request.args.getlist("tag"))]
    limit = request.args.get("limit", type=int)
    if limit is not None and limit < 1:
        abort(400, description="limit must be >= 1")

    chosen_categories = cat_filter if cat_filter else categories()
    data = {}
    total_count = 0

    for cat in chosen_categories:
        files = image_files_in(cat)
        if not files:
            # Skip non-existing/empty categories silently
            continue

        bucket = []
        for fname in files:
            url = f"{base_url()}/images/{cat}/{fname}"
            tags = TAGS.get(cat, {}).get(fname, [])

            # Apply tag filter if present (match any)
            if tag_filter:
                tags_l = [t.lower() for t in tags]
                if not any(t in tags_l for t in tag_filter):
                    continue

            bucket.append({
                "url": url,
                "filename": fname,
                "tags": tags,
                "category": cat,
            })

            # Enforce global limit across all categories
            if limit is not None:
                total_count += 1
                if total_count >= limit:
                    if bucket:
                        data[cat] = bucket
                    return jsonify(data)

        if bucket:
            data[cat] = bucket

    return jsonify(data)

@app.route("/images/<category>", methods=["GET"])
def list_images_by_category(category: str):
    """
    List images for a single category with optional filtering:
      - tag: repeated or comma-separated
      - limit: integer (items for this category)
    Response: [{"url": "...", "filename": "...", "tags": ["..."], "category":"..."}]
    """
    TAGS = load_tags()

    files = image_files_in(category)
    if not files:
        return jsonify({"error": "Category not found or empty"}), 404

    tag_filter = [t.lower() for t in parse_multi_param(request.args.getlist("tag"))]
    limit = request.args.get("limit", type=int)
    if limit is not None and limit < 1:
        abort(400, description="limit must be >= 1")

    items = []
    for fname in files:
        url = f"{base_url()}/images/{category}/{fname}"
        tags = TAGS.get(category, {}).get(fname, [])

        if tag_filter:
            tags_l = [t.lower() for t in tags]
            if not any(t in tags_l for t in tag_filter):
                continue

        items.append({
            "url": url,
            "filename": fname,
            "tags": tags,
            "category": category,
        })

        if limit is not None and len(items) >= limit:
            break

    return jsonify(items)

@app.route("/images-search", methods=["GET"])
def search_by_tag():
    """
    Search across *all* categories by tag (case-insensitive exact match by token).
      - tag: repeated or comma-separated (required)
      - limit: integer
    Response: [{"url": "...", "filename": "...", "tags": [...], "category": "..."}]
    """
    TAGS = load_tags()
    tag_filter = [t.lower() for t in parse_multi_param(request.args.getlist("tag"))]
    if not tag_filter:
        abort(400, description="tag query parameter is required")

    limit = request.args.get("limit", type=int)
    if limit is not None and limit < 1:
        abort(400, description="limit must be >= 1")

    results = []
    for cat in categories():
        for fname in image_files_in(cat):
            tags = TAGS.get(cat, {}).get(fname, [])
            tags_l = [t.lower() for t in tags]
            if any(t in tags_l for t in tag_filter):
                results.append({
                    "url": f"{base_url()}/images/{cat}/{fname}",
                    "filename": fname,
                    "tags": tags,
                    "category": cat,
                })
                if limit is not None and len(results) >= limit:
                    return jsonify(results)

    return jsonify(results)


# ---- Main -------------------------------------------------------------------

if __name__ == "__main__":
    # Use debug=True only for local development
    app.run(debug=True)
