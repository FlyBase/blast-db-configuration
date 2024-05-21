# blast-db-configuration

## Description

Code for generating the Alliance BLAST DB configuration file for FlyBase

## Requirements

* [Poetry](https://python-poetry.org/)
* [pre-commit](https://pre-commit.com/)

## Getting Started

```shell
git clone git@github.com:FlyBase/blast-db-configuration.git
cd blast-db-configuration
poetry install
pre-commit install
```

## Generating FlyBase BLAST Configuration

The following commands will generate a BLAST database configuration for all organisms
listed in the organisms.json file.


```shell
poetry run generate --release <FB_RELEASE> --dmel-annot-release <DMEL_ANNOT_VERSION>
```
e.g
```shell
poetry run generate --release FB2024_02 --dmel-annot-release r6.57
```

See `poetry run generate --help` for a full list of supported options.


## GitHub Action

The [Generate FlyBase BLAST Configuration](https://github.com/FlyBase/blast-db-configuration/actions/workflows/generate-blast-conf.yml) GitHub Action
can be used to generate the configuration. This workflow will generate a new configuration for the specified FlyBase
release and Dmel annotation and create a PR with the updated configuration file for review.
