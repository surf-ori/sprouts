import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt
    import datetime
    import json
    import boto3

    return boto3, datetime, json, mo


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


@app.cell
def _(datetime):
    local_catalog = f'catalog-{str(datetime.datetime.now()).replace(' ', 'T')}.ducklake'
    local_catalog
    return (local_catalog,)


@app.cell
def _(database, local_catalog, mo):
    _df = mo.sql(
        f"""
        ATTACH 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/catalog.ducklake' AS remote;
        ATTACH '{local_catalog}' AS local;
        COPY FROM DATABASE remote to local;
        DETACH remote; DETACH local;
        """
    )
    return


@app.cell
def _(config, local_catalog, mo):
    _df = mo.sql(
        f"""
        ATTACH 'ducklake:{local_catalog}' AS sprouts (DATA_PATH '{config["data-path"]}', OVERRIDE_DATA_PATH true);
        USE sprouts;
        """
    )
    return


@app.cell
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


@app.cell
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
def _(mo):
    _df = mo.sql(
        f"""
        CREATE OR REPLACE SCHEMA pid2portal;
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
        TO '{config["data-path"]}/pid2portal/openalex_NL_ror' (FORMAT 'parquet', FILE_SIZE_BYTES '2gb')
        """
    )
    return


@app.cell
def _(config, mo):
    _df = mo.sql(
        f"""
        CREATE OR REPLACE TABLE pid2portal.openalex_NL_ror AS
        	FROM '{config["data-path"]}/pid2portal/openalex_NL_ror/*.parquet'
            WITH NO DATA;

        CALL ducklake_add_data_files('sprouts', 'openalex_NL_ror', 
                        '{config["data-path"]}/pid2portal/openalex_NL_ror/*.parquet',
            			schema => 'pid2portal');
        """
    )
    return


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


@app.cell
def _(config, mo):
    _df = mo.sql(
        f"""
        CREATE OR REPLACE TABLE pid2portal.openaire_NL_ror AS
        	FROM '{config["data-path"]}/pid2portal/openaire_NL_ror/*.parquet'
            WITH NO DATA;

        CALL ducklake_add_data_files('sprouts', 'openaire_NL_ror', 
                        '{config["data-path"]}/pid2portal/openaire_NL_ror/*.parquet',
            			schema => 'pid2portal');
        """
    )
    return


@app.cell
def _(config, mo):
    _df = mo.sql(
        f"""
        copy (
        	select doi, affiliations, title, id
            from (
                select doi, list_sort(list({{'ror': ror, 'source': source}})) as affiliations
                from (
                    select 'https://doi.org/' || "cerif:DOI" as doi, repository_info.ror as ror, 'cris' as source
                        from cris.publications
                	union
                    select doi, ror, 'openaire' as source
                        from pid2portal.openaire_NL_ror
                	union
                    select doi, ror, 'openalex' as source
                        from pid2portal.openalex_NL_ror
                )
                group by doi
            )
            join (
                select id, mainTitle as title, 'https://doi.org/' || pid.value as doi
                from (
                    select *, unnest(pids) as pid
                    from "openaire-11.1.1".publications
                )
                where pid.scheme = 'doi'
            )
            using (doi)
        ) to '{config["data-path"]}/pid2portal/openaire_NL_subset' (FORMAT 'parquet', FILE_SIZE_BYTES '2gb')
        """
    )
    return


@app.cell
def _(config, mo):
    _df = mo.sql(
        f"""
        CREATE OR REPLACE TABLE pid2portal.openaire_NL_subset AS
        	FROM '{config["data-path"]}/pid2portal/openaire_NL_subset/*.parquet'
            WITH NO DATA;

        CALL ducklake_add_data_files('sprouts', 'openaire_NL_subset', 
                        '{config["data-path"]}/pid2portal/openaire_NL_subset/*.parquet',
            			schema => 'pid2portal');
        """
    )
    return


@app.cell
def _(config, mo):
    _df = mo.sql(
        f"""
        copy (
        	select doi, affiliations, title, id
            from (
                select doi, list_sort(list({{'ror': ror, 'source': source}})) as affiliations
                from (
                    select 'https://doi.org/' || "cerif:DOI" as doi, repository_info.ror as ror, 'cris' as source
                        from cris.publications
                	union
                    select doi, ror, 'openaire' as source
                        from pid2portal.openaire_NL_ror
                	union
                    select doi, ror, 'openalex' as source
                        from pid2portal.openalex_NL_ror
                )
                group by doi
            )
            join openalex.works
            using (doi)
        ) to '{config["data-path"]}/pid2portal/openalex_NL_subset' (FORMAT 'parquet', FILE_SIZE_BYTES '2gb')
        """
    )
    return


@app.cell
def _(config, mo):
    _df = mo.sql(
        f"""
        CREATE OR REPLACE TABLE pid2portal.openalex_NL_subset AS
        	FROM '{config["data-path"]}/pid2portal/openalex_NL_subset/*.parquet'
            WITH NO DATA;

        CALL ducklake_add_data_files('sprouts', 'openalex_NL_subset', 
                        '{config["data-path"]}/pid2portal/openalex_NL_subset/*.parquet',
            			schema => 'pid2portal');
        """
    )
    return


@app.cell
def _(boto3, config, local_catalog):
    client = boto3.client('s3',
                         'default',
                        endpoint_url='https://objectstore.surf.nl',
                        aws_access_key_id=config['objectstore-key'],
                        aws_secret_access_key=config['objectstore-secret']
    )

    with open(local_catalog, 'rb') as file_data:
        res = client.upload_fileobj(file_data, 'sprouts-dev', 'catalog.ducklake')
    return


if __name__ == "__main__":
    app.run()
