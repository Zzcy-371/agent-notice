from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    smtp_user: str
    smtp_auth_code: str
    email_to: str
    github_token: str | None = None

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> "Settings":
        for name in ("QQ_SMTP_USER", "QQ_SMTP_AUTH_CODE", "EMAIL_TO"):
            if not environ.get(name):
                raise ValueError(name)
        return cls(
            smtp_user=environ["QQ_SMTP_USER"],
            smtp_auth_code=environ["QQ_SMTP_AUTH_CODE"],
            email_to=environ["EMAIL_TO"],
            github_token=environ.get("GITHUB_TOKEN"),
        )
