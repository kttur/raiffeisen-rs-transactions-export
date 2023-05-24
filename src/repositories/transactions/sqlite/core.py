import pandas as pd
from pandas.errors import DatabaseError
from sqlite3 import connect

from src.repositories.transactions.base import BaseTransactionRepository


class SQLite(BaseTransactionRepository):
    def __init__(
            self,
            db_path: str,
            transaction_table_name: str = 'transactions',
    ):
        self.db_path = db_path
        self.transaction_table_name = transaction_table_name
        self.connection = None

    def __enter__(self):
        self.connection = connect(self.db_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.commit()
        self.connection.close()

    def get_connection(self):
        if not self.connection:
            self.connection = connect(self.db_path)
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()

    def find(
            self,
            account_id: str | None = None,
            transaction_ids: list[str] | None = None,
            currency: str | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
    ) -> pd.DataFrame:
        query = f"SELECT * FROM {self.transaction_table_name}"
        where = []
        if account_id:
            where.append(f"account = '{account_id}'")
        if transaction_ids:
            where.append(f"id IN {tuple(transaction_ids)}") \
                if len(transaction_ids) > 1 \
                else where.append(f"id = '{transaction_ids[0]}'")
        if currency:
            where.append(f"currency = '{currency}'")
        if start_date:
            where.append(f"datetime >= '{start_date}'")
        if end_date:
            where.append(f"datetime <= '{end_date}'")
        if where:
            query += f" WHERE {' AND '.join(where)}"
        try:
            df = pd.read_sql_query(query, self.get_connection())
        except DatabaseError:
            df = pd.DataFrame()
        return df

    def add(self, transactions: pd.DataFrame):
        transactions.to_sql(
            self.transaction_table_name,
            self.get_connection(),
            if_exists='append',
            index=False,
        )
