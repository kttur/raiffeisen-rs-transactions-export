import os
from datetime import date, timedelta

from config import settings
from src.raiffeisen_rs.api import RaiffeisenRsAPI
from src.repositories.transactions.sqlite.core import SQLite
from src.utils.email import SMTP
from src.utils.logger import get_logger

logger = get_logger(__name__, settings.log_level)


def main():
    logger.info("Starting export from Raiffeisen.rs")
    logger.debug(f"Settings: {settings}")

    api = RaiffeisenRsAPI(
        username=settings.username,
        password_hash=settings.password_hash,
    )

    start_date = date.today() - timedelta(days=settings.max_transaction_age_days)
    end_date = date.today() - timedelta(days=settings.min_transaction_age_days)

    logger.info(f"Exporting transactions from {start_date} to {end_date}")

    if settings.save_to_csv:
        logger.info(f"CSV files will be saved to {settings.csv_file_dir}")

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

    if settings.only_new:
        logger.info("Only new transactions will be exported")
        logger.debug(f"Connecting to database {settings.db_file}")
        db = SQLite(settings.db_file)
    else:
        logger.info("All transactions will be exported")
        db = None

    try:
        logger.debug(f"Logging in to Raiffeisen.rs API as {settings.username}")
        api.login()
        logger.info(f"Getting transactions...")
        account_transactions_groups = api.get_transactions(
            start_date=start_date,
            end_date=end_date,
        )

        for account_transactions in account_transactions_groups:
            if not account_transactions.transactions:
                continue

            account = account_transactions.account
            transactions = account_transactions.to_df()

            if settings.only_new:
                transaction_ids = transactions["id"].tolist()
                logger.debug(f"Getting transactions from database for {account.number}-{account.currency}")
                db_transactions = db.find(
                    account_id=account.number,
                    transaction_ids=transaction_ids,
                )
                if not db_transactions.empty:
                    transactions = transactions[~transactions["id"].isin(db_transactions["id"].tolist())]
                    if transactions.empty:
                        logger.debug(f"No new transactions for {account.number}-{account.currency}")
                        continue

            filename = "{from_date}_{to_date}_{account_number}_{account_currency}.csv".format(
                from_date=start_date.strftime("%Y-%m-%d"),
                to_date=end_date.strftime("%Y-%m-%d"),
                account_number=account.number,
                account_currency=account.currency,
            )
            file_path = f"{settings.csv_file_dir}/{filename}"
            account_id = f"{account.number}-{account.currency}"
            logger.debug(f"Writing CSV file with transactions for {account_id} to {file_path}")
            transactions.to_csv(file_path, index=False)

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

            if settings.only_new:
                logger.debug(f"Saving transactions to database for {account_id}")
                db.add(transactions)
    finally:
        if db:
            logger.debug(f"Closing database connection")
            db.close()

    logger.info("Finished export from Raiffeisen.rs")


if __name__ == '__main__':
    main()
