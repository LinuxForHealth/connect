import setuptools
from importlib.machinery import SourceFileLoader

# load README for packaging description
with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

# parse the version without loading the entire app
version = SourceFileLoader('version', 'pyconnect/version.py').load_module()

setuptools.setup(
    name='LinuxForHealth pyConnect',
    version=version.version,
    description='LinuxForHealth Connectors for Inbound Data Processing',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://linuxforhealth.github.io/docs',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.8',
        'Intended Audience :: Healthcare Industry'
    ],
    keywords='healthit linuxforhealth x12 fhir hl7 linux',
    project_urls={
        'Issues': 'https://github.com/LinuxForHealth/pyconnect/issues',
        'Source': 'https://github.com/LinuxForHealth/pyconnect'
    },
    packages=setuptools.find_packages(),
    install_requires=[
        'fastapi==0.63.0',
        'uvicorn==0.13.3',
        'requests==2.25.1',
        'pyaml==20.4.0',
        'xworkflows==1.0.4',
        'fhir.resources==6.1.0'
    ],
    extras_require={
        'test': ['pytest==6.1.2'],
        'dev': ['autopep8==1.5.5', 'pylint==2.6.0']
    },
    python_requires='>=3.8'
)
