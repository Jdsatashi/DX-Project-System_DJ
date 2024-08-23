import os
import re

from django.core.files import File

from app.logs import app_log
from marketing.product.models import ProductCategory, Product
from system.file_upload.models import FileUpload, RegistrationCertFile, ProductCateFile, upload_location


def normalize_name(name):
    return re.sub(r'\s+', ' ', name.strip().lower())


def import_files_from_directory(directory_path, file_type):
    if not os.path.exists(directory_path):
        raise ValueError("Directory does not exist")
    not_found = []
    for root, dirs, files in os.walk(directory_path):
        for i, file in enumerate(files):
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                django_file = File(f)
                filename, ext = os.path.splitext(file)

                app_log.info(f"{filename} | {ext}")
                if file_type == 'register':
                    filename_list = filename.split(' ')
                    search_filename = filename_list[1:]
                else:  # == 'image'
                    search_filename = filename.split('_')
                while len(search_filename) >= 1:
                    search_filename = " ".join(search_filename)
                    result = ProductCategory.objects.filter(name__icontains=search_filename)
                    if result.exists():
                        product_cate = result.first()
                        app_log.info(f"Found product cate: {product_cate}")

                        file_instance = FileUpload.objects.create(file=django_file)
                        docs_type = filename_list[0].lower() if filename_list[0] in ['gdk', 'cbhq'] else None
                        ProductCateFile.objects.create(file=file_instance, product_cate=product_cate, docs_type=docs_type)
                        break
                    else:
                        app_log.info(f"Product cate not found")
                        if len(search_filename) == 1:
                            not_found.append(f"File: {filename}")
                        search_filename = search_filename.split(' ')
                        search_filename.pop()
                        continue

    app_log.info(f"Not found list: {not_found}")


document_path = r"/home/jdsatashi/GDK"
image_path = r"/home/jdsatashi/Hinh Thuoc"


def add_doc():
    import_files_from_directory(document_path, 'register')


def add_img():
    import_files_from_directory(image_path, 'image')
