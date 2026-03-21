# LinkedIn Skill for OpenClaw

<p align="center">
  <img src="images/logo.png" alt="LinkedIn Skill logo" width="96" />
</p>

> An OpenClaw skill that guides browser-based LinkedIn profile management, posting, and engagement workflows.

[![OpenClaw](https://img.shields.io/badge/OpenClaw-skill-ff6b6b)](#about)
[![Requires](https://img.shields.io/badge/Requires-browser-blue)](#requirements)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.txt)

## About

This repo packages a single OpenClaw skill definition for LinkedIn use cases. The actual capability lives in `SKILL.md`, which tells OpenClaw to use the `browser` tool for profile edits, content publishing, and feed engagement.

## What Is In This Repo

| Path | Purpose |
|------|---------|
| `SKILL.md` | Skill metadata, allowed tools, and usage guidance |
| `images/logo.png` | Skill logo |
| `README.md` | Repository overview |

## Requirements

| Requirement | Details |
|------------|---------|
| Host app | OpenClaw |
| Required tool | `browser` |
| Account | A LinkedIn account with an active logged-in browser session |

## Supported Workflows

- View and update profile sections such as headline, About, and skills
- Draft and publish LinkedIn posts
- Like, comment on, and repost feed content
- Follow LinkedIn-specific tone and branding guidance during browser automation

## Install

Clone the repo into your local OpenClaw skills directory:

```bash
git clone https://github.com/tylerdotai/linkedin-skill.git ~/.openclaw/skills/linkedin
```

Then restart OpenClaw so it reloads the skill registry.

## Usage

Once the skill is available, prompt OpenClaw with a LinkedIn task such as:

```text
Update my LinkedIn headline to "Founder building AI tooling"
```

```text
Create a LinkedIn post about shipping a new product demo
```

For the full workflow guide, read `SKILL.md`.

## Notes

- This repo does not ship LinkedIn API integrations or standalone automation code
- Actions depend on OpenClaw's browser tool and your authenticated LinkedIn session
- Review generated copy before publishing

## License

MIT License - see `LICENSE.txt`.
