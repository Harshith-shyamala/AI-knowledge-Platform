from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def test_evaluation_run_scores_grounded_agent_answer(client: TestClient) -> None:
    session = _register(client)
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]
    document = _upload_document(
        client,
        organization_id,
        workspace_id,
        token,
        title="Access Review Policy",
        body="Quarterly access reviews require manager approval and audit evidence.",
    )
    _index_document(client, organization_id, workspace_id, document["id"], token)

    response = client.post(
        _evaluation_runs_url(organization_id, workspace_id),
        headers=_auth(token),
        json={
            "examples": [
                {
                    "question": "What do quarterly access reviews require?",
                    "expected_answer": "manager approval and audit evidence",
                }
            ],
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["prompt_version"] == "agent-rag-v1"
    assert payload["workflow_version"] == "deterministic-agent-v1"
    assert len(payload["examples"]) == 1
    example = payload["examples"][0]
    assert example["citation_count"] == 1
    assert "manager approval and audit evidence" in example["actual_answer"]
    scores = _scores_by_name(example["scores"])
    assert scores["groundedness"]["passed"] is True
    assert scores["faithfulness"]["passed"] is True
    assert scores["answer_relevance"]["passed"] is True
    assert scores["context_recall"]["passed"] is True
    aggregate_scores = _scores_by_name(payload["aggregate_scores"])
    assert aggregate_scores["groundedness"]["score"] == 1.0


def test_evaluation_run_flags_ungrounded_answer(client: TestClient) -> None:
    session = _register(
        client,
        email="evaluation-empty@example.com",
        org_name="Evaluation Empty Org",
    )
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.post(
        _evaluation_runs_url(organization_id, workspace_id),
        headers=_auth(token),
        json={
            "examples": [
                {
                    "question": "What evidence is required?",
                    "expected_answer": "SOC 2 evidence",
                }
            ]
        },
    )

    assert response.status_code == 200
    example = response.json()["examples"][0]
    scores = _scores_by_name(example["scores"])
    assert example["citation_count"] == 0
    assert scores["groundedness"]["score"] == 0.0
    assert scores["groundedness"]["passed"] is False
    assert scores["context_recall"]["passed"] is False


def test_evaluation_metrics_returns_evaluator_catalog(client: TestClient) -> None:
    session = _register(
        client,
        email="evaluation-catalog@example.com",
        org_name="Evaluation Catalog Org",
    )
    token = session["tokens"]["access_token"]
    organization_id = session["memberships"][0]["organization_id"]
    workspace_id = _create_workspace(client, organization_id, token)["id"]

    response = client.get(
        f"/organizations/{organization_id}/workspaces/{workspace_id}/evaluation",
        headers=_auth(token),
    )

    assert response.status_code == 200
    evaluators = response.json()["evaluators"]
    assert {evaluator["name"] for evaluator in evaluators} == {
        "groundedness",
        "faithfulness",
        "answer_relevance",
        "context_recall",
    }
    assert all(evaluator["evaluator_version"] for evaluator in evaluators)


def _scores_by_name(scores: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {score["name"]: score for score in scores}


def _register(
    client: TestClient,
    email: str = "evaluation@example.com",
    org_name: str = "Evaluation Org",
) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct horse battery staple",
            "display_name": "Evaluation User",
            "organization_name": org_name,
        },
    )
    assert response.status_code == 201
    return dict(response.json())


def _create_workspace(client: TestClient, organization_id: str, token: str) -> dict[str, Any]:
    response = client.post(
        f"/organizations/{organization_id}/workspaces",
        headers=_auth(token),
        json={"name": "Knowledge"},
    )
    assert response.status_code == 201
    return dict(response.json())


def _upload_document(
    client: TestClient,
    organization_id: str,
    workspace_id: str,
    token: str,
    title: str,
    body: str,
) -> dict[str, Any]:
    response = client.post(
        f"/organizations/{organization_id}/workspaces/{workspace_id}/documents",
        headers=_auth(token),
        data={"title": title},
        files={"file": ("policy.md", body.encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 201
    return dict(response.json()["document"])


def _index_document(
    client: TestClient,
    organization_id: str,
    workspace_id: str,
    document_id: str,
    token: str,
) -> None:
    response = client.post(
        f"/organizations/{organization_id}/workspaces/{workspace_id}/documents/{document_id}/index",
        headers=_auth(token),
    )
    assert response.status_code == 200


def _evaluation_runs_url(organization_id: str, workspace_id: str) -> str:
    return f"/organizations/{organization_id}/workspaces/{workspace_id}/evaluation/runs"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
