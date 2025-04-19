import logging
from typing import Self, TypedDict

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

_logger = logging.getLogger(__name__)


class PostGuide(BaseModel):
    title: str
    review: str
    max_length: int
    keywords: list[str]
    foods: list[str]
    restaurant: str | None = Field(default=None)

    def with_restaurant(self, restaurant: str) -> Self:
        self.restaurant = restaurant
        return self


class WritingPlanDetail(BaseModel):
    """Post's detail structure"""

    subject: str
    letter_count: int


class WritingPlan(BaseModel):
    """Post's structure"""

    introduction: WritingPlanDetail
    bodies: list[WritingPlanDetail]
    conclution: WritingPlanDetail


class DraftDetail(BaseModel):
    plan: WritingPlanDetail
    paragraph: str


class Draft(BaseModel):
    """Post's draft"""

    introduction: DraftDetail | None = Field(default=None)
    bodies: list[DraftDetail] = Field(default_factory=list)
    conclusion: DraftDetail | None = Field(default=None)


class FeedbackDetail(BaseModel):
    score: int  # 0(worst) to 10(best)
    advise: str


class Feedback(BaseModel):
    introduction: FeedbackDetail
    bodies: list[FeedbackDetail]
    conclusion: FeedbackDetail
    overall: FeedbackDetail


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


def plan_writing_post(post_guide: PostGuide) -> WritingPlan:
    """Plan how to write the post. The plan needs to write long contents."""

    system_prompt = """
As a food columnist, your task is to plan how to write blog posts based on guidelines.
The posts is written by reader's requests.

---
Please follow these guidelines ordered by **their priorities**.
1. The length of a paragraph should be close to **500 letters**.
2. The total length of all paragraphs should be in between {min_letter_count} and {max_letter_count}.

---
Please response as JSON defined by python.

class WritingPlan(TypedDict):
    introduction: WritingPlanDetail
    bodies: list[WritingPlanDetail]
    conclution: WritingPlanDetail

class WritingPlanDetail(TypedDict):
    subject: str
    letter_count: int
---
Please do your best. Let's start!
""".strip()
    human_prompt = "{post_guide}"
    template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt), MessagesPlaceholder("messages")]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=1000)
    chain = template | llm.with_structured_output(WritingPlan)

    min_letter_count = post_guide.max_length - 100
    max_letter_count = post_guide.max_length + 100
    prompt = {
        "messages": [],
        "post_guide": post_guide.model_dump_json(indent=4, exclude=["restaurant", "max_length"]),
        "restaurant": post_guide.restaurant,
        "min_letter_count": min_letter_count,
        "max_letter_count": max_letter_count,
    }
    res: WritingPlan = chain.invoke(prompt)
    log_msg: str = f"Writing Plan: {res.model_dump_json(indent=4)}"
    _logger.info(log_msg)
    letter_count = (
        res.introduction.letter_count + sum(body.letter_count for body in res.bodies) + res.conclution.letter_count
    )
    while not (min_letter_count <= letter_count <= max_letter_count):
        log_msg = (
            f"Plan's total letter count is invalid: {letter_count} not in [{min_letter_count}, {max_letter_count}]"
        )
        _logger.warning(log_msg)
        prompt["messages"].append(AIMessage(content=res.model_dump_json()))
        prompt["messages"].append(
            HumanMessage(
                content=f"The total length of all paragraphs is {letter_count}. The length should be between {min_letter_count} and {max_letter_count}."
            )
        )
        res: WritingPlan = chain.invoke(prompt)

        log_msg = f"Writing Plan: {res.model_dump_json(indent=4)}"
        _logger.info(log_msg)

        letter_count = (
            res.introduction.letter_count + sum(body.letter_count for body in res.bodies) + res.conclution.letter_count
        )
    return res


def write_post(post_guide: PostGuide) -> str:
    log_msg: str = f"Write post by the guide: {post_guide.model_dump_json(indent=4)}"
    _logger.info(log_msg)
    plan: WritingPlan = plan_writing_post(post_guide)
    draft = Draft()

    post: str = ""
    introduction: str = _write_post_introduction(post_guide, plan.introduction)
    post += introduction
    draft.introduction = DraftDetail(plan=plan.introduction, paragraph=introduction)

    for body_plan in plan.bodies:
        body: str = _write_post_body(post_guide, body_plan, post)
        post += "\n\n" + body
        draft.bodies.append(DraftDetail(plan=body_plan, paragraph=body))

    conclusion: str = _write_post_conclusion(post_guide, plan.conclution, post)
    post += "\n\n" + conclusion
    draft.conclusion = DraftDetail(plan=plan.conclution, paragraph=conclusion)

    feedback: Feedback = _feedback_draft(post_guide, draft)
    result: str = _revise_draft(post_guide, draft, feedback)
    log_msg = f"Final post\n{result}"
    _logger.info(log_msg)
    return result


def _write_post_introduction(post_guide: PostGuide, plan: WritingPlanDetail) -> str:
    system_prompt = """
As a food columnist, your task is to write blog post's introduction based on guidelines.
The posts is written by reader's requests.

---
Please follow these guidelines ordered by **their priorities**.
1. Introduction's subject is {subject}.
2. The length of introduction should be longer than {letter_count} letters.
3. Introduction should be written attractive IN THE CALM TONE and MUST NOT use exaggerated or recommending expressions even if given informations contain these expressions.
    - Examples about prohibited expressions are "추천", "너무", "정말", "특별한", "최고", and more.
4. Introduction should be written IN KOREAN and the PAST TENSE.
5. Introduction should use at least one given keywords by contexts. If the length is longer than 300 letters, you should use more keywords.
6. Introduction should start with "안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!"

---
Please consider these LLM configurations.
- temperature: 0.52

---
Please response as plain text. You don't need to use markdown.

---
Please do your best. Let's start!
""".strip()
    human_prompt = "{post_guide}"
    template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt), MessagesPlaceholder("messages")]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=2000)
    chain = template | llm

    prompt = {
        "messages": [],
        "post_guide": post_guide.model_dump_json(exclude=["max_length"]),
        "subject": plan.subject,
        "letter_count": plan.letter_count,
        "restaurant": post_guide.restaurant,
    }
    res = chain.invoke(prompt)

    log_msg: str = f"Introduction: {res.content}"
    _logger.info(log_msg)
    while (letter_count := len(res.content)) < plan.letter_count:
        log_msg = f"Letter count is less than desired letter count. {letter_count} < {plan.letter_count}"
        _logger.warning(log_msg)

        prompt["messages"].append(res)
        prompt["messages"].append(
            HumanMessage(
                content=f"The length of introduction is {letter_count} letters. And this is shorter than the guideline({plan.letter_count}). Revise the introduction."
            )
        )
        res = chain.invoke(prompt)
        log_msg = f"Introduction: {res.content}"
        _logger.info(log_msg)
    return res.content


def _write_post_body(post_guide: PostGuide, plan: WritingPlanDetail, post: str) -> str:
    system_prompt = """
As a food columnist, your task is to write blog post's current paragraph based on guidelines.
The posts is written by reader's requests.

---
Please follow these guidelines ordered by **their priorities**.
1. Paragraph's subject is {subject}.
2. The length of paragraph should be longer than {letter_count} letteres.
3. Paragraph should be written attractive IN THE CALM TONE and MUST NOT use exaggerated or recommending expressions even if given informations contain these expressions.
    - Examples about prohibited expressions are "추천", "너무", "정말", "특별한", "최고", and more.
4. Paragraph should be written IN KOREAN and the PAST TENSE.
5. Paragraph should use at least one given keywords by contexts. If the length is longer than 300 letters, you should use more keywords.

---
Please consider these LLM configurations.
- temperature: 0.52

---
Please response as plain text. You don't need to use markdown.

---
Please do your best. Let's start!
""".strip()
    human_prompt = "{post_guide}"
    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt),
            ("ai", post),
            ("human", "Please write current paragraph"),
            MessagesPlaceholder("messages"),
        ]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=2000)
    chain = template | llm

    prompt = {
        "messages": [],
        "post_guide": post_guide.model_dump_json(exclude=["max_length"]),
        "subject": plan.subject,
        "letter_count": plan.letter_count,
        "restaurant": post_guide.restaurant,
    }
    res = chain.invoke(prompt)

    log_msg: str = f"Body Paragraph: {res.content}"
    _logger.info(log_msg)
    while (letter_count := len(res.content)) <= plan.letter_count:
        log_msg = f"Letter count is less than desired letter count. {letter_count} < {plan.letter_count}"
        _logger.warning(log_msg)

        prompt["messages"].append(res)
        prompt["messages"].append(
            HumanMessage(
                content=f"The length of paragraph is {letter_count} letters. And this is shorter than the guideline({plan.letter_count}). Revise the paragraph."
            )
        )
        res = chain.invoke(prompt)

        log_msg: str = f"Body Paragraph: {res.content}"
        _logger.info(log_msg)
    return res.content


def _write_post_conclusion(post_guide: PostGuide, plan: WritingPlanDetail, post: str) -> str:
    system_prompt = """
As a food columnist, your task is to write blog post's conclusion based on guidelines.
The posts is written by reader's requests.

---
Please follow these guidelines ordered by **their priorities**.
1. Conclusion's subject is {subject}.
2. The length of conclusion should be longer than {letter_count} letters.
3. Conclusion should be written attractive IN THE CALM TONE and MUST NOT use exaggerated or recommending expressions even if given informations contain these expressions.
    - Examples about prohibited expressions are "추천", "너무", "정말", "특별한", "최고", and more.
4. Conclusion should be written IN KOREAN and the PAST TENSE.
5. Conclusion should use at least one given keywords by contexts. If the length is longer than 300 letters, you should use more keywords.
6. Conclusion should end with sentences about visiting {restaurant}.

---
Please consider these LLM configurations.
- temperature: 0.52

---
Please response as plain text. You don't need to use markdown.

---
Please do your best. Let's start!
""".strip()
    human_prompt = "{post_guide}"
    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt),
            ("ai", post),
            ("human", "Please write conclusion"),
            MessagesPlaceholder("messages"),
        ]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=2000)
    chain = template | llm

    prompt = {
        "messages": [],
        "post_guide": post_guide.model_dump_json(exclude=["max_length"]),
        "subject": plan.subject,
        "letter_count": plan.letter_count,
        "restaurant": post_guide.restaurant,
    }
    res = chain.invoke(prompt)

    log_msg: str = f"Conclusion Paragraph: {res.content}"
    _logger.info(log_msg)
    while (letter_count := len(res.content)) <= plan.letter_count:
        log_msg = f"Letter count is less than desired letter count. {letter_count} < {plan.letter_count}"
        _logger.warning(log_msg)

        prompt["messages"].append(res)
        prompt["messages"].append(
            HumanMessage(
                content=f"The length of conclusion is {letter_count} letters. And this is shorter than the guideline({plan.letter_count}). Revise the conclusion."
            )
        )
        res = chain.invoke(prompt)

        log_msg = f"Conclusion Paragraph: {res.content}"
        _logger.info(log_msg)
    return res.content


def _feedback_draft(post_guide: PostGuide, draft: Draft) -> Feedback:
    system_prompt = """
As a blog editor, your task is to review the food blog post's draft and feedback how to revise it based on guidelines.
The posts is written by food columnist.

---
Please follow theses guidelinse order by **their priorities**.
1. Each paragraph should be align with it's subject.
2. Each paragraph's length should be **same or longer than it's letter_count.**
3. All paragraphs should be written attractive IN THE CALM TONE and MUST NOT use exaggerated or recommending expressions even if given informations contain these expressions.
    - Examples about prohibited expressions are "추천", "너무", "정말", "특별한", "최고", and more.
4. All paragraphs should be written IN KOREAN and the PAST TENSE.
5. All paragraphs should use at least one given keywords by contexts. If the length is longer than 300 letters, the paragraph should contain more keywords.
6. Introduction should start with "안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!"
7. Conclusion should end with sentences about visiting {restaurant}.

---
Please response as JSON defined by python.

class Feedback(TypedDict):
    introduction: FeedbackDetail # introduction feedback
    bodies: list[FeedbackDetail] # bodies feedback
    conclusion: FeedbackDetail # conclusion feedback
    overall: FeedbackDetail # overall feedback

class FeedbackDetail(TypedDict):
    score: int # 0(worst) to 10(best)
    advise: str # advise the draft based on guidelines
""".strip()
    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{draft}"),
        ]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=1000)
    chain = template | llm.with_structured_output(Feedback)
    res: Feedback = chain.invoke({"restaurant": post_guide.restaurant, "draft": draft.model_dump_json()})

    log_msg: str = f"Feedback: {res.model_dump_json(indent=4)}"
    _logger.info(log_msg)
    return res


def _revise_draft(post_guide: PostGuide, draft: Draft, feedback: Feedback) -> str:
    system_prompt = """
As a food columnist, your task is to revise blog post's draft based on feedbacks.
The post is written by reader's request and feedbacks are written by the blog editor based on guidelines.

---
Please follow theses guidelinse order by **their priorities**.
1. Each paragraph should be align with it's subject.
2. Each paragraph's length should be **same or longer than it's letter_count.**
3. All paragraphs should be written attractive IN THE CALM TONE and MUST NOT use exaggerated or recommending expressions even if given informations contain these expressions.
    - Examples about prohibited expressions are "추천", "너무", "정말", "특별한", "최고", and more.
4. All paragraphs should be written IN KOREAN and the PAST TENSE.
5. All paragraphs should use at least one given keywords by contexts. If the length is longer than 300 letters, the paragraph should contain more keywords.
6. Introduction should start with "안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!"
7. Conclusion should end with sentences about visiting {restaurant}.

---
Please follow these llm configurations.
- temperature: 0.52

---
Please response as plain text. You don't need to use markdown.
""".strip()

    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Request is here.\n{post_guide}"),
            ("ai", "Draft is here.\n{draft}"),
            ("human", "Feedback is here.\n{feedback}"),
            ("human", "Based on the draft, please write the final post. You should consider feedbacks and guidelines."),
            MessagesPlaceholder("messages"),
        ]
    )
    llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0.52, max_completion_tokens=2000)
    chain = template | llm

    prompt = {
        "restaurant": post_guide.restaurant,
        "post_guide": post_guide.model_dump_json(exclude=["restaurant", "max_length"], indent=4),
        "draft": draft.model_dump_json(indent=4),
        "feedback": feedback.model_dump_json(indent=4),
        "messages": [],
    }
    res = chain.invoke(prompt)

    log_msg: str = f"Revised post: {res.content}"
    _logger.info(log_msg)

    messages = []
    while len(res.content) < post_guide.max_length:
        log_msg = (
            f"The length of the post is {len(res.content)}. This is shorter than the guideline({post_guide.max_length})"
        )
        _logger.warning(log_msg)
        messages = [
            res,
            HumanMessage(
                f"The length of the post is {len(res.content)}. This is shorter than the guideline({post_guide.max_length}). Please revise the post."
            ),
        ]
        prompt = prompt | {"messages": messages}
        res = chain.invoke(prompt)

        log_msg = f"Revised post: {res.content}"
        _logger.info(log_msg)
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
    res: list[str] = hashtags + keyword_hashtags

    log_msg: str = f"Hashtags: {res}"
    _logger.info(log_msg)
    return res
