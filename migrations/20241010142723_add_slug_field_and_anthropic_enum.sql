-- Add value to enum type: "model_engines"
ALTER TYPE "public"."model_engines" ADD VALUE 'ANTHROPIC';
-- Modify "bots" table
ALTER TABLE "public"."bots" ADD COLUMN "slug" character varying(255) NULL;
