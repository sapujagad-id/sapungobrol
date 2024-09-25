-- Create enum type "message_adapters"
CREATE TYPE "public"."message_adapters" AS ENUM ('SLACK');
-- Modify "bots" table
ALTER TABLE "public"."bots" ADD COLUMN "adapter" "public"."message_adapters" NOT NULL;
