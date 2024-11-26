-- Create "threads" table
CREATE TABLE "public"."threads" (
    "id" uuid NOT NULL,
    "bot_id" uuid NOT NULL,
    "created_at" timestamptz NULL DEFAULT now(),
    PRIMARY KEY ("id"),
    CONSTRAINT "fk_bot" FOREIGN KEY ("bot_id") REFERENCES "public"."bots" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);
