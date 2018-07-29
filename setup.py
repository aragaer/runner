#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="yet-another-runner",
    version="0.1.1.1",
    author="Ilya Konovalov",
    author_email="aragaer@gmail.com",
    description="Simple process runner",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="run command shell socket",
    url="https://github.com/aragaer/runner",
    packages=["runner"],
    classifiers=[
        "Topic :: Utilities",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ]
)
