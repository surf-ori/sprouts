.shell mkdir -p sources/{dataset}/schemas/

.mode jsonl
.once sources/{dataset}/schemas/{table}_.json
-- PIVOT (
    SELECT column_name, column_type
    FROM (
        DESCRIBE
        FROM read_{format}('{rawdatapath}/{dataset}/{tablepath}')
    );
-- )
-- ON column_name
-- USING first(column_type);

-- .shell <sources/{dataset}/schemas/{table}_.json jq >sources/{dataset}/schemas/{table}.json
.shell <sources/{dataset}/schemas/{table}_.json jq -s '[.[] | {{(.column_name): .column_type}}] | add' >sources/{dataset}/schemas/{table}.json
.shell rm sources/{dataset}/schemas/{table}_.json