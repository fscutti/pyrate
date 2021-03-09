#!/usr/bin/env python3

# An example basic setup script for installing pyrate as a package

from setuptools import setup


with open("requirements.txt", "r") as f:
	required_packages = [line.strip() for line in  f.readlines()]

	setup(name="pyrate",
	      version="1.0",
	      description="A dynamic and flexible data processing framework for analysis in the SABRE experiment, written in python",
	      url="https://bitbucket.org/darkmatteraustralia/pyrate",
	      author="Federico Scutti",
	      author_email="fscutti@unimelb.edu.au",
	      license="GPL2",
	      packages=["pyrate"],
	      install_requires=required_packages,
	      zip_safe=False)
