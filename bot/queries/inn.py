import requests
from bs4 import BeautifulSoup
from .common import get_declarator_data, QueryFailureError
from ..utils import only_digits, prettify as pr


def get_collisions(name, data):
    collisions = []
    for thing in data:
        if not thing['inn'] in [x['inn'] for x in collisions]:
            collisions.append({
                'person': name,
                'inn': thing['inn'],
                'description': f'ИНН {thing["inn"]}',
                'param': 'inn',
                'param_value': thing['inn'],
            })
    return collisions


def get_ip_data(name, results_ul):
    ips = []

    results_entries = results_ul.find_all('li')

    for child in results_entries:
        inn = child.find('div', {'class': "u-requisites"})
        if inn:
            inn = inn.find_all('div', {'class': 'u-reqline'})
            if inn:
                inn = only_digits(inn[1].get_text())

        link = child.find('a', {'class': "u-name"})
        if link:
            link = 'http://www.rusprofile.ru' + link.get('href')

        ips.append({'inn': inn, 'link': link})
    return ips


def get_company_data(name, results_ul):

    def parse_company(url):
        content = requests.get(url).text
        soup = BeautifulSoup(content, 'html.parser')
        subceo = soup.find('span', {'class': 'subceo'})
        inn = None
        if subceo:
            inn = only_digits(subceo.get_text())
        return {'inn': inn}

    companies = []

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

        inn = company_data['inn']
        company = {
            'link': link,
            'name': name,
            'address': address,
            'inn': inn
        }
        companies.append(company)
    return companies


def get_rusprofile_data(name):
    data = []

    url = 'http://www.rusprofile.ru/search?query=' + "+".join(name.split(" "))
    content = requests.get(url).text
    soup = BeautifulSoup(content, 'html.parser')

    results =  soup.find_all('div', {"class": "search-results"})

    companies = []
    ips = []
    for results_div in results:
        results_ul = results_div.find('ul')
        if results_div.get('class') and 'fiz' in results_div.get('class'):
            ips = get_ip_data(name, results_ul)
        else:
            companies = get_company_data(name, results_ul)

    if companies:
        data.append(f'В rusprofile найдено {len(companies)} юрлиц, где числится этот человек.')
        data.append('')
    for company in companies:
        data.append(f'Название: {company["name"]}, адрес: {company["address"]}, ссылка: {company["link"]}, инн владельца: {company["inn"]}')
        data.append('')
    if ips:
        data.append(f'В rusprofile найдено {len(ips)} ИП, с такими именами.')
    for ip in ips:
        data.append(f'ИНН: {ip["inn"]}, ссылка: {ip["link"]}')

    collisions = get_collisions(name, companies + ips)
    return '\n'.join(data), collisions


def inn_query(person):
    """Returns a log of query process and a list of collisions"""
    query_results = []
    name = pr(person["name"])
    position = pr(person["position"])
    declarator_data = get_declarator_data(name, position=position)

    if not declarator_data:
        raise(QueryFailureError(f'Я не нашел в деклараторе данные про "{name}"'))
    query_results.append(declarator_data)
    query_results.append('')

    rusprofile_data, collisions = get_rusprofile_data(name)
    if rusprofile_data:
        query_results.append(rusprofile_data)
    return '\n'.join(query_results), collisions
