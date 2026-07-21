import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app

from .extensions import db
from .models import MfaChallenge, MfaCredential


RECOVERY_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def utcnow():
    return datetime.now(timezone.utc)


def as_utc(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def required_for(user):
    return user.role in set(current_app.config.get("MFA_REQUIRED_ROLES") or [])


def enabled_credential(user_id):
    return MfaCredential.query.filter(
        MfaCredential.user_id == user_id,
        MfaCredential.enabled_at.is_not(None),
    ).first()


def _fernet():
    try:
        return Fernet(current_app.config["MFA_ENCRYPTION_KEY"].encode("ascii"))
    except (KeyError, ValueError, TypeError, UnicodeEncodeError) as error:
        raise RuntimeError("MFA encryption is not configured correctly") from error


def encrypt_secret(secret):
    return _fernet().encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_secret(ciphertext):
    try:
        return _fernet().decrypt(ciphertext.encode("ascii")).decode("ascii")
    except (InvalidToken, ValueError, TypeError, UnicodeEncodeError) as error:
        raise RuntimeError("Stored MFA credential cannot be decrypted") from error


def _normalize_recovery_code(code):
    return "".join(character for character in str(code or "").upper() if character.isalnum())


def _recovery_digest(code):
    normalized = _normalize_recovery_code(code)
    return hmac.new(
        current_app.config["JWT_SECRET_KEY"].encode("utf-8"),
        normalized.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def generate_recovery_codes(count=10):
    codes = []
    for _ in range(count):
        raw = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(12))
        codes.append(f"{raw[:4]}-{raw[4:8]}-{raw[8:]}")
    return codes


def set_recovery_codes(credential, codes):
    credential.recovery_code_hashes = json.dumps([_recovery_digest(code) for code in codes])


def verify_totp(credential, code, consume=True):
    normalized = "".join(character for character in str(code or "") if character.isdigit())
    if len(normalized) != 6:
        return False
    totp = pyotp.TOTP(decrypt_secret(credential.secret_ciphertext))
    current_step = int(utcnow().timestamp()) // totp.interval
    for offset in (-1, 0, 1):
        step = current_step + offset
        expected = totp.at(step * totp.interval)
        if hmac.compare_digest(expected, normalized):
            if credential.last_used_step is not None and step <= credential.last_used_step:
                return False
            if consume:
                credential.last_used_step = step
            return True
    return False


def verify_factor(credential, code):
    if verify_totp(credential, code):
        return "totp"
    supplied_hash = _recovery_digest(code)
    hashes = json.loads(credential.recovery_code_hashes or "[]")
    for index, stored_hash in enumerate(hashes):
        if hmac.compare_digest(stored_hash, supplied_hash):
            hashes.pop(index)
            credential.recovery_code_hashes = json.dumps(hashes)
            return "recovery"
    return None


def begin_setup(user):
    credential = MfaCredential.query.filter_by(user_id=user.id).first()
    if credential is not None and credential.enabled_at is not None:
        raise ValueError("MFA is already enabled")
    secret = pyotp.random_base32()
    if credential is None:
        credential = MfaCredential(user_id=user.id, secret_ciphertext=encrypt_secret(secret))
        db.session.add(credential)
    else:
        credential.secret_ciphertext = encrypt_secret(secret)
        credential.recovery_code_hashes = "[]"
        credential.last_used_step = None
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=current_app.config["MFA_ISSUER"])
    return credential, secret, uri


def issue_challenge(user):
    now = utcnow()
    MfaChallenge.query.filter(
        MfaChallenge.user_id == user.id,
        MfaChallenge.consumed_at.is_(None),
    ).update({MfaChallenge.consumed_at: now}, synchronize_session=False)
    raw_token = secrets.token_urlsafe(48)
    challenge = MfaChallenge(
        user_id=user.id,
        token_hash=digest(raw_token),
        created_at=now,
        expires_at=now + timedelta(minutes=current_app.config["MFA_CHALLENGE_MINUTES"]),
    )
    db.session.add(challenge)
    return challenge, raw_token


def verify_challenge(raw_token, code):
    challenge = MfaChallenge.query.filter_by(token_hash=digest(str(raw_token or ""))).first()
    now = utcnow()
    if (
        challenge is None
        or challenge.consumed_at is not None
        or as_utc(challenge.expires_at) <= now
        or challenge.failed_attempts >= 5
    ):
        return None, None
    credential = enabled_credential(challenge.user_id)
    factor = verify_factor(credential, code) if credential else None
    if factor is None:
        challenge.failed_attempts += 1
        if challenge.failed_attempts >= 5:
            challenge.consumed_at = now
        return challenge, None
    challenge.consumed_at = now
    return challenge, factor
