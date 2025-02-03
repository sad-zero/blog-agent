
from typing import Literal, Self, TypedDict
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate

class ReviewGuide(BaseModel):
    category: str
    product: str
    score: int = Field(ge=0, le=5)
    max_length: int = Field(ge=500)
    positive_review: str
    negative_review: str
    sponsored: bool
    purchased_date: str
    arrived_date: str
    packaging_state: str
    keywords: list[str] | None = Field(default=None)

    def with_keywords(self, keywords: list[str]) -> Self:
        return ReviewGuide(
            keywords=keywords,
            **self.model_dump(exclude_none=True),
        )


def extract_keywords(review_guide: ReviewGuide) -> list[str]:
    class Response(TypedDict):
        keywords: list[str]
    
    system_prompt = """
As a product reviewer, your task is to extract attractive keywords based on a request.
---
Please follow these guidelines ordered by their proirities.
1. Keywords should represent the core of the request. They are used as subtitles of the review.
2. Keywords should be short terms.
3. Keywords should be extracted between 2 to 5.
4. If a request doesn't an advertisement, "내돈내산" should be one of keywords.
---
Please response as JSON and follow schema below(defined by Python).
class Response(TypedDict):
    keywords: list[str]
---
Please do your best. Let's start!
""".strip()
    human_prompt = """
Product's category is here.
{category}
---
Product's name is here.
{product}
---
Review score is here. The score is between 0(worst) to 5(best).
{score}
---
Product's positive review is here.
{positive_review}
---
Product's negative review is here.
{negative_review}
---
Whether it is an advertisement or not is here.
{sponsored}
---
Purchased date is here.
{purchased_date}
---
Arrived date is here.
{arrived_date}
---
Packaging state is here.
{packaging_state}
""".strip()
    template = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        ('human', human_prompt),
    ])
    llm = ChatOpenAI(model='gpt-4o-2024-11-20', temperature=0.52, max_completion_tokens=200)
    chain = template | llm.with_structured_output(Response, method='json_schema')
    res: Response = chain.invoke(review_guide.model_dump())
    return res['keywords']


class Review(BaseModel):
    title: str
    product_review: str
    seller_review: str

def write_product_review(review_guide: ReviewGuide) -> Review:
    seller_review = _write_seller_review(review_guide=review_guide)
    product_review = _write_product_review(review_guide=review_guide)
    return Review(
        seller_review=seller_review,
        product_review=product_review['review'],
        title=product_review['title'],
    )

def _write_seller_review(review_guide: ReviewGuide) -> str:
    system_prompt = """
As a product reviewer, your task is to write product's review for its seller.
---
Please follow these guidelines.
- You should write an attractive review.
- You should write the review in korean.
- You should write the review in the past tense.
- You should write the review as PLAINTEXT, not markdown.
- The review should use emojis and punctuation marks like !, ~, etc.
- The review's word count should be less than 300 words.
---
Please consider these LLM configurations.
- temperature: 0.52
---
Please do your best. Let's start!
""".strip()
    human_prompt = """
Purchased date is here.
{purchased_date}
---
Arrived date is here.
{arrived_date}
---
Packaging state is here.
{packaging_state}
""".strip()
    template = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        ('human', human_prompt),
    ])
    llm = ChatOpenAI(model='gpt-4o-2024-11-20', temperature=0.52, max_completion_tokens=1000)
    chain = template | llm
    res = chain.invoke(review_guide.model_dump())
    return res.content

def _write_product_review(review_guide: ReviewGuide) -> dict[Literal["title", "review"], str]:
    class Response(TypedDict):
        review: str
        title: str
    system_prompt = """
As a product reviewer, your task is to write product's review for other customers.
---
Please follow these guidelines.
- You should write an attractive review.
- You should write the review in korean.
- You should write the review in the past tense.
- The review's word count should be less than {max_length}.
- Keywords should be used as subtitles by their orders.
- Last subtitle should be "결론"
- The review should end with comments attracting readers to buy the product.
- The review should use emojis and punctuation marks like !, ~, etc.
- Positive and negative reviews should be mixed.
- The title should summarize the review.
- The title should be a phrase, not sentence.
- The title should be emphasized as "내돈내산" keyword If a request doesn't an advertisement.
---
Please consider these LLM configurations.
- temperature: 0.52
---
Please response as JSON and follow schema below(defined by Python).
class Response(TypedDict):
    review: str
    title: str
***
The review format is here.
## {{subtitle}}
{{pharagraph}}
---
Please do your best. Let's start!
""".strip()
    human_prompt = """
Product's category is here.
{category}
---
Product's name is here.
{product}
---
Review score is here. The score is between 0(worst) to 5(best).
{score}
---
Product's positive review is here.
{positive_review}
---
Product's negative review is here.
{negative_review}
---
Whether it is an advertisement or not is here.
{sponsored}
---
Purchased date is here.
{purchased_date}
---
Arrived date is here.
{arrived_date}
---
Packaging state is here.
{packaging_state}
---
Review's keywords are here.
{keywords}
""".strip()
    template = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        ('human', human_prompt),
    ])
    llm = ChatOpenAI(model='gpt-4o-2024-11-20', temperature=0.52, max_completion_tokens=2000)
    chain = template | llm.with_structured_output(Response, method='json_schema')
    res: Response = chain.invoke(review_guide.model_dump())
    return res
