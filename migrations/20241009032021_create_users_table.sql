-- Create enum type "login_methods"
CREATE TYPE "public"."login_methods" AS ENUM ('GOOGLE');
-- Create "users" table
CREATE TABLE "public"."users" ("id" uuid NOT NULL, "sub" character varying(127) NOT NULL, "name" character varying(127) NOT NULL, "picture" character varying(255) NOT NULL, "email" character varying(127) NOT NULL, "email_verified" boolean NOT NULL, "login_method" "public"."login_methods" NOT NULL DEFAULT 'GOOGLE', "created_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY ("id"));
