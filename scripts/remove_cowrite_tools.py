#!/usr/bin/env python3
"""
Remove co-write tools from claude_agent_handler.py
They are now in cowrite_tools.py and will be lazy-loaded
"""

# Read the file
with open('slack_bot/claude_agent_handler.py', 'r') as f:
    lines = f.readlines()

# Keep lines before co-write section (0-453) and after (841+)
# Note: Python uses 0-indexing, so line 454 is index 453
new_lines = lines[:453]  # Lines 1-453

# Add comment about moved tools
new_lines.append('\n')
new_lines.append('# ================== CO-WRITE TOOLS MOVED TO cowrite_tools.py ==================\n')
new_lines.append('# Co-write tools (generate_post_*, quality_check_*, apply_fixes_*) are now\n')
new_lines.append('# lazy-loaded only when user explicitly requests co-write mode.\n')
new_lines.append('# This ensures batch mode is used by default (99% of requests).\n')
new_lines.append('\n')

# Add batch tools section (line 841 onwards)
new_lines.extend(lines[840:])  # Line 841 is index 840

# Write the modified file
with open('slack_bot/claude_agent_handler.py', 'w') as f:
    f.writelines(new_lines)

print(f"Removed {840 - 453} lines of co-write tools")
print("Co-write tools section replaced with comment")