-- Modify "bots" table
ALTER TABLE "public"."bots" ADD COLUMN "user_id" uuid NULL, ADD CONSTRAINT "fk_user" FOREIGN KEY ("user_id") REFERENCES "public"."users" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION;
