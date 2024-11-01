-- Modify "data_sources" table
ALTER TABLE "public"."data_sources" DROP COLUMN "created_by";
ALTER TABLE "public"."data_sources" ADD COLUMN "name" character varying(255) NOT NULL;
