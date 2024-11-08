-- Modify "users" table
ALTER TABLE "public"."users" ADD COLUMN "access_level" integer NOT NULL DEFAULT 0;
