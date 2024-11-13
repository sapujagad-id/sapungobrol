-- Create enum type "reactions"
CREATE TYPE "public"."reactions" AS ENUM ('POSITIVE', 'NEGATIVE');
-- Create "reaction_events" table
CREATE TABLE "public"."reaction_events" ("id" uuid NOT NULL, "bot_id" uuid NOT NULL, "reaction" "public"."reactions" NOT NULL, "source_adapter" "public"."message_adapters" NOT NULL, "source_adapter_message_id" character varying(255) NOT NULL, "source_adapter_user_id" character varying(255) NOT NULL, "message" text NOT NULL, "created_at" timestamptz NULL DEFAULT now(), PRIMARY KEY ("id"));
