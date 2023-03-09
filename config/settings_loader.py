from argparse import ArgumentParser
from dataclasses import dataclass, field
from os import environ


@dataclass
class SMTPSettings:
    host: str
    port: int
    username: str
    password: str = field(repr=False)
    use_tls: bool


@dataclass
class Settings:
    username: str
    password_hash: str = field(repr=False)
    max_transaction_age_days: int
    min_transaction_age_days: int
    only_new: bool
    db_file: str | None
    save_to_csv: bool
    csv_file_dir: str
    wallet_emails: dict[str, str]
    smtp_settings: SMTPSettings | None
    log_level: str = "INFO"


def get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="raiffeisen_rs_wallet_exporter",
        description="Export Raiffeisen RS transactions to Wallet or CSV file.",
    )
    parser.add_argument('-u', '--username', help="Raiffeisen RS username.")
    parser.add_argument('-p', '--password', help="Raiffeisen RS password hash.")
    parser.add_argument('-d', '--days', help="Max transaction age in days.")
    parser.add_argument('-s', '--skip-days', help="Skip transactions younger than X days.")
    parser.add_argument('-n', '--new', help="Export only new transactions.")
    parser.add_argument('-b', '--db', help="Database file.")
    parser.add_argument('-c', '--csv', help="Save transactions to CSV file.")
    parser.add_argument('--path', help="CSV file directory.")
    parser.add_argument(
        '-e', '--email',
        action='append',
        help="Wallet email. Format: 'raiffeisen_account_number:wallet_email'. You can use multiple -e arguments.")
    parser.add_argument('-f', '--file', help="Wallet email file.")
    parser.add_argument('--smtp-host', help="SMTP host.")
    parser.add_argument('--smtp-port', help="SMTP port.")
    parser.add_argument('--smtp-username', help="SMTP username.")
    parser.add_argument('--smtp-password', help="SMTP password.")
    parser.add_argument('--smtp-use-tls', help="SMTP use TLS.")
    parser.add_argument('--log-level', help="Log level.")
    return parser


def load_settings() -> Settings:
    parser = get_parser()
    args = parser.parse_args()

    log_level = (
        args.log_level
        if args.log_level is not None
        else environ.get("LOG_LEVEL", "INFO")
    )

    username = args.username or environ.get("USERNAME")
    password_hash = args.password or environ.get("PASSWORD_HASH")
    max_transaction_age_days = (
        args.days
        if args.days is not None
        else int(environ.get("MAX_TRANSACTION_AGE_DAYS", 1))
    )
    min_transaction_age_days = (
        args.skip_days
        if args.skip_days is not None
        else int(environ.get("MIN_TRANSACTION_AGE_DAYS", 0))
    )
    only_new = (
        bool(args.new)
        if args.new is not None
        else bool(environ.get("ONLY_NEW", False))
    )
    db_file = args.db or environ.get("DB_FILE", "db.sqlite")
    save_to_csv = (
            args.csv
            if args.csv is not None
            else bool(environ.get("SAVE_TO_CSV", False))
    )
    csv_file_dir = args.path or environ.get("CSV_FILE_DIR", ".")
    wallet_email_file = args.file or environ.get("WALLET_EMAIL_FILE")
    wallet_emails = args.email or environ.get("WALLET_EMAILS").split(',') if environ.get("WALLET_EMAILS") else []
    smtp_host = args.smtp_host or environ.get("SMTP_HOST")
    smtp_port = args.smtp_port or int(environ.get("SMTP_PORT", 587))
    smtp_username = args.smtp_username or environ.get("SMTP_USERNAME")
    smtp_password = args.smtp_password or environ.get("SMTP_PASSWORD")
    smtp_use_tls = (
        bool(args.smtp_use_tls)
        if args.smtp_use_tls is not None
        else bool(environ.get("SMTP_USE_TLS", True))
    )

    if not username:
        raise ValueError("Username is required.")

    if not password_hash:
        raise ValueError("Password hash is required.")

    emails = {}

    if wallet_email_file:
        with open(wallet_email_file, 'r') as f:
            for line in f:
                emails[line.split(':')[0]] = line.split(':')[1]

    for wallet_email in wallet_emails:
        account_number, email = wallet_email.split(':')
        emails[account_number] = email

    if emails:
        if not smtp_host:
            raise ValueError("SMTP host is required.")

        if not smtp_port:
            raise ValueError("SMTP port is required.")

        if not smtp_username:
            raise ValueError("SMTP username is required.")

        if not smtp_password:
            raise ValueError("SMTP password is required.")

        smtp_settings = SMTPSettings(
            host=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=smtp_use_tls,
        )
    else:
        smtp_settings = None

    if not emails and not save_to_csv:
        raise ValueError("Either wallet emails or save to CSV must be set.")

    return Settings(
        username=username,
        password_hash=password_hash,
        max_transaction_age_days=max_transaction_age_days,
        min_transaction_age_days=min_transaction_age_days,
        only_new=only_new,
        db_file=db_file,
        save_to_csv=save_to_csv,
        csv_file_dir=csv_file_dir,
        wallet_emails=emails,
        smtp_settings=smtp_settings,
        log_level=log_level,
    )
