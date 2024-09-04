from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.core.exceptions import FieldError, FieldDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.fields.related import ForeignKey

from app.logs import app_log


def is_valid_query2(field, value, model):
    field_type = model._meta.get_field(field).get_internal_type()

    if field_type in ['IntegerField', 'FloatField', 'DecimalField']:
        try:
            float(value)
        except ValueError:
            return False

    elif field_type in ['DateField']:
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return False

    elif field_type in ['TimeField']:
        try:
            datetime.strptime(value, '%H:%M:%S')
        except ValueError:
            return False

    elif field_type in ['DateTimeField']:
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return False

    elif field_type in ['BooleanField']:
        if value.lower() not in ['true', 'false']:
            return False

    return True


def is_valid_query(field, value, model):
    # Handle ForeignKey fields
    field_parts = field.split('__')
    current_model = model

    for part in field_parts:
        try:
            field_object = current_model._meta.get_field(part)
        except FieldDoesNotExist:
            return False

        if isinstance(field_object, ForeignKey):
            current_model = field_object.related_model
        else:
            break

    field_type = field_object.get_internal_type()

    if field_type in ['IntegerField', 'FloatField', 'DecimalField']:
        try:
            float(value)
        except ValueError:
            return False

    elif field_type in ['DateField']:
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return False

    elif field_type in ['TimeField']:
        try:
            datetime.strptime(value, '%H:%M:%S')
        except ValueError:
            return False

    elif field_type in ['DateTimeField']:
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return False

    elif field_type in ['BooleanField']:
        if value.lower() not in ['true', 'false']:
            return False

    return True


def get_query_parameters(request):
    data = request.data if isinstance(request.data, dict) else {}
    query = data.get('query') or request.query_params.get('query', '')
    limit = int(data.get('limit') or request.query_params.get('limit', 10))
    page = int(data.get('page') or request.query_params.get('page', 1))
    order_by = data.get('order_by', '') or request.query_params.get('order_by', '')
    strict = data.get('strict') or request.query_params.get('strict', 0)
    strict = int(strict)
    strict = strict if strict in [0, 1] else 0
    strict_mode = bool(strict)
    from_date = data.get('from_date') or request.query_params.get('from_date', '')
    to_date = data.get('to_date') or request.query_params.get('to_date', '')
    date_field = data.get('date_field') or request.query_params.get('date_field', 'created_at')
    return query, strict_mode, limit, page, order_by, from_date, to_date, date_field


def dynamic_q(queries, fields, strict_mode, model):
    dynamic_query = Q()
    query_type = '__icontains' if not strict_mode else '__exact'
    for query in queries:
        sub_query = Q()
        for field in fields:
            if is_valid_query(field, query, model):
                sub_query |= Q(**{f'{field}{query_type}': query})
                print(sub_query)
        dynamic_query &= sub_query
    return dynamic_query


def filter_data(self, request, query_fields, **kwargs):
    # Get query set if exists or get default
    try:
        model = self.serializer_class.Meta.model
    except AttributeError:
        serializer_classes = self.get_serializer_class()
        model = serializer_classes.Meta.model
    queryset = kwargs.get('queryset', self.get_queryset())
    order_by_required = kwargs.get('order_by_required', True)
    # Split query search, strict mode, limit, page, order_by
    query, strict_mode, limit, page, order_by, from_date, to_date, date_field = get_query_parameters(request)
    # If query exists, filter queryset
    if query != '':
        queries = query.split(',')
        query_filter = dynamic_q(queries, query_fields, strict_mode, model)
        print(f"Test query: {query_filter}")
        queryset = queryset.filter(query_filter)
    if from_date or to_date:
        try:
            app_log.info(f"Check date field: {date_field}")
            if from_date:
                app_log.info(f"Check from date 1: {from_date}")
                from_date = datetime.strptime(from_date, '%d/%m/%Y')
                app_log.info(f"Check from date 2: {from_date}")
                queryset = queryset.filter(**{f'{date_field}__gte': from_date})
            if to_date:
                app_log.info(f"Check to date 1: {to_date}")
                to_date = datetime.strptime(to_date, '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1)
                app_log.info(f"Check to date 2: {to_date}")
                queryset = queryset.filter(**{f'{date_field}__lte': to_date})
        except ValueError:
            pass
    # Get fields in models
    valid_fields = [f.name for f in self.serializer_class.Meta.model._meta.get_fields()]
    # Check field order_by exists, then order queryset
    try:
        if order_by in valid_fields or order_by.lstrip('-') in valid_fields:
            queryset = queryset.order_by(order_by)
        elif not order_by_required:
            pass
        else:
            try:
                queryset = queryset.order_by('created_at')
            except FieldError:
                queryset = queryset.order_by('id')
            except Exception as e:
                app_log.error(f"Error order_by fields")
                raise e
    except FieldError:
        pass

    # Get total items
    total_count = queryset.count()

    # Check when limit is 0, return all data
    if limit == 0:
        try:
            serializer = self.serializer_class(queryset, many=True)
        except Exception as e:
            serializer_classes = self.get_serializer_class()
            serializer = serializer_classes(queryset, many=True)
        response_data = {
            'data': serializer.data,
            'total_page': 1,
            'current_page': 1,
            'total_count': total_count,
            'next_page': None,
            'prev_page': None
        }
        return response_data
    # Paginate queryset
    paginator = Paginator(queryset, limit)
    # Get page object
    page_obj = paginator.get_page(page)
    # Get serializer data in page objects data
    try:
        serializer = self.serializer_class(page_obj, many=True)
    except Exception as e:
        serializer_classes = self.get_serializer_class()
        serializer = serializer_classes(page_obj, many=True)
    # Validate page number
    if page < 0:
        page = 1
    elif page > paginator.num_pages:
        page = paginator.num_pages
    # Add total and current page and data to response data
    response_data = {
        'data': serializer.data,
        'total_page': paginator.num_pages,
        'current_page': page,
        'total_count': total_count,
    }
    # if page_obj.has_next():
    #     next_page = request.build_absolute_uri(
    #         '?page={}&limit={}&query={}&order_by={}&date_field={}&from_date={}&to_date={}'.format(
    #             page_obj.next_page_number(), limit, query, order_by, date_field, from_date, to_date))
    #     response_data['next_page'] = next_page
    # if page_obj.has_previous():
    #     prev_page = request.build_absolute_uri(
    #         '?page={}&limit={}&query={}&order_by={}&date_field={}&from_date={}&to_date={}'.format(
    #             page_obj.previous_page_number(), limit, query, order_by, date_field, from_date, to_date))
    #     response_data['prev_page'] = prev_page

    extra_params = kwargs.get('extra_params', {})

    # If has next page, add urls to response data
    if page_obj.has_next():
        next_page = build_absolute_uri_with_params(request, {'page': page_obj.next_page_number(), 'limit': limit,
                                                             **extra_params})
        response_data['next_page'] = next_page

    # If has previous page, add urls to response data
    if page_obj.has_previous():
        prev_page = build_absolute_uri_with_params(request, {'page': page_obj.previous_page_number(), 'limit': limit,
                                                             **extra_params})
        response_data['prev_page'] = prev_page

    return response_data


def build_absolute_uri_with_params(request, extra_params=None):
    params = request.GET.copy()

    if extra_params:
        params.update(extra_params)

    filtered_params = {key: value for key, value in params.items() if value}

    url = request.build_absolute_uri('?' + urlencode(filtered_params))
    return url
