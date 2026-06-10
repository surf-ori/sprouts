import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt

    return alt, mo


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        use memory; detach sprouts;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        ATTACH 'ducklake:https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts/catalog.ducklake' AS sprouts; USE sprouts;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        select count() from openalex.works; --old
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        select count() from openalex.works; --new ingestion
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        -- Bianca's pub year logic
        -- WHERE
        --     (b.crossref.cr_issued_year BETWEEN {{ var('start_year') }}
        --   AND {{ var('end_year') }}
        --    OR c.openalex.openalex_publication_year BETWEEN {{ var('start_year') }}
        --   AND {{ var('end_year') }}
        --    OR d.openaire.openaire_publication_year BETWEEN {{ var('start_year') }}
        --   AND {{ var('end_year') }}
        --     )
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        COPY (
            SELECT id, doi, ror, authorship --first(doi) as doi, ror
            FROM (
                SELECT id, doi, unnest(authorship.institutions).ror AS ror, authorship
                FROM (
                	SELECT id, doi, unnest(authorships) as authorship FROM openalex.works LIMIT 10000
                )
                WHERE authorship.institutions IS NOT NULL
            )
            WHERE ror
            IN (
            	SELECT ROR_LINK FROM "nl-orgs".baseline
            )
            -- GROUP BY id, ror
        )
        TO 'openalex_NL' (FORMAT 'parquet', FILE_SIZE_BYTES '2gb', OVERWRITE)
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        SELECT id, doi, unnest(authorships) FROM openalex.works LIMIT 10;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        select * from 'openalex_NL/*.parquet';
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        select * from "nl-orgs".baseline limit 10;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        describe openaire.publications;
        """
    )
    return


app._unparsable_cell(
    r"""
    select count() from openaire.publications where organizations is not null limit 10;
    """,
    name="_"
)


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        select organizations from openaire.publications where organizations is not null limit 10;
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        select (authorship.author.orcid IS NOT NULL) AS has_orcid from 'openalex_NL/*.parquet';
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        select *, (repository is not null) as included
            from 'openalex_NL/*.parquet'
            left join (
            	from cris.publications 
                -- where repository_info.ror = 'https://ror.org/02jz4aj89'
            )    
            on doi = 'https://doi.org/' || "cerif:DOI"
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    df = mo.sql(
        f"""
        select ror, included, count()
        from (
            select *, (repository is not null) as included
            from 'openalex_NL/*.parquet'
            left join (
            	from cris.publications 
                -- where repository_info.ror = 'https://ror.org/02jz4aj89'
            )    
            on doi = 'https://doi.org/' || "cerif:DOI"
        )
        group by ror, included
        """
    )
    return (df,)


@app.cell
def _(alt, df):
    (
        alt.Chart(df)
        .mark_bar()
        .encode(
            alt.X(field='count_star()', type='quantitative'),
            alt.Y(field='ror'),
            alt.Color(field='included')
        )
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
