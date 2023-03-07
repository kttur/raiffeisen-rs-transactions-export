import requests
from dataclasses import dataclass

from raiffeisen_rs.utils import decode_response, parse_date


@dataclass
class Transaction:
    currency_code: str
    currency: str
    datetime: str
    title: str
    debit: float
    credit: float
    additional_info: str
    transaction_type: str
    description: str

    def to_dict(self):
        return self.__dict__


@dataclass
class RSDTransaction(Transaction):
    balance: str

    @classmethod
    def from_list(cls, transaction):
        kwargs = {
            'currency_code': transaction[1],
            'currency': transaction[2],
            'datetime': transaction[3],
            'title': transaction[5],
            'debit': transaction[7],
            'credit': transaction[8],
            'balance': transaction[9],
            'additional_info': transaction[10],
            'transaction_type': transaction[12],
            'description': transaction[13],
        }
        return cls(**kwargs)


@dataclass
class EURTransaction(Transaction):
    card_number: str

    @classmethod
    def from_list(cls, transaction):
        kwargs = {
            'currency_code': transaction[1],
            'currency': transaction[2],
            'datetime': transaction[3],
            'card_number': transaction[5],
            'title': transaction[6],
            'debit': transaction[8],
            'credit': transaction[9],
            'additional_info': transaction[11],
            'transaction_type': transaction[13],
            'description': transaction[14],
        }
        return cls(**kwargs)


@dataclass
class USDTransaction(Transaction):
    card_number: str

    @classmethod
    def from_list(cls, transaction):
        kwargs = {
            'currency_code': transaction[1],
            'currency': transaction[2],
            'datetime': transaction[3],
            'card_number': transaction[5],
            'title': transaction[6],
            'debit': transaction[8],
            'credit': transaction[9],
            'additional_info': transaction[11],
            'transaction_type': transaction[13],
            'description': transaction[14],
        }
        return cls(**kwargs)


class TransactionFactory:
    @classmethod
    def from_list(cls, transaction):
        match transaction[2]:
            case 'RSD':
                return RSDTransaction.from_list(transaction)
            case 'EUR':
                return EURTransaction.from_list(transaction)
            case 'USD':
                return USDTransaction.from_list(transaction)


class Account:
    """Account class."""

    def __init__(self, api_obj, number, currency, currency_code, product_core_id):
        self.api_obj = api_obj
        self.number = number
        self.currency = currency
        self.currency_code = currency_code
        self.product_core_id = product_core_id

    def __repr__(self):
        return f'Account({self.number}, {self.currency})'

    def to_dict(self):
        return {
            'number': self.number,
            'currency': self.currency,
            'currency_code': self.currency_code,
            'product_core_id': self.product_core_id,
        }

    def get_transactions(
            self,
            start_date=None,
            end_date=None,
            from_amount=None,
            to_amount=None,
    ) -> list[Transaction]:
        """
        Get account transactions.
        Args:
            start_date (str | int | datetime | date): Start date. Default is None. Supported format is %d.%m.%Y or ISO format.
            end_date (str | int | datetime | date): End date. Default is None. Supported format is %d.%m.%Y or ISO format.
            from_amount (float): Filter transactions by min amount. Default is None.
            to_amount (float): Filter transactions by max amount. Default is None.
        Returns:
            list[Transaction]: List of transactions.
        """

        self.api_obj.session.headers['Referer'] = 'https://rol.raiffeisenbank.rs/Retail/user/accounts'
        filters = {
            'CurrencyCodeNumeric': self.currency_code,
            'FromDate': parse_date(start_date),
            'ToDate': parse_date(end_date),
            'FromAmount': from_amount,
            'ToAmount': to_amount,
        }

        response = self.api_obj.session.post(
            'https://rol.raiffeisenbank.rs/Retail/Protected/Services/DataService.svc/GetTransactionalAccountTurnover',
            json={
                'accountNumber': self.number,
                'productCoreID': self.product_core_id,
                'filterParam': filters,
                'gridName': 'RetailAccountTurnoverTransactionDomesticPreviewMasterDetail-S',
            }
        )
        response.raise_for_status()
        data = decode_response(response)
        return [
            TransactionFactory.from_list(transaction)
            for transaction in data[0][1]
        ] if data and len(data[0]) > 1 else []


class RaiffeisenRsAPI:
    """Raiffeisen.rs Online Banking API."""

    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash
        self.accounts = []
        self.request_token = None
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) '
                          'Gecko/20100101 Firefox/110.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://rol.raiffeisenbank.rs',
            'Host': 'rol.raiffeisenbank.rs',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json; charset=utf-8',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Holos-Session': '1',
            'X-Requested-With': 'XMLHttpRequest',
        }

    def login(self):
        """Login to Raiffeisen.rs Online Banking."""

        self.session.headers['Referer'] = 'https://rol.raiffeisenbank.rs/Retail/Home/Login'
        response = self.session.post(
            'https://rol.raiffeisenbank.rs/Retail/Protected/Services/RetailLoginService.svc/LoginFont',
            json={
                'username': self.username,
                'password': self.password_hash,
                'sessionID': 1,
            }
        )
        response.raise_for_status()
        data = decode_response(response)
        self.request_token = data['RequestToken']
        self.session.headers['X-Holos-RequestToken'] = self.request_token

    def get_accounts(self) -> list[dict]:
        """
        Get accounts from server.
        Returns:
            list[dict]: List of accounts.
        """

        self.session.headers['Referer'] = 'https://rol.raiffeisenbank.rs/Retail/user/accounts'
        response = self.session.post(
            'https://rol.raiffeisenbank.rs/Retail/Protected/Services/DataService.svc/GetAllAccountBalance',
            json={
                'gridName': 'RetailAccountBalancePreviewFlat-L',
            }
        )
        response.raise_for_status()
        data = decode_response(response)
        accounts = [
            {
                "number": item[1],
                "currency": item[3],
                "currency_code": item[14],
                "product_core_id": item[13],
            }
            for item in data
        ]
        return accounts

    def update_accounts(self):
        """
        Update accounts from server.
        """

        accounts = self.get_accounts()
        self.accounts = [
            Account(
                self,
                number=account['number'],
                currency=account['currency'],
                currency_code=account['currency_code'],
                product_core_id=account['product_core_id'],
            )
            for account in accounts
        ]

    def get_transactions(
            self,
            start_date=None,
            end_date=None,
            from_amount=None,
            to_amount=None,
            group_by_account=True,
    ) -> list[Transaction | dict[dict, list[Transaction]]]:
        """
        Get transactions from all accounts.
        Args:
            start_date (str | int | datetime | date): Start date. Default is None. Supported format is %d.%m.%Y or ISO format.
            end_date (str | int | datetime | date): End date. Default is None. Supported format is %d.%m.%Y or ISO format.
            from_amount (float): Filter transactions by min amount. Default is None.
            to_amount (float): Filter transactions by max amount. Default is None.
            group_by_account (bool): Group transactions by account. Default is True.
        Returns:
            list[Transaction | dict[dict, list[Transaction]]]: List of transactions if group_by_account is False
            or list of dicts with account data and transactions if group_by_account is True.
        """

        if not self.accounts:
            self.update_accounts()

        transactions = []
        for account in self.accounts:
            account_transactions = account.get_transactions(
                start_date=start_date,
                end_date=end_date,
                from_amount=from_amount,
                to_amount=to_amount,
            )

            if group_by_account:
                transactions.append({
                    'account': account.to_dict(),
                    'transactions': account_transactions
                })
            else:
                transactions.extend(account_transactions)

        return transactions
