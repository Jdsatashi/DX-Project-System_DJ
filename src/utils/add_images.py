import os

from django.core.files import File

from app.logs import app_log
from app.settings import PROJECT_DIR
from marketing.product.models import Product, ProductCategory
from system.file_upload.models import FileUpload, ProductFile, ProductCateFile


def import_images():
    directory = os.path.join(PROJECT_DIR, 'product_image')
    image_files = [f for f in os.listdir(directory) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    file_names = []

    for image_name in image_files:
        file_path = os.path.join(directory, image_name)
        with open(file_path, 'rb') as file:
            django_file = File(file)
            file_instance = FileUpload(
                file=django_file,
            )
            file_instance.save()
            file_name = image_name.split('.')[0]
            file_names = file_name.split('_')
            attempt = len(file_names)

            while attempt > 0:
                full_file_name = " ".join(file_names[:attempt])
                product = Product.objects.filter(name__icontains=full_file_name).first()
                if product:
                    app_log.info(f"Product found: {product}")
                    ProductFile.objects.create(product=product, file=file_instance)
                    break
                else:
                    app_log.info(f"No product found with name: {full_file_name}")
                    attempt -= 1
                if attempt == 0:
                    app_log.info("No matching product found after all attempts.")
                    file_instance.note = f"Not found product with file name: {file_name}"
                    file_instance.save()
            file_names.append(image_name)

    return file_names


def add_images_to_categories():
    image_files = FileUpload.objects.filter(id__gt=124)
    not_founds = []
    for image_file in image_files:
        file_name = image_file.file_name
        file_names = file_name.split('_')
        space_name = " ".join(file_name.split('_'))
        app_log.info(space_name)
        attempt = len(file_names)
        while attempt > 0:
            full_file_name = " ".join(file_names[:attempt])
            product_cate = ProductCategory.objects.filter(name__icontains=full_file_name).first()
            if product_cate:
                add_files = ProductCateFile.objects.create(product_cate=product_cate, file=image_file)
                app_log.info(f"Product found: {add_files}")
                break
            else:
                app_log.info(f"No product found with name: {full_file_name}")
                attempt -= 1
            if attempt == 0:
                not_founds.append((image_file.id, space_name))
                app_log.info("No matching product found after all attempts.")
                image_file.note = f"Not found product category with file name: {file_name}"
                image_file.save()
    app_log.info(f"Not found name: \n - {not_founds}")
