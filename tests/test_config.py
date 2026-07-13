import pytest

from agent_notice.config import Settings


def test_settings_requires_qq_authorization_code():
    with pytest.raises(ValueError, match="QQ_SMTP_AUTH_CODE"):
        Settings.from_env({"QQ_SMTP_USER": "a@qq.com", "EMAIL_TO": "b@test.com"})
