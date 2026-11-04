import string

import jinja2
from django.template import Engine, Template as DjangoTemplate, engines
from flask import Flask, render_template_string, stream_template_string
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.sandbox import ImmutableSandboxedEnvironment, SandboxedEnvironment
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, SystemMessagePromptTemplate
from mako.lookup import TemplateLookup
from mako.template import Template as MakoTemplate
from openai import OpenAI
from tornado import template as tornado_template

client = OpenAI()
app = Flask(__name__)
env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())
sandbox = SandboxedEnvironment(autoescape=True)

PAGE = "<h1>Answer</h1><div>{{ answer }}</div>"


def ask(question):
    completion = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    return completion.choices[0].message.content


@app.route("/answer")
def flask_answer():
    reply = client.responses.create(model="gpt-5", input="Summarize the ticket")
    # ruleid: llm-output-as-template
    return render_template_string(f"<h1>Answer</h1><p>{reply.output_text}</p>")


@app.route("/answer-fixed")
def flask_answer_fixed():
    reply = client.responses.create(model="gpt-5", input="Summarize the ticket")
    # ok: llm-output-as-template
    return render_template_string(PAGE, answer=reply.output_text)


@app.route("/stream")
def flask_stream():
    reply = client.responses.create(model="gpt-5", input="Write the update")
    body = "<article>" + reply.output_text + "</article>"
    # ruleid: llm-output-as-template
    return app.response_class(stream_template_string(body, user="ops"))


def jinja_template():
    reply = client.messages.create(model="claude-sonnet-5-5", max_tokens=800, messages=[])
    text = reply.content[0].text
    # ruleid: llm-output-as-template
    page = jinja2.Template(text).render(customer="Ada")
    # ok: llm-output-as-template
    safe = jinja2.Template(PAGE).render(answer=text)
    return page, safe


def env_from_string():
    reply = client.responses.create(model="gpt-5", input="Draft the digest template")
    # ruleid: llm-output-as-template
    template = env.from_string(reply.output_text)
    return template.render(name="Ada")


def env_get_template():
    reply = client.responses.create(model="gpt-5", input="Write the digest body")
    # ok: llm-output-as-template
    return env.get_template("digest.html").render(body=reply.output_text)


def inline_environment():
    reply = client.responses.create(model="gpt-5", input="Draft the subject line")
    # ruleid: llm-output-as-template
    return jinja2.Environment().from_string(reply.output_text).render()


def flask_app_env():
    reply = client.responses.create(model="gpt-5", input="Draft the banner")
    # ruleid: llm-output-as-template
    return app.jinja_env.from_string(reply.output_text).render()


def sandboxed():
    reply = client.responses.create(model="gpt-5", input="Draft the digest template")
    # ok: llm-output-as-template
    template = sandbox.from_string(reply.output_text)
    immutable = ImmutableSandboxedEnvironment()
    # ok: llm-output-as-template
    other = immutable.from_string(reply.output_text)
    # ok: llm-output-as-template
    inline = SandboxedEnvironment().from_string(reply.output_text)
    return template, other, inline


def django_templates():
    reply = client.responses.create(model="gpt-5", input="Write the notice")
    # ruleid: llm-output-as-template
    notice = DjangoTemplate(reply.output_text)
    # ruleid: llm-output-as-template
    banner = engines["django"].from_string(reply.output_text)
    engine = Engine.get_default()
    # ruleid: llm-output-as-template
    footer = engine.from_string("{% load i18n %}" + reply.output_text)
    return notice, banner, footer


def mako_and_tornado():
    reply = client.responses.create(model="gpt-5", input="Write the report")
    # ruleid: llm-output-as-template
    report = MakoTemplate(reply.output_text).render(user="ops")
    # ruleid: llm-output-as-template
    summary = MakoTemplate(text=reply.output_text, strict_undefined=True)
    lookup = TemplateLookup(directories=["templates"])
    # ruleid: llm-output-as-template
    lookup.put_string("generated.mako", reply.output_text)
    # ok: llm-output-as-template
    fixed = MakoTemplate(filename="templates/report.mako").render(body=reply.output_text)
    # ruleid: llm-output-as-template
    page = tornado_template.Template(reply.output_text).generate(user="ops")
    return report, summary, fixed, page


def langchain_templates():
    reply = client.responses.create(model="gpt-5", input="Write a follow-up prompt")
    # ruleid: llm-output-as-template
    follow_up = PromptTemplate.from_template(reply.output_text, template_format="jinja2")
    # ruleid: llm-output-as-template
    direct = PromptTemplate(template=reply.output_text, input_variables=["q"], template_format="jinja2")
    chat = ChatPromptTemplate.from_messages(
        # ruleid: llm-output-as-template
        [("system", reply.output_text), ("human", "{{ question }}")],
        template_format="jinja2",
    )
    built = ChatPromptTemplate(
        # ruleid: llm-output-as-template
        [("system", reply.output_text)],
        template_format="jinja2",
    )
    # ruleid: llm-output-as-template
    system = SystemMessagePromptTemplate.from_template(reply.output_text, template_format="jinja2")
    # ok: llm-output-as-template
    plain = PromptTemplate.from_template(reply.output_text)
    # ok: llm-output-as-template
    mustache = ChatPromptTemplate.from_template(reply.output_text, template_format="mustache")
    return follow_up, direct, chat, built, system, plain, mustache


def stdlib_substitution():
    text = ask("Write the reminder text with $name in it")
    # ok: llm-output-as-template
    reminder = string.Template(text).safe_substitute(name="Ada")
    # ok: llm-output-as-template
    greeting = text.format(name="Ada")
    return reminder, greeting


def metadata_only():
    reply = client.chat.completions.create(model="gpt-5", messages=[])
    # ok: llm-output-as-template
    return jinja2.Template("Model {{ m }}: " + reply.model).render(m=1)
