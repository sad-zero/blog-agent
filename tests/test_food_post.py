import pytest

from blog_agent.agent import PostGuide, find_restaurant, write_hashtags, write_post


def test_write_post():
    # given
    post_guide = PostGuide(
        title = '서울의 "소고기 천국" 다녀왔어요!',
        review = "정말 맛있는 소고기를 직접 구워주셨습니다!",
        max_length = 1500,
        keywords = ["숯불", "직화", "맛집"],
        foods = ["소고기", "냉면"],
    )
    # when
    restaurant: str = find_restaurant(title=post_guide.title)
    post_guide = post_guide.with_restaurant(restaurant)
    post: str = write_post(post_guide=post_guide)
    # then
    assert post.startswith(f"안녕하세요, 오늘 소개해드릴 곳은 소고기 천국입니다!")
    assert len(post.split()) <= post_guide.max_length
    chunks: list[str] = [post[i:i+300] for i in range(0, len(post), 300)]
    for chunk in chunks:
        assert any(keyword in chunk for keyword in post_guide.keywords)


@pytest.fixture
def post_info():
    post_guide = PostGuide(
        title = '서울의 "소고기 천국" 다녀왔어요!',
        review = "정말 맛있는 소고기를 직접 구워주셨습니다!",
        max_length = 1500,
        keywords = ["숯불", "직화", "맛집"],
        foods = ["소고기", "냉면"],
    )
    # when
    restaurant: str = find_restaurant(post_guide.title)
    post_guide = post_guide.with_restaurant(restaurant)
    return post_guide, write_post(post_guide=post_guide)


def test_write_hashtags(post_info):
    # given
    post_guide, post = post_info
    keywords = set(post_guide.keywords)
    # when
    hashtags: list[str] = write_hashtags(post=post, post_guide=post_guide)
    # then
    assert len(hashtags) == 20
    cleaned_hashtags = {hashtag[1:] for hashtag in hashtags}

    assert keywords & cleaned_hashtags == keywords
