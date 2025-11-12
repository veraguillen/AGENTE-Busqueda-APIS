from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="agente_busqueda",
    version="0.1.0",
    packages=find_packages(include=['agents', 'app', 'services', 'utils']),
    install_requires=requirements,
    include_package_data=True,
    python_requires='>=3.10',
    
    # Metadatos
    author="Tu Nombre",
    author_email="tu@email.com",
    description="Agente de búsqueda para productos y vendedores",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/tu_usuario/agente-busqueda",
    
    # Clasificadores
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    
    # Puntos de entrada para scripts de consola
    entry_points={
        'console_scripts': [
            'agente-busqueda=app.main:main',
        ],
    },
    
    # Incluir archivos de datos no-Python
    package_data={
        '': ['*.json', '*.yaml', '*.yml'],
    },
)
