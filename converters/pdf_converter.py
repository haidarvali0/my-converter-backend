import os
import base64
import zipfile
from io import BytesIO
from PIL import Image

class PDFConverter:

    @staticmethod
    def to_image(input_path, output_folder, unique_id):
        """
        PDF ko JPG mein convert karo
        - 3 ya kam pages = JSON mein base64 images
        - 4+ pages = ZIP file
        """
        try:
            from pdf2image import convert_from_path

            # PDF convert karo
            images = convert_from_path(
                input_path,
                dpi=150,
                fmt='jpeg'
            )

            total_pages = len(images)

            # =========================================
            # 3 ya kam pages - Base64 JSON return karo
            # =========================================
            if total_pages <= 3:
                encoded_images = []

                for i, img in enumerate(images):
                    # Image ko bytes mein convert karo
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=90)
                    buffer.seek(0)

                    # Base64 encode karo
                    encoded = base64.b64encode(
                        buffer.getvalue()
                    ).decode('utf-8')

                    encoded_images.append(encoded)

                return {
                    'success': True,
                    'type': 'images',
                    'data': encoded_images,
                    'total_pages': total_pages
                }

            # =========================================
            # 4+ pages - ZIP file banao
            # =========================================
            else:
                zip_filename = f"{unique_id}_pages.zip"
                zip_path = os.path.join(output_folder, zip_filename)

                with zipfile.ZipFile(
                    zip_path, 'w', zipfile.ZIP_DEFLATED
                ) as zip_file:

                    for i, img in enumerate(images):
                        # Image bytes
                        img_buffer = BytesIO()
                        img.save(
                            img_buffer,
                            format='JPEG',
                            quality=90
                        )
                        img_buffer.seek(0)

                        # ZIP mein daal do
                        zip_file.writestr(
                            f'Page_{i + 1:03d}.jpg',
                            img_buffer.getvalue()
                        )

                return {
                    'success': True,
                    'type': 'zip',
                    'file_path': zip_path,
                    'total_pages': total_pages
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }