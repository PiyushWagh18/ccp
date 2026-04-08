"""
Setup configuration for piyush-cloudlib package.
A Python library providing OOP abstractions over AWS cloud services.
"""
from setuptools import setup, find_packages

setup(
    name="piyush-cloudlib",
    version="1.0.0",
    description="A Python library for managing AWS cloud services with OOP abstractions",
    long_description=open("readme.txt").read(),
    author="Piyush Wagh",
    author_email="Waghpiyush436@gmail.com",
    url="https://github.com/PiyushWagh18/ccp",
    packages=find_packages(include=["cloudlib", "cloudlib.*"]),
    install_requires=[
        "boto3>=1.26.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
