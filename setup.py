#!/usr/bin/env python
import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="backend-service",
    version="1.0",
    description="Features Backend Service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/findfeatures/backend-service",
    packages=setuptools.find_packages(exclude=["tests", "alembic", "build", "dist"]),
    zip_safe=True,
    install_requires=[
        "nameko==3.0.0-rc6",
        "nameko-sentry==1.0.0",
        "ddtrace==0.27.1",
        "nameko-sqlalchemy==1.5.0",
        "psycopg2-binary==2.8.3",
        "regex==2019.6.8",
        "udatetime==0.0.16",
        "marshmallow==3.0.1",
        "python-dateutil==2.8.0",
        "SQLAlchemy-Utils==0.36.0",
        "passlib==1.7.2",
        "marshmallow==3.0.1",
        "alembic==1.2.1",
        "PyJWT==1.7.1",
        "sendgrid==6.1.1",
        "walrus==0.8.0",
        "munch==2.5.0",
        "stripe==2.42.0"
    ],
    extras_require={
        "dev": [
            "pre-commit==1.16.1",
            "isort==4.3.21",
            "black==19.3b0",
            "pylint==2.3.1",
            "pytest==4.5.0",
            "allure-pytest==2.6.3",
            "coverage==4.5.3",
            "pytest-cov==2.7.1",
            "pytest-pgsql==1.1.1",
            "pdbpp==0.10.2",
            "responses==0.10.6",
        ]
    },
)
