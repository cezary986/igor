import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="igor_server",
    version="0.1.2",
    author="Cezary Maszczyk",
    author_email="cezary.maszczyk@gmail.com",
    description="Simple solution fo integrating python and modern web-based desktop apps e.g build using Elector",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cezary986/igor",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
