import numpy as np
import pandas as pd

plan = pd.DataFrame({
    "id_materia": list(range(1, 45)),

    "nombre": [
        # PRIMER AÑO
        "Introducción a la Filosofía y a las Cs. Sociales",
        "Introducción al Derecho",
        "Derecho Constitucional",
        "Historia Constitucional Argentina",
        "Derecho Privado Parte General",
        "Taller de Acceso a la Información Jurídica",

        # SEGUNDO AÑO
        "Derecho de las Obligaciones",
        "Historia del Derecho",
        "Economía Política",
        "Derechos Humanos",
        "Derechos Reales",
        "Derecho de Daños",
        "Finanzas y Derecho Financiero",

        # TERCER AÑO
        "Derecho Penal I",
        "Derecho de los Contratos",
        "Derecho Político",
        "Derecho Tributario",
        "Derecho Procesal I",
        "Derecho de la Empresa y el Mercado",
        "Derecho Agrario",
        "Práctica Profesional I",

        # CUARTO AÑO
        "Derecho de las Personas Jurídicas",
        "Derecho Procesal II",
        "Sociología General y del Derecho",
        "Derecho Penal II",
        "Derecho de las Familias",
        "Derecho del Trabajo y de la Seguridad Social",
        "Derecho Ambiental",
        "Derecho del Consumidor",

        # QUINTO AÑO
        "Derecho Administrativo I",
        "Derecho Procesal III",
        "Políticas Democráticas de Seguridad Ciudadana",
        "Títulos Valores",
        "Práctica Profesional II",
        "Derecho de la Insolvencia",
        "Derecho Administrativo II",
        "Derecho Internacional Público",
        "Derecho del Transporte y la Navegación",

        # SEXTO AÑO
        "Derecho Internacional Privado",
        "Filosofía del Derecho",
        "Derecho de la Integración",
        "Derecho de las Sucesiones",
        "Práctica Profesional III",
        "Idioma Extranjero",

    ],

    "correlativas": [
        # PRIMER AÑO
        [],       # 1
        [],       # 2
        [],       # 3
        [],       # 4
        [],       # 5
        [],       # 6

        # SEGUNDO AÑO
        [5],          # 7  Derecho Privado Parte General
        [1, 2],       # 8  Filosofía, Introducción al Derecho
        [1, 2],       # 9  Filosofía, Introducción al Derecho
        [4, 3, 8],    # 10 HCA, Constitucional, Historia del Derecho
        [2, 7],       # 11 Introducción al Derecho, Obligaciones
        [5],          # 12 Derecho Privado Parte General
        [3, 9],       # 13 Constitucional, Economía Política

        # TERCER AÑO
        [1, 2, 3, 10], # 14 Filosofía, Introducción, Constitucional, DDHH
        [3, 7],        # 15 Constitucional, Obligaciones
        [8, 9],        # 16 Historia del Derecho, Economía Política
        [13],          # 17 Finanzas y Derecho Financiero
        [14, 15],      # 18 Penal I, Contratos
        [2, 7],        # 19 Introducción al Derecho, Obligaciones
        [11, 15],      # 20 Derechos Reales, Contratos
        [3, 7, 6, 12], # 21 Constitucional, Obligaciones, TAIJ, Daños

        # CUARTO AÑO
        [1, 15],       # 22 Introducción a la Filosofía, Contratos
        [18],          # 23 Derecho Procesal I
        [16],          # 24 Derecho Político
        [14],          # 25 Derecho Penal I
        [11, 14, 15],  # 26 Reales, Penal I, Contratos
        [18],          # 27 Derecho Procesal I
        [18],          # 28 Derecho Procesal I
        [23],          # 29 Derecho Procesal II

        # QUINTO AÑO
        [13, 16, 22, 24, 25], # 30 Finanzas, Político, Personas Jurídicas, Sociología, Penal II
        [25, 18],             # 31 Penal II, Procesal I
        [24, 25],             # 32 Sociología, Penal II
        [18, 22],             # 33 Procesal I, Personas Jurídicas
        [23, 26],             # 34 Procesal II, Familias
        [22, 23, 27],         # 35 Personas Jurídicas, Procesal II, Trabajo y Seguridad Social
        [23, 30],             # 36 Procesal II, Administrativo I
        [23, 30],             # 37 Procesal II, Administrativo I
        [23, 27],             # 38 Procesal II, Trabajo y Seguridad Social

        # SEXTO AÑO
        [22, 26],             # 39 Personas Jurídicas, Familias
        [24],                 # 40 Sociología General y del Derecho
        [37],                 # 41 Derecho Internacional Público
        [26],                 # 42 Derecho de las Familias
        [23, 27, 29],         # 43 Procesal II, Trabajo, Consumidor
        [],                   # 44 Sin correlativas
    ],

    "año": [
        1, 1, 1, 1, 1, 1,
        2, 2, 2, 2, 2, 2, 2,
        3, 3, 3, 3, 3, 3, 3, 3,
        4, 4, 4, 4, 4, 4, 4, 4,
        5, 5, 5, 5, 5, 5, 5, 5, 5,
        6, 6, 6, 6, 6, 6,
    ]
})