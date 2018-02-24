import requests
from ..utils import prettify as pr

class QueryFailureError(Exception):
    pass


def get_declarator_persons(name, position=None, full_output = False):
    name = pr(name)
    if position:
        position = pr(position)
    persons = []
    url = f'https://declarator.org/api/v1/search/person-sections/?name={"%20".join(name.split(" "))}'
    response = requests.get(url).json()
    for person in response['results']:
        word_set_name = set(pr(name).split(' '))
        word_set_person_name = set(pr(person['name']).split(' '))
        if word_set_person_name.intersection(word_set_name):
            if position and (not person['sections'] or position not in pr(person['sections'][0]['position'])):
                continue
            if full_output:
                persons.append(person)
            else:
                person_position = person['sections'][0]['position'] if person['sections'] else ''
                persons.append({'id': person['id'], 'name': person['name'], 'position': person_position})
    return persons


def get_declarator_data(name, position=None):
    data = []
    persons = get_declarator_persons(name, position, full_output=True)
    if len(persons) > 1:
        raise(QueryFailureError('Два человека с таким именем и позицией, не знаю что делать с таким запросом.'))
    if len(persons) == 0:
        raise (QueryFailureError('Не нашел такого человека в базе декларатора'))

    person = persons[0]

    human_url = f'https://declarator.org/person/{person["id"]}/'
    data.append(f'Найдены декларации этого человека в Деклараторе.')
    data.append(f'Ссылка: {human_url}')

    return '\n'.join(data)