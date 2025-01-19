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
    raise NotImplemented

def write_post(title: str, restaurant: str, review: str, max_length: int) -> str:
    system_prompt = """
As a food blog writer, your task is to write a post based on user's request.
---
Please follow these guidelines.
- You should start with "안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!"
- You should write an attractive post.
- The post's word count should be less than {max_length}.
- You should end with sentences to recommend visiting {restaurant}.
- You should write the post in korean.
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
""".strip()
    template = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", human_prompt)])
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=1500)
    chain = template | llm
    res = chain.invoke(
        {
            "title": title,
            "restaurant": restaurant,
            "review": review,
            "max_length": max_length,
        }
    )
    return res.content


def write_hashtags(post: str) -> list[str]:
    class Response(TypedDict):
        hashtags: list[str]

    system_prompt = """
As a blog writer, your task is to write hashtags related to the user's post.
---
Please follow these guidelines.
- The number of hashtags should be equal to 20.
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
    chain = {"post": RunnablePassthrough()} | template | llm.with_structured_output(Response, method="json_schema")
    response: Response = chain.invoke(post)
    return response["hashtags"]
