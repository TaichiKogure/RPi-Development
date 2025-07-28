from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="battery-sim-analyzer",
    version="1.0.0",
    author="JetBrains",
    author_email="info@jetbrains.com",
    description="A comprehensive tool for simulating and analyzing lithium-ion battery degradation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jetbrains/battery-sim-analyzer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "battery-sim-analyzer=main_app:main",
        ],
    },
)