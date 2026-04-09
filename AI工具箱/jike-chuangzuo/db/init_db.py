#!/usr/bin/env python3
"""初始化 jike-chuangzuo SQLite 数据库"""
import sqlite3, pathlib, sys

SCHEMA_PATH = pathlib.Path(__file__).parent / "schema.sql"
DB_PATH = pathlib.Path(__file__).parent / "jike.db"

def init():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
    conn.close()
    print(f"DB initialized: {DB_PATH}")

if __name__ == "__main__":
    init()
