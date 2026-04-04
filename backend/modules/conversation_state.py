"""
conversation_state.py — In-memory session state manager for the Conversational Orchestrator.

Each session tracks:
  - Chat history (user + AI messages)
  - Active constraints (accumulated from each conversational turn)
  - Rejected candidates (with rejection reasons)
  - Last full pipeline result
  - Clarification state (pending questions)
  - Agent status (for live activity feed polling)
"""

import uuid
import time
import threading

# ── Session Store ──────────────────────────────────────────────────────────
_sessions = {}
_lock = threading.Lock()

SESSION_TIMEOUT = 1800  # 30 minutes


def create_session(molecule=None):
    """Create a new session and return its ID + initial state."""
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "created_at": time.time(),
        "last_active": time.time(),
        "molecule": molecule,

        # Chat history: list of {role: "user"|"assistant", content: str, timestamp: float}
        "history": [],

        # Accumulated constraints from conversation turns
        "active_constraints": {},

        # Rejected candidates: list of {drug: str, reason: str, timestamp: float}
        "rejected_candidates": [],

        # Last pipeline result (avoid re-running unnecessarily)
        "last_result": None,

        # Clarification state
        "pending_clarification": None,

        # Agent status for live feed: dict of agent_name -> status string
        "agent_status": {
            "clinical": "idle",
            "patents": "idle",
            "market": "idle",
            "regulatory": "idle",
            "pubmed": "idle",
            "mechanism": "idle",
            "synthesizer": "idle",
        },

        # Pipeline running flag
        "pipeline_running": False,
    }

    with _lock:
        _sessions[session_id] = session
    return session_id, session


def get_session(session_id):
    """Retrieve a session by ID. Returns None if not found or expired."""
    with _lock:
        session = _sessions.get(session_id)
    if session is None:
        return None
    if time.time() - session["last_active"] > SESSION_TIMEOUT:
        delete_session(session_id)
        return None
    session["last_active"] = time.time()
    return session


def update_session(session_id, updates):
    """Merge updates into an existing session."""
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            return None
        session.update(updates)
        session["last_active"] = time.time()
        return session


def delete_session(session_id):
    """Remove a session."""
    with _lock:
        _sessions.pop(session_id, None)


# ── History Management ─────────────────────────────────────────────────────

def add_message(session_id, role, content):
    """Append a message to the session chat history."""
    session = get_session(session_id)
    if session is None:
        return None
    session["history"].append({
        "role": role,
        "content": content,
        "timestamp": time.time(),
    })
    return session


def get_history(session_id):
    """Return the full chat history for a session."""
    session = get_session(session_id)
    if session is None:
        return []
    return session["history"]


# ── Constraint Management ──────────────────────────────────────────────────

def add_constraints(session_id, new_constraints):
    """Merge new constraints into the session's active constraint set."""
    session = get_session(session_id)
    if session is None:
        return {}
    session["active_constraints"].update(new_constraints)
    return session["active_constraints"]


def remove_constraint(session_id, constraint_key):
    """Remove a single constraint by key."""
    session = get_session(session_id)
    if session is None:
        return {}
    session["active_constraints"].pop(constraint_key, None)
    return session["active_constraints"]


def get_constraints(session_id):
    """Return the active constraints for a session."""
    session = get_session(session_id)
    if session is None:
        return {}
    return session["active_constraints"]


# ── Candidate Rejection ────────────────────────────────────────────────────

def reject_candidate(session_id, drug_name, reason=""):
    """Add a drug to the rejected list."""
    session = get_session(session_id)
    if session is None:
        return []
    # Avoid duplicates
    existing = [r["drug"].lower() for r in session["rejected_candidates"]]
    if drug_name.lower() not in existing:
        session["rejected_candidates"].append({
            "drug": drug_name,
            "reason": reason,
            "timestamp": time.time(),
        })
    return session["rejected_candidates"]


def get_rejected(session_id):
    """Return list of rejected candidates."""
    session = get_session(session_id)
    if session is None:
        return []
    return session["rejected_candidates"]


# ── Agent Status ───────────────────────────────────────────────────────────

def update_agent_status(session_id, agent_name, status):
    """Update the status of a specific agent for the live feed."""
    session = get_session(session_id)
    if session is None:
        return
    session["agent_status"][agent_name] = status


def set_all_agents(session_id, status):
    """Set all agents to the same status (e.g. 'idle', 'complete')."""
    session = get_session(session_id)
    if session is None:
        return
    for agent in session["agent_status"]:
        session["agent_status"][agent] = status


def set_pipeline_running(session_id, running):
    """Mark the pipeline as running or stopped."""
    session = get_session(session_id)
    if session is None:
        return
    session["pipeline_running"] = running


# ── Cleanup ────────────────────────────────────────────────────────────────

def cleanup_expired():
    """Remove all expired sessions. Call periodically."""
    now = time.time()
    with _lock:
        expired = [sid for sid, s in _sessions.items()
                   if now - s["last_active"] > SESSION_TIMEOUT]
        for sid in expired:
            del _sessions[sid]
    return len(expired)


def get_session_summary(session_id):
    """Return a JSON-safe summary for the /session endpoint."""
    session = get_session(session_id)
    if session is None:
        return None
    return {
        "session_id": session["session_id"],
        "molecule": session["molecule"],
        "history": session["history"],
        "active_constraints": session["active_constraints"],
        "rejected_candidates": session["rejected_candidates"],
        "agent_status": session["agent_status"],
        "pipeline_running": session["pipeline_running"],
        "pending_clarification": session["pending_clarification"],
    }
