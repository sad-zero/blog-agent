import pytest

from blog_agent.agent import write_hashtags, write_post


def test_write_post():
    # given
    title = "맛있는 소고기 구이집 추천"
    review = "정말 맛있는 소고기를 직접 구워주셨습니다!"
    restaurant = "소고기천국"
    max_length = 100
    # when
    post: str = write_post(title=title, restaurant=restaurant, review=review, max_length=max_length)
    # then
    assert post.startswith(f"안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!")
    assert len(post.split()) <= max_length


@pytest.fixture
def post():
    title = "맛있는 소고기 구이집 추천"
    review = "정말 맛있는 소고기를 직접 구워주셨습니다!"
    restaurant = "소고기천국"
    max_length = 100
    return write_post(title=title, restaurant=restaurant, review=review, max_length=max_length)


def test_write_hashtags(post: str):
    # when
    hashtags: list[str] = write_hashtags(post)
    # then
    assert len(hashtags) == 20
