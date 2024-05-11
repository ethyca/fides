import argparse
import time

from loguru import logger

from fides.api.db.session import get_db_session
from fides.config import CONFIG

BATCH_SIZE = 100000
SLEEP_DURATION = 10


def update_privacy_preference_history_for_2_27_x():
    start = time.time()
    logger.info("Starting Privacy Preference History Data Manual Migration for 2.27.x")
    SessionLocal = get_db_session(CONFIG)
    db = SessionLocal()

    while True:
        res = db.execute(
            """
            SELECT id 
            FROM privacypreferencehistory 
            WHERE preference IS NULL
            LIMIT 1
        """
        )

        if not res.first():
            logger.info(
                "Privacy Preference History 2.7.x Manual Data Migration Complete"
            )
            break

        db.execute(
            """
            UPDATE privacypreferencehistory
            SET 
                preference = CAST(preference_old_column AS varchar),
                notice_name = privacynoticehistory.name,
                notice_key = privacynoticehistory.notice_key,
                notice_mechanism = privacynoticehistory.consent_mechanism
            FROM privacynoticehistory
            WHERE privacypreferencehistory.privacy_notice_history_id = privacynoticehistory.id
            AND privacypreferencehistory.id IN (
                SELECT id
                FROM privacypreferencehistory
                WHERE privacypreferencehistory.preference IS NULL
                LIMIT :limit
            );
        """,
            {"limit": BATCH_SIZE},
        )
        db.commit()
        logger.info(
            f"Privacy preference batch <= {BATCH_SIZE} committed. Sleeping for {SLEEP_DURATION} s"
        )
        time.sleep(SLEEP_DURATION)

    end = time.time()
    logger.info(f"Total elapsed time {end-start} s")

    db.close()


def update_served_notice_history_for_2_27_x():
    start = time.time()
    logger.info("Starting Served Notice History Data Manual Migration for 2.27.x")
    SessionLocal = get_db_session(CONFIG)
    db = SessionLocal()

    while True:
        res = db.execute(
            """
            SELECT id 
            FROM servednoticehistory 
            WHERE privacy_notice_history_id IS NOT NULL 
            AND notice_name IS NULL
            LIMIT 1
        """
        )

        if not res.first():
            logger.info("Served Notice History 2.7.x Manual Data Migration Complete")
            break

        db.execute(
            """
            UPDATE servednoticehistory
            SET 
                notice_name = privacynoticehistory.name,
                notice_key = privacynoticehistory.notice_key,
                notice_mechanism = privacynoticehistory.consent_mechanism,
                served_notice_history_id = servednoticehistory.id
            FROM privacynoticehistory
            WHERE servednoticehistory.privacy_notice_history_id = privacynoticehistory.id  
            AND servednoticehistory.id IN (
                SELECT id
                FROM servednoticehistory
                WHERE servednoticehistory.notice_name IS NULL
                AND privacy_notice_history_id IS NOT NULL 
                LIMIT :limit
            );
        """,
            {"limit": BATCH_SIZE},
        )
        db.commit()
        logger.info(
            f"Served Notice History batch <= {BATCH_SIZE} committed. Sleeping for {SLEEP_DURATION} s"
        )
        time.sleep(SLEEP_DURATION)

    end = time.time()
    logger.info(f"Total elapsed time {end-start} s")

    db.close()


if __name__ == "__main__":
    """Script for manually migrating Privacy Preference History and Served Notice History for 2.27.x"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-table", type=str)
    parsed_args = parser.parse_args()

    if parsed_args.table == "privacypreferencehistory":
        update_privacy_preference_history_for_2_27_x()

    elif parsed_args.table == "servednoticehistory":
        update_served_notice_history_for_2_27_x()

    else:
        raise Exception("table value not supported")


# Follow-ups:
# Make privacypreferencehistory.preference non-nullable
# Remove privacypreferencehistory.preference_old_column


"""
ALTER TABLE privacypreferencehistory DROP COLUMN preference_old_column;

Downtime for this one?
ALTER privacypreferencehistory ALTER COLUMN preference SET NOT NULL;
"""
