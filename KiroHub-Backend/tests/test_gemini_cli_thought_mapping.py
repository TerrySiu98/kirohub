import unittest

from app.services.gemini_cli_api_service import (
    _OpenAIStreamState,
    _gemini_cli_event_to_openai_chunks,
    _gemini_cli_response_to_openai_response,
)


class TestGeminiCLIThoughtMapping(unittest.TestCase):
    def test_stream_thought_signature_maps_to_reasoning_content(self) -> None:
        event = {
            "response": {
                "responseId": "r1",
                "modelVersion": "gemini-test",
                "createTime": "2026-01-31T00:00:00Z",
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "hello",
                                    "thoughtSignature": "sig",
                                }
                            ]
                        }
                    }
                ],
            }
        }
        state = _OpenAIStreamState(created=0, function_index=0)
        chunks = _gemini_cli_event_to_openai_chunks(event, state=state)
        self.assertTrue(chunks)
        delta = chunks[0]["choices"][0]["delta"]
        self.assertEqual(delta["role"], "assistant")
        self.assertEqual(delta["reasoning_content"], "hello")
        self.assertIsNone(delta["content"])

    def test_response_thought_signature_maps_to_reasoning_content(self) -> None:
        raw = {
            "response": {
                "responseId": "r2",
                "modelVersion": "gemini-test",
                "createTime": "2026-01-31T00:00:00Z",
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [
                                {
                                    "text": "think",
                                    "thoughtSignature": "sig",
                                }
                            ]
                        },
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 1,
                    "candidatesTokenCount": 1,
                    "totalTokenCount": 2,
                    "thoughtsTokenCount": 1,
                },
            }
        }
        out = _gemini_cli_response_to_openai_response(raw)
        msg = out["choices"][0]["message"]
        self.assertEqual(msg.get("reasoning_content"), "think")


if __name__ == "__main__":
    unittest.main()

