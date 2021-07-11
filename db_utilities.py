import sqlite3 as sql

def create_table():
    try:
        sql.create_connection("cantocards.db")
    except Exception:
        pass
    
    with sql.connect("cantocards.db") as conn:
        cur = conn.cursor()
        cur.execute(
            """
            create table if not exists vocabulary (
                id bigserial primary key,
                taishanese text,
                mandarin text,
                english text,
                audio text
            )
            """
        )

if __name__ == '__main__':
    ...