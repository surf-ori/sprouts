# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "duckdb==1.4.4",
#     "marimo>=0.20.2",
#     "numpy==2.4.2",
#     "polars[pyarrow]==1.38.1",
#     "pydantic-ai==1.63.0",
#     "sqlglot==29.0.1",
# ]
# ///

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
async def _():
    import marimo as mo
    import micropip
    # Install the packages when running in WAS
    await micropip.install(["polars"])

    import requests
    import json
    import duckdb
    import polars as pl
    import altair as alt
    import numpy as np

    return duckdb, json, mo, pl, requests


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e5e5e5;
        margin-bottom: 1rem;
    ">
        <div>
            <h1 style="margin: 0;">
                Open Research Information | Datasets Overview
            </h1>
            <div style="color: #666; font-size: 0.9rem;">
                Overview of available and actively queryable ORI datasets.
            </div>
        </div>
        <img
            src="https://www.surf.nl/themes/surf/logo.svg"
            alt="SURF logo"
            style="height: 100px;"
        />
    </div>
    """)
    return


@app.cell
def _(datasets_count, mo, total_records, volume_bytes):
    datasets_stat = mo.stat(
        value=f"{datasets_count:,}",
        label="Datasets",
        caption="Number of datasets",
        direction="none"
    )

    total_records_stat = mo.stat(
        value=f"{total_records:,}",
        label="Total records",
        caption="Total number of records across all datasets",
        direction="none"
    )

    volume_bytes_stat = mo.stat(
        value=_format_gb(volume_bytes),
        label="Data volume",
        caption="Total data volume in GB",
        direction="none"
    )

    mo.hstack([datasets_stat, total_records_stat, volume_bytes_stat], justify="center", gap="2rem")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This dashboard is part of the [**PID to Portal project**](https://communities.surf.nl/en/open-research-information/article/from-pid-to-portal-strengthening-the-open-research-information) from SURF and UNL.

    Our goals is to create an overview of available and actively queryable Open Research Information Resources / Datasets, that the ORI community can start using freely.
    """)
    return


@app.cell
def _(mo):
    background = mo.md("""
    In our approach, we aim to avoid BigTech. We curate the queryable databases ourselves but welcome others to share their data catalogs. We utilize the DuckLake catalog from DuckDB and store the actual data as Parquet files on an S3-compatible object store. This separation of storage and compute helps us keep costs low.

    This catalog lists all the ORI data resoures, their tables and columns. also it holds information about the changes in time of all the data resources, like  deleted, updated and added records, and schema changes.

    This alows you to 'time-travel' in the data, and not only use the last state. For example detecting when an article flips from open access to closed access.

    **Compute:** You can query the datasets directly from your browser (no login required)! When you query the databases, a portion of the requested data is transferred over HTTPS to your local machine where the SQL operations are performed. Larger data requests result in longer transfer times, and the speed of your local machine affects the query completion time. The size of your machine is up to you.

    At SURF, we also provide ready-made [services](https://www.surf.nl/en/services) for SQL computation, such as a Marimo notebook in a virtual machine on SURF Research Cloud or a Superset dashboard on a Kubernetes cluster.

    Below, you will see the ORI data resources we currently curate. (This overview was inspired by the [ORION-DBS initiative](https://orion-dbs.community/).)

    We want to add the following datasets: OpenAIRE, OpenALEX, OpenAPC, ROR, Harvest metadata from CRISes, Harvest metdata from Repositories, Crossref, SURF Journal Catalogue, CWTS Leiden Ranking, ORCID, DOAJ, DOAB, OpenCitations, DataCite, PKP beacon.
    """)
    mo.sidebar(
        mo.accordion(
            {"Background": background},
            lazy=True,
        )
    )
    return


@app.cell
def _(json, requests):
    response = requests.get('https://raw.githubusercontent.com/surf-ori/sprouts/refs/heads/notebooks/config.json')
    config = json.loads(response.text)
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        -- UPDATE __ducklake_metadata_sprouts.ducklake_metadata
        -- SET value = 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-demo/data'
        -- WHERE key = 'data_path'
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        USE memory;
        DETACH sprouts;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ORI data catalog

    This URL gives you access to the ORI data catalog. Copy this URL to attach it as a ducklake to your own query engine.
    """)
    return


@app.cell
def _(mo):
    url = mo.ui.text_area(value='https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts/catalog.ducklake')
    # url = mo.ui.text_area(value='https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:boto3bucket/sprouts.ducklake')
    url
    return (url,)


@app.cell(disabled=True)
def _(url):
    url.value
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        USE memory;
        DETACH sprouts;
        """
    )
    return


@app.cell
def _(mo, url):
    _df = mo.sql(
        f"""
        ATTACH 'ducklake:{url.value}' as sprouts;
        USE sprouts;
        """
    )
    return


@app.cell
def _(mo):
    quick_statistics = mo.sql(
        f"""
        SELECT table_name, record_count, file_size_bytes
            FROM __ducklake_metadata_sprouts.ducklake_table_stats
            FULL JOIN __ducklake_metadata_sprouts.ducklake_table
        	USING (table_id)
        """,
        output=False
    )
    return (quick_statistics,)


@app.cell(hide_code=True)
def _():
    ## ORI data resources
    return


@app.cell
def _(mo):
    datasets = mo.sql(
        f"""
        FROM __ducklake_metadata_sprouts.ducklake_schema
        WHERE schema_name != 'main';
        """,
        output=False
    )
    return (datasets,)


@app.cell(hide_code=True)
def _():
    ## ORI tables
    return


@app.cell
def _(mo):
    tables = mo.sql(
        f"""
        SELECT *
        FROM __ducklake_metadata_sprouts.ducklake_table t
        JOIN __ducklake_metadata_sprouts.ducklake_table_stats s
        ON t.table_id = s.table_id
        JOIN __ducklake_metadata_sprouts.ducklake_tag c
        ON t.table_id = c.object_id
        WHERE key = 'comment'
        """,
        output=False
    )
    return (tables,)


@app.cell(hide_code=True)
def _():
    ## ORI columns
    return


@app.cell
def _(mo):
    columns = mo.sql(
        f"""
        SELECT *
        FROM __ducklake_metadata_sprouts.ducklake_column c
        JOIN __ducklake_metadata_sprouts.ducklake_column_tag t
        ON c.column_id = t.column_id
        """,
        output=False
    )
    return (columns,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ORI datasets, tables, columns
    """)
    return


@app.cell
def _(columns):
    # polars DataFrame operations: sort and take first row of each group
    latest_columns = (
        columns.sort('begin_snapshot')
               .unique(subset=['table_id', 'column_id'], keep='first')
    )
    return (latest_columns,)


@app.cell
def _(datasets, mo):
    # build a tabs selector from polars DataFrame
    options = {row['schema_name']: '' for row in datasets.to_dicts()}
    initial = datasets['schema_name'][0]
    selector = mo.ui.tabs(options, value=initial)
    selector
    return (selector,)


@app.cell
def _():
    # TODO: add information about the selected dataset, at least the date_Created and date_lastUpdated, Also the description, and the link to the orginal source, and the licence

    "Description, dateCreated, dateLastUpdated, link to source, Licence"
    return


@app.cell
def _(datasets, latest_columns, mo, pl, quick_statistics, selector, tables):
    # For the selected dataset show the tables as accordeons and within each accordion show the list of colums, their types and a description

    # Determine the selected schema ID based on the user's selection
    selected_schema_id = datasets.filter(pl.col('schema_name') == selector.value)['schema_id'][0]

    # Filter tables that belong to the selected schema
    filtered_tables = tables.filter(pl.col('schema_id') == selected_schema_id)

    # Initialize a dictionary to hold the accordion data
    accordion_data = {}

    # Iterate over each table in the filtered tables
    for row in filtered_tables.to_dicts():
        table_id = row['table_id']
        table_name = row['table_name']
        record_count = quick_statistics.filter(pl.col('table_name') == table_name).to_dict()['record_count'][0]

        # Filter columns that belong to the current table
        cols = latest_columns.filter(pl.col('table_id') == table_id)

        # Select relevant column details and convert to dictionaries
        records = cols.select(['column_name', 'column_type', 'value']).to_dicts()

        # Create a marimo UI table for the current table's columns and add it to the accordion data
        accordion_data[f'{table_name} ({record_count} records)'] = mo.ui.table(data=records)

    # Display the accordion with the collected table data
    mo.accordion(accordion_data, lazy=True)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Query the datasets yourself

    Below you can run queries yourself, use the table names and colums you see above, and start exploring the data live!

    This of course will run in your browser. You have access to all the data, you are now not limited to you imagination, but the limitation now the CPU and RAM of your computer.
    """)
    return


@app.cell
def _(mo):
    initial_code = """SELECT * 
    FROM openapc.apc 
    LIMIT 100
    """

    editor = mo.ui.code_editor(value=initial_code, language="sql").form(submit_button_label="Run")
    editor
    return (editor,)


@app.cell
def _(duckdb, editor, mo):
    mo.ui.table(duckdb.sql(editor.value))
    return


if __name__ == "__main__":
    app.run()
