import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt
    import json

    return json, mo


@app.cell
def _(mo):
    config_path = mo.ui.text(value='config-cloud.json', full_width=True)
    config_path
    return (config_path,)


@app.cell
def _(config_path, json):
    with open(config_path.value) as f:
        config = json.load(f)
    config
    return (config,)


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
        ATTACH 'ducklake:https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/catalog.ducklake' AS sprouts; USE sprouts;
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
def _(config, mo):
    _df = mo.sql(
        f"""
        -- secret necessary to write data back to the object store
        CREATE OR REPLACE SECRET objectstore (
            TYPE s3,
            ENDPOINT 'objectstore.surf.nl',
            URL_STYLE 'path',
            PROVIDER config,
            KEY_ID '{config["objectstore-key"]}',
            SECRET '{config["objectstore-secret"]}'
        );
        """
    )
    return


@app.cell
def _(config, mo):
    _df = mo.sql(
        f"""
        -- select works from OpenAlex that have at least one author who is affiliated with a Dutch organization
        -- each record represents one unique work-author-affiliation combination,
        -- so there might be multiple records for the same author if multiple affiliations are listed
        COPY (
            SELECT id, doi, ror, authorship
            FROM (
                SELECT *, unnest(authorship.institutions).ror AS ror
                FROM (
                	SELECT id, case when doi == 'https://doi.org/' then null else doi end as doi, unnest(authorships) as authorship
            		FROM openalex.works
                )
                WHERE authorship.institutions IS NOT NULL
            )
            WHERE ror IN (
            	SELECT ROR_LINK FROM "nl-orgs".baseline
            )
        )
        TO '{config["data-path"]}/pid2portal/openalex_NL_ror' (FORMAT 'parquet', FILE_SIZE_BYTES '2gb', OVERWRITE)
        """
    )
    return


@app.cell
def _(config, mo):
    _df = mo.sql(


@app.cell
def _(config, mo):
    expl = mo.sql(
        f"""
        -- select works from OpenAire that have at least one author who is affiliated with a Dutch organization
        -- each record represents one unique work-author-affiliation combination,
        -- so there might be multiple records for the same author if multiple affiliations are listed
        -- optimized query
        copy (
        	select
                id,
                unnest(
                    ifnull(
                        list('https://doi.org/' || pid.value) FILTER (pid.scheme = 'doi'), [null]
                    )
                ) as doi,
            	ror,
            	authorship
            from (
                select id, unnest(ifnull(pids, [null])) as pid, ror,
            		{{'author': person, 'affiliation': declaredAffiliation}} as authorship
                from (
                    select *, unnest(declaredAffiliation.matchingOrganizations).ror as ror
                    from (
                        select person, product as id, unnest(declaredAffiliations) as declaredAffiliation 
                        from "openaire-11.1.1".authorships
                    )
                )
                join "openaire-11.1.1".publications
                using (id)
                where ror in (
                        SELECT ROR_LINK FROM "nl-orgs".baseline
                )
            )
            group by (id, ror, authorship)
        ) to '{config["data-path"]}/pid2portal/openaire_NL_ror' (FORMAT 'parquet', FILE_SIZE_BYTES '2gb')

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        select * from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openalex_NL_ror/data_0.parquet' limit 100;
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        select * from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openaire_NL_ror/data_0.parquet' limit 100;
        """
    )
    return


if __name__ == "__main__":
    app.run()
