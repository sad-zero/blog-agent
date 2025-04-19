FROM ubuntu:latest AS builder

WORKDIR /blog-agent
COPY . .

ENV PATH=$PATH:/root/.local/bin
RUN apt-get update 
RUN apt-get install -y pipx
RUN pipx ensurepath
RUN pipx install hatch
RUN hatch config set dirs.env.virtual .venv
RUN hatch run builder:build-wheel

FROM python:3.12 AS runner
WORKDIR /blog-agent
COPY --from=builder /blog-agent/dist/blog_agent*.whl .
COPY logconfig.json logconfig.json

RUN pip install blog_agent*.whl

ENV OPENAI_API_KEY "<<YOUR OPENAI API KEY>>"
# If you want to trace agent by LANGSMITH, change to true.
ENV LANGCHAIN_TRACING_V2 "false"
ENV LANGCHAIN_API_KEY "<<YOUR LANGSMITH API KEY>>"
ENV LANGCHAIN_PROJECT "<<YOUR LANGSMITH PROJECT NAME>>"

# Secret Key
ENV SECRET "<<YOUR SECRET>>"

EXPOSE 8501
ENTRYPOINT [ "blog_agent_web" ]
