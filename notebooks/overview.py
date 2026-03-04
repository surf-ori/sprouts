# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "duckdb==1.4.4",
#     "marimo>=0.20.2",
#     "polars[pyarrow]==1.38.1",
#     "pydantic-ai==1.63.0",
#     "sqlglot==29.0.1",
# ]
# ///

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This dashboard is part of the [**PID to Portal project**](https://communities.surf.nl/en/open-research-information/article/from-pid-to-portal-strengthening-the-open-research-information) from SURF and UNL.

    Our goals is to create an overview of available and actively queryable Open Research Information Resources / Datasets, that the ORI community can start using freely.

    In our approach we want to stay away from BigTech. We currently curate the quaryable databases ourselves, but welcome others to share their data-catalogues. We use the DuckLake cataloge from DuckDB, and store the actual data as parquet files on an S3-compatibe Object store. This way we can keep costs low, by separating storage and compute.

    Compute: You can [query the datasets from your browser, right now!](#link-to-html-page) When you want to query the databases, you attach the ducklake catalog, and you see all the available datasets. When you run an SQL query, a portion of the data requested by your query is transfered over HTTPS to your local machine where the SQL operations take place in your machine. The bigger the requested daa, the longer the data transfer. The biger your local machine, the faster your query operation completes. how big your machine is, that is up to you.

    At SURF we also offer ready-made [services](https://www.surf.nl/en/services) for that SQL compute, where you can start working in. like a Marimo notebook in a virtual machine on SURF Research Cloud, or a Superset dashboard on a Kubernetes cluster.

    Below you will see the ORI data resources we currently curate. (This overview was inspired by the [ORION-DBS initiative](https://orion-dbs.community/).)
    """)
    return


@app.cell
def _():
    import marimo as mo
    import json
    import duckdb
    import polars as pl

    return duckdb, json, mo, pl


@app.cell
def _(json):
    with open('./config.json') as f:
        config = json.load(f)
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

    This URL gives you access to the ORI data catalog.

    This catalog lists all the ORI data resoures, their tables and columns. also it holds infomration about the changes in time of all the data resources, like  deleted, updated and added records, and schema changes.

    This alows you to 'time-travel' in the data, and not only use the last state. For example detecting when an article flips from open access to closed access.

    Use this URL to attach it as a ducklake to your query engine.
    """)
    return


@app.cell
def _(mo):
    url = mo.ui.text_area(value='https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts/catalog.ducklake')
    # url = mo.ui.text_area(value='https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:boto3bucket/sprouts.ducklake')
    url
    return (url,)


@app.cell
def _(url):
    url.value
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ORI data statistics

    This table below shows you some quick statistics on the volume of the ORI datasets and their tables. For each table this can be the number of records, number of columns, total table size in bytes, etc.
    """)
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
        SELECT table_name, record_count
            FROM __ducklake_metadata_sprouts.ducklake_table_stats
            FULL JOIN __ducklake_metadata_sprouts.ducklake_table
        	USING (table_id)
        """
    )
    return


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
def _(datasets, latest_columns, mo, pl, selector, tables):
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

        # Filter columns that belong to the current table
        cols = latest_columns.filter(pl.col('table_id') == table_id)

        # Select relevant column details and convert to dictionaries
        records = cols.select(['column_name', 'column_type', 'value']).to_dicts()

        # Create a marimo UI table for the current table's columns and add it to the accordion data
        accordion_data[table_name] = mo.ui.table(data=records)

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
    initial_code = """SELECT mainTitle 
    FROM openaire.publications 
    LIMIT 10
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
