-- Modify "documents" table
ALTER TABLE "public"."documents" ADD COLUMN "access_level" integer NULL DEFAULT 0;
