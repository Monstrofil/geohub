from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "tree_items" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "type" VARCHAR(20) NOT NULL,
    "tags" JSONB NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "path" LTREE NOT NULL DEFAULT 'root'
);
        DROP TABLE IF EXISTS "collections";
        DROP TABLE IF EXISTS "files";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "tree_items";"""


MODELS_STATE = (
    "eJztVm1P2zAQ/itRPoHUVRDKi6ZpUoFOdIJ2grBNIBS5sZtaJHaIL4MK9b/Pdl4bSNuVhg"
    "/bvjTN3eW583OXe/JsBhwTX7S7JKLuxPxoPJsoDOU1dZgtw2QoIIUlC5UOQCNfe1BuogyT"
    "JyKk8fZO3gaIIY9gecti35cGNBIQIRekZYx8QaQpvHfGlPhYJ89yUazQYkYfYnUPUaxCMR"
    "mj2IcCLkmHiwhlT6vK8PHIcbkfB6zAxdyVZVDmFUgeYSRCUMbSVTkwDXVFfQZfdJnS43Km"
    "jkEZCF21pyI+WLudw87R3kHnSIboEnLL4UxXL9yIhkA5K/KGU5hwlmeRkGZSc5E9yaFrGN"
    "jmbPb6AcYpjQX3VlCxcItXLBgBKpkK/n+RSKg6y03ICa3vQhayrA0l+CW9yB6fb8bJBEW1"
    "3QjQk+MT5oGaZ2t/f1XuJcgC7r93L0/OupdbEnBbhXE5xsn0D1KXlfhUgwoi1dvUEIkpdM"
    "ME7u7sbJZACVhLoPbNEyiLA5K8FU2QWIJfi8ivV8NBHZGr8nbNpPcWUxdahk8F3C1gUeVT"
    "7kCIB79M3tZF92eV15Pz4bEyhVyAF2kUDXAsOb6rKy5h2QHuEZiQKFsVI+TeP6IIOy8WTe"
    "6p7Bd1/FQz7IiQPpBgJYHJg8sSA9LoUGkV7ykz5qdxzFzFjxHHFLfVT+ez2WpKeV6fsevr"
    "/ulbZ0yXr4AWzJYeo72D7erI6MfeR3f0taFXPcP+yxVHgzdEYYbdNIUblhyrXnGsF4IDyB"
    "NL+CuthVFMfaBMtNX6rmyGlVlNM/5bAjQn8hFRh3TQ2jqPYuAO449/Iv1zSdci/1R6gQak"
    "dqxlCjxk/jTViVUbglPcdvbHLB3RQbikOzVtsvsXvSu7e/FtrlenXbunPJa2TivWrYNK/3"
    "IQ40ffPjPUrXEzHPSqLc3j7JtKY+MQb66xKyrtfM7/fW2iryGCybIlGXEO6y3EDH2t3p2r"
    "78e3bsTFunJuX/Z67/MNPfsN+6ujCQ=="
)
