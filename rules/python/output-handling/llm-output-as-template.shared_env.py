# The environments are built in another module; this file only imports them.
import json

import litellm
from app.templating import env, sandboxed_env


def weekly_digest(kpis):
    response = litellm.completion(model="gpt-5", messages=[{"role": "user", "content": json.dumps(kpis)}])
    draft = response.choices[0].message.content
    # ruleid: llm-output-as-template
    template = env.from_string(draft)
    # ok: llm-output-as-template
    preview = sandboxed_env.from_string(draft)
    return template.render(kpis=kpis), preview.render(kpis=kpis)

