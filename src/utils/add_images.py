import os

from django.core.files import File

from app.settings import PROJECT_DIR
from marketing.product.models import Product
from system.file_upload.models import FileUpload, ProductFile


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
                    print(f"Product found: {product}")
                    ProductFile.objects.create(product=product, file=file_instance)
                    break
                else:
                    print(f"No product found with name: {full_file_name}")
                    attempt -= 1
                if attempt == 0:
                    print("No matching product found after all attempts.")
                    file_instance.note = f"Not found product with file name: {file_name}"
                    file_instance.save()
            file_names.append(image_name)

    return file_names
