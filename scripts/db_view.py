"""Visualizador simples do banco SQLite do Tubify.

Uso:
    py scripts/db_view.py            # lista todas as tabelas e seus registros
    py scripts/db_view.py users      # mostra só a tabela 'users'
"""
import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tubify.db")


def print_table(cur, table):
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    print(f"\n=== {table} ({len(rows)} registro(s)) ===")
    if not rows:
        print("  (vazio)")
        return
    # Larguras de coluna
    widths = [len(c) for c in cols]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
    widths = [min(w, 45) for w in widths]

    def fmt(values):
        return " | ".join(str(v)[:45].ljust(widths[i]) for i, v in enumerate(values))

    print("  " + fmt(cols))
    print("  " + "-+-".join("-" * w for w in widths))
    for row in rows:
        print("  " + fmt(row))


def main():
    if not os.path.exists(DB_PATH):
        print(f"Banco não encontrado em {DB_PATH}. Rode o app uma vez para criá-lo.")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if len(sys.argv) > 1:
        tables = sys.argv[1:]
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [r[0] for r in cur.fetchall()]
    print(f"Banco: {DB_PATH}")
    for t in tables:
        try:
            print_table(cur, t)
        except sqlite3.OperationalError as e:
            print(f"\n=== {t} ===\n  erro: {e}")
    conn.close()


if __name__ == "__main__":
    main()
