from typing import Self, TypedDict

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class PostGuide(BaseModel):
    title: str
    review: str
    max_length: int
    keywords: list[str]
    foods: list[str]
    restaurant: str | None = Field(default=None)

    def with_restaurant(self, restaurant: str) -> Self:
        if not isinstance(restaurant, str):
            err_msg: str = f"restaurant is not str: {restaurant}"
            raise TypeError(err_msg)
        return PostGuide(
            title=self.title,
            review=self.review,
            max_length=self.max_length,
            keywords=self.keywords,
            foods=self.foods,
            restaurant=restaurant,
        )


class WritingPlanDetail(BaseModel):
    """Post's detail structure"""

    subject: str
    word_count: int


class WritingPlan(BaseModel):
    """Post's structure"""

    introduction: WritingPlanDetail
    bodies: list[WritingPlanDetail]
    conclution: WritingPlanDetail


def find_restaurant(title: str) -> str:
    class Response(TypedDict):
        restaurant: str

    system_prompt = """
Please find a restaurant's name in the given title.
---
Please response as JSON and follow schema below(defined by Python).
class Response(TypedDict):
    restaurant: str
---
Please do your best. Let's start!
""".strip()
    human_prompt = """
Title is here.
{title}
""".strip()
    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt),
        ]
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.52, max_completion_tokens=100)
    chain = template | llm.with_structured_output(Response, method="json_schema")
    response: Response = chain.invoke({"title": title})
    return response["restaurant"]


def plan_writing_post(post_guide: PostGuide) -> dict:
    """Plan how to write the post. The plan needs to write long contents."""

    system_prompt = """
As a food columnist, your task is to plan how to write blog posts based on guidelines.
The posts is written by reader's requests.
---
Please follow these guidelines ordered by **their priorities**.
1. Post should be written attractive IN THE CALM TONE and MUST NOT use exaggerated or recommending expressions even if given informations contain these expressions.
    - Examples about prohibited expressions are "추천", "너무", "정말", "특별한", "최고", and more.
2. Post should be written IN KOREAN and the PAST TENSE.
3. Post should use given keywords in every 300 words as the context.
4. Post should start with "안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!" and end with sentences about visiting {restaurant}.
5. Post's word count should be between {max_length} +- 100.
---
Please response as JSON defined by python.

class WritingPlan(TypedDict):
    introduction: WritingPlanDetail
    bodies: list[WritingPlanDetail]
    conclution: WritingPlanDetail

class WritingPlanDetail(TypedDict):
    subject: str
    word_count: int
---
Please do your best. Let's start!
""".strip()
    human_prompt = "{post_guide}"
    template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt), MessagesPlaceholder("messages")]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=500)
    chain = template | llm.with_structured_output(WritingPlan, method="json_schema")

    prompt = {
        "messages": [],
        "post_guide": post_guide.model_dump_json(indent=4, exclude=["restaurant", "max_length"]),
        "restaurant": post_guide.restaurant,
        "max_length": post_guide.max_length,
    }
    res: WritingPlan = chain.invoke(prompt)
    return res


def write_post(post_guide: PostGuide) -> str:
    system_prompt = """
As a food blog writer, your task is to answer questions based on guidelines.
---
Please follow these guidelines ordered by **their priorities**.
1. Post should be written attractive IN THE CALM TONE and MUST NOT use exaggerated or recommending expressions even if given informations contain these expressions.
    - Examples about prohibited expressions are "추천", "너무", "정말", "특별한", "최고", and more.
2. Post should be written IN KOREAN and the PAST TENSE.
3. Post should use given keywords in every 300 words as the context.
4. Post should start with "안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!" and end with sentences about visiting {restaurant}.
5. Post's word count should be less than {max_length}.
---
Please consider these LLM configurations.
- temperature: 0.52
---
Please do your best. Let's start!
""".strip()
    human_prompt = """
Please write a post based on contexts below.
---
Post's title is here.
{title}
---
Restaurant's name is here.
{restaurant}
---
Food's review is here.
{review}
---
Post's maximum lenght is here.
{max_length}
---
Keywords are here.
{keywords}
---
Eaten foods are here.
{foods}
""".strip()
    template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt), MessagesPlaceholder("messages")]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=2000)
    chain = template | llm

    prompt = {"messages": [], **post_guide.model_dump()}
    res = chain.invoke(prompt)
    prompt["messages"].append(res)
    prompt["messages"].append(
        HumanMessage(
            content="""
Please score between 0(worst) to 10(best) at every guidelines whether the post follows them.
After scoring the post, please feedback how to improving it.
Especially, **please find all prohibitted expressions in the post**
---
Please response as bullet list like below.
```markdown
## Prohibitted expressions
- {{expressions}}

## {{guideline}}
- score: ...
- feedback: ...
```""".strip()
        )
    )
    res = chain.invoke(prompt)
    prompt["messages"].append(res)
    prompt["messages"].append(HumanMessage(content="Please write an improved post."))
    res = chain.invoke(prompt)
    return res.content


def write_hashtags(post: str, post_guide: PostGuide) -> list[str]:
    class Response(TypedDict):
        hashtags: list[str]

    system_prompt = """
As a blog writer, your task is to write hashtags related to the user's post.
---
Please follow these guidelines.
- The number of hashtags should be equal to {number}.
- You should write hashtags aligning with user's post.
- You should write the post in korean.
---
Please consider these LLM configurations.
- temperature: 0.52
---
Please response as JSON and follow schema below(defined by Python).
class Response(TypedDict):
    hashtags: list[str]
---
Please do your best. Let's start!
""".strip()
    human_prompt = """
Post is here.

{post}
""".strip()
    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt),
        ]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=500)
    chain = template | llm.with_structured_output(Response, method="json_schema")
    if number := max(0, 20 - len(post_guide.keywords)):
        response: Response = chain.invoke({"post": post, "number": number})
    hashtags: list[str] = response["hashtags"]
    keyword_hashtags: list[str] = ["#" + keyword.strip("# ") for keyword in post_guide.keywords[: 20 - len(hashtags)]]
    return hashtags + keyword_hashtags
