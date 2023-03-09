from abc import ABC, abstractmethod

from pandas import DataFrame


class BaseTransactionRepository(ABC):
    @abstractmethod
    def find(
            self,
            account_id: str | None = None,
            transaction_ids: list[str] | None = None,
            currency: str | None = None,
            start_date: str | None = None,
            end_date: str | None = None,
    ) -> DataFrame:
        pass

    @abstractmethod
    def add(self, transactions: DataFrame):
        pass
