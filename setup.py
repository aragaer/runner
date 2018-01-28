#!/usr/bin/env python3

from setuptools import setup

setup(
    name="yet-another-runner",
    version="0.1.1",
    author="Ilya Konovalov",
    author_email="aragaer@gmail.com",
    description="Simple process runner",
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
