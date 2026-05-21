from pydantic import BaseModel

from fides.service.mcp.intent.inference import (
    InferenceClient,
    InferenceError,
    InferenceTimeout,
    StructuredCompletion,
)


class _Out(BaseModel):
    answer: str


def test_structured_completion_carries_parsed_and_model():
    sc = StructuredCompletion(parsed=_Out(answer="ok"), model="m", raw_content="")
    assert sc.parsed.answer == "ok"
    assert sc.model == "m"


def test_inference_timeout_is_timeout_error_subclass():
    assert issubclass(InferenceTimeout, TimeoutError)


def test_inference_error_is_runtime_error_subclass():
    assert issubclass(InferenceError, RuntimeError)


def test_inference_client_is_runtime_checkable_protocol():
    """A concrete impl satisfies the Protocol via duck-typing."""

    class Fake:
        async def complete_structured(
            self, *, system_prompt, user_prompt, output_model, timeout_s, max_tokens=1024, model=None,
        ):
            return StructuredCompletion(parsed=output_model(answer="x"), model="m", raw_content="")

    assert isinstance(Fake(), InferenceClient)
