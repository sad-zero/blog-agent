import pytest

from blog_agent.agent import PostGuide, find_restaurant, write_hashtags, write_post
from blog_agent.agent.post import WritingPlan, plan_writing_post


@pytest.fixture
def post_guide() -> PostGuide:
    return PostGuide(
        title='서울의 "소고기 천국" 다녀왔어요!',
        review="""
직접 구워주시는 소고기는 촉촉함의 극치였어요!
한번만 먹을 수 없는 그 맛..
정말 열번 가도 또 가고 싶습니다.
방문 적극 추천해요!
대단히 맛있던 냉면은 소고기와 함께 먹을때 최고의 궁합을 자랑했어요
        """.strip(),
        max_length=1500,
        keywords=["서울맛집", "소고기대장", "직화구이"],
        foods=["소고기", "냉면"],
    )


def test_plan_writing_post(post_guide):
    # given
    post_length_offset = 100
    paragraph_max_word_count = 500
    restaurant: str = find_restaurant(title=post_guide.title)
    post_guide = post_guide.with_restaurant(restaurant)
    # when
    plan: WritingPlan = plan_writing_post(post_guide)
    # then
    actual_word_count = (
        plan.introduction.word_count + sum(x.word_count for x in plan.bodies) + plan.conclution.word_count
    )
    assert plan.introduction.word_count <= paragraph_max_word_count
    assert all(x.word_count <= paragraph_max_word_count for x in plan.bodies)
    assert plan.conclution.word_count <= paragraph_max_word_count
    assert post_guide.max_length - post_length_offset <= actual_word_count <= post_guide.max_length + post_length_offset


def test_write_post(post_guide):
    # given
    # when
    restaurant: str = find_restaurant(title=post_guide.title)
    post_guide = post_guide.with_restaurant(restaurant)
    post: str = write_post(post_guide=post_guide)
    # then
    assert post.startswith("안녕하세요, 오늘 소개해드릴 곳은 소고기 천국입니다!")
    assert len(post) >= post_guide.max_length
    chunks: list[str] = [post[i : i + 300] for i in range(0, len(post), 300)]
    for chunk in chunks:
        assert any(keyword in chunk for keyword in post_guide.keywords)


@pytest.fixture
def post_info(post_guide):
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
