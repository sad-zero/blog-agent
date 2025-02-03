# blog-agent
Blog Agent helps you to write and revise blog posts.

## Installation
1. Clone this repostiroy.
2. Enter `hatch shell`
3. Set `OPENAI_API_KEY` environment.
4. Run `streamlit run src/blog_agent/web.py`!

## Environment Variables
You should set environments below.
- `OPENAI_API_KEY`: Blog agent uses OpenAI's gpt models.
- `SECRET`: To authenticate accesses, add your secret.
### (Optional) Tracing with Langsmith
- `LANGCHAIN_TRACING_V2 = true`
- `LANGCHAIN_API_KEY = <Langsmith API Key>`
- `LANGCHAIN_PROJECT = blog-agent`

## Usecase
- Food post
- Product review
