import streamlit as st

from blog_agent.agent import write_post, write_hashtags

title = st.text_input("Enter title")
restaurant = st.text_input("Enter restaurant")
review = st.text_area("Enter review")
max_length = st.number_input("Enter post's length", min_value=100, max_value=1000)

if not st.button("Write!"):
    st.stop()
if not (title and restaurant and review and max_length):
    st.warning("Fill all inputs")
    st.stop()

post: str = write_post(title=title, restaurant=restaurant, review=review, max_length=max_length)
hashtags: list[str] = write_hashtags(post=post)

result = f'''
# {title}
{post}
## Hashtags
{hashtags}
'''.strip()
st.markdown(result)