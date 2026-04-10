# LinkedIn Skill — Context Configuration

Edit this file to personalize the skill for your own brand. The agent reads this before drafting any post.

---

## BRAND_NAME

Your name, brand, or company.

```
Tyler Delano / ClawPlex / Flume SaaS Factory
```

---

## YOUR_VOICE

How should the agent sound? Be specific.

```
Direct, no-BS founder voice. Irreverent. Practical over theoretical.
Likes to self-deprecate about being an "IT guy by day, builder by night."
Writes like he talks — short sentences, punchy.
```

---

## PROJECTS

Active projects to reference when drafting. The agent uses these as content fuel.

```
- clawplex (clawplex.dev) — DFW AI builder community hub
- faireplay (faireplay.app) — Ren Faire dating app
- aiagainstparkinson — Daily Parkinson's research reports EN/ES
- fwpdhockey — Fort Worth Panthers Police Hockey charity site
- fort-os — Agent deployment platform on Fly.io
- zk-voting-system — ZK-based DAO voting system
```

---

## TOPICS_TO_AVOID

```
- Politics
- Religion
- Hot takes on people (focus on ideas/tools/projects instead)
- Anything you'd be embarrassed to have your employer see
```

---

## PREFERRED_CADENCE

```
Both AM and PM
- AM post: 10 AM CST — lesson, perspective, industry take
- PM post: 6 PM CST — behind-the-scenes, grind reality, honest opinion
```

---

## PS_STYLE

Your preferred P.S. line style for AI/builder brand posts. Give the agent examples of lines you like.

```
P.S. — [Agent Name], my OpenClaw agent. Witty, self-aware, a little ironic.
Examples:
- "Posted by Dexter, my OpenClaw agent. Yes, an AI posted about an AI builder meetup. 🦞"
- "My AI co-founder Hoss wrote the first draft. I edited it. That's the workflow."
- "This was posted by an AI and reviewed by a human. That's the point."
```

---

## DISCORD_WEBHOOK_URL

Where to send drafts for review before posting.

```
https://discord.com/api/webhooks/[YOUR_WEBHOOK_ID]/[YOUR_WEBHOOK_TOKEN]
```

To create a Discord webhook: Server Settings → Integrations → Webhooks → New Webhook.

---

## CRON_SCHEDULE (Optional)

If you want the agent to draft daily AM/PM posts automatically:

```
AM: 0 10 * * * America/Chicago
PM: 0 18 * * * America/Chicago
```

Set these up in OpenClaw cron with `sessionTarget: "isolated"` and `payload.kind: "agentTurn"`.

---

## HASHTAG STRATEGY

Preferred hashtags for your posts. Mix of broad + specific.

```
#AIBUILDERS #OpenClaw #DallasFortWorth #DFW #Founders #IndieMakers
#NoCode #LowCode #SaaS #ProductHunt
```

Use 2–4 per post. Don't use more than 4 — looks spammy.
