import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

RESIZABLE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def shrink_image(uploaded_file, max_size):
    """Return a copy of an uploaded image whose longest side is at most `max_size` pixels.

    Small images (and formats we don't resize, such as GIF) are returned unchanged.
    Phone photos are rotated according to their EXIF orientation before resizing.
    """
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as original:
        image_format = original.format
        if image_format not in RESIZABLE_FORMATS or max(original.size) <= max_size:
            uploaded_file.seek(0)
            return uploaded_file

        image = ImageOps.exif_transpose(original)
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        if image_format == 'JPEG' and image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        buffer = BytesIO()
        image.save(buffer, format=image_format, quality=85, optimize=True)
    return ContentFile(buffer.getvalue(), name=os.path.basename(uploaded_file.name))


def validate_upload_size(uploaded_file, max_mb):
    """Raise ValueError with a friendly message when a file is larger than `max_mb` megabytes."""
    if uploaded_file and uploaded_file.size > max_mb * 1024 * 1024:
        raise ValueError(f'Please upload an image smaller than {max_mb} MB.')
