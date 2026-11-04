"""Partner API keys for the finance agent endpoint.

Keys are issued per partner team and stored hashed in the secrets volume; this module only
compares hashes.
"""

import hashlib
import hmac
import json
import os

from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError, SimpleUser

KEYS_FILE = os.environ.get("INSIGHTS_PARTNER_KEYS", "/run/secrets/insights-partner-keys.json")


def _known_hashes() -> dict[str, str]:
    with open(KEYS_FILE, encoding="utf-8") as fh:
        return json.load(fh)


class PartnerKeyBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        presented = conn.headers.get("x-partner-key", "")
        digest = hashlib.sha256(presented.encode()).hexdigest()
        for team, known in _known_hashes().items():
            if hmac.compare_digest(digest, known):
                return AuthCredentials(["partner"]), SimpleUser(team)
        raise AuthenticationError("unknown partner key")
