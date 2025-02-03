import streamlit as st

from blog_agent.agent.review import Review, ReviewGuide, extract_keywords, write_product_review
from blog_agent.web import AUTH_KEY

if not st.session_state.get(AUTH_KEY):
    st.stop()
category = st.text_input("Enter category. Example) 전자제품")
product = st.text_input("Enter product's name")
score = st.number_input("Enter review's score. 0(worst) - 5(best)", min_value=0, max_value=5)
max_length = st.number_input("Enter post's length", min_value=500, max_value=2000)
positive_review = st.text_area("Enter positive review")
negative_review = st.text_area("Enter negative review")
sponsored = st.checkbox("Sponsored")
purchased_date = st.date_input("Purchased date", format="YYYY-MM-DD")
arrived_date = st.date_input("Arrived date", format="YYYY-MM-DD")
packaging_state = st.text_input("Packaging state")

if not st.button("Write!"):
    st.stop()
if not (
    category
    and product
    and score
    and max_length
    and positive_review
    and negative_review
    and purchased_date
    and arrived_date
    and packaging_state
):
    st.warning("Fill all inputs")
    st.stop()

review_guide = ReviewGuide(
    category=category,
    product=product,
    score=score,
    max_length=max_length,
    positive_review=positive_review,
    negative_review=negative_review,
    sponsored=sponsored,
    purchased_date=purchased_date.strftime("%Y-%m-%d"),
    arrived_date=arrived_date.strftime("%Y-%m-%d"),
    packaging_state=packaging_state,
)
keywords: list[str] = extract_keywords(review_guide=review_guide)
review_guide = review_guide.with_keywords(keywords=keywords)

review: Review = write_product_review(review_guide=review_guide)
product_review: str = review.product_review
review_text = f"""
> Seller Review

{review.seller_review}

---

> Product Review

# {review.title}
{review.product_review}
""".strip()
st.markdown(review_text)
