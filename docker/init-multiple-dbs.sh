#!/bin/bash
# Creates multiple PostgreSQL databases on container startup.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE sales_db;
    CREATE DATABASE airflow;
    GRANT ALL PRIVILEGES ON DATABASE sales_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE airflow TO $POSTGRES_USER;
EOSQL
