import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tbsdq",
    version="0.0.1",
    author="Mike Sisk",
    author_email="Mike.Sisk@tbs-sct.gc.ca",
    description="A library for calculating specific data quality metrics on open data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/msisktbs/data",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)