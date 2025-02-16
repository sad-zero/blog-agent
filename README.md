# blog-agent
Blog Agent helps you to write and revise blog posts.

## Installation
1. Clone this repository.
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


## Run
### Docker
1. Clone this repository.
2. Run `docker build -t blog-agent:latest .`
3. Run `docker run -d -p <incoming-port>:8501 -e OPENAI_API_KEY=... -e LANGCHAIN_TRACING_V2=... -e LANGCHAIN_API_KEY=... -e LANGCHAIN_PROJECT=...`
   - You should set `OPENAI_API_KEY`

## Usecase
- Food post
- Product review
