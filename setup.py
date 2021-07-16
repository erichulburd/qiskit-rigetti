# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme = ""

setup(
    long_description=readme,
    name="qiskit-rigetti-provider",
    version="0.2.0",
    description="Provider for running Qiskit circuits on Rigetti QPUs and simulators.",
    python_requires="==3.*,>=3.7.0",
    author="Rigetti Computing",
    packages=["qiskit_rigetti_provider", "qiskit_rigetti_provider.gates", "qiskit_rigetti_provider.hooks"],
    package_dir={"": "."},
    package_data={"qiskit_rigetti_provider": ["*.typed"]},
    install_requires=[
        'importlib-metadata; python_version < "3.8"',
        "numpy==1.*,>=1.20.1",
        "pyquil==3.*,>=3.0.0.rc21",
        "qiskit==0.*,>=0.27.0",
    ],
    extras_require={
        "dev": [
            "black==20.*,>=20.8.0.b1",
            "flake8==3.*,>=3.8.1",
            "mypy==0.*,>=0.800.0",
            "pytest==6.*,>=6.2.2",
            "pytest-cov==2.*,>=2.11.1",
            "pytest-httpx==0.*,>=0.9.0",
            "pytest-mock==3.*,>=3.6.1",
        ]
    },
)
