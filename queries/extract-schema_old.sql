-- .mode json
-- SELECT column_name as key, replace(column_type, '"', '') as value
--     FROM (
--         DESCRIBE
--         FROM read_json('/Users/bey00001/dev/sprouts/exploration/explore-openaire/publication/part-00000-701d0814-12c8-4855-8340-65934f66e3f1-c000.json.gz')
--     );

-- .mode line
-- WITH types AS (
--         PIVOT (
--             SELECT column_name, column_type
--             FROM (
--                 DESCRIBE
--                 FROM read_json('/Users/bey00001/dev/sprouts/exploration/explore-openaire/publication/part-00000-701d0814-12c8-4855-8340-65934f66e3f1-c000.json.gz')
--             )
--         )
--         ON column_name
--         USING first(column_type)
--     )
-- SELECT t FROM types t


-- .header off
-- .mode tabs
-- .once schema.txt

-- SELECT '{' || string_agg(column_name || ': ''' || column_type || '''', ', ') || '}' AS columns
-- FROM (
--     DESCRIBE
--     FROM read_json('/Users/bey00001/dev/sprouts/exploration/explore-openaire/publication/part-00000-701d0814-12c8-4855-8340-65934f66e3f1-c000.json.gz')
-- );

.mode jsonl
.once schema.json
PIVOT (
    SELECT column_name, column_type
    FROM (
        DESCRIBE
        FROM read_json('/Users/bey00001/dev/sprouts/exploration/explore-openaire/publication/part-00000-701d0814-12c8-4855-8340-65934f66e3f1-c000.json.gz')
    )
)
ON column_name
USING first(column_type);

.shell <schema.json jq >schema-pretty.json

.header off
.mode tabs
.once schema.struct
with types as (select * from 'schema.json') select t from types t;