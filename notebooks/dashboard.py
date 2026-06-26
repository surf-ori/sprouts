import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt

    return alt, mo, pl


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        -- run in case you need to reattach to Ducklake
        use memory; detach db;
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        ATTACH 'ducklake:https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/catalog.ducklake' AS db; USE db;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    cris_doi = mo.sql(
        f"""
        SELECT repository, ("cerif:DOI" IS NOT NULL) AS has_doi, "cerif:PublicationDate"[0:4] as pubyear, count() AS records FROM cris.publications GROUP BY repository, pubyear, has_doi;
        """,
        output=False
    )
    return (cris_doi,)


@app.cell
def _(cris_doi, mo):
    repository_choice = mo.ui.dropdown(options=cris_doi['repository'].unique())
    return (repository_choice,)


@app.cell
def _(cris_doi, mo, pl, repository_choice):
    pubyear_choice = mo.ui.dropdown(options=cris_doi.filter(pl.col('repository')==repository_choice.value if repository_choice.value is not None else True)['pubyear'].unique().sort())
    mo.hstack([repository_choice, pubyear_choice])
    return (pubyear_choice,)


@app.cell
def _(alt, cris_doi, mo, pl, pubyear_choice, repository_choice):
    doi_chart = mo.ui.altair_chart(
        alt.Chart(
            cris_doi
            .filter(
                pl.col('repository')==repository_choice.value if repository_choice.value is not None else True,
                pl.col('pubyear')==pubyear_choice.value if pubyear_choice.value is not None else True,
                pl.col('repository').is_not_null()
            )
        )
        .mark_arc()
        .encode(
            color=alt.Color(field='has_doi', type='nominal'),#.legend(None),
            theta=alt.Theta(field='records', type='quantitative').stack(True).sort(field='pubyear'),
            tooltip=[
                alt.Tooltip(field='pubyear'),
                alt.Tooltip(field='records')
            ]
        )
    )
    doi_chart
    return


@app.cell
def _(alt, cris_doi, mo, pl, repository_choice):
    doi_time_chart = mo.ui.altair_chart(
        alt.Chart(
            cris_doi
            .filter(
                pl.col('repository')==repository_choice.value if repository_choice.value is not None else True,
                pl.col('pubyear').is_not_null()
            )
        )
        .mark_line()
        .encode(
            alt.X(field='pubyear'),
            alt.Y(field='records', type='quantitative'),
            alt.Color(field='has_doi'),
            tooltip=[
                alt.Tooltip(field='pubyear'),
                alt.Tooltip(field='records')
            ]
        )
    )
    doi_time_chart
    return


@app.cell
def _(mo):
    all_rors = mo.sql(
        f"""
        select full_name_in_English as name, ROR_LINK as ror from "nl-orgs".baseline;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    rors = mo.sql(
        f"""
        select distinct repository_info.ror as ror, repository_info.name as name from cris.publications;
        """
    )
    return (rors,)


@app.cell
def _(ror_selector):
    selected_ror = ror_selector.value
    selected_ror
    return (selected_ror,)


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        select
            sum(openaire = openalex)::bigint as both,
            sum(openaire is null)::bigint as not_openaire,
            sum(openalex is null)::bigint as not_openalex
        from (
            select distinct doi as openaire
            from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openaire_NL_ror/data_0.parquet'
        )
        full join (
            select distinct doi as openalex
            from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openalex_NL_ror/data_0.parquet'
        )
        on openaire = openalex
        """
    )
    return


@app.cell
def _(mo):
    sources = mo.sql(
        f"""
        select sources, count()
        from (
            select doi, LIST_SORT(list(source)) as sources
            from (
                select distinct 'https://doi.org/' || "cerif:DOI" as doi, 'cris' as source
                    from cris.publications
            	union
                select distinct doi as doi, 'openaire' as source
                    from pid2portal.openaire_NL_ror
            	union
                select distinct doi as doi, 'openalex' as source
                    from pid2portal.openalex_NL_ror
            )
            group by doi
        )
        group by sources
        order by sources
        """,
        output=False
    )
    return (sources,)


@app.cell
def _(sources):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn3

    numbers = sources.to_dicts()

    venn3(subsets = {'001': numbers[0]['count_star()'],
                     '011': numbers[1]['count_star()'],
                     '111': numbers[2]['count_star()'],
                     '101': numbers[3]['count_star()'],
                     '010': numbers[4]['count_star()'],
                     '110': numbers[5]['count_star()'],
                     '100': numbers[6]['count_star()'],
                    },
          set_labels=('OpenAlex', 'OpenAIRE', 'CRIS')
         )
    plt.show()
    return plt, venn3


@app.cell
def _(mo, selected_ror):
    sources_by_ror = mo.sql(
        f"""
        select sources, count()
        from (
            select ror, doi, list_sort(list(source)) as sources
            from (
                select 'https://doi.org/' || "cerif:DOI" as doi, repository_info.ror as ror, 'cris' as source
                    from cris.publications
            	union
                select doi, unnest(affiliations).ror as ror, 'openaire' as source
                    from pid2portal.openaire_NL_subset
            	union
                select doi, unnest(sources).ror as ror, 'openalex' as source
                    from pid2portal.openalex_NL_subset
            )
            group by ror, doi
        )
        where ror = '{selected_ror}'
        group by sources
        order by sources
        """
    )
    return (sources_by_ror,)


@app.cell
def _(mo, rors):
    ror_selector = mo.ui.dropdown(options={row['name']: row['ror'] for row in rors.sort(by='name').to_dicts()})
    ror_selector
    return (ror_selector,)


@app.cell
def _(mo, plt, sources_by_ror, venn3):
    numbers_by_ror = sources_by_ror.to_dicts()

    fig = plt.figure()
    venn3(subsets = {'001': numbers_by_ror[0]['count_star()'],
                     '011': numbers_by_ror[1]['count_star()'],
                     '111': numbers_by_ror[2]['count_star()'],
                     '101': numbers_by_ror[3]['count_star()'],
                     '010': numbers_by_ror[4]['count_star()'],
                     '110': numbers_by_ror[5]['count_star()'],
                     '100': numbers_by_ror[6]['count_star()'],
                    },
          set_labels=('OpenAlex', 'OpenAIRE', 'CRIS')
         )
    mo.mpl.interactive(fig)
    return


@app.cell
def _(mo, selected_ror):
    sources_by_ror_old = mo.sql(
        f"""
        select sources, count()
        from (
            select ror, doi, list_sort(list(source)) as sources
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
            group by ror, doi
        )
        where ror = '{selected_ror}'
        group by sources
        order by sources
        """,
        output=False
    )
    return (sources_by_ror_old,)


@app.cell
def _(mo, plt, sources_by_ror_old, venn3):
    numbers_by_ror_old = sources_by_ror_old.to_dicts()

    fig_old = plt.figure()
    venn3(subsets = {'001': numbers_by_ror_old[0]['count_star()'],
                     '011': numbers_by_ror_old[1]['count_star()'],
                     '111': numbers_by_ror_old[2]['count_star()'],
                     '101': numbers_by_ror_old[3]['count_star()'],
                     '010': numbers_by_ror_old[4]['count_star()'],
                     '110': numbers_by_ror_old[5]['count_star()'],
                     '100': numbers_by_ror_old[6]['count_star()'],
                    },
          set_labels=('OpenAlex', 'OpenAIRE', 'CRIS')
         )
    mo.mpl.interactive(fig_old)
    return


@app.cell(hide_code=True)
def _(mo, selected_ror):
    _df = mo.sql(
        f"""
        select doi, sources
        from (
            select ror, doi, list_sort(list(source)) as sources
            from (
                select 'https://doi.org/' || "cerif:DOI" as doi, repository_info.ror as ror, 'cris' as source
                    from cris.publications
            	union
                select doi, unnest(affiliations).ror as ror, 'openaire' as source
                    from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openaire_NL_subset/data_0.parquet'
            	union
                -- select doi, ror, 'openalex' as source
                --     from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openalex_NL_ror/data_0.parquet'
                select doi, unnest(sources).ror as ror, 'openalex' as source
                    from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openalex_NL_subset/data_0.parquet'
            )
            group by ror, doi
        )
        where ror = '{selected_ror}' -- and sources = ['openalex']
        -- group by sources
        -- order by sources
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        select * from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openalex_NL_subset/data_0.parquet' limit 20;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo, selected_ror):
    _df = mo.sql(
        f"""
        select *
        from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openalex_NL_ror/data_0.parquet'
        where ror = '{selected_ror}'
        """
    )
    return


@app.cell(hide_code=True)
def _(mo, selected_ror):
    _df = mo.sql(
        f"""
        select *
        from (
            select ror, doi, list_sort(list(source)) as sources
            from (
                select 'https://doi.org/' || "cerif:DOI" as doi, repository_info.ror as ror, 'cris' as source
                    from cris.publications
            	union
                select doi, ror, 'openaire' as source
                    from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openaire_NL_ror/data_0.parquet'
            	union
                select doi, ror, 'openalex' as source
                    from 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:sprouts-dev/data/pid2portal/openalex_NL_ror/data_0.parquet'
            )
            group by ror, doi
        )
        where ror = '{selected_ror}'
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT * FROM openaire.publications where pids not null limit 100;
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT * FROM openaire.relations limit 10;
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT s.schema_name, t.table_name, ts.record_count
        FROM __ducklake_metadata_db.ducklake_schema s
        JOIN __ducklake_metadata_db.ducklake_table t
        USING (schema_id)
        JOIN __ducklake_metadata_db.ducklake_table_stats ts
        USING (table_id)
        WHERE s.schema_name != 'main' AND t.end_snapshot IS NULL;
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""
        FROM __ducklake_metadata_db.ducklake_snapshot
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        FROM __ducklake_metadata_db.ducklake_table
        """
    )
    return


if __name__ == "__main__":
    app.run()
