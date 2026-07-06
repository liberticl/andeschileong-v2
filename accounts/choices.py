# -*- encoding: utf-8 -*-
# accounts/choices.py

ORGANIZATION_TYPES = (
    ('ong', 'ONG'),
    ('empresa', 'Empresa'),
    ('municipalidad', 'Municipalidad'),
    ('gobierno', 'Gobierno'),
    ('universidad', 'Universidad'),
    ('asociacion', 'Asociación'),
    ('cooperativa', 'Cooperativa'),
    ('otro', 'Otro'),
)

ACCESS_SECTIONS = (
    ('ciudadespendientes', 'Ciudades Pendientes'),
    # ('intranet', 'Intranet CMS'),
)

REQUEST_STATUS = (
    ('pending', 'Pendiente'),
    ('approved', 'Aprobada'),
    ('rejected', 'Rechazada'),
)
