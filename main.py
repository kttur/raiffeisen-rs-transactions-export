import os
from datetime import date, timedelta

from config import settings
from src.raiffeisen_rs.api import RaiffeisenRsAPI
from src.utils.csv import write_dict_to_csv
from src.utils.email import SMTP
from src.utils.logger import get_logger

logger = get_logger(__name__, settings.log_level)


def main():
    logger.info("Starting export from Raiffeisen.rs to CSV")
    logger.debug(f"Settings: {settings}")
    api = RaiffeisenRsAPI(
        username=settings.username,
        password_hash=settings.password_hash,
    )

    if settings.smtp_settings:
        smtp = SMTP(
            username=settings.smtp_settings.username,
            password=settings.smtp_settings.password,
            host=settings.smtp_settings.host,
            port=settings.smtp_settings.port,
            use_tls=settings.smtp_settings.use_tls,
        )
        logger.info("SMTP client configured, CSV files will be sent via email")
    else:
        smtp = None
        logger.info("SMTP client is not configured, CSV files will not be sent via email")

    if settings.save_to_csv:
        logger.info(f"CSV files will be saved to {settings.csv_file_dir}")

    logger.debug(f"Logging in to Raiffeisen.rs API as {settings.username}")
    api.login()

    start_date = date.today() - timedelta(days=settings.max_transaction_age_days)
    end_date = date.today() - timedelta(days=settings.min_transaction_age_days)
    logger.info(f"Getting transactions from {start_date} to {end_date}")
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
        account_id = f"{account['number']}-{account['currency']}"
        logger.debug(f"Writing CSV file with transactions for {account_id} to {file_path}")
        write_dict_to_csv(
            file_path=file_path,
            data=[x.to_dict() for x in account_group["transactions"]],
        )

        wallet_email = settings.wallet_emails.get(account_id)
        if wallet_email and smtp:
            logger.debug(f"Sending CSV file with transactions for {account_id} via email to {wallet_email}")
            smtp.send(
                to=wallet_email,
                subject=f"Raiffeisen RS transactions for {account_id} from {start_date} to {end_date}",
                attached_file=file_path,
            )
            logger.info(f"Sent CSV file with transactions for {account_id} via email to {wallet_email}")

        if not settings.save_to_csv:
            logger.debug(f"Deleting CSV file with transactions for {account_id}")
            os.remove(file_path)
        else:
            logger.info(f"Saved CSV file with transactions for {account_id} to {file_path}")


if __name__ == '__main__':
    main()
