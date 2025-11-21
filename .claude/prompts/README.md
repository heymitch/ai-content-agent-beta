# Custom Writing Style Overrides

Drop your custom prompt files in this folder to override the default writing style and rules.

## How It Works

The agent loads prompts with this priority:
1. **Your custom prompts** (this folder) - Highest priority
2. **Default prompts** (`prompts/styles/`) - Fallback if no custom file

Your customizations are **gitignored** - they won't be committed to the repository. This lets you customize writing style per-deployment without touching code.

---

## Available Prompts

### Global Overrides (Affect All Platforms)

**`writing_rules.md`** - Core writing guidelines
- Controls: Voice, tone, banned phrases, formatting rules
- Default: Clean, conversational, anti-AI style
- Customize: Add your brand voice, specific phrases to use/avoid

**`editor_standards.md`** - Editorial quality standards
- Controls: What gets flagged in quality checks
- Default: Anti-promotional, anti-generic guidelines
- Customize: Add your quality criteria, acceptable promotional language

### Platform-Specific Overrides

Create folders for each platform and drop `.md` files inside:

```
.claude/prompts/
├── linkedin/
│   ├── hooks.md          # Hook generation templates
│   ├── draft.md          # Post creation instructions
│   └── grading.md        # Scoring criteria
├── twitter/
│   ├── hooks.md
│   ├── draft.md
│   └── format_selection.md
└── email/
    ├── draft.md
    └── email_types.md
```

---

## Example: Customize LinkedIn Writing Style

Create `.claude/prompts/linkedin/draft.md`:

```markdown
When writing LinkedIn posts:

**Tone**: Professional but warm, thought-leadership style
**Structure**: Always start with a bold claim, then 3 examples, then insight
**Voice**: Use "we" not "I" (writing as company)
**CTAs**: Always end with "What's your experience with [topic]?"
**Banned phrases**: "game-changer", "disrupt", "leverage"
**Preferred phrases**: "transform", "improve", "enable"
```

Save that file, and all LinkedIn posts will follow your custom style!

---

## Example: Global Writing Rules Override

Create `.claude/prompts/writing_rules.md`:

```markdown
BRAND VOICE: Tech-forward but accessible

ALWAYS USE:
- Oxford commas
- Em-dashes for emphasis
- Active voice 100% of the time

NEVER USE:
- Exclamation points (except quotes)
- Rhetorical questions
- Lists with more than 5 items

TONE: Confident, specific, data-driven
```

This overrides the default writing rules for ALL platforms.

---

## Testing Your Customizations

1. Create your `.md` file in `.claude/prompts/`
2. Restart the app or wait for next content generation
3. The agent will automatically use your custom style
4. Check logs to see which prompts were loaded

**Pro tip**: Start by copying the defaults from `prompts/styles/` and editing them.

---

## Fallback Behavior

If a custom file is missing, the agent falls back gracefully:
1. Check `.claude/prompts/{platform}/prompt_name.md`
2. Check `.claude/prompts/prompt_name.md`
3. Check `prompts/styles/{platform}/default_prompt_name.md`
4. Check `prompts/styles/default_prompt_name.md`
5. Use emergency hardcoded fallback

**You can't break anything** - missing files just use defaults.

---

## Need Help?

See the defaults in `prompts/styles/` for examples.

Questions? Check the main README or deployment guide.
