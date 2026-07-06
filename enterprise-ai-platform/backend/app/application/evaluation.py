from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import mean
from typing import Protocol
from uuid import UUID, uuid4

from app.application.agents import AgentWorkflowService, RunAgentCommand
from app.core.errors import AppError

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True)
class EvaluationExample:
    question: str
    expected_answer: str


@dataclass(frozen=True)
class RunEvaluationCommand:
    organization_id: UUID
    workspace_id: UUID
    actor_user_id: UUID
    examples: list[EvaluationExample]
    top_k: int = 5


@dataclass(frozen=True)
class EvaluationScore:
    name: str
    score: float
    passed: bool
    threshold: float
    explanation: str
    evaluator_version: str


@dataclass(frozen=True)
class EvaluationExampleResult:
    question: str
    expected_answer: str
    actual_answer: str
    citation_count: int
    scores: list[EvaluationScore]


@dataclass(frozen=True)
class EvaluationRunResult:
    run_id: UUID
    examples: list[EvaluationExampleResult]
    aggregate_scores: list[EvaluationScore]
    prompt_version: str
    workflow_version: str


class Evaluator(Protocol):
    name: str
    threshold: float
    version: str

    def evaluate(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        citation_quotes: list[str],
    ) -> EvaluationScore:
        """Score one generated answer."""


@dataclass(frozen=True)
class EvaluationService:
    agent_workflow_service: AgentWorkflowService
    evaluators: tuple[Evaluator, ...]

    def run(self, command: RunEvaluationCommand) -> EvaluationRunResult:
        if not command.examples:
            raise AppError(
                code="evaluation.empty_dataset",
                message="Evaluation requires at least one example.",
                status_code=422,
                details={},
            )
        if len(command.examples) > 25:
            raise AppError(
                code="evaluation.dataset_too_large",
                message="Evaluation runs support at most 25 examples in local mode.",
                status_code=422,
                details={"example_count": len(command.examples)},
            )
        if command.top_k < 1 or command.top_k > 10:
            raise AppError(
                code="evaluation.invalid_top_k",
                message="top_k must be between 1 and 10.",
                status_code=422,
                details={"top_k": command.top_k},
            )

        example_results = [
            self._evaluate_example(command, example) for example in command.examples
        ]
        return EvaluationRunResult(
            run_id=uuid4(),
            examples=example_results,
            aggregate_scores=_aggregate_scores(example_results),
            prompt_version=self.agent_workflow_service.prompt_version,
            workflow_version=self.agent_workflow_service.workflow_version,
        )

    def evaluator_catalog(self) -> list[EvaluationScore]:
        return [
            EvaluationScore(
                name=evaluator.name,
                score=0.0,
                passed=False,
                threshold=evaluator.threshold,
                explanation="Evaluator metadata only; run an evaluation to compute a score.",
                evaluator_version=evaluator.version,
            )
            for evaluator in self.evaluators
        ]

    def _evaluate_example(
        self,
        command: RunEvaluationCommand,
        example: EvaluationExample,
    ) -> EvaluationExampleResult:
        question = example.question.strip()
        expected_answer = example.expected_answer.strip()
        if not question or not expected_answer:
            raise AppError(
                code="evaluation.invalid_example",
                message="Each evaluation example requires a question and expected_answer.",
                status_code=422,
                details={},
            )

        agent_result = self.agent_workflow_service.run(
            RunAgentCommand(
                organization_id=command.organization_id,
                workspace_id=command.workspace_id,
                actor_user_id=command.actor_user_id,
                question=question,
                top_k=command.top_k,
                include_trace=False,
            )
        )
        citation_quotes = [citation.quote for citation in agent_result.citations]
        scores = [
            evaluator.evaluate(
                question=question,
                expected_answer=expected_answer,
                actual_answer=agent_result.answer,
                citation_quotes=citation_quotes,
            )
            for evaluator in self.evaluators
        ]
        return EvaluationExampleResult(
            question=question,
            expected_answer=expected_answer,
            actual_answer=agent_result.answer,
            citation_count=len(agent_result.citations),
            scores=scores,
        )


class GroundednessEvaluator:
    name = "groundedness"
    threshold = 0.7
    version = "heuristic-groundedness-v1"

    def evaluate(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        citation_quotes: list[str],
    ) -> EvaluationScore:
        del question, expected_answer
        has_citations = bool(citation_quotes)
        fallback = "not have enough indexed knowledge" in actual_answer.lower()
        score = 1.0 if has_citations and not fallback else 0.0
        return _score(
            name=self.name,
            score=score,
            threshold=self.threshold,
            explanation=(
                "Answer has supporting citations."
                if score >= self.threshold
                else "Answer lacks supporting citations or used the fallback response."
            ),
            version=self.version,
        )


class FaithfulnessEvaluator:
    name = "faithfulness"
    threshold = 0.45
    version = "heuristic-faithfulness-v1"

    def evaluate(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        citation_quotes: list[str],
    ) -> EvaluationScore:
        del question, expected_answer
        citation_tokens = _terms(" ".join(citation_quotes))
        score = _coverage(_terms(actual_answer), citation_tokens)
        return _score(
            name=self.name,
            score=score,
            threshold=self.threshold,
            explanation="Measures how much of the answer is supported by citation text.",
            version=self.version,
        )


class AnswerRelevanceEvaluator:
    name = "answer_relevance"
    threshold = 0.35
    version = "heuristic-answer-relevance-v1"

    def evaluate(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        citation_quotes: list[str],
    ) -> EvaluationScore:
        del citation_quotes
        target_terms = _terms(f"{question} {expected_answer}")
        score = _coverage(target_terms, _terms(actual_answer))
        return _score(
            name=self.name,
            score=score,
            threshold=self.threshold,
            explanation=(
                "Measures overlap between the answer and the question plus "
                "expected answer."
            ),
            version=self.version,
        )


class ContextRecallEvaluator:
    name = "context_recall"
    threshold = 0.5
    version = "heuristic-context-recall-v1"

    def evaluate(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        citation_quotes: list[str],
    ) -> EvaluationScore:
        del question, actual_answer
        score = _coverage(_terms(expected_answer), _terms(" ".join(citation_quotes)))
        return _score(
            name=self.name,
            score=score,
            threshold=self.threshold,
            explanation="Measures whether cited context covers expected-answer terms.",
            version=self.version,
        )


def default_evaluators() -> tuple[Evaluator, ...]:
    return (
        GroundednessEvaluator(),
        FaithfulnessEvaluator(),
        AnswerRelevanceEvaluator(),
        ContextRecallEvaluator(),
    )


def _aggregate_scores(example_results: list[EvaluationExampleResult]) -> list[EvaluationScore]:
    scores_by_name: dict[str, list[EvaluationScore]] = {}
    for result in example_results:
        for score in result.scores:
            scores_by_name.setdefault(score.name, []).append(score)

    aggregates = []
    for name, scores in scores_by_name.items():
        average = round(mean(score.score for score in scores), 6)
        threshold = scores[0].threshold
        aggregates.append(
            _score(
                name=name,
                score=average,
                threshold=threshold,
                explanation=f"Average {name} score across {len(example_results)} example(s).",
                version=scores[0].evaluator_version,
            )
        )
    return aggregates


def _score(
    name: str,
    score: float,
    threshold: float,
    explanation: str,
    version: str,
) -> EvaluationScore:
    normalized = max(0.0, min(1.0, round(score, 6)))
    return EvaluationScore(
        name=name,
        score=normalized,
        passed=normalized >= threshold,
        threshold=threshold,
        explanation=explanation,
        evaluator_version=version,
    )


def _coverage(required_terms: set[str], observed_terms: set[str]) -> float:
    if not required_terms:
        return 0.0
    return len(required_terms & observed_terms) / len(required_terms)


def _terms(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)}
