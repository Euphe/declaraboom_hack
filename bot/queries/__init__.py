from .common import QueryFailureError, get_declarator_persons
from .inn import inn_query

queries = {
    "инн": inn_query,
}

def get_query_list():
    return list(queries.keys())

def run_query(method, person):
    method = method.lower().strip()
    query_function = queries.get(method)
    if not query_function:
        raise(QueryFailureError(f'Не знаю как искать {method}'))
    query_response, collisions = query_function(person)
    return query_response, collisions
