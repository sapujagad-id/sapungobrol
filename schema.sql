CREATE TYPE model_engines AS ENUM ('OPENAI', 'ANTHROPIC');

CREATE TYPE message_adapters AS ENUM('SLACK');

CREATE TYPE login_methods AS ENUM('GOOGLE');

CREATE TYPE data_source_type AS ENUM ('csv', 'pdf', 'txt', 'sql');

CREATE TABLE users (
    id UUID PRIMARY KEY,
    sub VARCHAR(127) NOT NULL,
    name VARCHAR(127) NOT NULL,
    picture VARCHAR(255) NOT NULL,
    email VARCHAR(127) NOT NULL,
    email_verified BOOLEAN NOT NULL,
    login_method login_methods NOT NULL DEFAULT 'GOOGLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bots (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id UUID, -- FK
    system_prompt TEXT NOT NULL,
    model model_engines NOT NULL,
    adapter message_adapters NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    slug VARCHAR(255),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE data_sources (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type data_source_type NOT NULL,
    object_url VARCHAR(2048),
    db_conn_url VARCHAR(2048),
    table_names TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);