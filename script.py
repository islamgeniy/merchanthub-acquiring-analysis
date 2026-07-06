"""
Экспортирует полную информацию по всем ds_ таблицам academy_db в CSV:
- overview.csv       — таблица / кол-во строк / кол-во колонок
- columns.csv        — таблица / колонка / тип данных / nullable
- sample_<table>.csv — первые 5 строк каждой таблицы

Требуется: pip install sqlalchemy psycopg2-binary pandas
"""

from pathlib import Path

import pandas as pd
try:
    from sqlalchemy import create_engine, text
except ImportError:
    raise SystemExit(
        "Missing dependency: sqlalchemy not found. Install with `pip install sqlalchemy psycopg2-binary pandas`"
    )

# --- параметры подключения: заполни своими значениями ---
DB_HOST = "thomas.proxy.rlwy.net"
DB_PORT = 51432
DB_NAME = "academy_db"
DB_USER = "ixojambetov"
DB_PASSWORD = "Ixojambetov@Db9842"

OUTPUT_DIR = Path("ds_tables_info")
OUTPUT_DIR.mkdir(exist_ok=True)

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

with engine.connect() as conn:
    # 1. список ds_ таблиц
    tables = pd.read_sql(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name ~ '^ds_'
            ORDER BY table_name
        """),
        conn,
    )["table_name"].tolist()

    print(f"Найдено таблиц: {len(tables)}")

    # 2. метаданные колонок сразу по всем таблицам
    columns_df = pd.read_sql(
        text("""
            SELECT table_name, ordinal_position, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name ~ '^ds_'
            ORDER BY table_name, ordinal_position
        """),
        conn,
    )
    columns_df.to_csv(OUTPUT_DIR / "columns.csv", index=False)

    # 3. кол-во строк + образец данных по каждой таблице
    overview_rows = []
    for table in tables:
        row_count = conn.execute(
            text(f'SELECT count(*) FROM public."{table}"')
        ).scalar()

        sample_df = pd.read_sql(
            text(f'SELECT * FROM public."{table}" LIMIT 5'), conn
        )
        sample_df.to_csv(OUTPUT_DIR / f"sample_{table}.csv", index=False)

        overview_rows.append({
            "table_name": table,
            "row_count": row_count,
            "column_count": len(sample_df.columns),
        })
        print(f"  {table}: {row_count} строк, {len(sample_df.columns)} колонок")

    pd.DataFrame(overview_rows).to_csv(OUTPUT_DIR / "overview.csv", index=False)

print(f"\nГотово. Все CSV сохранены в: {OUTPUT_DIR.resolve()}")
