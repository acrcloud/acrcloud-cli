"""
ACRCloud CLI Setup
"""

from setuptools import setup, find_packages

setup(
    name='acrcloud-cli',
    version='1.0.0',
    description='A command-line interface for ACRCloud Console API',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'click>=8.0.0',
        'requests>=2.25.0',
    ],
    entry_points={
        'console_scripts': [
            'acrcloud=acrcloud_cli.main:cli',
        ],
    },
)
