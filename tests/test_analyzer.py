from setuptools import setup, find_packages

setup(
    name="codeguard-wit",
    version="1.0.0",
    description="Wit VCS with integrated CodeGuard code-quality analysis.",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1",
        "requests>=2.32",
        "fastapi>=0.111",
        "uvicorn[standard]>=0.30",
        "python-multipart>=0.0.9",
        "pydantic>=2.7",
        "matplotlib>=3.9",
    ],
    entry_points={
        "console_scripts": [
            "wit = wit.cli:cli",
        ],
    },
)
