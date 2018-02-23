from .common import QueryFailureError, get_declarator_persons
from .inn import inn_query

queries = {
    "инн": inn_query,
}

def get_query_list():
    return list(queries.keys())

def run_query(method, text):
    method = method.lower().strip()
    text = text.lower().strip()
    query_function = queries.get(method)
    if not query_function:
        raise(QueryFailureError(f'Не знаю как искать {method}'))
    query_response, collisions = query_function(text)
    return query_response, collisions
