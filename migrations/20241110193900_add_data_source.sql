-- Create enum type "document_type"
CREATE TYPE "public"."document_type" AS ENUM ('csv', 'pdf', 'txt');
-- Create "documents" table
CREATE TABLE "public"."documents" ("id" uuid NOT NULL, "type" "public"."document_type" NOT NULL, "title" character varying(255) NOT NULL, "object_name" character varying(255) NOT NULL, "created_at" timestamptz NULL DEFAULT now(), "updated_at" timestamptz NULL DEFAULT now(), PRIMARY KEY ("id"));
