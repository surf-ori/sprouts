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
        path = os.path.join('generated', datalake, dataset, query_set)
        if os.path.exists(path):
            shutil.rmtree(path, )
        os.makedirs(path)
        for i, query in enumerate(queries):
            with open(f'{path}/{i:03}_{query['name']}.sql', 'w') as f:
                f.write(query['string'])
    return (write_queries,)


@app.cell
def _(os, subprocess):
    def run_queries(datalake, dataset, query_set):
        path = os.path.join('generated', datalake, dataset, query_set)
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
    return


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
    dataset_selection = mo.ui.dropdown(options=sources)
    dataset_selection
    return (dataset_selection,)


@app.cell
def _(dataset_selection):
    dataset = dataset_selection.value
    return (dataset,)


@app.cell
def _():
    # schema_queries = generate_schema_queries(config, dataset)
    # write_queries(schema_queries, config['datalake'], dataset, 'schema-extraction')
    # run_queries(config['datalake'], dataset, 'schema-extraction')
    return


@app.cell
def _(config, dataset, generate_load_queries):
    loading = generate_load_queries(config, dataset)
    return (loading,)


@app.cell
def _(config, dataset, loading, write_queries):
    write_queries(loading, config['datalake'], dataset, 'loading')
    return


@app.cell
def _(config, dataset, run_queries):
    run_queries(config['datalake'], dataset, 'loading')
    return


@app.cell
def _():
    #steps = {source: generate_queries(config, source) for source in sources}
    return


@app.cell
def _(steps):
    steps
    return


@app.cell
def _(json, wrapper):
    status = json.loads(wrapper.read_text())
    return (status,)


@app.cell
def _(mo, status, table):
    mo.accordion({
        mo.md('{name} {status}').batch(name=q['name'], status=q['status']): mo.md(f'```sql\n{q['string']}\n```') for q in status[table.value]
    })
    return


@app.cell
def _(mo):
    run = mo.ui.button(value=False, on_click=lambda value: not value, kind='success')
    run
    return (run,)


@app.cell
def _(run):
    if run.value:
        print('yeah')
    return


@app.cell
def _(mo):
    wrapper = mo.watch.file('status.json')
    return (wrapper,)


@app.cell
def _():
    mapping = {
        "loaded": "success",
        "loading": "warn",
        "not loaded": "neutral",
        "error": "danger"
    }
    return


@app.cell
def _():
    # with open('status.json', 'w') as f2:
    #     json.dump({
    #         "dataset1":{
    #             "table1": "loaded",
    #             "table2": "error",
    #             "table3": "not loaded"
    #         },
    #         "dataset2":{
    #             "table1": "loaded",
    #             "table2": "loaded",
    #             "table3": "not loaded"
    #         }
    #     }, f2)
    return


@app.cell
def _():
    # table = mo.ui.radio(options=[name for name in steps])
    # mo.sidebar(table)
    return


@app.cell
def _(mo):
    mo.sidebar(
        mo.nav_menu({
            '/?dataset=openaire': 'OpenAIRE',
            '/?dataset=openalex': 'OpenAlex'
        }, orientation='vertical')
    )
    return


@app.cell
def _(mo):
    m = mo.query_params()
    m
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
