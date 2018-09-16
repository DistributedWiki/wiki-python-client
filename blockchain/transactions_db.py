import os
import sqlite3

from common.utils import get_prefix_path


class TransactionsDB:
    def __init__(self, name):
        self.path = os.path.join(get_prefix_path(), name)

    def init_db(self):
        db = sqlite3.connect(self.path)
        c = db.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS transactions "
            "(hash text, description text, nonce integer, status text)")
        db.commit()

        return db

    def get_pending_tx(self):
        db = self.init_db()

        res = db\
            .execute("SELECT hash FROM transactions WHERE status = 'pending'")\
            .fetchall()

        db.close()
        return res

    def update_pending_tx(self, data):
        db = self.init_db()
        c = db.cursor()

        c.executemany("UPDATE transactions SET status = ? WHERE hash = ?", data)

        db.commit()
        count = c.rowcount
        db.close()

        return count

    def number_of_pending_tx(self):
        db = self.init_db()
        c = db.cursor()

        c.execute("SELECT count(*) FROM transactions WHERE status = 'pending'")

        count = c.fetchone()[0]
        db.close()

        return count

    def get_tx_list(self, number):
        db = self.init_db()
        tx_list = []
        c = db.cursor()
        tx_n = c.execute(
            "SELECT description, status FROM transactions "
            "ORDER BY nonce DESC LIMIT ?", (number,))

        for tx in tx_n:
            tx_list.append({'description': tx[0], 'status': tx[1]})

        db.close()

        return tx_list

    def add_transaction(self, hash, description, status, nonce):
        db = self.init_db()
        db.execute("INSERT INTO transactions VALUES (?, ?, ?, ?)",
                   (hash, description, nonce, status))
        db.commit()
        db.close()
