from setuptools import find_packages, setup

setup(
    name = 'TracRecaptchaRegister',
    version = '0.3.1',
    author = 'Alejandro J. Cura, Pedro Algarvio',
    author_email = 'alecu@vortech.com.ar, ufs@ufsoft.org',
    url = 'http://trac-hacks.org/wiki/RecaptchaRegisterPlugin',
    description = 'Adds a recaptcha while registering, depends on AccountManagerPlugin',
    license = 'GPL',
    packages = find_packages(exclude=['*.tests*']),
    install_requires = [
        'trac>=0.11',
        #'AccountManagerPlugin==0.2.1',
        'recaptcha_client>=1.0.2',
    ],
    entry_points = {
        'trac.plugins': [
            'recaptcharegister = recaptcharegister.web_ui'
        ]
    },
)
