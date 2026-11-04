# No templating import: a settings object that happens to have from_string.
import litellm
from app.settings import environment


def load_overrides(prompt):
    response = litellm.completion(model="gpt-5", messages=[{"role": "user", "content": prompt}])
    # ok: llm-output-as-template
    return environment.from_string(response.choices[0].message.content)
