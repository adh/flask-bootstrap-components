from setuptools import setup, find_packages, Extension
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="Flask-Bootstrap-Components",
    version="0.1",
    author = "Ales Hakl",
    author_email = "ales@hakl.net",
    description = ("Collection of HTML generation helpers for Flask with Bootstrap 4"),
    long_description=read('README.rst'),
    url="https://github.com/adh/flask-bootstrap-components",
    
    license="MIT",
    keywords="flask bootstrap",
    install_requires=[
        'Flask>=1.0',
    ],

    packages=[
        "flask_bootstrap_components",
    ],
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',

        "Framework :: Flask",
        "License :: OSI Approved :: MIT License",

        'Intended Audience :: Developers',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],    
)
