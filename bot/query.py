import requests
from bs4 import BeautifulSoup

def remove_letters(text):
    return "".join(_ for _ in text if _ in ".1234567890")

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

def get_rusprofile_data(name):
    data = []

    def parse_company(url):
        content = requests.get(url).text
        soup = BeautifulSoup(content, 'html.parser')
        subceo = soup.find('span', {'class': 'subceo'})
        ceo_inn = None
        if subceo:
            ceo_inn = remove_letters(subceo.get_text())
        return {'ceo_inn': ceo_inn}

    url = 'http://www.rusprofile.ru/search?query=' + "+".join(name.split(" "))
    content = requests.get(url).text
    soup = BeautifulSoup(content, 'html.parser')

    results_ul = soup.find('div', {"class": "search-results"}).find('ul')

    companies = [

    ]

    results_entries = results_ul.find_all('li')

    for child in results_entries:
        ceoname = child.find('span', {'class': 'u-ceoname'})
        if ceoname and ceoname.get_text().lower() == name:
            ceoname = ceoname.get_text()
        else:
            continue

        link = child.find('a', {'class': "u-name"})
        if link:
            link = 'http://www.rusprofile.ru' + link.get('href')
        name = child.find('span', {'class': "und"})
        if name:
            name = name.get_text()

        address = child.find('div', {'class': "u-address"})
        if address:
            address = address.get_text()

        company_data = parse_company(link)

        ceo_inn = company_data['ceo_inn']
        company = {
            'link': link,
            'name': name,
            'address': address,
            'ceo_inn': ceo_inn
        }
        companies.append(company)

    if companies:
        data.append(f'В rusprofile найдено {len(companies)} юрлиц, где числится этот человек.\n')

    for company in companies:
        data.append(f'Название: {company["name"]}, адрес: {company["address"]}, ссылка: {company["link"]}, инн владельца: {company["ceo_inn"]}')

    return '\n'.join(data)


def inn_query(name):
    query_results = [ ]

    declarator_data = get_declarator_data(name)

    if not declarator_data:
        raise(Exception(f'Я не нашел в деклараторе данные про "{name}"'))
    query_results.append(declarator_data)
    query_results.append('')
    rusprofile_data = get_rusprofile_data(name)
    if rusprofile_data:
        query_results.append(rusprofile_data)
    return '\n'.join(query_results)


queries = {
    "инн": inn_query,
}


def query(method, text):
    method = method.lower().strip()
    text = text.lower().strip()
    query_function = queries.get(method)
    if not query_function:
        raise(Exception(f'Не знаю как искать {method}'))
    return query_function(text)