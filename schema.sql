CREATE TYPE model_engines AS ENUM ('OPENAI', 'ANTHROPIC');

CREATE TYPE message_adapters AS ENUM('SLACK');

CREATE TYPE login_methods AS ENUM('GOOGLE');

CREATE TYPE document_type AS ENUM ('csv', 'pdf', 'txt');

CREATE TYPE reactions AS ENUM('POSITIVE', 'NEGATIVE');

CREATE TABLE users (
    id UUID PRIMARY KEY,
    sub VARCHAR(127) NOT NULL,
    name VARCHAR(127) NOT NULL,
    picture VARCHAR(255) NOT NULL,
    email VARCHAR(127) NOT NULL,
    email_verified BOOLEAN NOT NULL,
    login_method login_methods NOT NULL DEFAULT 'GOOGLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_level INTEGER DEFAULT 0 NOT NULL
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

CREATE TABLE documents (
  id uuid PRIMARY KEY, 
  type document_type NOT NULL, 
  title VARCHAR(255) NOT NULL,
  object_name VARCHAR(255) NOT NULL, 
  access_level int DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(), 
  updated_at TIMESTAMPTZ DEFAULT NOW()
  -- created_by uuid NOT NULL, 
  -- FOREIGN KEY (created_by) REFERENCES users (id),
);

CREATE TABLE reaction_events (
    id UUID PRIMARY KEY,
    bot_id UUID NOT NULL, -- FK to bots(id)
    reaction reactions NOT NULL,
    source_adapter message_adapters NOT NULL,
    source_adapter_message_id VARCHAR(255) NOT NULL,
    source_adapter_user_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);