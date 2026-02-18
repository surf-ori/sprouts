import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import duckdb
    import json
    import os
    import subprocess
    import shutil
    return json, mo, os, shutil, subprocess


@app.cell
def _(os):
    def load_query_templates(path):
        query_templates = {}
        template_names = [f for f in os.listdir(path) if f.endswith('.sql')]
        for template_name in template_names:
            with open(os.path.join(path, template_name)) as f:
                query_templates[os.path.splitext(template_name)[0]] = f.read()
        return query_templates
    return (load_query_templates,)


@app.cell
def _(os, shutil):
    def write_queries(queries, datalake, dataset, query_set):
        path = os.path.join('build/queries', datalake, dataset, query_set)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        for i, query in enumerate(queries):
            with open(f'{path}/{i:03}_{query['name']}.sql', 'w') as f:
                f.write(query['string'])
    return (write_queries,)


@app.cell
def _(os, subprocess):
    def run_queries(datalake, dataset, query_set):
        path = os.path.join('build/queries', datalake, dataset, query_set)
        # subprocess.run(['ls', path])
        for f in sorted(os.listdir(path)):
            subprocess.run(['duckdb', '-f', os.path.join(path, f)])
    return (run_queries,)


@app.cell
def _(json, load_query_templates):
    def generate_load_queries(config, dataset):

        queries = []
        templates = load_query_templates('queries')

        with open(f'sources/{dataset}/metadata.json') as f:
            metadata = json.load(f)

        attach_query = templates['attach-to-ducklake'].format(
                                        catalogpath=config["catalog-path"],
                                        datapath=config["data-path"],
                                        datalake=config["datalake"],
                                        key=config["objectstore-key"],
                                        secret=config["objectstore-secret"])
        detach_query = templates['detach'].format(catalogpath=config["catalog-path"],
                                                  datapath=config["data-path"],
                                                  datalake=config["datalake"])

        for table, table_props in metadata['tables'].items():

            query = templates[f'{table_props["raw-files"]["format"]}-to-parquet'].format(
                                                datapath=config["data-path"],
                                                datalake=config["datalake"],
                                                rawdatapath=config["raw-data-path"],
                                                dataset=dataset,
                                                table=table,
                                                tablepath=table_props["raw-files"]["path"],
                                                tableschema=table_props['schema']
                                                )
            queries.append({'name': f'{table_props["raw-files"]["format"]}-to-parquet_({table})',
                            'string': attach_query + query + detach_query})

            query = templates['load-in-ducklake'].format(datapath=config["data-path"],
                                                         datalake=config["datalake"],
                                    dataset=dataset,
                                    table=table
                                    )        
            queries.append({'name': f'load-in-ducklake_({table})', 'string': attach_query + query + detach_query})

            query = templates['comment-on-table'].format(datapath=config["data-path"],
                                                         dataset=dataset,
                                                         table=table,
                                                         description=table_props['description'])

            for column, description in table_props['column-descriptions'].items():
                query += '\n' + templates['comment-on-column'].format(datapath=config["data-path"],
                                                                      dataset=dataset,
                                                                      table=table,
                                                                      column=column,
                                                                      description=description
                                                                     )

            queries.append({'name': f'add-comments_({table})', 'string': attach_query + query + detach_query})

        return queries
    return (generate_load_queries,)


@app.cell
def _(json, load_query_templates):
    def generate_schema_queries(config, dataset):
        queries = []
        templates = load_query_templates('queries')

        with open(f'sources/{dataset}/metadata.json') as f:
            metadata = json.load(f)

        for table, table_props in metadata['tables'].items():

            query = templates['extract-schema'].format(datapath=config["data-path"],
                                                rawdatapath=config["raw-data-path"],
                                                dataset=dataset,
                                                table=table,
                                                tablepath=table_props["raw-files"]["path"],
                                                format=table_props["raw-files"]['format']
                                                )
            queries.append({'name': f'extract-schema_({table})', 'string': query})

        return queries
    return (generate_schema_queries,)


@app.cell
def _(load_query_templates):
    def generate_init_queries(config):
        queries = []
        templates = load_query_templates('queries')

        query = templates['init-ducklake'].format(catalogpath=config["catalog-path"], datapath=config["data-path"], datalake=config["datalake"])
        queries.append({'name': 'init-ducklake', 'string': query})

        return queries
    return (generate_init_queries,)


@app.cell
def _(subprocess):
    def download_dataset(dataset):
        subprocess.run(f'./sources/{dataset}/download.sh', shell=True)
    return (download_dataset,)


@app.cell
def _(json):
    with open('config.json') as f:
        config = json.load(f)
    return (config,)


@app.cell
def _(config, generate_init_queries, run_queries, write_queries):
    init_query = generate_init_queries(config)
    write_queries(init_query, config['datalake'], 'general', 'init')
    run_queries(config['datalake'], 'general', 'init')
    return


@app.cell
def _(mo, os):
    sources = os.listdir('sources')
    dataset_selection = mo.ui.dropdown(options=sources).form(submit_button_label="Run")
    dataset_selection
    return (dataset_selection,)


@app.cell
def _(dataset_selection, mo):
    dataset = dataset_selection.value
    mo.stop(dataset is None, 'Select a dataset first')
    return (dataset,)


@app.cell
def _(dataset, download_dataset):
    download_dataset(dataset)
    return


@app.cell
def _(config, dataset, generate_schema_queries, run_queries, write_queries):
    schema_queries = generate_schema_queries(config, dataset)
    write_queries(schema_queries, config['datalake'], dataset, 'schema-extraction')
    run_queries(config['datalake'], dataset, 'schema-extraction')
    return


@app.cell
def _(config, dataset, generate_load_queries):
    load_queries = generate_load_queries(config, dataset)
    return (load_queries,)


@app.cell
def _(config, dataset, load_queries, write_queries):
    write_queries(load_queries, config['datalake'], dataset, 'loading')
    return


@app.cell
def _(config, dataset, run_queries):
    run_queries(config['datalake'], dataset, 'loading')
    return


if __name__ == "__main__":
    app.run()
