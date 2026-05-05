"""
Test script for migration ae57c33876cc (rename abandoned->stopped, make created_by nullable).

Run inside the fides container:
    python /fides/scripts/test_migration_ae57c33876cc.py

Steps:
  1. Downgrade to parent (d71c7d274c04)
  2. Seed test data — happy path AND edge cases
  3. Upgrade to ae57c33876cc
  4. Verify upgrade transformations
  5. Insert post-upgrade rows (simulates app running after deploy)
  6. Downgrade back to d71c7d274c04
  7. Verify downgrade transformations (including post-upgrade rows)
  8. Re-upgrade to leave DB in correct state
  9. Clean up seed data
"""

import os
import sys
from uuid import uuid4

import sqlalchemy as sa
from alembic import command as alembic_command
from alembic.config import Config

MIGRATION_REV = "ae57c33876cc"
PARENT_REV = "d71c7d274c04"

DB_URL = "postgresql+psycopg2://postgres:fides@fides-db:5432/fides"

SEED_PREFIX = "mig_test_"
RUN_ID = uuid4().hex[:8]

engine = sa.create_engine(DB_URL)

ALEMBIC_DIR = "/fides/src/fides/api/alembic"
os.chdir(ALEMBIC_DIR)
alembic_cfg = Config(os.path.join(ALEMBIC_DIR, "alembic.ini"))


def run_alembic(cmd, rev):
    try:
        if cmd == "upgrade":
            alembic_command.upgrade(alembic_cfg, rev)
        elif cmd == "downgrade":
            alembic_command.downgrade(alembic_cfg, rev)
        else:
            raise ValueError(f"Unknown command: {cmd}")
        print(f"  alembic {cmd} {rev} OK")
    except Exception as e:
        print(f"ALEMBIC {cmd} {rev} FAILED: {e}")
        sys.exit(1)


def seed_id(suffix):
    return f"{SEED_PREFIX}{suffix}_{RUN_ID}"


def insert_version(conn, ids, key, answer_id, created_by, version_num):
    vid = seed_id(f"version_{key}")
    ids[f"version_{key}"] = vid
    conn.execute(
        sa.text(
            "INSERT INTO answer_version "
            "(id, answer_id, version_number, answer_status, answer_source, change_type, created_by, evidence, source_references, created_at, updated_at) "
            "VALUES (:id, :aid, :vnum, 'needs_input', 'system', 'ai_generated', :created_by, '{}', '{}', now(), now())"
        ),
        {"id": vid, "aid": answer_id, "vnum": version_num, "created_by": created_by},
    )


def seed_data(conn):
    """Insert test rows at parent revision (pre-upgrade). Returns IDs for verification."""
    ids = {}

    # --- Scaffold: template -> question -> assessment -> answer ---
    ids["template"] = tid = seed_id("template")
    conn.execute(
        sa.text(
            "INSERT INTO assessment_template "
            "(id, version, name, assessment_type, region, is_active, fides_revision, is_managed, created_at, updated_at) "
            "VALUES (:id, 'v1', 'Migration Test Template', :atype, 'test', true, 1, false, now(), now())"
        ),
        {"id": tid, "atype": f"mig_test_{RUN_ID}"},
    )

    ids["question"] = qid = seed_id("question")
    conn.execute(
        sa.text(
            "INSERT INTO assessment_question "
            "(id, template_id, question_key, question_text, requirement_key, requirement_title, group_order, question_order, created_at, updated_at) "
            "VALUES (:id, :tid, 'test_q1', 'Test question?', 'test_req', 'Test Requirement', 0, 0, now(), now())"
        ),
        {"id": qid, "tid": tid},
    )

    ids["assessment"] = aid = seed_id("assessment")
    conn.execute(
        sa.text(
            "INSERT INTO privacy_assessment "
            "(id, template_id, name, status, completeness, system_fides_key, created_at, updated_at) "
            "VALUES (:id, :tid, 'Migration Test Assessment', 'in_progress', 0.0, 'test_system', now(), now())"
        ),
        {"id": aid, "tid": tid},
    )

    ids["answer"] = ansid = seed_id("answer")
    conn.execute(
        sa.text(
            "INSERT INTO assessment_answer "
            "(id, assessment_id, question_id, created_at, updated_at) "
            "VALUES (:id, :aid, :qid, now(), now())"
        ),
        {"id": ansid, "aid": aid, "qid": qid},
    )

    # --- Questionnaire with 'abandoned' status ---
    ids["questionnaire"] = qnid = seed_id("questionnaire")
    conn.execute(
        sa.text(
            "INSERT INTO questionnaire "
            "(id, assessment_id, title, status, current_question_index, reminder_count, provider_context, created_at, updated_at) "
            "VALUES (:id, :aid, 'Test Questionnaire', 'abandoned', 0, 0, '{}', now(), now())"
        ),
        {"id": qnid, "aid": aid},
    )

    # --- FidesUser WITH email (for username->email backfill) ---
    ids["user_with_email"] = seed_id("user_with_email")
    test_username = f"testuser_{RUN_ID}"
    test_email = f"testuser_{RUN_ID}@example.com"
    conn.execute(
        sa.text(
            "INSERT INTO fidesuser "
            "(id, username, email_address, hashed_password, salt, created_at, updated_at) "
            "VALUES (:id, :username, :email, '$2b$12$fake', 'fakesalt', now(), now())"
        ),
        {"id": ids["user_with_email"], "username": test_username, "email": test_email},
    )

    # --- FidesUser WITHOUT email (edge case #1) ---
    ids["user_no_email"] = seed_id("user_no_email")
    username_no_email = f"noemail_{RUN_ID}"
    conn.execute(
        sa.text(
            "INSERT INTO fidesuser "
            "(id, username, email_address, hashed_password, salt, created_at, updated_at) "
            "VALUES (:id, :username, NULL, '$2b$12$fake', 'fakesalt', now(), now())"
        ),
        {"id": ids["user_no_email"], "username": username_no_email},
    )

    # --- FidesUser with @ in username (edge case #2) ---
    ids["user_at_username"] = seed_id("user_at_username")
    username_with_at = f"admin@corp_{RUN_ID}"
    email_for_at_user = f"admin_corp_{RUN_ID}@example.com"
    conn.execute(
        sa.text(
            "INSERT INTO fidesuser "
            "(id, username, email_address, hashed_password, salt, created_at, updated_at) "
            "VALUES (:id, :username, :email, '$2b$12$fake', 'fakesalt', now(), now())"
        ),
        {
            "id": ids["user_at_username"],
            "username": username_with_at,
            "email": email_for_at_user,
        },
    )

    # --- AnswerVersion rows: happy path ---
    vnum = [0]  # mutable counter

    def next_vnum():
        vnum[0] += 1
        return vnum[0]

    # Sentinels -> NULL
    insert_version(conn, ids, "sentinel_system", ansid, "system", next_vnum())
    insert_version(conn, ids, "sentinel_scheduler", ansid, "scheduler", next_vnum())
    insert_version(conn, ids, "sentinel_unknown", ansid, "unknown", next_vnum())

    # Username with matching user+email -> rewritten to email
    insert_version(conn, ids, "username_match", ansid, test_username, next_vnum())

    # Username with no matching user -> stays as-is
    insert_version(
        conn, ids, "username_no_match", ansid, "nonexistent_user_xyz", next_vnum()
    )

    # Already an email -> stays as-is (LIKE '%@%' guard)
    insert_version(
        conn, ids, "already_email", ansid, "existing@example.com", next_vnum()
    )

    # --- AnswerVersion rows: edge cases ---

    # Edge case #1: FidesUser exists but has NULL email -> username stays as-is
    insert_version(conn, ids, "user_null_email", ansid, username_no_email, next_vnum())

    # Edge case #2: Username contains @ -> LIKE guard skips even though fidesuser match exists
    insert_version(conn, ids, "username_with_at", ansid, username_with_at, next_vnum())

    # Edge case #3: Case-sensitive sentinel ('System' != 'system') -> stays as-is
    insert_version(conn, ids, "sentinel_case_upper", ansid, "System", next_vnum())
    insert_version(conn, ids, "sentinel_case_mixed", ansid, "SCHEDULER", next_vnum())

    # Edge case #4: Empty string -> not a sentinel, no user match, stays as empty string
    insert_version(conn, ids, "empty_string", ansid, "", next_vnum())

    # Edge case #5: Whitespace around sentinel -> not matched
    insert_version(conn, ids, "sentinel_whitespace", ansid, " system ", next_vnum())

    print(f"  Seeded {len(ids)} rows (run_id={RUN_ID})")
    return {
        "ids": ids,
        "test_username": test_username,
        "test_email": test_email,
        "username_no_email": username_no_email,
        "username_with_at": username_with_at,
        "answer_id": ansid,
    }


def insert_post_upgrade_rows(conn, seed_info):
    """Simulate app inserting rows AFTER upgrade (created_by is now nullable)."""
    ids = seed_info["ids"]
    ansid = seed_info["answer_id"]

    # App-inserted row with NULL created_by (valid post-upgrade)
    vid = seed_id("version_post_upgrade_null")
    ids["version_post_upgrade_null"] = vid
    conn.execute(
        sa.text(
            "INSERT INTO answer_version "
            "(id, answer_id, version_number, answer_status, answer_source, change_type, created_by, evidence, source_references, created_at, updated_at) "
            "VALUES (:id, :aid, 100, 'needs_input', 'system', 'ai_generated', NULL, '{}', '{}', now(), now())"
        ),
        {"id": vid, "aid": ansid},
    )

    # App-inserted row with a real email (valid post-upgrade)
    vid2 = seed_id("version_post_upgrade_email")
    ids["version_post_upgrade_email"] = vid2
    conn.execute(
        sa.text(
            "INSERT INTO answer_version "
            "(id, answer_id, version_number, answer_status, answer_source, change_type, created_by, evidence, source_references, created_at, updated_at) "
            "VALUES (:id, :aid, 101, 'needs_input', 'system', 'ai_generated', 'newuser@example.com', '{}', '{}', now(), now())"
        ),
        {"id": vid2, "aid": ansid},
    )

    print("  Inserted 2 post-upgrade rows")


def verify_upgrade(conn, seed_info):
    ids = seed_info["ids"]
    errors = []

    def check(label, row_key, expected):
        row = conn.execute(
            sa.text("SELECT created_by FROM answer_version WHERE id = :id"),
            {"id": ids[row_key]},
        ).fetchone()
        actual = row[0]
        if actual != expected:
            errors.append(f"{label}: expected {expected!r}, got {actual!r}")

    # --- Enum rename ---
    row = conn.execute(
        sa.text("SELECT status FROM questionnaire WHERE id = :id"),
        {"id": ids["questionnaire"]},
    ).fetchone()
    if row[0] != "stopped":
        errors.append(f"Questionnaire status: expected 'stopped', got '{row[0]}'")

    count = conn.execute(
        sa.text("SELECT count(*) FROM questionnaire WHERE status::text = 'abandoned'")
    ).scalar()
    if count > 0:
        errors.append(f"Found {count} questionnaires still with 'abandoned' status")

    # --- Nullable ---
    col_info = conn.execute(
        sa.text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name = 'answer_version' AND column_name = 'created_by'"
        )
    ).fetchone()
    if col_info[0] != "YES":
        errors.append(f"created_by nullable: expected YES, got {col_info[0]}")

    # --- Happy path ---
    check("sentinel_system", "version_sentinel_system", None)
    check("sentinel_scheduler", "version_sentinel_scheduler", None)
    check("sentinel_unknown", "version_sentinel_unknown", None)
    check("username_match", "version_username_match", seed_info["test_email"])
    check("username_no_match", "version_username_no_match", "nonexistent_user_xyz")
    check("already_email", "version_already_email", "existing@example.com")

    # --- Edge cases ---
    check(
        "user_null_email (user exists, email NULL)",
        "version_user_null_email",
        seed_info["username_no_email"],
    )
    check(
        "username_with_at (@ in username, skipped by LIKE guard)",
        "version_username_with_at",
        seed_info["username_with_at"],
    )
    check(
        "sentinel_case_upper ('System' != 'system')",
        "version_sentinel_case_upper",
        "System",
    )
    check(
        "sentinel_case_mixed ('SCHEDULER' != 'scheduler')",
        "version_sentinel_case_mixed",
        "SCHEDULER",
    )
    check("empty_string", "version_empty_string", "")
    check(
        "sentinel_whitespace (' system ' != 'system')",
        "version_sentinel_whitespace",
        " system ",
    )

    return errors


def verify_downgrade(conn, seed_info):
    ids = seed_info["ids"]
    errors = []

    def check(label, row_key, expected):
        row = conn.execute(
            sa.text("SELECT created_by FROM answer_version WHERE id = :id"),
            {"id": ids[row_key]},
        ).fetchone()
        actual = row[0]
        if actual != expected:
            errors.append(f"{label}: expected {expected!r}, got {actual!r}")

    # --- Enum rename back ---
    row = conn.execute(
        sa.text("SELECT status FROM questionnaire WHERE id = :id"),
        {"id": ids["questionnaire"]},
    ).fetchone()
    if row[0] != "abandoned":
        errors.append(f"Questionnaire status: expected 'abandoned', got '{row[0]}'")

    # --- NOT NULL restored ---
    col_info = conn.execute(
        sa.text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name = 'answer_version' AND column_name = 'created_by'"
        )
    ).fetchone()
    if col_info[0] != "NO":
        errors.append(f"created_by nullable: expected NO, got {col_info[0]}")

    # --- Sentinels: were NULL, now 'system' ---
    check("sentinel_system downgrade", "version_sentinel_system", "system")
    check("sentinel_scheduler downgrade", "version_sentinel_scheduler", "system")
    check("sentinel_unknown downgrade", "version_sentinel_unknown", "system")

    # --- Username->email is NOT reversed (lossy) ---
    check(
        "username_match downgrade (email kept)",
        "version_username_match",
        seed_info["test_email"],
    )

    # --- Unchanged values survive round-trip ---
    check(
        "username_no_match downgrade",
        "version_username_no_match",
        "nonexistent_user_xyz",
    )
    check("already_email downgrade", "version_already_email", "existing@example.com")

    # --- Edge cases survive round-trip ---
    check(
        "user_null_email downgrade",
        "version_user_null_email",
        seed_info["username_no_email"],
    )
    check(
        "username_with_at downgrade",
        "version_username_with_at",
        seed_info["username_with_at"],
    )
    check(
        "sentinel_case_upper downgrade (not nullified, so not touched)",
        "version_sentinel_case_upper",
        "System",
    )
    check("sentinel_case_mixed downgrade", "version_sentinel_case_mixed", "SCHEDULER")
    check("empty_string downgrade", "version_empty_string", "")
    check("sentinel_whitespace downgrade", "version_sentinel_whitespace", " system ")

    # --- Post-upgrade rows ---
    # NULL inserted after upgrade -> 'system' after downgrade
    check(
        "post_upgrade_null downgrade (NULL -> 'system')",
        "version_post_upgrade_null",
        "system",
    )
    # Email inserted after upgrade -> unchanged
    check(
        "post_upgrade_email downgrade",
        "version_post_upgrade_email",
        "newuser@example.com",
    )

    return errors


def cleanup(conn, seed_info):
    ids = seed_info["ids"]
    for key in list(ids.keys()):
        if key.startswith("version_"):
            conn.execute(
                sa.text("DELETE FROM answer_version WHERE id = :id"), {"id": ids[key]}
            )
    conn.execute(
        sa.text("DELETE FROM assessment_answer WHERE id = :id"), {"id": ids["answer"]}
    )
    conn.execute(
        sa.text("DELETE FROM questionnaire WHERE id = :id"),
        {"id": ids["questionnaire"]},
    )
    conn.execute(
        sa.text("DELETE FROM privacy_assessment WHERE id = :id"),
        {"id": ids["assessment"]},
    )
    conn.execute(
        sa.text("DELETE FROM assessment_question WHERE id = :id"),
        {"id": ids["question"]},
    )
    conn.execute(
        sa.text("DELETE FROM assessment_template WHERE id = :id"),
        {"id": ids["template"]},
    )
    conn.execute(
        sa.text("DELETE FROM fidesuser WHERE id = :id"), {"id": ids["user_with_email"]}
    )
    conn.execute(
        sa.text("DELETE FROM fidesuser WHERE id = :id"), {"id": ids["user_no_email"]}
    )
    conn.execute(
        sa.text("DELETE FROM fidesuser WHERE id = :id"), {"id": ids["user_at_username"]}
    )
    print("  Cleanup complete")


def main():
    print("=" * 60)
    print("Migration test: ae57c33876cc")
    print("  abandoned->stopped rename + created_by nullable backfill")
    print(f"  run_id={RUN_ID}")
    print("=" * 60)

    # Step 1: Downgrade to parent
    print("\n[1/9] Downgrade to parent revision...")
    run_alembic("downgrade", PARENT_REV)

    # Step 2: Seed data (at parent revision, pre-upgrade state)
    print("\n[2/9] Seeding test data...")
    with engine.connect() as conn:
        seed_info = seed_data(conn)

    # Step 3: Upgrade
    print("\n[3/9] Upgrading to target revision...")
    run_alembic("upgrade", MIGRATION_REV)

    # Step 4: Verify upgrade
    print("\n[4/9] Verifying upgrade...")
    with engine.connect() as conn:
        upgrade_errors = verify_upgrade(conn, seed_info)
    if upgrade_errors:
        print("  UPGRADE FAILURES:")
        for e in upgrade_errors:
            print(f"    x {e}")
    else:
        print("  OK - All upgrade checks passed")

    # Step 5: Insert post-upgrade rows (simulates app running after deploy)
    print("\n[5/9] Inserting post-upgrade rows...")
    with engine.connect() as conn:
        insert_post_upgrade_rows(conn, seed_info)

    # Step 6: Downgrade
    print("\n[6/9] Downgrading back to parent...")
    run_alembic("downgrade", PARENT_REV)

    # Step 7: Verify downgrade (including post-upgrade rows)
    print("\n[7/9] Verifying downgrade...")
    with engine.connect() as conn:
        downgrade_errors = verify_downgrade(conn, seed_info)
    if downgrade_errors:
        print("  DOWNGRADE FAILURES:")
        for e in downgrade_errors:
            print(f"    x {e}")
    else:
        print("  OK - All downgrade checks passed")

    # Step 8: Re-upgrade to leave DB in correct final state
    print("\n[8/9] Re-upgrading to leave DB at head...")
    run_alembic("upgrade", MIGRATION_REV)

    # Step 9: Cleanup
    print("\n[9/9] Cleaning up seed data...")
    with engine.connect() as conn:
        cleanup(conn, seed_info)

    # Summary
    print("\n" + "=" * 60)
    all_errors = upgrade_errors + downgrade_errors
    if all_errors:
        print(f"RESULT: {len(all_errors)} FAILURE(S)")
        for e in all_errors:
            print(f"  x {e}")
        sys.exit(1)
    else:
        print("RESULT: ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
