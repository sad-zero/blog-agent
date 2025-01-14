from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def write_post(title: str, restaurant: str, review: str, max_length: int) -> str:
    system_prompt = '''
As a food blog writer, your task is to write a post based on user's request.
---
Please follow these guidelines.
- You should start with "안녕하세요, 오늘 소개해드릴 곳은 {restaurant}입니다!"
- You should write an attractive post.
- The post's word count should be less than {max_length}.
- You should end with sentences to recommend visiting {restaurant}.
---
Please consider these LLM configurations.
- temperature: 0.52
---
Please do your best. Let's start!
'''.strip()
    human_prompt = '''
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
'''.strip()
    template = ChatPromptTemplate.from_messages([
        ('system', system_prompt),
        ('human', human_prompt)
    ])
    llm = ChatOpenAI(model='gpt-4o-2024-11-20', temperature=0.52, max_completion_tokens=1500)
    chain = template | llm
    res = chain.invoke({
        'title': title,
        'restaurant': restaurant,
        'review': review,
        'max_length': max_length,
    })
    return res.content

def write_hashtags(post: str) -> list[str]:
    # TODO: Write hashtags
    raise NotImplemented