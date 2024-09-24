-- Create enum type "model_engines"
CREATE TYPE "public"."model_engines" AS ENUM ('OPENAI');
-- Create "bots" table
CREATE TABLE "public"."bots" ("id" uuid NOT NULL, "name" character varying(255) NOT NULL, "system_prompt" text NOT NULL, "model" "public"."model_engines" NOT NULL, "created_at" timestamptz NULL DEFAULT now(), "updated_at" timestamptz NULL DEFAULT now(), PRIMARY KEY ("id"));
