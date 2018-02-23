import requests
import logging


class QueryFailureError(Exception):
    pass


def get_declarator_persons(name, position=None, full_output = False):
    persons = []
    url = f'https://declarator.org/api/v1/search/person-sections/?name={"%20".join(name.split(" "))}'
    response = requests.get(url).json()
    for person in response['results']:
        logging.getLogger().info(sorted(person['name'].lower().split(' ')), sorted(name.lower().split(' ')))
        word_set_name = set(name.lower().strip().split(' '))
        word_set_person_name = set(person['name'].lower().split(' '))
        if word_set_person_name.intersection(word_set_name):
            if position and (not person['sections'] or not position in person['sections'][0]['position'].lower().strip()):
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