from setuptools import setup, find_packages

setup(
    name="evalguard",
    version="0.1.0",
    description="CI/CD Quality Gate & Automated Red-Teaming for GenAI & LLM Applications",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "evalguard=evalguard.cli:main",
        ],
    },
    python_requires=">=3.8",
)
