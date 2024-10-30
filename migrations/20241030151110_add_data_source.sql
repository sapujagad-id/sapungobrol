-- Create enum type "data_source_type"
CREATE TYPE "public"."data_source_type" AS ENUM ('csv', 'pdf', 'txt', 'sql');
-- Create "data_sources" table
CREATE TABLE "public"."data_sources" ("id" uuid NOT NULL, "type" "public"."data_source_type" NOT NULL, "object_url" character varying(2048) NULL, "db_conn_url" character varying(2048) NULL, "table_names" text NULL, "created_by" uuid NOT NULL, "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, "updated_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY ("id"), CONSTRAINT "data_sources_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION);
