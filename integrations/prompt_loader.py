"""
System Prompt Loader
====================

Two purposes:
1. Load writing style/rules prompts with client override support (Claude Projects-style)
2. Compose system prompts with client business context from CLAUDE.md

Priority hierarchy for style prompts:
1. .claude/prompts/{platform}/{prompt_name}.md (client platform-specific)
2. .claude/prompts/{prompt_name}.md (client global override)
3. prompts/styles/{platform}/default_{prompt_name}.md (default platform-specific)
4. prompts/styles/default_{prompt_name}.md (global default)
5. Hardcoded emergency fallback
"""
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# In-memory cache for loaded prompts
_PROMPT_CACHE: Dict[str, str] = {}

# Base directories for style prompts
_CLAUDE_PROMPTS_DIR = Path(__file__).parent.parent / ".claude" / "prompts"
_DEFAULTS_DIR = Path(__file__).parent.parent / "prompts" / "styles"

# Emergency fallback prompts (minimal)
_EMERGENCY_FALLBACKS = {
    "writing_rules": "Write like a human. Be clear, specific, and conversational. Avoid jargon and AI clichés.",
    "editor_standards": "Check for promotional language, overused phrases, and generic claims. Be specific and concrete.",
}


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


# ============================================================================
# STYLE PROMPT LOADING (NEW - Claude Projects-style overrides)
# ============================================================================

def load_prompt(
    prompt_name: str,
    platform: Optional[str] = None,
    use_cache: bool = True,
    emergency_fallback: Optional[str] = None
) -> str:
    """
    Load writing style/rules prompt with fallback hierarchy and caching.

    Args:
        prompt_name: Name of prompt file (without .md extension)
        platform: Optional platform (linkedin, twitter, email, etc.)
        use_cache: Whether to use in-memory cache (default: True)
        emergency_fallback: Custom fallback if all files missing

    Returns:
        Prompt content as string

    Examples:
        >>> load_prompt("writing_rules")  # Global rules
        >>> load_prompt("system_prompt", platform="linkedin")  # LinkedIn-specific
        >>> load_prompt("hooks", platform="twitter", use_cache=False)  # Bypass cache
    """
    # Create cache key
    cache_key = f"{platform}:{prompt_name}" if platform else prompt_name

    # Check cache first
    if use_cache and cache_key in _PROMPT_CACHE:
        logger.debug(f"Prompt cache hit: {cache_key}")
        return _PROMPT_CACHE[cache_key]

    # Try loading from files in priority order
    content = None

    # Priority 1: Client platform-specific override
    if platform:
        client_platform_path = _CLAUDE_PROMPTS_DIR / platform / f"{prompt_name}.md"
        content = _try_load_file(client_platform_path, f"client {platform}")

    # Priority 2: Client global override
    if not content:
        client_global_path = _CLAUDE_PROMPTS_DIR / f"{prompt_name}.md"
        content = _try_load_file(client_global_path, "client global")

    # Priority 3: Default platform-specific
    if not content and platform:
        default_platform_path = _DEFAULTS_DIR / platform / f"default_{prompt_name}.md"
        content = _try_load_file(default_platform_path, f"default {platform}")

    # Priority 4: Global default
    if not content:
        global_default_path = _DEFAULTS_DIR / f"default_{prompt_name}.md"
        content = _try_load_file(global_default_path, "global default")

    # Priority 5: Emergency fallback
    if not content:
        content = emergency_fallback or _EMERGENCY_FALLBACKS.get(prompt_name)
        if content:
            logger.warning(
                f"Using emergency fallback for {cache_key} "
                f"(no files found in any location)"
            )
        else:
            raise FileNotFoundError(
                f"Prompt '{prompt_name}' not found in any location:\n"
                f"  - .claude/prompts/{platform or ''}\n"
                f"  - .claude/prompts/\n"
                f"  - prompts/styles/{platform or ''}\n"
                f"  - prompts/styles/\n"
                f"  - Emergency fallbacks\n"
                f"Please create the file or provide an emergency_fallback parameter."
            )

    # Cache the result
    if use_cache:
        _PROMPT_CACHE[cache_key] = content
        logger.debug(f"Cached prompt: {cache_key}")

    return content


def _try_load_file(path: Path, source_description: str) -> Optional[str]:
    """
    Try to load a file, return None if it doesn't exist.

    Args:
        path: Path to file
        source_description: Human-readable description for logging

    Returns:
        File content or None if file doesn't exist
    """
    if not path.exists():
        return None

    try:
        content = path.read_text(encoding='utf-8')
        logger.info(f"Loaded prompt from {source_description}: {path.name}")
        return content
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        return None


def reload_prompts(prompt_name: Optional[str] = None):
    """
    Clear cache to force reload from disk.

    Useful when:
    - Client updates their custom prompts while app is running
    - Testing different prompt versions
    - Debugging prompt loading

    Args:
        prompt_name: Specific prompt to reload, or None to clear entire cache

    Examples:
        >>> reload_prompts()  # Clear all cached prompts
        >>> reload_prompts("writing_rules")  # Reload just writing rules
    """
    if prompt_name:
        # Clear specific prompt (all platform variations)
        keys_to_remove = [k for k in _PROMPT_CACHE if prompt_name in k]
        for key in keys_to_remove:
            del _PROMPT_CACHE[key]
        logger.info(f"Reloaded prompt: {prompt_name}")
    else:
        _PROMPT_CACHE.clear()
        logger.info("Cleared all cached prompts")


def get_cache_stats() -> Dict[str, any]:
    """
    Get cache statistics for debugging.

    Returns:
        Dictionary with cache size and keys
    """
    return {
        "cache_size": len(_PROMPT_CACHE),
        "cached_prompts": list(_PROMPT_CACHE.keys())
    }


# Convenience functions for common prompts
def load_writing_rules() -> str:
    """Load global writing rules (WRITE_LIKE_HUMAN_RULES)."""
    return load_prompt("writing_rules")


def load_editor_standards() -> str:
    """Load editor-in-chief standards."""
    return load_prompt("editor_standards")
