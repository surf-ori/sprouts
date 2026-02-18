# Sprouts

A light-weight data lakehouse for Open research information based on [DuckLake](https://ducklake.select).


## Prerequisites

You need to have the package manager [uv](https://docs.astral.sh/uv/getting-started/installation/) installed. Then you can clone the repo and set up the required dependencies:

```shell
git clone https://github.com/surf-ori/sprouts.git
cd sprouts
uv sync
```

## Usage

Either you use [marimo](https://marimo.io) to run the build pipeline in an interactive notebook environment:

```shell
uv run marimo edit ingest-pipeline.py
```

Or you simply run the pipeline as a script:

```shell
uv run ingest-pipeline.py -dataset openapc
```

Based on your config.json your data lakehouse will be setup in the `build` directory (default) or whereever else you wish. You can supply an S3 URL as data path (for example `s3://my-bucket/data`) as long as you also provide the required key and secret as well (only works with the SURF object store at the moment).