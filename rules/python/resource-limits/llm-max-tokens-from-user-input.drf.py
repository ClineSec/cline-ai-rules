from django.conf import settings
from openai import OpenAI
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

client = OpenAI()


class SummarySerializer(serializers.Serializer):
    text = serializers.CharField()
    max_tokens = serializers.IntegerField(min_value=1, max_value=2048)
    choices = serializers.IntegerField(min_value=1)


@api_view(["POST"])
def summarize(request):
    ser = SummarySerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    out = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": ser.validated_data["text"]}],
        # ok: llm-max-tokens-from-user-input
        max_tokens=ser.validated_data["max_tokens"],
        # ruleid: llm-max-tokens-from-user-input
        n=ser.validated_data["choices"],
    )
    return Response({"summary": out.choices[0].message.content})


@api_view(["POST"])
def summarize_raw(request):
    # ruleid: llm-max-tokens-from-user-input
    out = client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=request.data.get("max_tokens", 256))
    return Response({"summary": out.choices[0].message.content})


@api_view(["POST"])
def summarize_settings(request):
    # ok: llm-max-tokens-from-user-input
    out = client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=settings.SUMMARY_MAX_TOKENS)
    return Response({"summary": out.choices[0].message.content})
