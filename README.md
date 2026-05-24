# LinkedIn Skill for OpenClaw

**An OpenClaw agent skill that drafts LinkedIn posts, sends them to Discord for review, and publishes only when you approve.**

> For agents, founders, and builders who want a consistent LinkedIn presence without the content overhead.

[![OpenClaw](https://img.shields.io/badge/Powered%20by-OpenClaw-ff6b00?style=for-the-badge)](https://openclaw.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE.txt)

---

## What It Does

This skill turns an OpenClaw agent into a LinkedIn content partner that:

1. **Drafts posts** in your configured voice — no emoji in the body, clear angle, 2–4 hashtags
2. **Sends drafts to Discord** for your review before anything goes live
3. **Publishes on approval** — you say "post it", the agent navigates to LinkedIn and posts via browser automation
4. **Supports AM/PM cadence** — AM posts for lessons and perspective, PM posts for behind-the-scenes

The agent never auto-posts. Draft → Discord review → your approval → post. That is the only flow.

---

## The Format

```
[LinkedIn post body — 150–280 chars, specific, no emoji]

#HashTag #HashTag #HashTag

---

P.S. — [Optional: for AI/builder brand posts] Posted by [Agent Name], my AI agent that helps me ship. [witty self-aware line]
```

**Rules:**
- No emoji in the post body
- Specific over generic — names, numbers, concrete outcomes
- AM posts: industry perspective, lessons, teachable moments
- PM posts: behind-the-scenes, honest takes, the grind reality
- 2–4 hashtags, text only

---

## Install

```bash
git clone https://github.com/tylerdotai/linkedin-skill.git ~/.openclaw/skills/linkedin
```

Then restart OpenClaw. The skill will appear in your agent's registry automatically.

---

## Configure

Edit `CONTEXT.md` with your own:

| What | Where | Example |
|------|-------|---------|
| Your name / brand | `CONTEXT.md` | `Your Name / Your Brand` |
| Your projects | `CONTEXT.md` | `project1.com, project2.com` |
| Your Discord webhook | `CONTEXT.md` | `https://discord.com/api/webhooks/...` |
| Posting cadence | `CONTEXT.md` | AM and PM, or just one |
| P.S. style | `CONTEXT.md` | Optional witty self-aware footer |

---

## Workflow

### Option A — Daily cadence

Set up cron jobs in OpenClaw for AM and PM posts. The agent gathers context (recent GitHub activity, project status), picks an angle, writes both drafts, and sends them to Discord for your review.

- **AM post:** Daily ~10am your timezone — lesson, perspective, industry take
- **PM post:** Daily ~6pm your timezone — behind-the-scenes, grind reality

### Option B — On-demand

Tell your agent:

```
Write me a LinkedIn post about [thing you built / learned / have an opinion on]
```

It will draft, send to Discord, and wait for your approval before posting.

---

## Review Pipeline

Every post goes to Discord first. This is the human-in-the-loop guardrail. The agent will not post until you explicitly tell it to. Draft → review → approve → post.

---

## Requirements

- [OpenClaw](https://openclaw.ai)
- A LinkedIn account (the agent uses browser automation to post)
- Discord webhook URL (for the draft review pipeline)
- Optional: cron scheduling for daily AM/PM cadence

---

## Customizing the Voice

Edit `CONTEXT.md` with your own:

- **Brand personality** — what tone fits you? (e.g., "direct, no-BS founder voice" or "thoughtful engineer")
- **Topics to avoid** — political, controversial, anything you would not want your employer to see
- **Posting preferences** — frequency, preferred angles, self-promotion vs. value-add ratio
- **P.S. style** — optional witty self-aware footer for AI/builder brand posts

---

## Example

**Prompt to agent:**
```
Write me a LinkedIn post about shipping a new feature
```

**Agent drafts:**
```
Just shipped the onboarding flow that users actually wanted.

Three rounds of feedback. Two rewrites. One late night that turned into a 4am "why does this keep breaking" session.

It works now. Users complete setup in under 2 minutes instead of abandoning halfway through.

That's the gap between "it works" and "people actually use it."

#IndieMakers #BuildInPublic #ProductDesign

---

P.S. — Posted by [Agent Name], my AI agent. Yes, an AI posted about shipping. That's the workflow.
```

**Agent sends to Discord → you review → you say "post it" → it posts via browser automation.**

---

## Related

- [OpenClaw](https://openclaw.ai) — the agent platform that runs this skill

---

## License

MIT