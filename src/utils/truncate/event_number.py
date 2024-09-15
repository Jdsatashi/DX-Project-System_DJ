from marketing.pick_number.models import EventNumber, NumberSelected


def update_repeat_count(event_number_id):
    evn = EventNumber.objects.get(pk=event_number_id)
    numbers_list = evn.number_list.all()
    numbers_selected = NumberSelected.objects.filter(user_event__event=evn)
    numbers_selected_list = numbers_selected.values_list('number__number', flat=True).distinct()

    updated_count = list()

    for number_selected in numbers_selected_list:
        number_in_list = numbers_list.filter(number=number_selected).first()
        number_in_list.repeat_count = numbers_selected.filter(number__number=number_selected).count()
        print(f"Test count: {number_in_list.repeat_count}")
        updated_count.append(number_in_list)
        # number_in_list.save()
