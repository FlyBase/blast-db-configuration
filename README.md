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

The GitHub action workflows described below do the following:

- Create or update a BLAST DB configuration file
- Create a PR with the resulting changes
- Pull the changes from FlyBase into the Alliance BLAST DB repo
- Create a PR for the Alliance to review and act on


### Procedure

#### Generate FlyBase Configuration

1. Visit the [Actions tab](https://github.com/FlyBase/blast-db-configuration/actions) for the repo.
2. Click on the [Generate FlyBase BLAST Configuration](https://github.com/FlyBase/blast-db-configuration/actions/workflows/generate-blast-conf.yml) workflow.
3. Click "Run workflow" and enter in the FlyBase release and Dmel annotation version number (e.g. FB2024_02 and r6.57).
4. After the workflow has run, there will be a pull request with the resulting configuration file. Review
   the pull request changes and merge if all looks good.

#### Copy Configuration to the Alliance

1. Visit the [Actions tab](https://github.com/alliance-genome/agr_blast_service_configuration/actions) for the Alliance BLAST configurations.
2. Click on the [Update FlyBase Configuration](https://github.com/alliance-genome/agr_blast_service_configuration/actions/workflows/flybase.yml) workflow.
3. Click "Run workflow" and enter in the FlyBase release (e.g. FB2024_04). This is only used for the pull request text.
4. Review the pull request changes and follow the Alliance procedures.


