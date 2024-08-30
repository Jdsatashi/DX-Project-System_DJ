from django.db import transaction

from marketing.product.models import RegistrationCert, ProductCategory
from utils.helpers import self_id


def update_register_cert():
    for cert in RegistrationCert.objects.all():
        new_id = self_id('GDK', RegistrationCert, 4)

        with transaction.atomic():
            # Step 1: Change the name temporarily to avoid unique constraint violation
            origin_name = cert.name
            temp_name = f"temp_origin_name"
            RegistrationCert.objects.filter(id=cert.id).update(name=temp_name)

            # Step 2: Create a new RegistrationCert with the new id and original name
            new_cert = RegistrationCert(
                id=new_id,
                name=origin_name,
                date_activated=cert.date_activated,
                date_expired=cert.date_expired,
                registered_unit=cert.registered_unit,
                producer=cert.producer
            )
            new_cert.save()

            # Step 3: Update the foreign keys in related table(s)
            ProductCategory.objects.filter(registration_id=cert.id).update(registration_id=new_cert.id)

            # Step 4: Delete the old cert
            cert.delete()
