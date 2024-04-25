from django.core.paginator import Paginator
from django.db.models import Q


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
    return query, strict_mode, limit, page, order_by


def dynamic_q(query, fields, strict_mode):
    dynamic_q = Q()
    query_type = '__icontains' if not strict_mode else '__exact'
    for field in fields:
        print(f'{field}{query_type}')
        dynamic_q |= Q(**{f'{field}{query_type}': query})
    return dynamic_q


def filter_data(self, request, query_fields, *args, **kwargs):
    query, strict_mode, limit, page, order_by = get_query_parameters(request)
    products = self.get_queryset()
    if query != '':
        query_filter = dynamic_q(query, query_fields, strict_mode)
        products = products.filter(query_filter)
    valid_fields = [f.name for f in self.serializer_class.Meta.model._meta.get_fields()]
    if order_by in valid_fields or order_by.lstrip('-') in valid_fields:
        products = products.order_by(order_by)
    print(f"TEST -------------------------")
    print(products)
    if limit == 0:
        serializer = self.serializer_class(products, many=True)
        response_data = {
            'data': serializer.data,
            'total_page': 1,
            'current_page': 1,
            'next_page': None,
            'prev_page': None
        }
        return response_data
    paginator = Paginator(products, limit)
    page_obj = paginator.get_page(page)
    serializer = self.serializer_class(page_obj, many=True)
    if page < 0:
        page = 1
    elif page > paginator.num_pages:
        page = paginator.num_pages
    response_data = {
        'data': serializer.data,
        'total_page': paginator.num_pages,
        'current_page': page
    }
    if page_obj.has_next():
        next_page = request.build_absolute_uri(
            '?page={}&limit={}&query={}'.format(page_obj.next_page_number(), limit, query))
        response_data['next_page'] = next_page
    if page_obj.has_previous():
        prev_page = request.build_absolute_uri(
            '?page={}&limit={}&query={}'.format(page_obj.previous_page_number(), limit, query))
        response_data['prev_page'] = prev_page
    return response_data
