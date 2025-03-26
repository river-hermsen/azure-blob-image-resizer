from flask import Flask, request, send_file
from services.blob_service import BlobService
from utils.image_helpers import (
    resize_image,
    calculate_requested_size,
    split_image_name,
    generate_resized_image_name,
    determine_mime_type,
)
from io import BytesIO
from PIL import Image
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
blob_service = BlobService()


def validate_resize_parameters():
    """
    Validate the resize parameters from the request.

    Returns:
        tuple: (requested_width, requested_height) or raises an exception
    """
    requested_width = None
    requested_height = None

    if request.args.get("w"):
        if not request.args.get("w").isdigit():
            logger.warning(f"Invalid width parameter: {request.args.get('w')}")
            raise ValueError("Width parameter must be a positive integer")
        requested_width = round(int(request.args.get("w")) / 10) * 10

    if request.args.get("h"):
        if not request.args.get("h").isdigit():
            logger.warning(f"Invalid height parameter: {request.args.get('h')}")
            raise ValueError("Height parameter must be a positive integer")
        requested_height = round(int(request.args.get("h")) / 10) * 10

    if not (requested_width or requested_height):
        logger.warning("No width or height parameters provided")
        raise ValueError("Must specify width or height")

    if requested_width and requested_height:
        logger.warning("Both width and height parameters provided")
        raise ValueError("Cannot specify both width and height")

    return requested_width, requested_height


@app.route("/<container_name>/<image_name>", methods=["GET"])
def get_image(container_name, image_name):
    start_time = time.time()
    request_id = f"{int(start_time)}-{container_name}-{image_name}"

    logger.info(
        f"[{request_id}] Processing request for image {image_name} in container {container_name}"
    )

    try:
        requested_width, requested_height = validate_resize_parameters()
    except ValueError as e:
        logger.error(f"[{request_id}] Parameter validation failed: {str(e)}")
        return str(e), 400

    # Get some metadata about the image
    try:
        image_filename, image_extension = split_image_name(image_name)
        resized_image_name = generate_resized_image_name(
            image_filename,
            image_extension,
            requested_width=requested_width,
            requested_height=requested_height,
        )
        mime_type = determine_mime_type(image_extension)
    except Exception as e:
        logger.error(f"[{request_id}] Error processing image metadata: {str(e)}")
        return f"Error processing image: {str(e)}", 500

    # Check if the image exists in the blob storage with given size and then return this
    if requested_width or requested_height:
        resized_image_data = blob_service.download_image(
            resized_image_name, container_name
        )

        if resized_image_data:
            logger.info(
                f"[{request_id}] Resized image found in cache, returning without processing"
            )
            processing_time = time.time() - start_time
            logger.info(
                f"[{request_id}] Request completed in {processing_time:.3f}s (cached)"
            )
            return send_file(BytesIO(resized_image_data), mimetype=mime_type)

    # Get the image data from Azure Blob Storage
    original_image_data = blob_service.download_image(image_name, container_name)

    if not original_image_data:
        logger.error(f"[{request_id}] Original image not found: {image_name}")
        return "Image not found", 404

    try:
        # Open the image to get dimensions
        original_image = Image.open(BytesIO(original_image_data))

        if requested_width > original_image.width:
            logger.warning(
                f"[{request_id}] Requested width {requested_width} exceeds original width {original_image.width}. Returning original image."
            )
            return send_file(BytesIO(original_image_data), mimetype=mime_type)
        elif requested_height > original_image.height:
            logger.warning(
                f"[{request_id}] Requested height {requested_height} exceeds original height {original_image.height}. Returning original image."
            )
            return send_file(BytesIO(original_image_data), mimetype=mime_type)

        requested_size = calculate_requested_size(
            original_width=original_image.width,
            original_height=original_image.height,
            requested_width=requested_width,
            requested_height=requested_height,
        )

        # Resize the image
        resized_image_data = resize_image(original_image_data, requested_size)

        # Upload the resized image to Azure Blob Storage
        logger.info(f"[{request_id}] Uploading resized image to blob storage")
        blob_service.upload_image(
            image_data=resized_image_data,
            blob_name=resized_image_name,
            container_name=container_name,
        )
    except Exception as e:
        logger.error(
            f"[{request_id}] Error during image processing: {str(e)}", exc_info=True
        )
        return f"Error processing image: {str(e)}", 500

    # Return the image data
    processing_time = time.time() - start_time
    logger.info(f"[{request_id}] Request completed in {processing_time:.3f}s")
    return send_file(BytesIO(resized_image_data), mimetype=mime_type)


if __name__ == "__main__":
    logger.info("Starting Image Resizer service")
    app.run()
