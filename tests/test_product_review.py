import re
from blog_agent.agent.review import Review, ReviewGuide, extract_keywords, write_product_review
import pytest

@pytest.fixture
def review_guide_without_keywords():
    return ReviewGuide(
        category="전자제품",
        product="앱코 K517 레트로 기계식 (적축)",
        score=4,
        max_length=1000,
        positive_review="기계식 키보드 입문용으로 정말 좋습니다",
        negative_review="유선키보드라 조금 불편합니다",
        sponsored=False,
        purchased_date="2025-01-25",
        arrived_date="2025-02-01",
        packaging_state="good",
    )

def test_extract_keywords(review_guide_without_keywords: ReviewGuide):
    keywords: list[str] = extract_keywords(review_guide=review_guide_without_keywords)
    assert 2 <= len(keywords) <= 5

def test_review(review_guide_without_keywords: ReviewGuide):
    # given
    keywords: list[str] = extract_keywords(review_guide=review_guide_without_keywords)
    review_guide = review_guide_without_keywords.with_keywords(keywords=keywords)
    # when
    review: Review = write_product_review(review_guide=review_guide)

    # then
    assert "내돈내산" in review.title or "내돈내산" in review.product_review
    assert len(review.product_review.split()) <= review_guide.max_length
    assert len(review.seller_review.split()) <= 300
    assert '#' not in review.seller_review

    pattern = re.compile(r'## (.+?)\n')
    subtitles = pattern.findall(review.product_review)
    assert keywords + ["결론"] == [subtitle.strip() for subtitle in subtitles]
