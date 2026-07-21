# i-have-adhd

A tiny Claude Code plugin marketplace for the ADHD brain working inside a terminal.

It doesn't try to "fix" you. It just removes the specific friction points that make coding hard when your attention isn't a straight line: tasks that are too big to start, thoughts that won't stop interrupting, and the brutal cost of losing your place.

## Install

From Claude Code:

```
/plugin marketplace add ./i-have-adhd
```

(or point it at this repo's URL if it lives on GitHub)

Then browse and install plugins with:

```
/plugin
```

## What's inside

### `focus-mode` — start small, stay put
- `/focus:start [task]` — shrink an overwhelming task down to one tiny, unmissable first step and start a time-box.
- `/focus:next` — get *only* the single next step. No menu, no re-planning.
- `/focus:park [thought]` — capture a distraction so you can let it go and keep working.

### `brain-dump` — empty the churn
- `/dump [everything]` — offload the jumble in your head; Claude sorts it into **Do**, **Note**, and **Let go**.

### `where-was-i` — never pay the cold-start tax
- `/where-was-i:save` — drop a breadcrumb before you get pulled away.
- `/where-was-i:resume` — pick the thread back up in three lines when you return.

### `body-double` — quiet company
- A `body-double` subagent that co-works beside you: light check-ins, gentle redirection, zero nagging.

## How it stores things

Plugins write small scratch files under `.adhd/` in your working directory (`parking-lot.md`, `brain-dump.md`, `breadcrumb.md`). Add `.adhd/` to your `.gitignore` if you'd rather keep them out of version control.

## Made with care

Built for anyone whose brain runs a little differently. Distraction isn't a character flaw — it's just a thing to design around. 💛
