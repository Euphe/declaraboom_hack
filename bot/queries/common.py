import requests


class QueryFailureError(Exception):
    pass


def get_declarator_data(name):
    data = [ ]
    url = f'https://declarator.org/api/v1/search/person-sections/?name={"%20".join(name.split(" "))}'
    response = requests.get(url).json()
    if not response and not response['results']:
        return None

    person_declarations = []
    for declaration in response['results']:
        if declaration['name'].lower() == name.lower():
            person_declarations.append(declaration)
    if not person_declarations:
        return None

    data.append(f'Найдено {len(person_declarations)} деклараций этого человека в Деклараторе.')
    data.append(f'Запрос: {url}')

    return '\n'.join(data)