import jinja2
from flask import Blueprint, Flask, Response, jsonify, make_response, render_template, request
from markupsafe import Markup, escape

import litellm

app = Flask(__name__)
bp = Blueprint("assist", __name__)
reports = jinja2.Environment(loader=jinja2.PackageLoader("assist"), autoescape=False)


@app.route("/explain")
def explain():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.args["q"]}]
    )
    answer = resp.choices[0].message.content
    # ruleid: llm-output-rendered-as-html
    return f"<h1>Answer</h1><div>{answer}</div>"


@bp.post("/summarize")
def summarize():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.form["text"]}]
    )
    # ruleid: llm-output-rendered-as-html
    return resp.choices[0].message.content, 200


@bp.post("/summarize.json")
def summarize_json():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.form["text"]}]
    )
    payload = {"summary": resp.choices[0].message.content}
    # ok: llm-output-rendered-as-html
    return payload


@bp.post("/summarize.api")
def summarize_api():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.form["text"]}]
    )
    # ok: llm-output-rendered-as-html
    return jsonify(summary=resp.choices[0].message.content)


@app.get("/page")
def page():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.args["q"]}]
    )
    answer = resp.choices[0].message.content
    # ok: llm-output-rendered-as-html
    html = render_template("answer.html", answer=answer)
    # ruleid: llm-output-rendered-as-html
    trusted = render_template("answer.html", answer=Markup(answer))
    # ok: llm-output-rendered-as-html
    escaped = render_template("answer.html", answer=Markup("<b>{}</b>").format(answer))
    # ok: llm-output-rendered-as-html
    return html + trusted + escaped


@app.get("/plain")
def plain():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.args["q"]}]
    )
    # ok: llm-output-rendered-as-html
    return Response(resp.choices[0].message.content, mimetype="text/plain")


@app.get("/fragment")
def fragment():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.args["q"]}]
    )
    # ruleid: llm-output-rendered-as-html
    out = make_response(resp.choices[0].message.content)
    out.headers["Cache-Control"] = "no-store"
    # ok: llm-output-rendered-as-html
    return out


@app.get("/report")
def report():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.args["q"]}]
    )
    template = reports.get_template("report.html")
    # ruleid: llm-output-rendered-as-html
    body = template.render(summary=resp.choices[0].message.content)
    # ok: llm-output-rendered-as-html
    return body


@app.get("/escaped")
def escaped():
    resp = litellm.completion(
        model="gpt-5", messages=[{"role": "user", "content": request.args["q"]}]
    )
    # ok: llm-output-rendered-as-html
    return f"<pre>{escape(resp.choices[0].message.content)}</pre>"
