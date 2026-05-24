# PROJECT KNOWLEDGE BASE

**Generated:** 2026-05-22
**Commit:** 854e9d0
**Branch:** main

## OVERVIEW

OpenClaw skill that drafts LinkedIn posts in Tyler's voice, sends to Discord for human review, publishes on approval. No build step — pure Markdown/SKILL.md configuration.

## STRUCTURE

```
linkedin-skill/
├── SKILL.md       # Core workflow + voice rules (skill definition)
├── CONTEXT.md     # Brand config (projects, voice, cadence, webhook)
├── README.md      # User-facing install/config docs
├── images/        # Logo + screenshot (static assets)
└── .omo/          # opencode internal (ignore)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Draft a LinkedIn post | SKILL.md | Steps 1-9, voice rules, format |
| Configure brand voice | CONTEXT.md | YOUR_VOICE, PROJECTS, PS_STYLE |
| Set up Discord review | CONTEXT.md | DISCORD_WEBHOOK_URL |
| Schedule AM/PM cadence | CONTEXT.md | CRON_SCHEDULE (optional) |
| Change hashtag strategy | CONTEXT.md | HASHTAG_STRATEGY |

## CONVENTIONS

- Posts: 150-280 chars, no emoji in body, 2-4 hashtags
- P.S. pattern for AI/builder posts: self-aware, ironic
- AM post = lesson/perspective; PM post = behind-the-scenes
- Draft → Discord review → human approval → publish only on approval

## ANTI-PATTERNS (THIS PROJECT)

**DON'T in posts:**
- Emoji in body (plain text only)
- Generic marketing copy ("we're excited to announce")
- Overselling — show don't tell

**Content topics to avoid:**
- Politics, religion, hot takes on people
- Anything embarrassing to employer

**Workflow:**
- Never auto-post — always Discord review first
- AM and PM must be different angles same day

## UNIQUE STYLES

- P.S. footer pattern: self-aware AI agent humor for builder brand posts
- "IT guy by day, builder by night" founder voice
- Specific over generic — names, numbers, concrete outcomes

## COMMANDS

```bash
# No build/test — this is a skill, not a codebase
# Clone to install:
git clone https://github.com/tylerdotai/linkedin-skill.git ~/.openclaw/skills/linkedin
```

## NOTES

- No CI/CD, no tests, no TypeScript/Python — pure Markdown skill definition
- .omo/ directory is opencode internal — not part of the skill distribution
- images/ contains logo.png and screenshot.png for README display
