# -*- encoding: utf-8 -*-
"""
@File        :sqlite.py
@Time        :2022/12/09 15:08:10
@Author      :Reid
@Version     :1.0
@Desc        :暂时没用, 没有把数据放到sqlite3 中
"""

# here put the import lib

import sqlite3
from sqlite3 import OperationalError


class DB:
    def __init__(self, db_path: str, tb: str, account: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.tb_name = f"{tb}_{account}"
        self.create_nick_account_tb()

    def create_nick_account_tb(self) -> bool:
        sql = f"""
        create table if not exists {self.tb_name}(
            id INTEGER PRIMARY KEY autoincrement,
            nick_name varchar not null,
            account varcahr not null,
            createdate datetime default (datetime('now', 'localtime'))
        )
        """
        ok = self.conn.execute(sql)
        if ok:
            return True
        else:
            return False

    def insert_nick_tb(self, nick_name: str, account: str):
        sql = f"""
            insert into {self.tb_name}(nick_name, account) values 
            ('{nick_name}', '{account}')
        """
        ok = self.conn.execute(sql)
        if ok:
            return True
        else:
            return False

    def execute(self, sql: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(sql)
            print("create table success")
            return True
        except OperationalError as o:
            print(str(o))
            return False
        except Exception as e:
            print(e)
            return False
        finally:
            self.conn.commit()
            cur.close()

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    db_path = "../sql/wechat.db"
    db = DB(db_path, "account", "robot")
    db.insert_nick_tb("昵称", "@111111111")
    db.close()
