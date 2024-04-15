from setuptools import setup

APP = ['run.py']
OPTIONS = {'includes': ['colorclass', 'terminaltables']}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)