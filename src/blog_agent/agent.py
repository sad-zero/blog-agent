from typing import Self, TypedDict

from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
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
            err_msg: str = f'restaurant is not str: {restaurant}'
            raise TypeError(err_msg)
        return PostGuide(
            title=self.title,
            review=self.review,
            max_length=self.max_length,
            keywords=self.keywords,
            foods=self.foods,
            restaurant=restaurant,
        )

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
    template = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        ('human', human_prompt),
    ])
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.52, max_completion_tokens=100)
    chain = template | llm.with_structured_output(Response, method='json_schema')
    response: Response = chain.invoke({'title': title})
    return response['restaurant']

def write_post(post_guide: PostGuide) -> str:
    system_prompt = """
As a food blog writer, your task is to write a post based on user's request.
---
Please follow these guidelines.
- You should write an attractive post.
- You should write the post in korean.
- You should start with "안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!"
- The post's word count should be less than {max_length}.
- You should use given keywords in every 300 words as the context.
- You should end with sentences about visiting {restaurant}.
- You must not use recommendation sentences like "추천합니다".
---
Please consider these LLM configurations.
- temperature: 0.52
---
Please do your best. Let's start!
""".strip()
    human_prompt = """
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
    template = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", human_prompt)])
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=1500)
    chain = template | llm
    res = chain.invoke(
        post_guide.model_dump()
    )
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
    keyword_hashtags: list[str] = ['#' + keyword.strip('# ') for keyword in post_guide.keywords[:20 - len(hashtags)]]
    result = hashtags + keyword_hashtags
    return result