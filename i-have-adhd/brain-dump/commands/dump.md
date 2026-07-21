---
description: Dump everything on your mind, unfiltered — Claude will sort it into tasks, notes, and noise.
argument-hint: [everything you're holding in your head]
---

The user is doing a brain dump — offloading a jumble of thoughts so their working memory stops churning. Raw input: **$ARGUMENTS**

If `$ARGUMENTS` is empty, invite them to just start typing everything — messy is fine, no order needed — and stop.

When you have their dump, do NOT judge it, expand it into projects, or add your own ideas. Sort what's there:

1. **Read the whole thing first.** Don't react item by item.
2. **Sort into three buckets, and only these:**
   - **▶ Do** — real, actionable next steps. Rewrite each as a concrete action starting with a verb.
   - **📝 Note** — things worth keeping but not actions (ideas, facts, references).
   - **🌫 Let go** — worries, vents, or "shoulds" that don't need action. Naming them so they can be released is the whole point — be gentle here.
3. **Append the Do and Note items** to `.adhd/brain-dump.md` (create it if needed) with today's date as a heading, so nothing gets lost.
4. **End by asking one question:** which single "Do" item do they want to start with? Offer to hand it to `/focus:start`.

Keep the buckets tight. The goal is relief, not a bigger to-do list.
