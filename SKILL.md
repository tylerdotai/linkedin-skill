---
name: linkedin-posting
description: "Write, review, and publish LinkedIn posts from an OpenClaw agent. Use when asked to create a LinkedIn post, write LinkedIn content, draft a post for review, or publish to LinkedIn. Posts are drafted first and sent to Discord for human review before publishing — never auto-post. Supports AM/PM cadence, brand voice guidance, hashtag strategy, and the P.S. pattern for AI/builder brand posts. Configure: set BRAND_NAME, PROJECTS, DISCORD_WEBHOOK_URL, and optional CRON_SCHEDULE in CONTEXT.md."
---

# LinkedIn Posting Skill

An OpenClaw agent skill for writing and publishing LinkedIn posts in your voice — with a human review gate before anything goes live.

## Core Workflow

```
1. Gather context (recent activity, project news, opinions)
2. Pick angle — AM (lesson/perspective) or PM (behind-the-scenes)
3. Draft post — specific, no emoji in body, 150–280 chars
4. Add hashtags (2–4, text only)
5. Add optional P.S. line for AI/builder brand posts
6. Save draft to memory/content-drafts/YYYY-MM-DD.md
7. Send draft to Discord review channel
8. WAIT — do not post until human approves
9. Publish on approval
```

## Voice Rules

**DO:**
- Write in first person ("I", "we", "just shipped")
- Be specific — names, numbers, concrete outcomes
- Keep paragraphs short (1–2 sentences)
- End with a clear CTA or thought-provoking line
- Use the P.S. pattern for AI/agent-built projects

**DON'T:**
- Use emoji in the post body
- Write generic marketing copy ("we're excited to announce")
- Oversell — show don't tell
- Post without human review

## Post Structure

```
[Body — 150–280 chars, specific angle, professional but human]
[Blank line]
#HashTag #HashTag #HashTag
[Blank line, three dashes]
P.S. — [Optional AI-brand self-aware line]
```

## P.S. Pattern

For posts about AI-built projects or agent activity, add a P.S. line:

```
P.S. — This was posted by [Agent Name], my AI agent that helps me ship. [witty self-aware line]
```

Examples:
- `P.S. — Posted by Dexter, my OpenClaw agent. Yes, an AI posted about an AI builder meetup. 🦞`
- `P.S. — My AI co-founder Hoss wrote the first draft of this. I edited it. That's the workflow.`
- `P.S. — This post was drafted by an AI and reviewed by a human. That's the point.`

## AM vs PM Angles

**AM posts (10am cadence):**
- A lesson learned or mistake made
- Industry opinion or hot take
- Something specific you shipped and what it taught you
- Useful framework or mental model

**PM posts (6pm cadence):**
- Behind-the-scenes of how something was built
- Honest take on the grind — what working on your own projects actually looks like
- Late-night session reality
- Contrast / comparison that reveals something

**Rule: AM and PM must be DIFFERENT angles. Don't repeat the same message twice in one day.**

## Draft → Review → Post Flow

1. Save draft to `memory/content-drafts/YYYY-MM-DD-linkedin.md`
2. POST to Discord review channel (see `DISCORD_WEBHOOK_URL` in `CONTEXT.md`)
3. Include this header in the Discord message:

```
**LinkedIn Draft — Tyler review before posting**

[DRAFT HERE]

---
React ✅ to approve, ❌ to discard
```

4. Wait for human reaction on Discord before posting
5. On approval: use browser tool to navigate to LinkedIn and publish

## Context Variables

Read `CONTEXT.md` for these before drafting:

| Variable | What it is |
|----------|-----------|
| `BRAND_NAME` | Your name or company brand |
| `YOUR_VOICE` | Tone/personality guidance |
| `PROJECTS` | Active projects to reference |
| `TOPICS_TO_AVOID` | Sensitive topics |
| `PREFERRED_CADENCE` | AM only, PM only, or both |
| `DISCORD_WEBHOOK_URL` | Where to send drafts for review |
| `PS_STYLE` | Your preferred P.S. line style |

## Content Sources

When gathering context before drafting:

```bash
# Recent GitHub activity
gh run list --limit 10

# Recent commits
gh api repos/{owner}/{repo}/commits --limit 5

# Read memory files for recent decisions
ls memory/ | sort | tail -7
```

## Quality Checklist

Before sending to Discord, verify:
- [ ] No emoji in the body
- [ ] Specific — names, numbers, outcomes
- [ ] Clear angle — not unfocused rambling
- [ ] Hashtags relevant (not overused generic tags)
- [ ] P.S. line if the post is about AI-built content
- [ ] Fits 150–280 chars (LinkedIn short post range)
