-- Create "workspace_data" table
CREATE TABLE "public"."workspace_data" ("id" uuid NOT NULL, "team_id" character varying(255) NOT NULL, "access_token" character varying(255) NOT NULL, "installed_at" timestamptz NULL DEFAULT now(), PRIMARY KEY ("id"));
