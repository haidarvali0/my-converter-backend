import os
import base64
import zipfile
from io import BytesIO
from PIL import Image

class PDFConverter:

    @staticmethod
    def to_image(input_path, output_folder, unique_id):
        """
        PDF ko JPG mein convert karo - MEMORY EFFICIENT
        - 5 ya kam pages = JSON mein base64 images
        - 6-25 pages = ZIP file (ek-ek karke process)
        - 25+ pages = Error (free tier limit)
        """
        try:
            from pdf2image import convert_from_path, pdfinfo_from_path

            # Step 1: Pehle sirf page count nikalo (bina memory use kiye)
            info = pdfinfo_from_path(input_path)
            total_pages = int(info["Pages"])

            # Step 2: FREE TIER LIMIT - 25 pages max
            MAX_PAGES = 25
            if total_pages > MAX_PAGES:
                return {
                    'success': False,
                    'error': f'Free version mein sirf {MAX_PAGES} pages tak allowed. Aapki PDF mein {total_pages} pages hain. Kam pages wali PDF daalo.'
                }

            # =========================================
            # CASE 1: 5 ya kam pages = Direct Images
            # =========================================
            if total_pages <= 5:
                images = convert_from_path(input_path, dpi=100, fmt='jpeg')
                encoded_images = []

                for img in images:
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    buffer.seek(0)
                    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    encoded_images.append(encoded)

                return {
                    'success': True,
                    'type': 'images',
                    'data': encoded_images,
                    'total_pages': total_pages
                }

            # =========================================
            # CASE 2: 6-25 pages = ZIP (Memory Efficient)
            # =========================================
            else:
                zip_filename = f"{unique_id}_pages.zip"
                zip_path = os.path.join(output_folder, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    
                    # EK-EK PAGE process karo - memory bachao
                    for page_num in range(1, total_pages + 1):
                        images = convert_from_path(
                            input_path,
                            dpi=100,              # Lower DPI = less memory
                            first_page=page_num,
                            last_page=page_num,   # Sirf 1 page
                            fmt='jpeg'
                        )

                        if images:
                            img = images[0]
                            img_buffer = BytesIO()
                            img.save(img_buffer, format='JPEG', quality=85)
                            img_buffer.seek(0)

                            zip_file.writestr(
                                f'Page_{page_num:03d}.jpg',
                                img_buffer.getvalue()
                            )

                            # Memory free karo explicitly
                            del img
                            del images

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