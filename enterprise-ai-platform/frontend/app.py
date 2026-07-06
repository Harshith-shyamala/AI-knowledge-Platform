from __future__ import annotations

import json
from typing import Any

import httpx
import streamlit as st

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


def main() -> None:
    st.set_page_config(
        page_title="EAKP Console",
        page_icon="EAKP",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()
    _init_state()

    with st.sidebar:
        _render_sidebar()

    st.title("Enterprise AI Knowledge Platform")
    _render_status_strip()

    if not _ready_for_workspace_actions():
        st.info("Sign in and select a workspace to continue.")
        return

    documents_tab, search_tab, chat_tab, agent_tab, evaluation_tab, metrics_tab = st.tabs(
        ["Documents", "Search", "Chat", "Agent", "Evaluation", "Metrics"]
    )
    with documents_tab:
        _render_documents()
    with search_tab:
        _render_search()
    with chat_tab:
        _render_chat()
    with agent_tab:
        _render_agent()
    with evaluation_tab:
        _render_evaluation()
    with metrics_tab:
        _render_metrics()


def _init_state() -> None:
    defaults: dict[str, Any] = {
        "api_base_url": DEFAULT_API_BASE_URL,
        "access_token": "",
        "user": None,
        "memberships": [],
        "organizations": [],
        "workspaces": [],
        "organization_id": "",
        "workspace_id": "",
        "conversation_id": "",
        "last_chat": None,
        "last_agent": None,
        "last_evaluation": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _render_sidebar() -> None:
    st.header("Console")
    st.session_state.api_base_url = st.text_input(
        "API base URL",
        value=st.session_state.api_base_url,
        key="api_base_input",
    ).rstrip("/")

    if st.button("Check health", use_container_width=True):
        try:
            health = _request("GET", "/health/live", authenticated=False)
            st.success(f"{health['service']} is {health['status']}")
        except ApiError as exc:
            st.error(str(exc))

    if st.session_state.access_token:
        user = st.session_state.user or {}
        st.caption(f"Signed in as {user.get('email', 'unknown')}")
        if st.button("Sign out", use_container_width=True):
            _clear_session()
            st.rerun()
    else:
        _render_auth()

    st.divider()
    _render_workspace_context()


def _render_auth() -> None:
    login_tab, register_tab = st.tabs(["Login", "Register"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", value="demo@example.com")
            password = st.text_input(
                "Password",
                value="correct horse battery staple",
                type="password",
            )
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            _authenticate("/auth/login", {"email": email, "password": password})

    with register_tab:
        with st.form("register_form"):
            email = st.text_input("Email", value="demo@example.com", key="register_email")
            display_name = st.text_input("Display name", value="Demo User")
            organization_name = st.text_input("Organization", value="Demo Org")
            password = st.text_input(
                "Password",
                value="correct horse battery staple",
                type="password",
                key="register_password",
            )
            submitted = st.form_submit_button("Register", use_container_width=True)
        if submitted:
            _authenticate(
                "/auth/register",
                {
                    "email": email,
                    "password": password,
                    "display_name": display_name,
                    "organization_name": organization_name,
                },
            )


def _authenticate(path: str, payload: dict[str, Any]) -> None:
    try:
        session = _request("POST", path, json_body=payload, authenticated=False)
    except ApiError as exc:
        st.error(str(exc))
        return
    st.session_state.access_token = session["tokens"]["access_token"]
    st.session_state.user = session["user"]
    st.session_state.memberships = session["memberships"]
    if session["memberships"]:
        st.session_state.organization_id = session["memberships"][0]["organization_id"]
    _refresh_context()
    st.success("Authenticated")
    st.rerun()


def _render_workspace_context() -> None:
    st.subheader("Workspace")
    if not st.session_state.access_token:
        st.caption("Authentication required")
        return

    if st.button("Refresh context", use_container_width=True):
        _refresh_context()

    organizations = st.session_state.organizations
    if organizations:
        org_options = {org["name"]: org["id"] for org in organizations}
        selected_org_name = _label_for_value(org_options, st.session_state.organization_id)
        selected_org = st.selectbox(
            "Organization",
            options=list(org_options.keys()),
            index=list(org_options.keys()).index(selected_org_name),
        )
        if org_options[selected_org] != st.session_state.organization_id:
            st.session_state.organization_id = org_options[selected_org]
            st.session_state.workspace_id = ""
            _refresh_workspaces()
            st.rerun()
    else:
        st.warning("No organizations found")

    workspaces = st.session_state.workspaces
    if workspaces:
        workspace_options = {workspace["name"]: workspace["id"] for workspace in workspaces}
        selected_workspace_name = _label_for_value(
            workspace_options,
            st.session_state.workspace_id,
        )
        selected_workspace = st.selectbox(
            "Workspace",
            options=list(workspace_options.keys()),
            index=list(workspace_options.keys()).index(selected_workspace_name),
        )
        st.session_state.workspace_id = workspace_options[selected_workspace]
    else:
        st.caption("No workspaces yet")

    with st.form("create_workspace_form"):
        workspace_name = st.text_input("New workspace", value="Knowledge")
        submitted = st.form_submit_button("Create workspace", use_container_width=True)
    if submitted:
        _create_workspace(workspace_name)


def _refresh_context() -> None:
    try:
        st.session_state.organizations = _request("GET", "/organizations")
        if not st.session_state.organization_id and st.session_state.organizations:
            st.session_state.organization_id = st.session_state.organizations[0]["id"]
        _refresh_workspaces()
    except ApiError as exc:
        st.error(str(exc))


def _refresh_workspaces() -> None:
    organization_id = st.session_state.organization_id
    if not organization_id:
        st.session_state.workspaces = []
        return
    st.session_state.workspaces = _request("GET", f"/organizations/{organization_id}/workspaces")
    if not st.session_state.workspace_id and st.session_state.workspaces:
        st.session_state.workspace_id = st.session_state.workspaces[0]["id"]


def _create_workspace(name: str) -> None:
    if not st.session_state.organization_id:
        st.error("Select an organization first.")
        return
    try:
        workspace = _request(
            "POST",
            f"/organizations/{st.session_state.organization_id}/workspaces",
            json_body={"name": name},
        )
    except ApiError as exc:
        st.error(str(exc))
        return
    st.session_state.workspace_id = workspace["id"]
    _refresh_workspaces()
    st.success("Workspace created")
    st.rerun()


def _render_status_strip() -> None:
    cols = st.columns(4)
    user = st.session_state.user or {}
    cols[0].metric("User", user.get("email", "Not signed in"))
    cols[1].metric("Organizations", len(st.session_state.organizations))
    cols[2].metric("Workspaces", len(st.session_state.workspaces))
    cols[3].metric("API", st.session_state.api_base_url.replace("http://", ""))


def _render_documents() -> None:
    st.subheader("Documents")
    upload_col, list_col = st.columns([0.42, 0.58])

    with upload_col:
        with st.form("upload_document_form"):
            title = st.text_input("Title", value="Security Policy")
            uploaded_file = st.file_uploader("File", type=["txt", "md", "csv", "json"])
            submitted = st.form_submit_button("Upload", use_container_width=True)
        if submitted and uploaded_file is not None:
            try:
                response = _upload_document(title, uploaded_file)
                st.success(f"Uploaded {response['document']['title']}")
            except ApiError as exc:
                st.error(str(exc))

    with list_col:
        documents = _safe_api(lambda: _workspace_request("GET", "/documents"), [])
        st.dataframe(_document_rows(documents), use_container_width=True, hide_index=True)
        if documents:
            selected_title = st.selectbox(
                "Document to index",
                options=[document["title"] for document in documents],
            )
            document = next(item for item in documents if item["title"] == selected_title)
            if st.button("Index selected document", use_container_width=True):
                try:
                    result = _workspace_request("POST", f"/documents/{document['id']}/index")
                    st.success(
                        f"Indexed {result['chunks_indexed']} chunk(s), "
                        f"{result['embeddings_indexed']} embedding(s)"
                    )
                except ApiError as exc:
                    st.error(str(exc))


def _render_search() -> None:
    st.subheader("Search")
    query = st.text_input("Query", value="SOC 2 evidence")
    top_k = st.slider("Top K", min_value=1, max_value=10, value=5)
    if st.button("Search workspace", use_container_width=True):
        try:
            results = _workspace_request(
                "POST",
                "/search",
                json_body={"query": query, "top_k": top_k},
            )
            _render_search_results(results["results"])
        except ApiError as exc:
            st.error(str(exc))


def _render_chat() -> None:
    st.subheader("Chat")
    message = st.text_area("Message", value="What evidence is required before onboarding?")
    top_k = st.slider("Chat Top K", min_value=1, max_value=10, value=5)
    if st.button("Ask", use_container_width=True):
        payload: dict[str, Any] = {"message": message, "top_k": top_k}
        if st.session_state.conversation_id:
            payload["conversation_id"] = st.session_state.conversation_id
        try:
            result = _workspace_request("POST", "/chat", json_body=payload)
            st.session_state.last_chat = result
            st.session_state.conversation_id = result["conversation"]["id"]
        except ApiError as exc:
            st.error(str(exc))

    if st.session_state.last_chat:
        result = st.session_state.last_chat
        st.markdown(f"**Answer**\n\n{result['assistant_message']['content']}")
        _render_citations(result["citations"])

    if st.button("Load conversation history", use_container_width=True):
        try:
            history = _workspace_request("GET", "/chat/history")
            st.dataframe(history, use_container_width=True, hide_index=True)
        except ApiError as exc:
            st.error(str(exc))


def _render_agent() -> None:
    st.subheader("Agent")
    question = st.text_area(
        "Question",
        value="What do quarterly access reviews require?",
        key="agent_question",
    )
    top_k = st.slider("Agent Top K", min_value=1, max_value=10, value=5)
    include_trace = st.checkbox("Include trace", value=True)
    if st.button("Run agent", use_container_width=True):
        try:
            st.session_state.last_agent = _workspace_request(
                "POST",
                "/agents/runs",
                json_body={
                    "question": question,
                    "top_k": top_k,
                    "include_trace": include_trace,
                },
            )
        except ApiError as exc:
            st.error(str(exc))

    if st.session_state.last_agent:
        result = st.session_state.last_agent
        st.markdown(f"**Answer**\n\n{result['answer']}")
        _render_citations(result["citations"])
        if result["steps"]:
            st.dataframe(result["steps"], use_container_width=True, hide_index=True)


def _render_evaluation() -> None:
    st.subheader("Evaluation")
    default_examples = [
        {
            "question": "What do quarterly access reviews require?",
            "expected_answer": "manager approval and audit evidence",
        }
    ]
    examples_text = st.text_area(
        "Golden examples JSON",
        value=json.dumps(default_examples, indent=2),
        height=180,
    )
    top_k = st.slider("Evaluation Top K", min_value=1, max_value=10, value=5)
    if st.button("Run evaluation", use_container_width=True):
        try:
            examples = json.loads(examples_text)
            st.session_state.last_evaluation = _workspace_request(
                "POST",
                "/evaluation/runs",
                json_body={"examples": examples, "top_k": top_k},
            )
        except (json.JSONDecodeError, ApiError) as exc:
            st.error(str(exc))

    if st.session_state.last_evaluation:
        result = st.session_state.last_evaluation
        st.dataframe(result["aggregate_scores"], use_container_width=True, hide_index=True)
        with st.expander("Example results", expanded=True):
            st.json(result["examples"])

    if st.button("Evaluator catalog", use_container_width=True):
        try:
            catalog = _workspace_request("GET", "/evaluation")
            st.dataframe(catalog["evaluators"], use_container_width=True, hide_index=True)
        except ApiError as exc:
            st.error(str(exc))


def _render_metrics() -> None:
    st.subheader("Metrics")
    if st.button("Refresh metrics", use_container_width=True):
        try:
            metrics = _request_text("GET", "/metrics", authenticated=False)
            st.code(metrics, language="text")
        except ApiError as exc:
            st.error(str(exc))


def _upload_document(title: str, uploaded_file: Any) -> dict[str, Any]:
    org_id = st.session_state.organization_id
    workspace_id = st.session_state.workspace_id
    path = f"/organizations/{org_id}/workspaces/{workspace_id}/documents"
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    return _request("POST", path, data={"title": title}, files=files)


def _workspace_request(
    method: str,
    suffix: str,
    json_body: dict[str, Any] | None = None,
) -> Any:
    org_id = st.session_state.organization_id
    workspace_id = st.session_state.workspace_id
    return _request(
        method,
        f"/organizations/{org_id}/workspaces/{workspace_id}{suffix}",
        json_body=json_body,
    )


def _request(
    method: str,
    path: str,
    json_body: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    authenticated: bool = True,
) -> Any:
    headers = _headers(authenticated)
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.request(
                method,
                f"{st.session_state.api_base_url}{path}",
                json=json_body,
                data=data,
                files=files,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise ApiError(f"API request failed: {exc}") from exc

    if response.status_code >= 400:
        raise ApiError(_error_message(response), response.status_code)
    if not response.content:
        return {}
    return response.json()


def _request_text(method: str, path: str, authenticated: bool = True) -> str:
    headers = _headers(authenticated)
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.request(
                method,
                f"{st.session_state.api_base_url}{path}",
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise ApiError(f"API request failed: {exc}") from exc
    if response.status_code >= 400:
        raise ApiError(_error_message(response), response.status_code)
    return response.text


def _headers(authenticated: bool) -> dict[str, str]:
    if not authenticated:
        return {}
    token = st.session_state.access_token
    return {"Authorization": f"Bearer {token}"} if token else {}


def _error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return f"HTTP {response.status_code}: {response.text}"
    error = payload.get("error", {})
    message = error.get("message", response.text)
    code = error.get("code", "http.error")
    return f"{code}: {message}"


def _safe_api(fetch: Any, fallback: Any) -> Any:
    try:
        return fetch()
    except ApiError as exc:
        st.error(str(exc))
        return fallback


def _ready_for_workspace_actions() -> bool:
    return bool(
        st.session_state.access_token
        and st.session_state.organization_id
        and st.session_state.workspace_id
    )


def _document_rows(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": document["title"],
            "status": document["status"],
            "mime_type": document["mime_type"],
            "current_version_id": document["current_version_id"],
        }
        for document in documents
    ]


def _render_search_results(results: list[dict[str, Any]]) -> None:
    if not results:
        st.warning("No results")
        return
    for result in results:
        with st.expander(
            f"Score {result['score']} - chunk {result['chunk_index']}",
            expanded=True,
        ):
            st.write(result["content"])
            st.caption(
                f"Document {result['document_id']} - "
                f"Version {result['document_version_id']} - "
                f"Chunk {result['chunk_id']}"
            )


def _render_citations(citations: list[dict[str, Any]]) -> None:
    if not citations:
        st.caption("No citations")
        return
    for index, citation in enumerate(citations, start=1):
        with st.expander(f"Citation {index} - score {citation['score']}", expanded=False):
            st.write(citation["quote"])
            st.caption(
                f"Document {citation['document_id']} - "
                f"Version {citation['document_version_id']} - "
                f"Chunk {citation['chunk_id']}"
            )


def _label_for_value(options: dict[str, str], value: str) -> str:
    for label, option_value in options.items():
        if option_value == value:
            return label
    return next(iter(options))


def _clear_session() -> None:
    for key in [
        "access_token",
        "organization_id",
        "workspace_id",
        "conversation_id",
    ]:
        st.session_state[key] = ""
    for key in [
        "user",
        "last_chat",
        "last_agent",
        "last_evaluation",
    ]:
        st.session_state[key] = None
    st.session_state.memberships = []
    st.session_state.organizations = []
    st.session_state.workspaces = []


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #d9e2ef;
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid #d9e2ef;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.65rem 0.85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
