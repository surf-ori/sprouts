CREATE OR REPLACE SECRET objectstore (
    TYPE s3,
    ENDPOINT 'objectstore.surf.nl',
    URL_STYLE 'path',
    PROVIDER config,
    KEY_ID '{key}',
    SECRET '{secret}'
);

ATTACH 'ducklake:{catalogpath}/{datalake}.ducklake' as {datalake};
USE {datalake};

