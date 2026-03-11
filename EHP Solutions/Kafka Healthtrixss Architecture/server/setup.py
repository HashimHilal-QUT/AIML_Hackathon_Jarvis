from setuptools import setup, find_packages

setup(
    name="healthtrixss",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-cors',
        'kafka-python',
        'redis',
        'pandas'
    ]
)