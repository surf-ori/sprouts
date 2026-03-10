import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import json
    import os
    import argparse
    import subprocess
    import shutil
    import time
    import datetime
    from joblib import Parallel, delayed
    import boto3

    return argparse, boto3, datetime, json, mo, os, shutil, subprocess


@app.cell
def _(argparse):
    parser = argparse.ArgumentParser()
    parser.add_argument('datasets', nargs='*')
    parser.add_argument('--new-ducklake', action="store_true")
    args = parser.parse_args()
    return (args,)


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
def _(get_log_file, os, subprocess):
    def run_queries(datalake, dataset, query_set):
        path = os.path.join('build/queries', datalake, dataset, query_set)
        log_file = get_log_file(dataset, query_set)
        with open(log_file, 'wb') as f:
            for filename in sorted(os.listdir(path)):
                query_path = os.path.join(path, filename)
                print(f'running query "{query_path}"', end='')
                f.write(f'running query "{query_path}"\n'.encode('utf-8'))
                f.flush()
                exit_code = subprocess.run(['duckdb', '-f', query_path], stdout=f, stderr=f)
                print('❌' if exit_code.returncode > 0 else '✔️')

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
            queries.append({'name': f'{table_props["raw-files"]["format"]}-to-parquet_({table})', 'string': query})

            tableschemasql = ', '.join(f'"{k}" {v}' for k,v in table_props['schema'].items())

            query = templates['load-in-ducklake'].format(datapath=config["data-path"],
                                                         datalake=config["datalake"],
                                    dataset=dataset,
                                    table=table,
                                    tableschemasql=tableschemasql
                                    )        
            queries.append({'name': f'load-in-ducklake_({table})', 'string': attach_query + query + detach_query})

            query = templates['comment-on-table'].format(datapath=config["data-path"],
                                                         dataset=dataset,
                                                         table=table,
                                                         description=table_props['description'].replace("'", "''")
                                                        )

            for column, description in table_props['column-descriptions'].items():
                query += '\n' + templates['comment-on-column'].format(datapath=config["data-path"],
                                                                      dataset=dataset,
                                                                      table=table,
                                                                      column=column,
                                                                      description=description.replace("'", "''")
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
        print(f'downloading dataset "{dataset}"', end='')
        # log_file = get_log_file(dataset, 'download')
        # with open(log_file, 'wb') as f:
        exit_code = subprocess.run(f'./sources/{dataset}/download.sh', shell=True, executable='/bin/bash')#, stdout=f, stderr=f)
        print('❌' if exit_code.returncode > 0 else '✔️')

    return (download_dataset,)


@app.cell
def _(config, datetime, os):
    def get_log_file(dataset, step):
        path = f'{config['log-path']}/{dataset}'
        if not os.path.exists(path):
            os.makedirs(path)
        return f'{path}/{step}-{str(datetime.datetime.now()).replace(' ', 'T')}.txt'

    return (get_log_file,)


@app.cell
def _(mo):
    config_path = mo.ui.text(value='config.json', full_width=True)
    config_path
    return (config_path,)


@app.cell
def _(config_path, json, mo):
    with open(config_path.value) as f:
        config_preset = json.load(f)
    config_form = mo.ui.dictionary(elements={
        k: mo.ui.text(value=v)
        for k, v in config_preset.items()
    }).form(submit_button_label='Load config')
    config_form
    return (config_form,)


@app.cell
def _(config_form, json):
    config = config_form.value
    with open('config_current.json', 'w') as current_f:
        json.dump(config, current_f)
    return (config,)


@app.cell
def _(config, os):
    catalog_file = os.path.join(config['catalog-path'], f'{config['datalake']}.ducklake')
    exists = os.path.exists(catalog_file)
    return catalog_file, exists


@app.cell
def _(catalog_file, exists, mo):
    mo.md(f'DuckLake at `{catalog_file}` already exists' if exists else '')
    return


@app.cell
def _(exists, mo):
    options = {'reuse DuckLake catalog': False, 'replace DuckLake catalog': True} if exists else {'create new DuckLake'}
    new_ducklake_selection = mo.ui.radio(options=options).form(submit_button_label='Save')
    new_ducklake_selection
    return (new_ducklake_selection,)


@app.cell
def _(
    args,
    config,
    generate_init_queries,
    new_ducklake_selection,
    run_queries,
    write_queries,
):
    new_ducklake = new_ducklake_selection.value or args.new_ducklake
    if new_ducklake:
        init_query = generate_init_queries(config)
        write_queries(init_query, config['datalake'], 'general', 'init')
        run_queries(config['datalake'], 'general', 'init')
        print('created new Ducklake catalog')
    else:
        print('reusing Ducklake catalog')
    return


@app.cell
def _(config, mo, os):
    if not os.path.exists(config['raw-data-path']):
        os.makedirs(config['raw-data-path'])
    sources = os.listdir('sources')
    download_selection = mo.ui.multiselect(options=sources).form(submit_button_label="Download")
    download_selection
    return download_selection, sources


@app.cell
def _(download_dataset, download_selection):
    for d in download_selection.value:
        download_dataset(d)
    return


@app.cell
def _(config, mo):
    raw_data_dir = mo.watch.directory(config['raw-data-path'])
    return (raw_data_dir,)


@app.cell
def _(mo, os, raw_data_dir):
    downloaded_datasets = [os.path.basename(dir) for dir in raw_data_dir.iterdir() if os.path.isdir(dir)]
    extract_selection = mo.ui.multiselect(options=downloaded_datasets).form(submit_button_label="Extract schema")
    extract_selection
    return downloaded_datasets, extract_selection


@app.cell
def _(
    config,
    extract_selection,
    generate_schema_queries,
    run_queries,
    write_queries,
):
    for extract_dataset in extract_selection.value:
        schema_queries = generate_schema_queries(config, extract_dataset)
        write_queries(schema_queries, config['datalake'], extract_dataset, 'schema-extraction')
        run_queries(config['datalake'], extract_dataset, 'schema-extraction')
    return


@app.cell
def _(downloaded_datasets, mo):
    load_selection = mo.ui.multiselect(options=downloaded_datasets).form(submit_button_label="Load")
    load_selection
    return (load_selection,)


@app.cell
def _(args, load_selection, mo, sources):
    datasets = args.datasets or load_selection.value
    unknown_datasets = [dataset for dataset in datasets if dataset not in sources]
    if unknown_datasets:
        print(f'Do no know {unknown_datasets}. Select one of the following dataset: {sources}')
        mo.stop(True)
    return (datasets,)


@app.cell
def _(config, datasets, generate_load_queries, run_queries, write_queries):
    for dataset in datasets:
        load_queries = generate_load_queries(config, dataset)
        write_queries(load_queries, config['datalake'], dataset, 'loading')
        run_queries(config['datalake'], dataset, 'loading')
    return


@app.cell
def _(config, mo):
    if config['objectstore-key'] and config['objectstore-secret']:
        remote_catalog_path = mo.ui.dictionary({
            'bucket': mo.ui.text(value='sprouts'),
            'key': mo.ui.text(value='catalog.ducklake')
        }).form(submit_button_label='Upload')
    else:
        remote_catalog_path = mo.md('')

    remote_catalog_path
    return (remote_catalog_path,)


@app.cell
def _(datetime, remote_catalog_path):
    frozen_catalog = f'{str(datetime.datetime.now()).replace(' ', 'T')}-{remote_catalog_path.value['key']}'
    frozen_catalog
    return (frozen_catalog,)


@app.cell(hide_code=True)
def _(catalog_file, database, frozen_catalog, mo):
    _df = mo.sql(
        f"""
        ATTACH '{catalog_file}' as ducklake;
        ATTACH '{frozen_catalog}' as frozen_ducklake;
        COPY FROM DATABASE ducklake TO frozen_ducklake;
        UPDATE frozen_ducklake.ducklake_metadata
        SET value = replace(value, 's3://', 'https://objectstore.surf.nl/cea01a7216d64348b7e51e5f3fc1901d:')
        WHERE key = 'data_path';
        DETACH ducklake;
        DETACH frozen_ducklake;
        """
    )
    return


@app.cell
def _(boto3, config, frozen_catalog, remote_catalog_path):
    client = boto3.client('s3',
                            'default',
                            endpoint_url='https://objectstore.surf.nl',
                            aws_access_key_id=config['objectstore-key'],
                            aws_secret_access_key=config['objectstore-secret']
                           )

    with open(frozen_catalog, 'rb') as file_data:
        res = client.upload_fileobj(file_data,
                                    remote_catalog_path.value['bucket'],
                                    remote_catalog_path.value['key'])
    return


if __name__ == "__main__":
    app.run()
