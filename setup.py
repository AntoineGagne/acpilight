#! /usr/bin/env python

import os

from setuptools import find_packages, setup

DOCS_REQUIRE = ['Sphinx>=1.6.6']

LINTERS_REQUIRE = [
    'flake8>=3.5.0',
    'pylint>=1.8.1'
]

TESTS_REQUIRE = [
    'pytest-runner>=3.0',
    'pytest>=3.3.2',
    'coverage>=4.4.2'
]


def get_long_description(file_name):
    """Gets the long description from the specified file's name.

    :param file_name: The file's name
    :type file_name: str
    :return: The content of the file
    :rtype: str
    """
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


if __name__ == '__main__':
    setup(
        name='acpilight',
        version='1.0.1',
        description='A backward compatible `xbacklight` replacement.',
        author='Yuri D\'Elia',
        author_email='wavexx@thregr.org',
        url='https://github.com/wavexx/acpilight',
        license='GPL 3.0 License',
        zip_safe=False,
        platforms='linux',
        python_requires='>=2.7',
        packages=find_packages(
            exclude=[
                'tests'
            ]
        ),
        entry_points={
            'console_scripts': [
                'xbacklight = acpilight.acpilight:main'
            ]
        },
        data_files=[],
        include_package_data=True,
        long_description=get_long_description('README.rst'),
        test_suite='tests',
        scripts=[],
        install_requires=[
        ],
        extras_require={
            'dev': DOCS_REQUIRE + LINTERS_REQUIRE + TESTS_REQUIRE,
            'docs': DOCS_REQUIRE,
            'tests': TESTS_REQUIRE,
            'linters': LINTERS_REQUIRE
        },
        classifiers=[
            'Development Status :: 3 - Pre-Alpha',
            'Operating System :: Linux',
            'Programming Language :: Python :: 2'
        ],
        keywords=[
            'linux',
        ],
    )
