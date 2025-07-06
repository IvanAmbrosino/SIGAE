#!/usr/bin/python3
import pathlib
from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent

VERSION = '1.2.2'
PACKAGE_NAME = 'make-vfi-sched'
AUTHOR = 'Emiliano A. Baum'
AUTHOR_EMAIL = 'ebaum@conae.gov.ar'
URL = 'http://10.0.100.183/cgss/engineering/make-vfi.git'
LICENSE = 'MIT'
DESCRIPTION = 'Library for generete VFI Schedule' 
LONG_DESCRIPTION = (HERE / "README.md").read_text(encoding='utf-8')
LONG_DESC_TYPE = "text/markdown"

INSTALL_REQUIRES = []
classifiers=[
        'Development Status :: 2 - Develop',
        'Intended Audience :: CGSS/Operations',
        'Operating System :: POSIX :: Linux',  
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESC_TYPE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    install_requires=INSTALL_REQUIRES,
    license=LICENSE,
    packages=find_packages(),
    include_package_data=True
)
