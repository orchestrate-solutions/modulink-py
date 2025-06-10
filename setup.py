from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define requirements inline to avoid dependency on requirements.txt during build
requirements = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0", 
    "apscheduler>=3.10.0",
    "click>=8.1.0",
    "pydantic>=2.5.0",
    "typing-extensions>=4.8.0",
]

# Try to read from requirements.txt if available (for development)
requirements_file = "requirements.txt"
if os.path.exists(requirements_file):
    try:
        with open(requirements_file, "r", encoding="utf-8") as fh:
            file_requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
            # Use file requirements if they exist and are not empty
            if file_requirements:
                requirements = file_requirements
    except Exception:
        # Fall back to inline requirements if file reading fails
        pass

setup(
    name="modulink-py",
    version="2.0.1",
    author="Orchestrate LLC",
    author_email="support@orchestrate.dev",
    description="A Python library for building modular applications with unified triggers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JoshuaWink/modulink-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "flake8>=6.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
    },
)
