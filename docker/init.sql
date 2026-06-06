-- PostgreSQL 15+ removed the default CREATE grant on the public schema.
-- This runs once when the container's data volume is first initialised.
GRANT CREATE ON SCHEMA public TO gray;