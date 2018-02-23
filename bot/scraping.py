import requests
from bs4 import BeautifulSoup

def parse_company(url):
    content = requests.get(url).text
    soup = BeautifulSoup(content, 'html.parser')
    subceo = soup.find('span', {'class': 'subceo'})
    ceo_inn = None
    if subceo:
        ceo_inn = subceo.get_text()
    return {'ceo_inn': ceo_inn}

name = "алферов жорес иванович"
url = 'http://www.rusprofile.ru/search?query='+ "+".join(name.split(" "))
content = requests.get(url).text
soup = BeautifulSoup(content, 'html.parser')

results_ul = soup.find('div', {"class": "search-results"}).find('ul')

companies = [

]

results_entries = results_ul.find_all('li')

for child in results_entries:
    ceoname = child.find('span', {'class':'u-ceoname'})
    if ceoname and ceoname.get_text().lower() == name:
        ceoname = ceoname.get_text()
    else:
        continue

    link = child.find('a', {'class': "u-name"})
    if link:
        link = 'http://www.rusprofile.ru'+link.get('href')
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