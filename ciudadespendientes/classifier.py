import numpy as np


# https://sni.gob.cl/storage/docs/Ciclo-Rutas-2013.pdf (pag 16)
def sectra(travels, years, factor):
    travels = travels / factor
    by_day = travels / (365 * len(years))
    if (by_day > 250):
        return ['red', {"opacity": 0.9, "weight": 4}]
    elif (by_day > 150):
        return ['orange', {"opacity": 0.8, "weight": 3}]
    else:
        return ['green', {"opacity": 0.3, "weight": 3}]


def get_statistics(numlist, years=None):
    data = np.array(numlist)
    mean = np.mean(data)
    std = np.std(data)
    if (isinstance(years, list)):
        d = len(years)
        return (round(mean/d), round(std/d))
    return (mean, std)


def general(travels, years, statistics, factor):
    travels = travels / factor
    by_year = travels / len(years)
    mean, std = statistics
    if (by_year > mean + std):
        return ['red', {"opacity": 0.9, "weight": 4}]
    elif (by_year > mean):
        return ['orange', {"opacity": 0.8, "weight": 3}]
    else:
        return ['green', {"opacity": 0.3, "weight": 3}]


def classify(travels, years: list, method: str, factor=1,
             statistics=None, anual=False):
    if (method not in ['sectra', 'general']):
        return -1

    # If not anual, then len of years will always be 1
    years = years if anual else [years[0]]

    if (method == 'sectra'):
        return sectra(travels, years, factor)

    elif (method == 'general'):
        if (not isinstance(statistics, tuple)):
            print('No se indican estadísticas. Se clasificará según SECTRA.')
            return sectra(travels, years, factor)

        return general(travels, years, statistics, factor)

    else:
        return -1
