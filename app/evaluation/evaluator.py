from app.generation.llm_client import generate_answer


def parse_score(llm_output: str) -> dict:
    """Extracts SCORE and REASON from the judge LLM's structured response."""
    score = 0.0
    reason = llm_output.strip()
    for line in llm_output.splitlines():
        if line.strip().upper().startswith("SCORE:"):
            try:
                score = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        if line.strip().upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
    return {"score": score, "reason": reason}


def evaluate_faithfulness(answer: str, contexts: list[str]) -> dict:
    """Uses the LLM as a judge to check if the answer is fully supported by the context."""
    context_text = "\n\n".join(contexts)
    # print(f"[DEBUG] context length: {len(context_text)} chars")

    prompt = f"""You are an evaluation judge. Determine if the ANSWER below is fully
supported by the CONTEXT. The answer should not contain any claims that aren't
present in or directly inferable from the context.

Respond in EXACTLY this format, with SCORE on the very first line:
SCORE: <a number from 0 to 1, where 1 = fully supported, 0 = not supported at all>
REASON: <one sentence explaining your score>

CONTEXT:
{context_text}

ANSWER:
{answer}"""

    # print(f"[DEBUG] prompt length: {len(prompt)} chars")
    result = generate_answer(prompt, max_tokens=1000)
    # print(f"[DEBUG raw faithfulness output]: '{result}'")
    return parse_score(result)


def evaluate_relevance(question: str, answer: str) -> dict:
    """Uses the LLM as a judge to check if the answer actually addresses the question."""
    prompt = f"""You are an evaluation judge. Determine how well the ANSWER addresses
the QUESTION asked.

Respond in EXACTLY this format, with SCORE on the very first line:
SCORE: <a number from 0 to 1, where 1 = fully answers the question, 0 = completely irrelevant>
REASON: <one sentence explaining your score>

QUESTION: {question}

ANSWER: {answer}"""

    result = generate_answer(prompt, max_tokens=1000)
    return parse_score(result)