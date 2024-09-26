#!/usr/bin/env python

from setuptools import setup, find_namespace_packages

setup(
    name="proton-vpn-killswitch-network-manager",
    version="0.6.1",
    description="Proton Technologies VPN connector for linux",
    author="Proton AG",
    author_email="opensource@proton.me",
    url="https://github.com/ProtonVPN/python-proton-vpn-network-manager",
    packages=find_namespace_packages(include=['proton.vpn.killswitch.backend.linux.networkmanager']),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=["proton-vpn-api-core", "pygobject", "packaging"],
    extras_require={
        "development": ["wheel", "pytest", "pytest-cov", "pytest-asyncio", "flake8", "pylint"]
    },
    license="GPLv3",
    platforms="OS Independent",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Security",
    ]
)
