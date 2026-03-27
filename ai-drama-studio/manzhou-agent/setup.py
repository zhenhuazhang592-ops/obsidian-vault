"""setup.py - 漫舟导演Agent安装配置"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="manzhou-agent",
    version="9.0.0",
    description="漫舟导演Agent - AI漫剧分镜脚本生成工具（到分镜截止，AI生成由人工执行）",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Manzhou Studio",
    author_email="manzhou@studio.com",
    url="https://github.com/manzhou/manzhou-agent",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
        ],
    },
    entry_points={
        "console_scripts": [
            "manzhou=manzhou.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
)
