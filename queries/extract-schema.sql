.shell mkdir -p sources/openaire/schemas/

.mode jsonl
.once sources/openaire/schemas/communities_infrastructures.json
PIVOT (
    SELECT column_name, column_type
    FROM (
        DESCRIBE
        FROM read_json('sample-data/openaire/community_infrastructure.json.gz')
    )
)
ON column_name
USING first(column_type);

.shell cat schemas/openaire/publication.json | jq >schemas/openaire/publication_.json
.shell cat schemas/openaire/publication.json | jq >schemas/openaire/publication_.json