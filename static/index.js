const imageInput = document.getElementById("imageInput");
const uploadButton = document.getElementById("uploadButton");
const uploadArea = document.getElementById("uploadArea");
const originalImage = document.getElementById("originalImage");
const processedImage = document.getElementById("processedImage");
const uploadMessage = document.getElementById("uploadMessage");
const processMessage = document.getElementById("processMessage");
const toolButtons = document.querySelectorAll(".tool-button");

let uploadedFilename = null;

uploadButton.addEventListener("click", function () {
    imageInput.click();
});

imageInput.addEventListener("change", async function () {
    const file = imageInput.files[0];
    imageInput.value = "";

    if (file) {
        await uploadImage(file);
    }
});

uploadArea.addEventListener("dragover", function (event) {
    event.preventDefault();
    uploadArea.classList.add("drag-over");
});

uploadArea.addEventListener("dragleave", function (event) {
    if (!uploadArea.contains(event.relatedTarget)) {
        uploadArea.classList.remove("drag-over");
    }
});

uploadArea.addEventListener("drop", async function (event) {
    event.preventDefault();
    uploadArea.classList.remove("drag-over");

    const file = event.dataTransfer.files[0];
    if (file) {
        await uploadImage(file);
    }
});

async function uploadImage(file) {
    const extension = file.name.split(".").pop().toLowerCase();
    const allowedExtensions = ["png", "jpg", "jpeg"];

    if (!allowedExtensions.includes(extension)) {
        uploadMessage.textContent = "Choose a PNG, JPG, or JPEG image.";
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        uploadMessage.textContent = "This image is larger than the 10 MB limit.";
        return;
    }

    uploadMessage.textContent = "Uploading image...";
    uploadButton.disabled = true;

    const formData = new FormData();
    formData.append("image", file);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Upload failed");
        }

        uploadedFilename = data.filename;
        originalImage.src = data.image_url;
        originalImage.hidden = false;
        document.getElementById("originalPlaceholder").hidden = true;

        processedImage.hidden = true;
        document.getElementById("resultPlaceholder").hidden = false;
        document.getElementById("resultPlaceholder").textContent =
            "Processing result will appear here";

        document.getElementById("imageStatus").textContent = "Uploaded";
        document.getElementById("imageWidth").textContent = data.width + " px";
        document.getElementById("imageHeight").textContent = data.height + " px";
        document.getElementById("regionCount").textContent = "0";
        document.getElementById("regionArea").textContent = "0 pixels²";
        document.getElementById("operationName").textContent = "None";
        document.getElementById("processingStatus").textContent = "Waiting";
        document.getElementById("downloadButton").hidden = true;
        toolButtons.forEach(function (button) {
            button.classList.remove("selected");
        });

        uploadMessage.textContent = data.message;
        processMessage.textContent = "";
    } catch (error) {
        uploadMessage.textContent = error.message;
    } finally {
        uploadButton.disabled = false;
    }
}

toolButtons.forEach(function (button) {
    button.addEventListener("click", async function () {
        if (!uploadedFilename) {
            processMessage.textContent = "Please upload an image first.";
            return;
        }

        const operation = button.dataset.operation;
        processMessage.textContent = "Processing image...";
        document.getElementById("processingStatus").textContent = "Processing";
        toolButtons.forEach(function (item) {
            item.disabled = true;
            item.classList.toggle("selected", item === button);
        });

        try {
            const response = await fetch("/process", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    filename: uploadedFilename,
                    operation: operation
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Processing failed");
            }

            processedImage.src = data.result_url + "?t=" + Date.now();
            processedImage.hidden = false;
            document.getElementById("resultPlaceholder").hidden = true;

            document.getElementById("operationName").textContent =
                operation.replace("_", " ");
            document.getElementById("processingStatus").textContent = "Completed";
            document.getElementById("regionCount").textContent = data.region_count;
            document.getElementById("regionArea").textContent = data.area + " pixels²";

            const downloadButton = document.getElementById("downloadButton");
            downloadButton.href = data.result_url;
            downloadButton.hidden = false;
            processMessage.textContent = data.message;
        } catch (error) {
            document.getElementById("processingStatus").textContent = "Failed";
            processMessage.textContent = error.message;
        } finally {
            toolButtons.forEach(function (item) {
                item.disabled = false;
            });
        }
    });
});

document.querySelectorAll(".sidebar nav a").forEach(function (link) {
    link.addEventListener("click", function () {
        document.querySelectorAll(".sidebar nav a").forEach(function (item) {
            item.classList.remove("active");
        });
        link.classList.add("active");
    });
});
