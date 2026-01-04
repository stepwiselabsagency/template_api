# How this "multi-phase automation" works going forward

When Phase 03 starts:
1) Add `.github/phases/phase03/issues/*.md`
2) Add new label `phase-03` to `.github/labels.yml`
3) Run workflow:
   - `sync-labels`
   - `create-phase-issues` with input `phase03`
4) Manually add `label:phase-03` issues to the same Project board and set Phase=Phase 03

That's it.

---

# Quick start checklist (do this now)

1) **Commit the files** above
2) Run **Actions → sync-labels**
3) Add Phase 02 milestone markdown files (`09_...` to `16_...`)
4) Run **Actions → create-phase-issues (phase02)**
5) Manual:
   - Create Project v2 board + fields (one-time)
   - Add issues with `label:phase-02` to the project
   - Set Status = Backlog, Phase = Phase 02

