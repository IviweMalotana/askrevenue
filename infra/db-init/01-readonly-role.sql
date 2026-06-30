-- Provision the least-privilege read-only role used to execute user-generated SQL.
--
-- This runs once, on first container start, BEFORE any tables exist. We therefore
-- rely on ALTER DEFAULT PRIVILEGES so that every table later created by the owning
-- `askrevenue` role (via Alembic migrations) is automatically SELECT-able by the
-- read-only role. A belt-and-braces grant is also re-applied by `make grant-ro`.

DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'askrevenue_ro') THEN
      CREATE ROLE askrevenue_ro LOGIN PASSWORD 'askrevenue_ro';
   END IF;
END
$$;

GRANT CONNECT ON DATABASE askrevenue TO askrevenue_ro;
GRANT USAGE ON SCHEMA public TO askrevenue_ro;

-- Existing + future tables created by the owner become readable by the RO role.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO askrevenue_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE askrevenue IN SCHEMA public
    GRANT SELECT ON TABLES TO askrevenue_ro;

-- Make doubly sure the RO role can never escalate.
REVOKE CREATE ON SCHEMA public FROM askrevenue_ro;
