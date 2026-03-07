from setuptools import setup

setup(
    name='wit-vcs',
    version='0.1.0',
    py_modules=['wit_cli', 'wit_core', 'utils'],
    install_requires=[
        'click',
    ],
    entry_points={
        'console_scripts': [
            'wit = wit_cli:cli',
        ],
    },
)