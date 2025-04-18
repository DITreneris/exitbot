from setuptools import setup, find_packages

# Read requirements
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="exitbot",
    version="0.1.0",
    description="AI-powered exit interview assistant",
    author="ExitBot Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 