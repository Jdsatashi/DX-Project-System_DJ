from datetime import datetime, timedelta

from django.core.exceptions import FieldError
from django.core.paginator import Paginator
from django.db.models import Q

from app.logs import app_log


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
    return query, strict_mode, limit, page, order_by, from_date, to_date


def dynamic_q(queries, fields, strict_mode):
    dynamic_query = Q()
    query_type = '__icontains' if not strict_mode else '__exact'
    for query in queries:
        sub_query = Q()
        for field in fields:
            sub_query |= Q(**{f'{field}{query_type}': query})
        dynamic_query &= sub_query
    return dynamic_query


def filter_data(self, request, query_fields, **kwargs):
    # Get query set if exists or get default
    queryset = kwargs.get('queryset', self.get_queryset())
    # Split query search, strict mode, limit, page, order_by
    query, strict_mode, limit, page, order_by, from_date, to_date = get_query_parameters(request)
    # If query exists, filter queryset
    if query != '':
        queries = query.split(',')
        query_filter = dynamic_q(queries, query_fields, strict_mode)
        queryset = queryset.filter(query_filter)
    if from_date or to_date:
        try:
            if from_date:
                from_date = datetime.strptime(from_date, '%d/%m/%Y')
                queryset = queryset.filter(created_at__gte=from_date)
            if to_date:
                to_date = datetime.strptime(to_date, '%d/%m/%Y') + timedelta(days=1) - timedelta(seconds=1)
                queryset = queryset.filter(created_at__lte=to_date)
        except ValueError:
            pass
    # Get fields in models
    valid_fields = [f.name for f in self.serializer_class.Meta.model._meta.get_fields()]
    # Check field order_by exists, then order queryset
    try:
        if order_by in valid_fields or order_by.lstrip('-') in valid_fields:
            queryset = queryset.order_by(order_by)
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
    # Check when limit is 0, return all data
    if limit == 0:
        serializer = self.serializer_class(queryset, many=True)
        response_data = {
            'data': serializer.data,
            'total_page': 1,
            'current_page': 1,
            'next_page': None,
            'prev_page': None
        }
        return response_data
    # Paginate queryset
    paginator = Paginator(queryset, limit)
    # Get page object
    page_obj = paginator.get_page(page)
    # Get serializer data in page objects data
    serializer = self.serializer_class(page_obj, many=True)
    # Validate page number
    if page < 0:
        page = 1
    elif page > paginator.num_pages:
        page = paginator.num_pages
    # Add total and current page and data to response data
    response_data = {
        'data': serializer.data,
        'total_page': paginator.num_pages,
        'current_page': page
    }
    # If has next page, add urls to response data
    if page_obj.has_next():
        next_page = request.build_absolute_uri(
            '?page={}&limit={}&query={}&order_by={}&from_date={}&to_date={}'.format(
                page_obj.next_page_number(), limit, query, order_by, from_date, to_date))
        response_data['next_page'] = next_page
    # If has previous page, add urls to response data
    if page_obj.has_previous():
        prev_page = request.build_absolute_uri(
            '?page={}&limit={}&query={}&order_by={}&from_date={}&to_date={}'.format(
                page_obj.previous_page_number(), limit, query, order_by, from_date, to_date))
        response_data['prev_page'] = prev_page
    return response_data
