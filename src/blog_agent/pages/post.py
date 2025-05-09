import streamlit as st

from blog_agent.agent import PostGuide, find_restaurant, write_hashtags, write_post
from blog_agent.web import AUTH_KEY

if not st.session_state.get(AUTH_KEY):
    st.stop()

title = st.text_input("Enter title")
review = st.text_area("Enter review")
max_length = st.number_input("Enter post's length", min_value=500, max_value=2000)
keywords: list[str] | str = st.text_input("Enter comma-seperated keywords. Example) 맛집,서울")
keywords = [keyword.strip() for keyword in keywords.split(",")]
foods: list[str] | str = st.text_input("Enter comma-seperated foods. Example) 고기,냉면")
foods = [food.strip() for food in foods.split(",")]
restaurant = st.text_input("Enter restaurant(Deprecated)")

if not st.button("Write!"):
    st.stop()
if not (title and review and max_length and keywords and foods):
    st.warning("Fill all inputs")
    st.stop()

post_guide = PostGuide(
    title=title,
    review=review,
    max_length=max_length,
    keywords=keywords,
    foods=foods,
    restaurant=restaurant,
)
if not restaurant:
    restaurant = find_restaurant(title)

post_guide = post_guide.with_restaurant(restaurant)
post: str = write_post(post_guide=post_guide)
hashtags: list[str] = write_hashtags(post=post, post_guide=post_guide)

result = f"""
# {title}
| Property | Description |
| -------- | ----------- |
| Word     | {len(post.split())} |
| Letter   | {len(post)} |

{post}

## Hashtags
{hashtags}
""".strip()
st.markdown(result)
