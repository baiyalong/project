-- Create database if not exists (Postgres usually creates DB via Env var, but this is enabling extension maybe)
-- CREATE DATABASE heritage;

-- Connect to heritage (If manual)
-- \c heritage

-- Table creation is handled by SQLAlchemy `Base.metadata.create_all` in the pipeline.
-- However, we might want to create the user/db here if not using default postgres image env vars.

-- For this setup within docker-compose, using POSTGRES_DB env var is enough for DB creation.
-- The pipeline will create tables on connection.
