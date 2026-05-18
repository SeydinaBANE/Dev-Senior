-- Sessions de conversation (persistance API)
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    agent       TEXT NOT NULL,
    history     TEXT NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS sessions_agent_idx ON sessions (agent);
CREATE INDEX IF NOT EXISTS sessions_updated_idx ON sessions (updated_at);
