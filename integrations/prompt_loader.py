"""
System Prompt Loader
Composes base prompt (your instructions) + client context (their brand/audience)
"""
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_system_prompt(base_prompt: str) -> str:
    """
    Compose final system prompt from base instructions + client context.

    Architecture:
    - Base Prompt (hardcoded): Your workflow, quality rules, how to create content
    - Client Context (.claude/CLAUDE.md): Their brand voice, audience, messaging

    The base prompt stays stable (you maintain it).
    Client context is gitignored (they customize it without breaking your logic).

    Args:
        base_prompt: Your hardcoded instructions (workflow, rules, quality thresholds)

    Returns:
        Composed prompt: base + client context (if exists)

    Examples:
        >>> base = "You are a content agent. Score 18+/25."
        >>> # Without client context
        >>> load_system_prompt(base)
        "You are a content agent. Score 18+/25."

        >>> # With client context (.claude/CLAUDE.md exists)
        >>> load_system_prompt(base)
        "You are a content agent. Score 18+/25.\\n\\n---\\n\\nCLIENT CONTEXT\\n..."
    """
    claude_dir = Path(__file__).parent.parent / '.claude'
    claude_md = claude_dir / 'CLAUDE.md'

    # If no client context file, just return base
    if not claude_md.exists():
        logger.info("No .claude/CLAUDE.md found - using base prompt only")
        logger.info("Clients can add brand context by creating .claude/CLAUDE.md")
        return base_prompt

    # Load client context
    try:
        client_context = claude_md.read_text().strip()

        if not client_context:
            logger.warning(".claude/CLAUDE.md exists but is empty - using base prompt only")
            return base_prompt

        # Compose: base + client context
        composed = f"""{base_prompt}

---

## CLIENT BUSINESS CONTEXT

{client_context}

---

IMPORTANT: Use the above CLIENT BUSINESS CONTEXT to:
- Match their brand voice and tone exactly
- Target their specific audience (role, stage, pain points)
- Reference their products/services when relevant
- Align with their messaging pillars and key topics
- Avoid topics/phrases they specified to avoid
- Use their preferred CTAs

Your workflow and quality rules stay the same. The client context shapes WHAT you say and HOW you say it.
"""

        logger.info(f"✅ Loaded client context from .claude/CLAUDE.md ({len(client_context)} chars)")
        logger.info(f"📝 Final composed prompt: {len(composed)} chars")

        return composed

    except Exception as e:
        logger.error(f"Error reading .claude/CLAUDE.md: {e}")
        logger.warning("Falling back to base prompt only")
        return base_prompt


def get_client_context_path() -> Path:
    """
    Get the path to client context file.

    Returns:
        Path to .claude/CLAUDE.md
    """
    return Path(__file__).parent.parent / '.claude' / 'CLAUDE.md'


def client_context_exists() -> bool:
    """
    Check if client has provided custom context.

    Returns:
        True if .claude/CLAUDE.md exists and has content
    """
    path = get_client_context_path()
    if not path.exists():
        return False

    try:
        content = path.read_text().strip()
        return len(content) > 0
    except:
        return False
