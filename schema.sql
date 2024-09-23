CREATE TYPE model_engines AS ENUM ('OPENAI');


CREATE TABLE bots (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT NOT NULL,
    model model_engines NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);