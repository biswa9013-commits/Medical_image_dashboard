
import os
import cv2
import numpy as np

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
from uuid import uuid4


app = Flask(__name__, template_folder="Templates")

# Folder paths
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


# Check file extension
def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# Home page
@app.route("/")
def home():

    return render_template("index.html")


# Upload image
@app.route("/upload", methods=["POST"])
def upload_image():

    if "image" not in request.files:
        return jsonify({"error": "No image selected"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "Please select an image"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only JPG, JPEG and PNG files are allowed"}), 400

    try:

        image_data = file.read()

        # Verify image using Pillow
        pil_image = Image.open(__import__("io").BytesIO(image_data))
        pil_image.verify()

        # Generate unique filename
        filename = str(uuid4()) + ".png"

        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Convert image bytes to OpenCV format
        image_array = np.frombuffer(image_data, np.uint8)

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if image is None:
            return jsonify({"error": "Invalid image"}), 400

        cv2.imwrite(file_path, image)

        height, width = image.shape[:2]

        return jsonify({
            "success": True,
            "filename": filename,
            "image_url": f"/uploads/{filename}",
            "width": width,
            "height": height,
            "message": "Image uploaded successfully"
        })

    except Exception:
        return jsonify({"error": "Unable to read this image"}), 400


# Image processing
@app.route("/process", methods=["POST"])
def process_image():

    data = request.get_json()

    filename = data.get("filename")
    operation = data.get("operation")

    if not filename or not isinstance(filename, str):
        return jsonify({"error": "Please upload an image first"}), 400

    # Prevent path traversal
    if os.path.basename(filename) != filename:
        return jsonify({"error": "Invalid filename"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.isfile(input_path):
        return jsonify({"error": "Image not found"}), 404

    image = cv2.imread(input_path)

    if image is None:
        return jsonify({"error": "Unable to open image"}), 400

    # Convert to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    result = gray
    message = ""
    area = 0
    region_count = 0

    # 1. Grayscale
    if operation == "grayscale":

        result = gray
        message = "Grayscale conversion completed"

    # 2. Image enhancement
    elif operation == "enhance":

        result = cv2.equalizeHist(gray)
        message = "Image enhancement completed"

    # 3. Threshold segmentation
    elif operation == "threshold":

        _, result = cv2.threshold(
            gray,
            120,
            255,
            cv2.THRESH_BINARY
        )

        message = "Threshold segmentation completed"

    # 4. Edge detection
    elif operation == "edges":

        result = cv2.Canny(
            gray,
            50,
            150
        )

        message = "Edge detection completed"

    # 5. Noise removal
    elif operation == "denoise":

        result = cv2.medianBlur(
            image,
            5
        )

        message = "Noise removal completed"

    # 6. Region measurement
    elif operation == "measure":

        _, binary = cv2.threshold(
            gray,
            120,
            255,
            cv2.THRESH_BINARY
        )

        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        result = cv2.cvtColor(
            gray,
            cv2.COLOR_GRAY2BGR
        )

        for contour in contours:

            current_area = cv2.contourArea(contour)

            if current_area > 100:

                area += current_area
                region_count += 1

                x, y, w, h = cv2.boundingRect(contour)

                cv2.rectangle(
                    result,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

        message = "Region measurement completed"

    else:

        return jsonify({"error": "Invalid processing operation"}), 400

    # Save output
    output_filename = str(uuid4()) + ".png"

    output_path = os.path.join(
        OUTPUT_FOLDER,
        output_filename
    )

    cv2.imwrite(output_path, result)

    return jsonify({
        "success": True,
        "result_url": f"/outputs/{output_filename}",
        "operation": operation,
        "message": message,
        "area": round(area, 2),
        "region_count": region_count,
        "width": result.shape[1],
        "height": result.shape[0]
    })


# Display uploaded image
@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# Download processed image
@app.route("/outputs/<filename>")
def output_file(filename):

    return send_from_directory(
        OUTPUT_FOLDER,
        filename
    )


if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )
