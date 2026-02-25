import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import json
    import duckdb
    return json, mo


@app.cell
def _(json):
    with open('./config.json') as f:
        config = json.load(f)
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
    url = mo.ui.text_area(value='build/sprouts.ducklake')
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
    latest_columns = columns.sort_values('begin_snapshot').groupby(['table_id', 'column_id']).head(1)
    return (latest_columns,)


@app.cell
def _(datasets, mo):
    selector = mo.ui.tabs({
            dataset.schema_name: ''
            for dataset in datasets.itertuples()
        }, value=datasets.loc[0, 'schema_name']
    )
    selector
    return (selector,)


@app.cell
def _(datasets, latest_columns, mo, selector, tables):
    mo.accordion({table.table_name: mo.ui.table(data=latest_columns.loc[
                                               latest_columns.table_id == table.table_id,
                                               ['column_name', 'column_type', 'value']
                                           ].to_dict('records'))
                  for table in tables[
                      tables.schema_id == datasets[
                          datasets.schema_name == selector.value].iloc[0].schema_id
                      ].itertuples()
                                 },
                 lazy=True
    )
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
def _():
    return


if __name__ == "__main__":
    app.run()
