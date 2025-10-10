from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "geo_raster_files" DROP COLUMN "image_width";
        ALTER TABLE "geo_raster_files" DROP COLUMN "image_height";
        ALTER TABLE "geo_raster_files" DROP COLUMN "image_bands";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "geo_raster_files" ADD "image_width" INT;
        ALTER TABLE "geo_raster_files" ADD "image_height" INT;
        ALTER TABLE "geo_raster_files" ADD "image_bands" INT;"""


MODELS_STATE = (
    "eJztWutP4zgQ/1esfAKpdKFQyq1OJ5XXbk88Tmy5Oy2gyE3c1EdiZ21n2d6K//3GbvPsg1"
    "5JWMTmC5AZZ2bym/E8jL9bAXeJL5tdIqgzst6j7xYOQ/g9ZVgNZDEckJQSLwWGwgPfcHBC"
    "oswl34gE4s0dPAaYYY+48Mgi3wcCHkglsKOAMsS+JEAK7+0hJb5rlMe6qKulRYx+ifSzEp"
    "Fe6pIhjnyVipuoc9MVmj61KpbvDmyH+1HAUrkud8AMyrxUkkcYEVhlZRmrbDUOjUU9pk6N"
    "mcBxONOfQZmSxmpPr9hq7ex19g529/cOYIkxIaF0Ho310hE0VJSzVG84ViPOEi0g0prYnG"
    "qf6DA2XPStx8f5HzCcwphi3woKFN7iBYqLFc6QUvy/EiG1nVknJIAu9kK85Ck3ZMQ/4Yv4"
    "9bwzjkZYLPRGgL/ZPmGe0vHcardXxR6ELMH+z+7V0cfu1QYI3NTLOITxJPovpqzWhKcdlA"
    "Kpd1NFIE5FVwzgzvZ2uQCCwIUAGl4eQDBOkcmuqALEjPi1gPz90+XFIiBXxe2aAffGpY5q"
    "IJ9KdbcERa1PswMpv/hZ8DbOu38XcT06uzzUpJBL5QkjxQg4BIzvFhk3QdlW3CNqREScKg"
    "bYuX/AwrVnEk3CKeQX/fnTmnGFH06pMerp+hKvzRYYgR9Ask/kS9YY69dhxBwNDooi6jb1"
    "j73frEZVZWd+gF1f946fG2DGfC1oSWCZGNrd3yzGi3ltpuhY59pZaMgFAt8g4xu0ASuiAH"
    "aTbCDG2ZZHuAyxothHNAAfAZkop7l5y27ZBVfkPTonCusaBGF/T5Ac4R1EJZKKC+IiylBf"
    "ENJTJGgq7Bnfl1vluKAeZdi3DaGiDDOjpOKE3S47YbeXJOz2bMLWsWCD20dVAZpTUH31K7"
    "/8La1/8/GU9N/KAjSnYC08D6n3dHv8S6u1u9tpbe/uH7T3Op32wXbSJ8+ySmqYD3sfdM+c"
    "QztuolOEAxqQicCKEM4pqLrhLTtgW0vitTWnXxNEf4mN127ZcKS4zfjD/+nickrXQvgYuA"
    "r8tBBlUOFeMn88rfqrguxO5TbjP6zMJ9rYzXQRCxzR752ffOp3z//I9X3H3f6J5rQMdVyg"
    "buwXfJYIQX/1+h+RfkSfLy9OiuU+Wdf/XHBsFLrlOXbFvimvs/ZrWX6dbf6f1dClAVHu2B"
    "C3f9Yqc0OyODs4KCDaFKjFyeHG4oN/iKOStDx9hE79rp4qftRUcYglQQx/pR7Wqt+NKHyH"
    "cEZjZJyMHqgaoZD744CLcEQdJIhvVsoRDZHiSIbEgfCEZsZFaaSUOzVUOSy80Izwo0/FCn"
    "uvkrErr6LyoavsmWvJyLUAzULmKR/Lt5BvUtTiI4UlgGVy9SCivqJMNvUxXSFdrwpjrPHn"
    "OmjMYr7CsYAlOFfr4fusM4Ez3T88F+Dlm/usf3VyUo9Lb7etrselt+nXOeNSRZ1qFVPUEf"
    "d94kwNf3qOyixvZCYpJyHX/4R5LeNSOrNnvPNuyH2XCIm2kAYZYeaijH0IC/Jy/2Gpy9sb"
    "SoN1eXubfl16GlheZqmitn0g/ApLRcTK1wvyb2QrnEe4LQyrvmvwSsscuEiQIRGEORBkE2"
    "fFZ9Xg2H7v9LRRWDQ5qF5656CBqLRzb+WEgBV2ACHLgaywgOi1pZCNW6bvDgnu2yHXIIEL"
    "IgaDtd4Vhbex40QQJeOXrb317Yb6dsOrv92QxE+ZwKaVdk6g/mQA19dH6usj9fWRemCsB8"
    "bary8yMK7fo5c7JD7+B+8mC/Q="
)
