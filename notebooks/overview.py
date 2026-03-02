# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "duckdb==1.4.4",
#     "marimo>=0.20.2",
#     "polars[pyarrow]==1.38.1",
#     "pydantic-ai==1.63.0",
#     "sqlglot==29.0.1",
# ]
# ///

import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import json
    import duckdb
    import polars as pl

    return json, mo, pl


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


@app.cell
def _(mo):
    url = mo.ui.text_area(value='https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:boto3bucket/sprouts_http.ducklake')
    # url = mo.ui.text_area(value='https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:boto3bucket/sprouts.ducklake')
    url
    return (url,)


@app.cell
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
    _df = mo.sql(
        f"""
        SELECT table_name, record_count
            FROM __ducklake_metadata_sprouts.ducklake_table_stats
            FULL JOIN __ducklake_metadata_sprouts.ducklake_table
        	USING (table_id)
        """
    )
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
    # determine selected schema id
    selected_schema_id = datasets.filter(pl.col('schema_name') == selector.value)[
        'schema_id'
    ][0]

    filtered_tables = tables.filter(pl.col('schema_id') == selected_schema_id)
    accordion_data = {}
    for row in filtered_tables.to_dicts():
        table_id = row['table_id']
        table_name = row['table_name']
        cols = latest_columns.filter(pl.col('table_id') == table_id)
        records = cols.select(['column_name', 'column_type', 'value']).to_dicts()
        accordion_data[table_name] = mo.ui.table(data=records)

    mo.accordion(accordion_data, lazy=True)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
