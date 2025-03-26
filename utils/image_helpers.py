from PIL import Image
from io import BytesIO
import mimetypes


def calculate_requested_size(
    original_width, original_height, requested_width=None, requested_height=None
):
    """
    Calculate the dimensions while maintaining aspect ratio.

    Args:
        original_width: Original image width
        original_height: Original image height
        requested_width: Desired width (optional)
        requested_height: Desired height (optional)

    Returns:
        Tuple of (width, height) that maintains the original aspect ratio
    """
    if requested_width and requested_height:
        return (requested_width, requested_height)

    aspect_ratio = int(original_width) / int(original_height)

    if requested_width:
        new_height = int(requested_width / aspect_ratio)
        return (requested_width, new_height)
    elif requested_height:
        new_width = int(requested_height * aspect_ratio)
        return (new_width, requested_height)
    else:
        return None


def split_image_name(image_name):
    """
    Split the image name into base name and extension.

    Args:
        image_name: Image name with extension
    Returns:
        Tuple of (base name, extension)
    """
    image_name_parts = image_name.split(".")
    if len(image_name_parts) < 2:
        raise ValueError("Invalid image name")
    return image_name_parts[0], image_name_parts[1]


def generate_resized_image_name(
    image_filename, image_extension, requested_width=None, requested_height=None
):
    """
    Generate a new image name based on the requested dimensions.

    Args:
        image_name: Original image name
        requested_width: Desired width (optional)
        requested_height: Desired height (optional)
    Returns:
        New image name with dimensions appended
    """
    if requested_width and requested_height:
        raise ValueError("Cannot specify both width and height in the image name")
    elif requested_width:
        return f"{image_filename}-w={requested_width}.{image_extension}"
    elif requested_height:
        return f"{image_filename}-h={requested_height}.{image_extension}"
    else:
        raise ValueError(
            "Must specify either width or height to generate a resize image name"
        )


def resize_image(image_data, size):
    """
    Resize an image to the specified size and thne return the resized image data.

    Args:
        image_data: Image data as bytes
        size: Tuple of (width, height)

    Returns:
        Resized image data as bytes
    """
    img = Image.open(BytesIO(image_data))

    resized_img = img.resize(
        size,
        Image.Resampling.BILINEAR,
    )

    output = BytesIO()
    resized_img.save(output, format=img.format or "JPEG")
    output.seek(0)
    return output.getvalue()


def determine_mime_type(image_extension):
    """
    Determine the MIME type of the image based on its content.

    Args:
        image_data: Image data as bytes

    Returns:
        MIME type as a string
    """
    # Ensure the extension has a leading dot
    mime_type = mimetypes.guess_type(f"file.{image_extension}")[0]

    return mime_type if mime_type else "application/octet-stream"
