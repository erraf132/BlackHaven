"""
BlackHaven Framework
Copyright (c) 2026 erraf132 and Vyrn.exe Official
All rights reserved.
"""



from setuptools import find_packages, setup

setup(
    name="blackhaven",
    version="1.0.0",
    description="BlackHaven - OSINT & Security Auditing Toolkit",
    author="",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "colorama",
        "rich",
        "prompt_toolkit",
        "bcrypt",
        "argon2-cffi",
    ],
    entry_points={
        "console_scripts": [
            "blackhaven=blackhaven.main:main",
        ]
    },
    python_requires=">=3.9",
)
