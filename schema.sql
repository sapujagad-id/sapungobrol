CREATE TYPE model_engines AS ENUM ('OPENAI');

CREATE TYPE message_adapters AS ENUM('SLACK');

CREATE TABLE bots (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT NOT NULL,
    model model_engines NOT NULL,
    adapter message_adapters NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);