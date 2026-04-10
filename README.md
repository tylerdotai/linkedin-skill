<p align="center">
  <img src="images/logo.png" alt="LinkedIn Skill" width="96" />
</p>

# LinkedIn Skill for OpenClaw

**An AI agent that writes and publishes LinkedIn posts in your voice — drafts for your review first, posts only when you approve.**

> Built for founders, builders, and indie makers who want a consistent LinkedIn presence without the content overhead.

[![OpenClaw](https://img.shields.io/badge/Powered%20by-OpenClaw-ff6b00?style=for-the-badge)](https://openclaw.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE.txt)

---

## What It Does

This skill turns an OpenClaw agent into a LinkedIn content partner that:

1. **Drafts posts** in your voice — no emoji in the body, clear angle, relevant hashtags
2. **Saves drafts to Discord** for your review before anything goes live
3. **Publishes on approval** — you say "post it", the agent posts it
4. **Supports AI/builder brand voice** — includes a `P.S.` pattern for posts about AI-built content (a little self-aware humor earns credibility)

The agent knows the difference between an AM-style "lesson/perspective" post and a PM-style "behind-the-scenes" post. You pick the angle or let it pick.

---

## The Format

```
[LinkedIn post body — 150–280 chars, specific, no emoji]

#HashTag #HashTag #HashTag

---

P.S. — [Optional: for AI/builder brand posts] This was posted by [Agent Name], my AI agent that helps me ship. [witty self-aware line]
```

**Rules:**
- No emoji in the post body
- Specific over generic — "we replaced the hero section because users couldn't figure out what the page did in 3 seconds" beats "we improved our onboarding"
- AM posts: industry perspective, lessons, teachable moments
- PM posts: behind-the-scenes, honest takes, the grind reality

---

## Install

```bash
git clone https://github.com/tylerdotai/linkedin-skill.git ~/.openclaw/skills/linkedin
```

Then restart OpenClaw. The skill will appear in your agent's registry automatically.

---

## Configure

Edit the `SKILL.md` frontmatter `description` field to describe your own brand/project. Update the `CONTEXT.md` file with:

| What | Where | Example |
|------|-------|---------|
| Your name / brand | `CONTEXT.md` | `Tyler Delano / Flume SaaS Factory` |
| Your projects | `CONTEXT.md` | `clawplex.dev, faireplay.app, ...` |
| Your Discord webhook | Skill instructions | For review pipeline |
| Posting cadence | `CONTEXT.md` | AM: 10am CST, PM: 6pm CST |

---

## Workflow

### Option A — Agent prompts you (daily cadence)

Set up cron jobs in OpenClaw:

- **AM post:** Daily ~10 AM your timezone
- **PM post:** Daily ~6 PM your timezone

The agent gathers context (recent GitHub activity, project status), picks an angle, writes both drafts, and sends them to Discord for your review.

### Option B — On-demand

Just tell your agent:

```
Write me a LinkedIn post about [thing you built / learned / have an opinion on]
```

It will draft, save to Discord, and wait for your approval before posting.

---

## Review Pipeline

Posts go to Discord first — this is the human-in-the-loop guardrail. Nothing hits LinkedIn without your explicit approval.

The agent will not post without being told to. Draft → review → approve → post.

---

## Requirements

- [OpenClaw](https://openclaw.ai)
- A LinkedIn account (the agent uses browser automation)
- Discord webhook URL (for draft review pipeline)
- Optional: cron scheduling for daily AM/PM cadence

---

## Customizing the Voice

Edit `CONTEXT.md` with your own:

- **Brand personality** — what tone fits you? (e.g., "direct, no-BS founder voice" or "thoughtful engineer")
- **Topics to avoid** — political, controversial, etc.
- **Posting preferences** — frequency, preferred angles, self-promotion vs. value-add ratio
- **P.S. style** — optional witty self-aware footer for AI/builder brand posts

---

## Example

**Prompt to agent:**
```
Write me a LinkedIn post about our DFW Node 02 meetup in Arlington on April 15
```

**Agent drafts:**
```
Two DFW meetups coming up — grab a laptop and come show what you're building.

DFW Node 02 — Arlington
April 15, 2026 · 2–3 PM CDT
Spark Coworking · Texas Live! district
RSVP: luma.com/yppasqmp

DFW Node 03 — Fort Worth
May 6, 2026 · 2–3 PM CDT
CreateFW · Fort Worth, TX
RSVP: luma.com/0oum4slu

No agenda. No slides. Just builders with laptops showing up.

#DFW #AIBUILDERS #OpenClaw #DallasFortWorth

---

P.S. — This was posted by Dexter, my OpenClaw agent. Yes, an AI posted about an AI builder meetup. 🦞
```

**Agent sends to Discord → you review → you say "post it" → it posts.**

---

## Related

- [OpenClaw](https://openclaw.ai) — the agent platform that runs this skill
- [ClawPlex](https://clawplex.dev) — DFW AI Builder Community (where this was born)
- [zk-voting-system](https://github.com/tylerdotai/zk-voting-system) — another OpenClaw-powered project

---

## License

MIT
