from blog_agent.auth import authenticate

def test_simple_authencation():
    # given
    given_secret: str = "TEST_SECRET"
    # when
    is_valid: bool = authenticate(secret=given_secret)
    # then
    assert is_valid is True