.shell mkdir -p build/schemas/{dataset}

.mode jsonl
.once build/schemas/{dataset}/{table}_.json
SELECT column_name, column_type
FROM (
    DESCRIBE
    FROM read_{format}('{rawdatapath}/{dataset}/{tablepath}')
);

.shell <build/schemas/{dataset}/{table}_.json jq -s '[.[] | {{(.column_name): .column_type}}] | add' >build/schemas/{dataset}/{table}.json
.shell rm build/schemas/{dataset}/{table}_.json