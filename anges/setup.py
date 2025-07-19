from setuptools import setup, find_packages
import os

# Read the contents of README file from parent directory
this_directory = os.path.abspath(os.path.dirname(__file__))
parent_directory = os.path.dirname(this_directory)
readme_path = os.path.join(parent_directory, 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "Anges - Comprehensive Agent Orchestration Framework for AI-Powered Automation"

setup(
    name="anges",
    version="0.1.0",
    description="Anges - Comprehensive Agent Orchestration Framework for AI-Powered Automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Anges Team",
    author_email="me@anges.ai",
    url="https://github.com/anges-ai/anges",
    project_urls={
        "Documentation": "https://github.com/anges-ai/anges/tree/main/docs",
        "Examples": "https://github.com/anges-ai/anges/tree/main/examples",
        "Source": "https://github.com/anges-ai/anges",
        "Bug Tracker": "https://github.com/anges-ai/anges/issues",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'anges': [
            'templates/**/*',
            'static/**/*',
        ],
    },
    install_requires=[
        "flask>=2.0.0",
        "flask-cors>=3.0.0",
        "flask-login>=0.6.0",
        "openai>=1.0.0",
        "vertexai>=1.0.0",
        "anthropic>=0.3.0",
        "google-generativeai>=0.3.0",
        "python-dotenv>=0.19.0",
        "requests>=2.25.0",
        "pandas>=1.3.0",
    ],
    keywords=[
        "ai", "agent", "orchestration", "automation", "framework",
        "llm", "openai", "anthropic", "google", "vertexai",
        "workflow", "event-driven", "multi-agent", "assistant",
        "custom-actions", "plugin-system", "ai-automation"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: System :: Distributed Computing",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Framework :: Flask",
    ],
    python_requires=">=3.8",
    zip_safe=False,
)
