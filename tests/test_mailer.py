from agent_notice.config import Settings
from agent_notice.mailer import send_email


class FakeSmtp:
    def __init__(self): self.logged_in = None; self.message = None
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def login(self, user, password): self.logged_in = (user, password)
    def send_message(self, message): self.message = message.as_string()


def test_sends_qq_ssl_message_without_embedding_authorization_code():
    smtp, call = FakeSmtp(), {}
    def factory(host, port): call["address"] = (host, port); return smtp
    settings = Settings("sender@qq.com", "secret-code", "to@example.test")
    send_email(settings, "Subject", "Body", factory)
    assert call["address"] == ("smtp.qq.com", 465)
    assert smtp.logged_in == ("sender@qq.com", "secret-code")
    assert "secret-code" not in smtp.message
