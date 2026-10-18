"""
Datos iniciales de los catálogos de Nueva Salud JS.

Sin estos datos, una base de datos nueva no tiene qué ofrecerle al médico en los selectores de
diagnósticos y medicamentos de la consulta (RF-09), y el SRS exige que sean listados
estandarizados y no texto libre.

Los diagnósticos son un subconjunto de la CIE-10 con las causas de consulta más frecuentes en
medicina general. Los medicamentos son de uso común en consulta externa. Es una lista de partida:
el administrador puede ampliarla desde el panel de administración de Django mientras no estén
implementados los requisitos de gestión de enfermedades y medicamentos (RF-25 a RF-34).
"""

# (código CIE-10, nombre)
ENFERMEDADES = [
    # Enfermedades infecciosas y parasitarias
    ('A08.4', 'Infección intestinal viral, sin otra especificación'),
    ('A09', 'Diarrea y gastroenteritis de presunto origen infeccioso'),
    ('A90', 'Dengue clásico'),
    ('B34.9', 'Infección viral, no especificada'),
    ('B35.3', 'Tiña de los pies'),
    ('B37.9', 'Candidiasis, no especificada'),
    ('B82.9', 'Parasitosis intestinal, sin otra especificación'),
    ('B86', 'Escabiosis'),
    ('U07.1', 'COVID-19, virus identificado'),
    # Sangre, endocrinas y metabólicas
    ('D50.9', 'Anemia por deficiencia de hierro, sin otra especificación'),
    ('E03.9', 'Hipotiroidismo, no especificado'),
    ('E11.9', 'Diabetes mellitus tipo 2, sin mención de complicación'),
    ('E55.9', 'Deficiencia de vitamina D, no especificada'),
    ('E66.9', 'Obesidad, no especificada'),
    ('E78.5', 'Hiperlipidemia, no especificada'),
    # Trastornos mentales y del sistema nervioso
    ('F32.9', 'Episodio depresivo, no especificado'),
    ('F41.9', 'Trastorno de ansiedad, no especificado'),
    ('G43.9', 'Migraña, no especificada'),
    ('G44.2', 'Cefalea debida a tensión'),
    ('G47.0', 'Insomnio'),
    # Ojo y oído
    ('H10.9', 'Conjuntivitis, no especificada'),
    ('H60.9', 'Otitis externa, no especificada'),
    ('H66.9', 'Otitis media, no especificada'),
    # Sistema circulatorio
    ('I10', 'Hipertensión esencial (primaria)'),
    ('I83.9', 'Várices de los miembros inferiores sin úlcera ni inflamación'),
    # Sistema respiratorio
    ('J00', 'Rinofaringitis aguda (resfriado común)'),
    ('J01.9', 'Sinusitis aguda, no especificada'),
    ('J02.9', 'Faringitis aguda, no especificada'),
    ('J03.9', 'Amigdalitis aguda, no especificada'),
    ('J04.0', 'Laringitis aguda'),
    ('J06.9', 'Infección aguda de las vías respiratorias superiores, no especificada'),
    ('J11.1', 'Influenza con otras manifestaciones respiratorias, virus no identificado'),
    ('J18.9', 'Neumonía, no especificada'),
    ('J20.9', 'Bronquitis aguda, no especificada'),
    ('J30.4', 'Rinitis alérgica, no especificada'),
    ('J44.9', 'Enfermedad pulmonar obstructiva crónica, no especificada'),
    ('J45.9', 'Asma, no especificada'),
    # Sistema digestivo
    ('K02.9', 'Caries dental, no especificada'),
    ('K21.9', 'Enfermedad por reflujo gastroesofágico sin esofagitis'),
    ('K29.7', 'Gastritis, no especificada'),
    ('K30', 'Dispepsia'),
    ('K52.9', 'Gastroenteritis y colitis no infecciosas, sin otra especificación'),
    ('K58.9', 'Síndrome del colon irritable sin diarrea'),
    ('K59.0', 'Estreñimiento'),
    # Piel
    ('L02.9', 'Absceso cutáneo, forúnculo y carbunco, sitio no especificado'),
    ('L03.9', 'Celulitis, sin otra especificación'),
    ('L20.9', 'Dermatitis atópica, no especificada'),
    ('L30.9', 'Dermatitis, no especificada'),
    ('L50.9', 'Urticaria, no especificada'),
    ('L70.0', 'Acné vulgar'),
    # Sistema osteomuscular
    ('M10.9', 'Gota, no especificada'),
    ('M19.9', 'Artrosis, no especificada'),
    ('M25.5', 'Dolor en articulación'),
    ('M54.2', 'Cervicalgia'),
    ('M54.5', 'Lumbago no especificado'),
    ('M79.1', 'Mialgia'),
    # Sistema genitourinario
    ('N30.0', 'Cistitis aguda'),
    ('N39.0', 'Infección de vías urinarias, sitio no especificado'),
    ('N76.0', 'Vaginitis aguda'),
    ('N94.6', 'Dismenorrea, no especificada'),
    # Síntomas y signos
    ('R03.0', 'Lectura elevada de la presión sanguínea, sin diagnóstico de hipertensión'),
    ('R05', 'Tos'),
    ('R07.4', 'Dolor en el pecho, no especificado'),
    ('R10.4', 'Otros dolores abdominales y los no especificados'),
    ('R11', 'Náusea y vómito'),
    ('R19.7', 'Diarrea, no especificada'),
    ('R21', 'Erupción cutánea y otras erupciones cutáneas no específicas'),
    ('R42', 'Mareo y desvanecimiento'),
    ('R50.9', 'Fiebre, no especificada'),
    ('R51', 'Cefalea'),
    ('R53', 'Malestar y fatiga'),
    # Traumatismos y alergias
    ('S61.9', 'Herida de la muñeca y de la mano, parte no especificada'),
    ('S93.4', 'Esguince y torcedura del tobillo'),
    ('T14.9', 'Traumatismo, no especificado'),
    ('T78.4', 'Alergia, no especificada'),
    # Factores que influyen en el estado de salud
    ('Z00.0', 'Examen médico general'),
    ('Z00.1', 'Control de salud de rutina del niño'),
    ('Z30.0', 'Asesoramiento general sobre anticoncepción'),
    ('Z34.9', 'Supervisión de embarazo normal, no especificada'),
    ('Z76.0', 'Emisión de prescripción repetida'),
]

# (nombre, presentación) — el nombre es único en el catálogo
MEDICAMENTOS = [
    # Analgésicos y antiinflamatorios
    ('Acetaminofén', 'Tableta 500 mg'),
    ('Acetaminofén jarabe', 'Jarabe 150 mg/5 mL'),
    ('Ibuprofeno', 'Tableta 400 mg'),
    ('Ibuprofeno suspensión', 'Suspensión oral 100 mg/5 mL'),
    ('Naproxeno', 'Tableta 250 mg'),
    ('Diclofenaco', 'Tableta 50 mg'),
    ('Diclofenaco gel', 'Gel tópico 1 %'),
    ('Dipirona', 'Tableta 500 mg'),
    ('Ácido acetilsalicílico', 'Tableta 100 mg'),
    # Antibióticos y antiparasitarios
    ('Amoxicilina', 'Cápsula 500 mg'),
    ('Amoxicilina con ácido clavulánico', 'Tableta 875 mg/125 mg'),
    ('Azitromicina', 'Tableta 500 mg'),
    ('Cefalexina', 'Cápsula 500 mg'),
    ('Ciprofloxacino', 'Tableta 500 mg'),
    ('Trimetoprima con sulfametoxazol', 'Tableta 160 mg/800 mg'),
    ('Metronidazol', 'Tableta 500 mg'),
    ('Nitrofurantoína', 'Cápsula 100 mg'),
    ('Penicilina benzatínica', 'Polvo para inyección 1.200.000 UI'),
    ('Albendazol', 'Tableta 400 mg'),
    ('Ivermectina', 'Tableta 6 mg'),
    # Antimicóticos y dermatológicos
    ('Fluconazol', 'Cápsula 150 mg'),
    ('Clotrimazol crema', 'Crema tópica 1 %'),
    ('Hidrocortisona crema', 'Crema tópica 1 %'),
    ('Mupirocina ungüento', 'Ungüento tópico 2 %'),
    # Antialérgicos y respiratorios
    ('Loratadina', 'Tableta 10 mg'),
    ('Cetirizina', 'Tableta 10 mg'),
    ('Clorfeniramina', 'Tableta 4 mg'),
    ('Salbutamol inhalador', 'Inhalador 100 mcg/dosis'),
    ('Ambroxol jarabe', 'Jarabe 15 mg/5 mL'),
    ('Dextrometorfano jarabe', 'Jarabe 15 mg/5 mL'),
    ('Prednisona', 'Tableta 20 mg'),
    ('Dexametasona', 'Solución inyectable 4 mg/mL'),
    # Gastrointestinales
    ('Omeprazol', 'Cápsula 20 mg'),
    ('Hioscina butilbromuro', 'Tableta 10 mg'),
    ('Loperamida', 'Tableta 2 mg'),
    ('Sales de rehidratación oral', 'Sobre para solución oral'),
    ('Metoclopramida', 'Tableta 10 mg'),
    ('Hidróxido de aluminio y magnesio', 'Suspensión oral'),
    # Cardiovasculares y metabólicos
    ('Amlodipino', 'Tableta 5 mg'),
    ('Losartán', 'Tableta 50 mg'),
    ('Enalapril', 'Tableta 20 mg'),
    ('Hidroclorotiazida', 'Tableta 25 mg'),
    ('Atorvastatina', 'Tableta 20 mg'),
    ('Metformina', 'Tableta 850 mg'),
    ('Glibenclamida', 'Tableta 5 mg'),
    ('Levotiroxina', 'Tableta 50 mcg'),
    # Suplementos
    ('Ácido fólico', 'Tableta 1 mg'),
    ('Sulfato ferroso', 'Tableta 300 mg'),
    ('Colecalciferol (vitamina D)', 'Cápsula 1.000 UI'),
]
