__version__ = '1.0.0'

import random


def titulo_de_servicio_generator():
    return random.choice([
        'Servicios Profesionales',
        'Soporte',
        'Consultoría',
        'Mantenimiento de Solución',
        'Asesoramiento profesional',
        'Reparacion de sistema',
        'Honorarios',
        'Diseño de solucion',
        'Servicios de Optimizacion',
    ])
