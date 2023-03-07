import os
from datetime import date, timedelta

from config import settings
from src.raiffeisen_rs.api import RaiffeisenRsAPI
from src.utils.csv import write_dict_to_csv
from src.utils.email import SMTP


def main():
    api = RaiffeisenRsAPI(
        username=settings.username,
        password_hash=settings.password_hash,
    )
    api.login()

    if settings.smtp_settings:
        smtp = SMTP(
            username=settings.smtp_settings.username,
            password=settings.smtp_settings.password,
            host=settings.smtp_settings.host,
            port=settings.smtp_settings.port,
            use_tls=settings.smtp_settings.use_tls,
        )
    else:
        smtp = None

    start_date = date.today() - timedelta(days=settings.max_transaction_age_days)
    end_date = date.today()
    account_transaction_groups = api.get_transactions(
        start_date=start_date,
        end_date=end_date,
        group_by_account=True,
    )

    for account_group in account_transaction_groups:
        if not account_group["transactions"]:
            continue

        account = account_group["account"]
        filename = "{from_date}_{to_date}_{account_number}_{account_currency}.csv".format(
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d"),
            account_number=account["number"],
            account_currency=account["currency"],
        )
        file_path = f"{settings.csv_file_dir}/{filename}"
        write_dict_to_csv(
            file_path=file_path,
            data=[x.to_dict() for x in account_group["transactions"]],
        )

        account_id = f"{account['number']}-{account['currency']}"
        wallet_email = settings.wallet_emails.get(account_id)
        if wallet_email and smtp:
            smtp.send(
                to=wallet_email,
                subject=f"Raiffeisen RS transactions for {account_id} from {start_date} to {end_date}",
                attached_file=file_path,
            )

        if not settings.save_to_csv:
            os.remove(file_path)


if __name__ == '__main__':
    main()
