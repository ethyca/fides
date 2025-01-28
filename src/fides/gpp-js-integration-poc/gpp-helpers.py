import subprocess

from fides.api.db.base import *
from fides.api.models.privacy_experience import PrivacyExperience
from fides.api.api.deps import get_db_contextmanager as get_db


def run_gpp_poc():
    print("RUNNING NODE POC...")

    with get_db() as db:
        privacy_experience = db.query(PrivacyExperience).first()
        print("PRIVACY EXPERIENCE: ", privacy_experience)

    result = subprocess.run(["npm", "run", "poc"], stdout=subprocess.PIPE)
    print("NODE POC FINISHED: ", result)
    print("STDOUT: ", result.stdout)


if __name__ == "__main__":
    run_gpp_poc()
