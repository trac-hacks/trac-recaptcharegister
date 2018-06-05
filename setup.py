#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from setuptools import find_packages, setup

setup(
    name='TracRecaptchaRegister',
    version='0.3.4',
    author='Alejandro J. Cura, Pedro Algarvio',
    author_email='alecu@vortech.com.ar, ufs@ufsoft.org',
    url='https://trac-hacks.org/wiki/RecaptchaRegisterPlugin',
    description='Adds a registration recaptcha, depends on AccountManagerPlugin',
    license='GPL',
    packages=find_packages(exclude=['*.tests*']),
    install_requires=[
        'Trac',
        # 'AccountManagerPlugin==0.2.1',
        'recaptcha-client>=2.0.1',
    ],
    dependency_links=[
        'git+https://github.com/redhat-infosec/python-recaptcha.git#egg=recaptcha-client-2.0.1'
    ],
    entry_points={
        'trac.plugins': [
            'recaptcharegister = recaptcharegister.web_ui'
        ]
    },
)
