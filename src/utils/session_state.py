"""
Session State Management for Streamlit
"""

import streamlit as st
from typing import Any, Dict, List
from datetime import datetime


def initialize_session_state():
    """Initialize all session state variables"""

    # Messages and conversation
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Demo state
    if "demo_state" not in st.session_state:
        st.session_state.demo_state = "initial"

    # Customer information
    if "customer_info" not in st.session_state:
        st.session_state.customer_info = {}

    # Scenario configuration
    if "scenario" not in st.session_state:
        st.session_state.scenario = {}

    # Generated data
    if "generated_data" not in st.session_state:
        st.session_state.generated_data = {}

    # ES|QL queries
    if "esql_queries" not in st.session_state:
        st.session_state.esql_queries = []

    # Demo artifacts
    if "demo_artifacts" not in st.session_state:
        st.session_state.demo_artifacts = {}

    # Validation results
    if "validation_results" not in st.session_state:
        st.session_state.validation_results = {}

    # History tracking
    if "query_history" not in st.session_state:
        st.session_state.query_history = []

    # Current query/result
    if "current_query" not in st.session_state:
        st.session_state.current_query = ""

    if "current_result" not in st.session_state:
        st.session_state.current_result = None

    # Demo ID
    if "demo_id" not in st.session_state:
        st.session_state.demo_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Configuration
    if "config" not in st.session_state:
        st.session_state.config = {
            "retrieval_method": "hybrid",
            "top_k": 5,
            "min_score": 0.5
        }


def add_to_history(query: str, result: Any):
    """Add a query and result to history"""
    if "query_history" not in st.session_state:
        st.session_state.query_history = []

    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "result": result
    }

    st.session_state.query_history.append(history_entry)

    # Keep only last 50 entries
    if len(st.session_state.query_history) > 50:
        st.session_state.query_history = st.session_state.query_history[-50:]


def get_history(limit: int = 10) -> List[Dict]:
    """Get query history"""
    if "query_history" not in st.session_state:
        return []

    return st.session_state.query_history[-limit:]


def clear_history():
    """Clear query history"""
    st.session_state.query_history = []


def get_stats() -> Dict:
    """Get session statistics"""
    stats = {
        "total_queries": len(st.session_state.get("query_history", [])),
        "demo_state": st.session_state.get("demo_state", "unknown"),
        "queries_generated": len(st.session_state.get("esql_queries", [])),
        "datasets_created": len(st.session_state.get("generated_data", {})),
        "validation_complete": bool(st.session_state.get("validation_results", {}))
    }

    return stats


def update_demo_state(new_state: str):
    """Update the current demo state"""
    st.session_state.demo_state = new_state
    st.session_state.state_updated_at = datetime.now().isoformat()


def add_message(role: str, content: str, **kwargs):
    """Add a message to the conversation"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    message.update(kwargs)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.session_state.messages.append(message)


def get_messages(limit: int = None) -> List[Dict]:
    """Get conversation messages"""
    messages = st.session_state.get("messages", [])

    if limit:
        return messages[-limit:]
    return messages


def save_artifact(name: str, content: Any):
    """Save a demo artifact"""
    if "demo_artifacts" not in st.session_state:
        st.session_state.demo_artifacts = {}

    st.session_state.demo_artifacts[name] = {
        "content": content,
        "saved_at": datetime.now().isoformat()
    }


def get_artifact(name: str) -> Any:
    """Get a demo artifact"""
    if "demo_artifacts" not in st.session_state:
        return None

    artifact = st.session_state.demo_artifacts.get(name)
    if artifact:
        return artifact.get("content")
    return None


def reset_demo():
    """Reset demo to initial state"""
    st.session_state.demo_state = "initial"
    st.session_state.customer_info = {}
    st.session_state.scenario = {}
    st.session_state.generated_data = {}
    st.session_state.esql_queries = []
    st.session_state.demo_artifacts = {}
    st.session_state.validation_results = {}
    st.session_state.messages = []
    st.session_state.demo_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"