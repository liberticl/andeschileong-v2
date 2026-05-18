# -*- encoding: utf-8 -*-
# ciudadespendientes/choices.py

ZONE_TYPES = (
    ('País', 'País'),
    ('Comuna', 'Comuna'),
    ('Zona Regional', 'Zona Regional'),
    ('Particular', 'Particular')
)

COUNTRIES = (
    ('Chile', 'Chile'),
    ('Argentina', 'Argentina')
)

MONTHS = (
    ('01', 'Enero'),
    ('02', 'Febrero'),
    ('03', 'Marzo'),
    ('04', 'Abril'),
    ('05', 'Mayo'),
    ('06', 'Junio'),
    ('07', 'Julio'),
    ('08', 'Agosto'),
    ('09', 'Septiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre'),
    ('Todo el año', 'Todo el año'),
)

YEARS = (
    (2019, 2019),
    (2020, 2020),
    (2021, 2021),
    (2022, 2022),
    (2023, 2023),
    (2024, 2024),
    (2025, 2025),
)

REGIONS = (
    # Chile
    ('Arica y Parinacota', 'Arica y Parinacota'),
    ('Tarapacá', 'Tarapacá'),
    ('Antofagasta', 'Antofagasta'),
    ('Atacama', 'Atacama'),
    ('Coquimbo', 'Coquimbo'),
    ('Valparaíso', 'Valparaíso'),
    ('Región Metropolitana', 'Región Metropolitana'),
    ('O Higgins', 'O Higgins'),
    ('Maule', 'Maule'),
    ('Ñuble', 'Ñuble'),
    ('Biobío', 'Biobío'),
    ('La Araucanía', 'La Araucanía'),
    ('Los Ríos', 'Los Ríos'),
    ('Los Lagos', 'Los Lagos'),
    ('Aysén', 'Aysén'),
    ('Magallanes', 'Magallanes'),
    # Argentina
    ('Buenos Aires', 'Buenos Aires'),
    ('Tucumán', 'Tucumán'),
    ('Santa Fe', 'Santa Fe'),
)