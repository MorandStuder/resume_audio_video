from setuptools import setup, find_packages

setup(
    name="audio_processor",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pydub",
        "openai",
        "whisper",
        "pathlib",
    ],
    author="Votre Nom",
    author_email="votre.email@example.com",
    description="Système de traitement audio et transcription",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/votre-username/IA",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 