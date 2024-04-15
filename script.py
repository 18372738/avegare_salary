import requests
from terminaltables import AsciiTable
from environs import Env




def predict_salary(salary_from=0, salary_to=0):
    if not salary_to:
        return salary_from*1.2
    elif not salary_from:
        return salary_to*0.8
    else:
        return (salary_from + salary_to)/2


def predict_rub_salary_hh(vacancy):
    if not vacancy['salary']:
        return None
    if not vacancy['salary']['currency'] == 'RUR':
        return None
    if not vacancy['salary']['from'] and not vacancy['salary']['to']:
        return None
    return predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])


def predict_rub_salary_sj(vacancy):
    if not vacancy['payment_from'] and not vacancy['payment_to']:
        return None
    if not vacancy['currency'] == 'rub':
        return None
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_vacancy_statistics_hh(programming_languages):
    url = 'https://api.hh.ru/vacancies'
    per_page = 100
    moscow_id = 1
    vacancies_by_language = {}
    for language in programming_languages:
        page = 0
        page_number = 1
        params = {
            'page': page,
            'per_page': per_page,
            'text': f'Программист {language}',
            'area': moscow_id,
        }
        all_vacancies = []
        while page < page_number:
            response = requests.get(url, params=params)
            response.raise_for_status()
            page_params = response.json()
            all_vacancies += page_params['items']
            page_number = page_params['pages']
            page += 1
        vacancies_by_language[language] = get_salary_statistics(all_vacancies, predict_rub_salary_hh)
    return vacancies_by_language


def get_vacancy_statistics_sj(programming_languages, token):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    vacancies_per_page = 100
    moscow_id = 4
    vacancies_by_language = {}
    for language in programming_languages:
        page = 0
        more = True
        headers = {
            'X-Api-App-Id': token,
        }
        params = {
            'count': vacancies_per_page,
            'page': page,
            'town': moscow_id,
            'keyword': f'Программист {language}',
        }
        all_vacancies = []
        while more:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            page_params = response.json()
            page += 1
            more = page_params['more']
            all_vacancies += page_params['objects']
        vacancies_by_language[language] = get_salary_statistics(all_vacancies, predict_rub_salary_sj)
    return vacancies_by_language


def get_avegare_salary(sum_avegare_salaries, vacancies_processed):
    avegare_salary = 0
    if vacancies_processed:
        avegare_salary = int(sum_avegare_salaries / vacancies_processed)
    return avegare_salary


def get_salary_statistics(all_vacancies, predict_rub_salary):
    vacancies_processed = 0
    sum_avegare_salaries = 0
    for vacancy in all_vacancies:
        vacancy_salary = predict_rub_salary(vacancy)
        if vacancy_salary:
            vacancies_processed += 1
            sum_avegare_salaries += vacancy_salary
    avegare_salary = get_avegare_salary(sum_avegare_salaries, vacancies_processed)
    number_of_vacancies = {
      'vacancies_found': len(all_vacancies),
      'vacancies_processed': vacancies_processed,
      'average_salary': avegare_salary,
    }
    return number_of_vacancies


def get_table_statistics(statistics, title):
    table_statistics = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ]
    for language, statistics_vacancies in statistics.items():
        table_statistics.append([
            language,
            statistics_vacancies['vacancies_found'],
            statistics_vacancies['vacancies_processed'],
            statistics_vacancies['average_salary'],
        ])
    output_table = AsciiTable(table_statistics, title)
    return output_table.table

if __name__ == '__main__':
    programming_languages = ['Python', 'Java', 'JavaScript', 'C++', 'C#', 'C', 'TypeScript', 'PHP', 'Go', '1C']
    env = Env()
    env.read_env()
    sj_token = env.str('TOKEN_SJ')
    title = 'SuperJob Moscow'
    statistics = get_vacancy_statistics_sj(programming_languages, sj_token)
    print(get_table_statistics(statistics, title))

    print('')

    title = 'HeadHunter Moscow'
    statistics = get_vacancy_statistics_hh(programming_languages)
    print(get_table_statistics(statistics, title))
