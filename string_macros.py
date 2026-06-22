#!/usr/bin/env python3
"""
STRING MACROS - FEATURE LIST
===========================================================================

  Current version: v3.20.0
  File ratio (default 12): 2 Raw - 3 Inef - 7 Normal  (2:3:7)
  Time-sensitive ratio:    6 Raw - 0 Inef - 6 Normal  (1:1)

  NEW FEATURES IN v3.20.0:
  - (choose1) hub folder support: each cycle picks one child folder at random
    (equal probability per folder, regardless of file count), then picks one
    file from that child. Child folders can be named arbitrarily (no numeric
    prefix required). If a child folder itself carries (random) tag, its
    sub-subfolders are handled via the normal (random) logic.
  - Recursive pool size calculation for ManualHistoryTracker: fixes combination
    history deduplication for folders with hubs and nested structures.
  - parse_max_files now returns None if no -N- pattern is found, allowing
    proper override in same-number folder pooling.
  - Removed dead 'dmwm_file_set' variable and all related logic from
    scan_for_numbered_subfolders, string_cycle, apply_cycle_features, and main().

===========================================================================
                    GROUP 1: PAUSE BREAKS
===========================================================================

1. WITHIN-FILE PAUSES
   Files: Normal + Inef (Raw = 0%)
   Value: random % drawn fresh per file (decimal, never rounded):
     Normal: rng.uniform(2%, 5%)  e.g. 2.14%, 3.87%
     Inef:   rng.uniform(10%, 15%)  e.g. 11.6%, 13.2%
   e.g. 20s Normal file at 3.4% -> 0.68s pause
   One pause per file in middle 80%. Skips drags, rapid-clicks, pre-DragStart.

2. PRE-PLAY BUFFER
   Files: ALL (including between cycles in the outer loop)
   Value: rng.uniform(500, 800) ms * mult — applied before every file and
   between every cycle boundary (end of cycle N -> start of cycle N+1).
   Between-cycle buffer was added in v3.18.45 to prevent 0ms gap between
   the last DragEnd of one cycle and the cursor transition of the next,
   which caused drag-click at wrong position.

2b. PER-VERSION TARGET DURATION VARIANCE
    Each version gets a random target duration of base +/- 5 minutes.
    e.g. --target-minutes 60 produces versions targeting 55-65 min each.
    Drawn as rng.uniform(-300000, +300000) ms float per version.
    The effective target (used by the build loop) uses this per-version value.
    Inef massive pause budget is also pre-sampled against the per-version target.
    Shown in print output: "Target: 62m 14s (base 60m +2.2m)"

3. INEF BEFORE-FILE PAUSE
   Files: Inef only, only if current cycle >= 25s
   Value: rng.uniform(10000, 30000) ms flat (no mult)
   Added between each full cycle (F1->...->FN loop).
   Cursor drifts during this pause toward next file start position.

4. INEFFICIENT MASSIVE PAUSE
   Files: Inef only
   Value: rng.uniform(240000, 420000) ms flat (no mult) = 4-7 min
   One pause inserted at a safe random point after all cycles complete.
   Loop pre-samples pause so total file stays near target duration.
   Safe: no drag, no rapid-click, not pre-DragStart, not first/last 10%.

5. MULTIPLIER SYSTEM
   Continuous random range, 4 decimal places (never rounded):
     Raw:    rng.uniform(1.1, 1.2)  e.g. 1.13, 1.17
     Normal: rng.uniform(1.5, 1.7)  e.g. 1.53, 1.67
     Inef:   rng.uniform(2.0, 3.0)  e.g. 2.14, 2.87
   Multiplied (baked in at generation time):
     - Pre-play buffer: rng.uniform(500, 800) * mult
     - Cursor transition: rng.uniform(200, 400) * mult
     - Within-file % pause: file_duration * pct (pct not multiplied; the pause
       duration grows with larger files naturally)
     - Mid-event random pause (50% chance/cycle): rng.uniform(200, 800) * mult
   NOT multiplied (flat): inef before-file pause, massive pause, distraction files

===========================================================================
                    GROUP 2: PATTERN BREAKING
===========================================================================

6. CURSOR TRANSITION TO START POINT
   Files: ALL (SKIPPED for click-sensitive)
   Value: rng.uniform(200, 400) ms * mult — human path between files.
   Skipped entirely for click-sensitive folders.

7. IDLE CURSOR WANDERING
   Files: ALL (SKIPPED for click-sensitive)
   Fills existing recording gaps > 2000ms with cursor arcs/drifts.
   Does NOT add time — movements fit inside the existing gap.
   Not shown in manifest (zero time impact on total).

8. MOUSE JITTER
   Files: ALL (SKIPPED for click-sensitive)
   Value: 9-21% of mouse moves get +/-1-3px random offsets.
   Excluded near drags, rapid-click sequences, first/last 10% of file.

9. VIRTUAL QUEUE - SUBFOLDER FILES
   Each subfolder has its own shuffled queue. No file repeats until all
   others used. Boundary guard prevents same file at queue wrap.
   Same mechanism applies to distraction files (Feature 32).

===========================================================================
                    GROUP 3: SMOOTH OPERATION
===========================================================================

10. RAPID CLICK PROTECTION
    3+ clicks within 1500ms detected. Jitter exclusion extended to 1500ms.
    Detection set includes: Click, DragStart, LeftDown, LeftUp, RightDown, RightUp.
    LeftDown/LeftUp added (v3.18.81) so native button-event double-clicks are
    also protected — previously only 'Click' and 'DragStart' were detected.

11. DRAG OPERATION PROTECTION
    Hold+Move+Release detected. No jitter during entire drag sequence.

12. EVENT TIMING INTEGRITY
    No modifications inside drags, pre-DragStart, rapid-clicks, or first/
    last 10%. Prevents click-hold clamping (unintended long drags).

13. COMBINATION HISTORY
    Tracks used file combos per subfolder across cycles.
    Avoids repeating same combination. Persists via uploaded .txt files.

14. MANUAL HISTORY UPLOAD
    Upload COMBINATION_HISTORY_XX.txt to input_macros/combination_history/
    All .txt files read; those combos avoided in future runs.

15. ALPHABETICAL FILE NAMING
    Raw: ^XX_A  Inef: XX_C (not-sign prefix)  Normal: XX_E (no prefix)
    Output folder: (bundle_id) folder_name

16. FOLDER-NUMBER STRUCTURE
    F1, F2, F3.5 etc. F<N> prefix preferred; other numbers in name ignored.
    e.g. "F3- press 1 to bank" -> num=3, the "1" in name is ignored.

17. OPTIONAL TAG
    Default chance: rng.uniform(24%, 33%) per bundle (decimal, never rounded).
    Custom number: used as CENTRE of +/-2% random range (never rounded).
      e.g. "optional23" -> rng.uniform(21%, 25%)
           "optional50" -> rng.uniform(48%, 52%)
           "optional50.5" -> rng.uniform(48.5%, 52.5%)
    This adds variety so the same folder never hits the exact same threshold.
    Range clamped so it never goes below 1% or above 99%.
    Max-files/loops: "optional58-6-" = 58% centre, pick 1-6 files/loops.
    No optional: "F1-4-" = always included, pick 1-4 files.
    always_first/last wraps the entire picked group once (not per file).
    For nested folders: -N- means max N complete sub-cycles (loops), not files.

18. END TAG
    Uses word-boundary match (end) — "tend" does NOT match.
    Loop stops after this folder. Always included if reached.

19. OPTIONAL+END COMBO TAG
    Chosen = loop stops here. Skipped = loop continues.
    Renamed from "optional/end" in v3.18.42.

20. TIME SENSITIVE TAG
    Ratio: 1:1 (half raw, half normal, zero inef).
    Main folder tag propagates to ALL subfolders.

21. CLICK SENSITIVE TAG
    Disables ALL coordinate-changing features:
    cursor path, mouse jitter, idle wandering, distraction insertion.
    Main folder tag propagates to ALL subfolders.
    Accepted: "click sensitive" / "click/time sensitive" / "click+time sensitive"

22. CLICK/TIME SENSITIVE COMBO TAG
    Both tag rules active: 1:1 ratio + no cursor/jitter/idle/distraction.

23. DONT USE FEATURES ON ME TAG
    Exact folder name (case-insensitive). Files inserted completely unmodified.
    Marked [UNMODIFIED] in manifest.

24. ALWAYS FIRST / LAST FILES
    Tag in FILENAME (not folder name). Three modes:
    A) Root-level (next to F1/F2/F3 subfolders): fires ONCE per strung file,
       before all cycles start and after all cycles end.
    B) Inside a specific subfolder (e.g. F0): wraps ONLY that subfolder's files.
       Pattern: [AF] -> F0 files -> [AL] -> F1 -> F2 -> ...
    C) Flat/single-subfolder folder: fires ONCE at very start and very end.
    For nested folders (Feature 39): AF/AL wrap all loops together, not per loop.

25. COMPREHENSIVE MANIFEST
    !_MANIFEST_XX_!.txt in output folder. Shows per-version:
    - File type, multiplier, total pause added
    - Breakdown (x = mult applied, - = flat): PRE-Play Buffer, Within File Pauses,
      CURSOR to Start Point, POST-SNAP GAP, DISTRACTION File Pause,
      INEFFICIENT Before File Pause, INEFFICIENT MASSIVE PAUSE
    - Full file list with cumulative end times

26. SPECIFIC FOLDERS FILTERING
    --specific-folders <file>: process only folders (and optionally subfolders)
    listed in the file. Matching is case-insensitive, whitespace-stripped.

    File format (one entry per line):
      FolderName                   -> include folder, ALL its subfolders
      FolderName: F1, F3, F4       -> include folder, ONLY subfolders F1 F3 F4
      FolderName: F1, F3-F5        -> include folder, F1 and range F3 through F5

    Examples:
      22- Craft Dia- edge- lamp bank Z- S
      22- Craft Dia- edge- lamp bank Z- S: F1, F2, F4
      58- Smth R2H only: F1-F3

    - Subfolder numbers are case-insensitive (F1 = f1 = 1)
    - Decimal subfolders supported: F3.5
    - If a requested subfolder doesn't exist, it is skipped with a warning
    - Output folder: (bundle_id) folder_name

27. CHAT INSERTS
    --no-chat disables. After all versions are saved, floor(total * 0.20)
    files are chosen at random (all types eligible, including raw) and one
    chat file is spliced into each. 10 files → 2; 22 → 4; 5 → 1; 4 → 0.

28. PRE-PLAY BUFFER GUARANTEE
    files_added int counter (not list truthiness) ensures buffer fires before
    every file including always_first/last. Avoids Python nonlocal edge case.

29. FAIL-FAST ERROR HANDLING
    Fatal errors call sys.exit(1) so GitHub Actions fails at the right step.

30. FLAT FOLDER SUPPORT
    JSON files directly in main folder (no numbered subfolders) = single pool.
    All tags (always_first/last, time_sensitive, click_sensitive) still work.

31. DISTRACTION FILE GENERATION + INSERTION
    Trigger: DISTRACTIONS/ folder in input_macros/
    Generates 50 temp files (30s-2min), each using 3 of 7 features:
    wander, pause, right-click, typing, key-spam, shapes, backspace-hold.
    backspace-hold (v3.18.83): holds Backspace 1-3 s (float ms, not rounded).
    Chance: Normal 3.5-5%, Inef 3.5-7%, Raw 0%, Click-sensitive 0%.
    NOT multiplied — flat pre-built durations. Shown in manifest.

32. VIRTUAL QUEUE - DISTRACTION FILES
    All 50 distraction files rotate before any repeat.
    Boundary guard prevents consecutive repeat at queue wrap.

33. 2:3:7 FILE RATIO DISTRIBUTION
    raw=round(v x 2/12), inef=round(v x 3/12), normal=remainder.
    12->2:3:7, 24->4:6:14, 20->3:5:12.
    Time-sensitive override: 1:1 raw:normal, zero inef.

34. FILE TRANSITION START GAP PROTECTION
    80-150ms gap (POST-SNAP GAP) between snap MouseMove and first event of
    next file. Prevents zero-gap DragStart = cursor clamp at transition.
    Tracked in manifest as flat (no mult).

35. INTRA-FILE ZERO-GAP PROTECTION
    On load: two checks, both shift all events from the click forward.
    Part A — MouseMove->ButtonDown gap < 30ms shifted to 35ms.
    Prevents fast-cursor recordings clicking short of target tile.
    Raised from 15→30ms (v3.19.06): 15-29ms gaps were slipping through.
    Part B — DragEnd->DragStart gap < 200ms shifted to 200ms.
    Prevents rapid DragStart re-press. Threshold raised 150→200ms v3.18.92.
    Part C (v3.19.02) — any button-event->button-down gap < 200ms shifted
    to 200ms. Catches LeftUp→LeftDown, DragEnd→LeftDown, LD→LD (missing
    release), and all cross-type rapid re-press cases missed by A and B.
    Applied before any other features, to raw events only.

36. ORIGINAL FILES DEDUPLICATION
    Counts each unique filename once across all subfolders.
    Copied subfolders shown as "(N copied folder(s))" in manifest.

37. MAX-FILES TAG
    "-N-" in folder name = pick 1-N files (or loops for nested folders).
    "F3 optional58-6-" = 58% chance, 1-6 files.
    "F1-4-" = always included, 1-4 files.

38. PROBLEMATIC KEY FILTERING
    On load (before any features): strips keys that break macro playback.
    Filtered: HOME(36), END(35), PAGE_UP(33), PAGE_DOWN(34), PAUSE(19),
              PRINT_SCREEN(44)
    Kept: ESC(27) — valid in-game action (closing menus, cancelling dialogs).
    IMPORTANT: base_time captured BEFORE filtering so files whose only early
    event is a filtered key (e.g. END at t=90ms) keep their full duration.
    Without this, the 90ms anchor is lost and the file collapses to near-zero.

39. NESTED SUBFOLDER SUPPORT
    A numbered subfolder (e.g. F5) can contain its own F1/F2/F3/F4 instead
    of direct JSON files. Detected automatically during scanning.
    -N- on the outer folder = max N complete inner loops (not N files).
    always_first/last at F5's root level fire ONCE before all loops and
    ONCE after all loops (not per loop).
    Internal subfolders support all tags: optional, end, time/click sensitive.
    Separate ManualHistoryTracker maintained for nested folder's combos.

40. LOGOUT SEQUENCE FOLDER (Feature 40)
    Trigger: folder named 'LOGOUT, wait, in' (case-insensitive) at the root
    level of input_macros/.
    Contents: .json files assigned by numeric prefix in filename.
      Files assigned by numeric prefix in filename (e.g. '1- logout.json' → slot 1).
      Sub-slots supported (e.g. '1.1-' sorts between 1 and 2).
      Random wait fires after the last file whose prefix is 2.x.
      Any number of slots supported; minimum: one pre-2, one 2.x, one post-2.
    Two break files built per output folder (each with a fresh random wait):
    Long break:  7200000–16200000 ms (2h–4.5h)
    Short break: 1800000– 5400000 ms (30min–90min)
    Float ms, never rounded.
    Outputs: "@ LOGOUT LONG BREAK.json" + "@ LOGOUT SHORT BREAK.json"
    Features: NO anti-detection features applied (files inserted raw).
              filter_problematic_keys() is applied on load.
    Output: written to output_root/- logout.json, then copied to each
            bundle folder as "@ N LOGOUT.JSON" (same as static logout file).
    Priority: takes precedence over the legacy '- logout.json' static file.
    Fallback: if the folder is missing, the old static file search still runs.
    The folder is excluded from the main macro scan (not treated as a macro folder).
    Dedicated rng seeded from bundle_id + 31337 — does not affect main rng state.

41. SAME-NUMBER FOLDER POOLING (Feature 41)
    Multiple physical subfolders that share the same F-number are merged into
    a single logical slot in the cycle. The cycle still sees one slot per
    unique number; the combined pool of all matching folders is used for
    file selection and always_first/last picking.
    Examples:
      F2- Click anvil, F2- Click anvil - Copy, F2- dance
        → one F2 slot; files from all three folders pooled together
      F0 optional28-13-, F0 optional28-13- (1)
        → one F0 slot; 28% chance, pick up to 13 files from combined pool
    Merge rules:
      - files / always_first / always_last: concatenated
      - Boolean tags (is_optional, is_end, is_time_sensitive, is_click_sensitive):
        OR — if ANY contributing folder has the tag, the merged slot gets it
      - Scalar tags (optional_chance, max_files): first non-None value wins
      - Nested subfolders: inner dicts merged by inner slot number
    A [Pool] log line is printed for each merge: "F2: merged 'name' (X files total)"

42. GROUP FOLDER SUPPORT
    Organizer folders one level below input_macros/ whose children have
    F-numbered subfolders (but the organizer itself does not) are treated as
    group folders. Selecting a group name runs all its children individually.
    Structure: input_macros/GroupName/Macro1, Macro2, ...
    Special folders (DISTRACTIONS, LOGOUT, combination_history) are never groups.

===========================================================================
                    CRITICAL FEATURES — DO NOT BREAK
===========================================================================
The items below are load-bearing. If any of these are altered, removed,
or have their order/threshold changed without re-verifying against the
specific bug they were written to fix, strung files can come out with
broken loop actions, misfired clicks, or misparsed input. Each entry
names the exact mechanism, why it exists, and the version where it was
introduced or last hardened. Before touching ANY of the functions named
below, re-read the matching changelog entry for the full failure mode.

1. DUAL-COPY RULE (applies to every item below)
   The script contains two structurally identical copies of every function
   (a legacy block and an active block). EVERY fix in this list MUST be
   applied to BOTH copies or the bug reappears intermittently depending on
   which code path executes. This is the single most common cause of
   "the fix didn't work" reports — verify both copies after every edit.

2. Part A — MouseMove -> click gap enforcement (_ZERO_GAP_THRESHOLD=35ms)
   Function: filter_problematic_keys, both copies.
   Why: a click firing <35ms after the preceding MouseMove can register
   before the game client has processed the cursor position, causing a
   misclick on the wrong tile. Part A shifts the click +settling-MM so the
   cursor has time to land. v3.19.06, v3.19.18, v3.19.27 raised/tuned this
   threshold after real misclick reports — do not lower it casually.

3. Part B — DragEnd -> DragStart re-press gap (_DRAG_REPRESS_THRESHOLD=200ms)
   Function: filter_problematic_keys, both copies.
   Why: re-pressing too soon after releasing can be eaten by the client.
   MUST be skipped for genuine rapid/double-clicks (see item 5) or it will
   stretch intentional double-clicks into broken single clicks.

4. Part F — long-gap settling MouseMove (_LONG_GAP_SETTLE_MS=1000ms)
   Function: filter_problematic_keys, both copies.
   Why: after a long idle gap, inserts a MM at the EXACT click coordinates
   (no offset) just before the click fires, so the cursor visibly arrives
   before clicking instead of teleporting. Settling MM must never use a
   random offset — exact coords only, or the click can land off-target.

5. detect_rapid_click_sequences + soft double-click pre-scan
   Function: detect_rapid_click_sequences (apply_cycle_features) AND the
   "Rapid pre-scan" block inside filter_problematic_keys. Both copies of
   both. Pixel tolerance MUST stay at 20px (matches _RAPID_POS_TOL_SOFT) —
   lowering it back to 10px reopens the gap where clicks 11-20px apart lose
   protection from pause/jitter injection between them (fixed v3.19.43).
   Any two clicks within 2000ms and 20px of each other are a "click cluster"
   and every event between them is added to protected_set/_no_modify_set —
   this protected_set MUST be respected by Part B, intra-file pause,
   mid-event pause, and jitter, or genuine double/rapid clicks get stretched
   or deflected (the original CBD(50) bug class, v3.19.43/v3.19.49).

6. add_pre_click_jitter exclusion zone + convergence check
   Function: add_pre_click_jitter, both copies.
   - click_types for the 1000ms exclusion MUST include DragStart AND
     DragEnd (v3.19.43) — DragEnd was missing originally, leaving a gap
     where jitter could fire just after a release and before the next
     action.
   - The CONVERGENCE CHECK (v3.19.46, blind-spot fixed v3.19.49) excludes
     any MouseMove that is closer to an upcoming click than the previous
     MM was — i.e. part of an approach trajectory. Time-distance alone
     (1000ms) is NOT sufficient: approaches can run 1-5+ seconds, and
     without the convergence check jitter zigzags the cursor mid-approach,
     causing it to land on the wrong tile when the click fires (the
     FMFcraftdia bug, v3.19.46). _prev_mm_x/_prev_mm_y MUST be seeded from
     the first click's position, not None — seeding with None disables the
     check entirely for the first MouseMove in the file (v3.19.49).

7. insert_idle_mouse_movements click_proximity exclusion (click_window=3000ms)
   Function: insert_idle_mouse_movements, both copies.
   click_types set MUST include DragStart and DragEnd alongside
   Click/LeftDown/LeftUp/RightDown/RightUp (v3.19.61). Without DragStart/
   DragEnd in this set, gaps >2000ms before a drag-click are eligible for
   idle wandering, and the cursor may not have fully returned to position
   when the click fires — wrong-tile click. This was the longest-standing
   bug in the file; it predates all (random)-folder work and is unrelated
   to it. If "cursor hovers, darts away, comes back late for the click"
   resurfaces in a NORMAL (non-random) file, check this set first.

8. (random) folder pre-click gap floor (_RANDOM_MIN_PRECLICK_MS=38ms)
   Function: add_file_to_cycle event placement, slot_is_random branch,
   both copies. The (random)-folder speed/idle-gap compression (v3.19.56)
   divides ALL inter-event gaps by 2.5-3.5x INCLUDING the gap right before
   a click — without the 38ms floor, that gap can compress to <10ms and
   the cursor is still mid-approach when the click fires (v3.19.59). This
   floor must stay >= Part A's 35ms threshold (item 2) with margin.

9. protected_set / drag_set exclusions in insert_intra_file_pauses and
   the Step 3b mid-event pause (apply_cycle_features)
   Both pause-injection mechanisms MUST check protected_set (from item 5)
   AND drag_set (every index between a DragStart and its DragEnd) before
   selecting a pivot point. A pivot landing inside an active drag or a
   click cluster injects hundreds of ms into what should be a <200ms
   window, breaking double-click and drag timing.

10. Cache correctness (_raw_file_cache / _processed_events_cache)
    Function: add_file_to_cycle, both copies. Parts A-F (items 2-4) MUST
    run ONLY on the slow (cache-miss) path — they were originally outside
    the if/else and ran on every call including cache hits, which didn't
    break correctness but silently defeated the entire point of caching
    (v3.19.40). If restructuring this function, confirm Parts A-F are
    still indented inside the `else:` branch after any edit.

11. (random) sub-subfolder manifest folder_num override
    Function: _play_nested_loop / _play_nested_group, both copies.
    _parent_folder_num MUST be threaded through for _random_single items
    so the manifest reports the PARENT F-step number, not the sub-subfolder
    number — this is cosmetic, not a parsing risk, but breaking it makes
    manifests unreadable for (random) folders specifically (v3.19.53).

12. Group-folder output wrapping order: _group_name checked BEFORE
    args.specific_folders / args.group_subfolders
    Function: output folder assignment in main(), both copies. The check
    order matters: _group_name must be tested FIRST, or specific-folders
    mode silently ignores it and writes flat instead of wrapped output
    (v3.19.38). This is an output-organization bug, not a playback bug,
    but it has regressed twice already from refactors that reordered the
    if/elif chain — preserve the order.

WHEN ADDING A NEW FEATURE: if it touches event timing, event insertion,
or event removal in any function listed above, re-read that function's
docstring/comments for the EXACT threshold and EXACT exclusion set before
changing anything nearby. A "harmless" refactor of surrounding code that
moves a check outside its original if/else block, or changes a set literal
without noticing it gates click protection, is how every bug in this list
was introduced.

===========================================================================

CHANGELOG (recent):
===========================================================================
- v3.20.0: (choose1) hub folder support, recursive pool size calculation,
           parse_max_files returns None, removed dmwm_file_set dead code.
           See feature list above for details.
- v3.19.66: (choose1) now respects (random) tag on chosen child folder.
- v3.19.65: New folder tag: (choose1).
- v3.19.63: Added CRITICAL FEATURES documentation section.
- ... (earlier entries omitted for brevity)
===========================================================================
"""

import argparse, json, random, re, sys, os, math, shutil, itertools
from pathlib import Path

VERSION = "v3.20.0"
_MAX_SINGLE_PAUSE_MS = 1_536_000  # 25.6 min hard ceiling on any single pause

# Two-level file cache — shared across both main() copies (module-level)
_raw_file_cache:         dict = {}  # path_str -> raw JSON string (avoids re-reading disk)
_processed_events_cache: dict = {}  # path_str -> {'events': [...], 'base_time': float}
_fixed_logout_cache:     dict = {}  # str(profile_folder_path) -> {'slots': str, 'json': str}

# ============================================================================
# FEATURE DOCUMENTATION - ORGANIZED BY PURPOSE
# ============================================================================

# ============================================================================
# !! CRITICAL FEATURES — DO NOT MODIFY WITHOUT READING THIS SECTION FIRST !!
# ============================================================================
#
# MAINTENANCE REMINDER: whenever a future fix touches click timing, jitter,
# idle movement, drag/click parsing, loop sequencing, or output naming —
# and that fix would have caused real breakage if it had stayed wrong —
# add a new numbered entry below (same style as the existing ones) in the
# SAME edit that makes the fix. Do this immediately, not "later." This
# list is only useful if it stays current with every load-bearing change.
#
# Every item below was added because removing or altering it caused REAL
# observed breakage: misparsed clicks, wrong-tile clicks, broken loop
# sequencing, or corrupted strung output. Before changing ANY of the
# functions or values named here, re-read the corresponding changelog
# entry (search by version number) to understand exactly what broke and
# why the fix works. Treat these as load-bearing pillars — removing one
# without understanding it WILL silently reintroduce a known bug.
#
# DUAL-COPY RULE: this entire file has TWO copies of nearly every function
# (a legacy copy and an active copy). EVERY fix below must be applied to
# BOTH copies or the bug will resurface intermittently depending on which
# code path executes. Always grep for the exact string and verify count=2
# before editing.
#
# ----------------------------------------------------------------------
# 1. filter_problematic_keys() — Parts A through F (v3.18.x - v3.19.x)
# ----------------------------------------------------------------------
#   Six independent passes that fix click/timing issues found in raw
#   recordings BEFORE any cycle assembly happens. Each part has a narrow,
#   specific job — do not merge or "simplify" them, they were split apart
#   because combining logic caused cross-contamination bugs.
#     Part A: MM->click gap < 35ms -> shift +settle, insert settling MM
#             at the click's own coordinates (NEVER offset coordinates).
#     Part B: DragEnd->DragStart re-press gap < 200ms -> shift to 200ms.
#             Has a "soft path" pre-scan (v3.18.x) that walks back through
#             MouseMove-only gaps to find indirect DE->...->DS sequences,
#             tolerance 20px (_RAPID_POS_TOL_SOFT) - this MUST match the
#             20px tolerance in detect_rapid_click_sequences (item 3) or
#             clicks 11-20px apart lose protection on one side only.
#     Part C: adjacent button-event collision guard.
#     Part D: zero-gap DragEnd guard.
#     Part E: ONLY clamps idle-parked MouseMove positions that drift out
#             of bounds. NEVER touches click events. (v3.19.27 added,
#             v3.19.35 removed an overreaching variant that clamped
#             click events too — do not reintroduce that.)
#     Part F: long-gap settling MM, _LONG_GAP_SETTLE_MS=1000ms threshold.
#             Inserted MM uses the click's EXACT coordinates, never an
#             offset — an offset here is what causes "hover then jump to
#             wrong tile" symptoms.
#
# ----------------------------------------------------------------------
# 2. detect_rapid_click_sequences() — pixel tolerance MUST be 20px (v3.19.43)
# ----------------------------------------------------------------------
#   Groups clicks within 2000ms and <=20px into protected_ranges. This
#   tolerance was raised from 10px specifically to match Part B's soft
#   path (_RAPID_POS_TOL_SOFT=20). If these two values ever diverge again,
#   clicks 11-20px apart will have inconsistent protection: Part B skips
#   shifting them but intra/mid-event pause can still inject a pause
#   between them, breaking double-click timing. protected_ranges output
#   from this function feeds insert_intra_file_pauses AND the mid-event
#   pause valid-candidate filter (Step 3b) — both must respect it.
#
# ----------------------------------------------------------------------
# 3. add_pre_click_jitter() — convergence check (v3.19.46, fixed v3.19.49)
# ----------------------------------------------------------------------
#   click_types here MUST include DragEnd (v3.19.43) as well as DragStart,
#   Click, LeftDown/Up, RightDown/Up — DragEnd anchors its own +/-1000ms
#   exclusion zone for the post-release window.
#   The CONVERGENCE CHECK (v3.19.46) is what actually matters most: a
#   MouseMove is excluded from jitter if it is closer to the NEXT upcoming
#   click than the previous MM was — i.e. it's part of an approach
#   trajectory. Without this, jitter zigzags the cursor during a long
#   (>1000ms) approach sweep and misplaces it just before the click fires.
#   The convergence check is seeded from the position of the FIRST click
#   in the event list (v3.19.49) — without this seed, the very first
#   MouseMove in any file has no previous-position reference and bypasses
#   the convergence check entirely, regardless of how dangerous its
#   position is. Do not revert this seed to None.
#
# ----------------------------------------------------------------------
# 4. insert_idle_mouse_movements() — click_types MUST include drag events
#    (v3.19.61)
# ----------------------------------------------------------------------
#   click_proximity exclusion (3000ms window) is built from a click_types
#   set. THIS SET MUST INCLUDE DragStart AND DragEnd, not just Click/
#   LeftDown/LeftUp/RightDown/RightUp. Omitting drag events here means any
#   gap >2000ms before a DragStart is eligible for idle-wander insertion —
#   the cursor wanders away and may not have fully returned when the
#   DragStart fires, causing a click on the wrong tile. This bug existed
#   silently for a long time before being found — always check this set
#   first if "click registers on wrong tile despite hovering correctly in
#   the original recording" is reported.
#
# ----------------------------------------------------------------------
# 5. (random) folder event compression — pre-click floor (v3.19.56, fixed
#    v3.19.59)
# ----------------------------------------------------------------------
#   The (random)/(randomN) folder feature compresses ALL inter-event gaps
#   by clamping to _RANDOM_MAX_GAP_MS then dividing by _RANDOM_SPEED_MULT.
#   This is SAFE for ordinary movement but DANGEROUS for the gap
#   immediately preceding any click event — compressing it below ~35ms
#   (Part A's own minimum) means the cursor hasn't settled before the
#   click fires. _RANDOM_MIN_PRECLICK_MS=38ms is a hard floor applied
#   ONLY to the gap before DragStart/LeftDown/RightDown/Click. Removing
#   this floor reintroduces wrong-tile clicks specifically in (random)
#   tagged folders.
#
# ----------------------------------------------------------------------
# 6. Manifest folder_num for (random) sub-subfolders (v3.19.53)
# ----------------------------------------------------------------------
#   Not a click-safety item, but a parsing-consistency one: _random_single
#   items must carry _parent_folder_num so the manifest logs the PARENT
#   F-step number, not the sub-subfolder's own number. If this is dropped,
#   the manifest becomes inconsistent with the actual folder structure,
#   making it impossible to audit which step produced which file.
#
# ----------------------------------------------------------------------
# 7. Output folder naming / _effective_bid (v3.19.45, v3.19.50, v3.19.58,
#    v3.19.60, v3.19.62)
# ----------------------------------------------------------------------
#   Group-folder wrapping (nesting skill subfolders inside one
#   (bundle_id) skill_name/ folder) must remain UNCONDITIONAL — it was
#   made opt-in once (v3.19.45) and that broke the expected zip structure;
#   it was reverted to always-on in v3.19.50. Do not re-gate it behind a
#   flag without an explicit request.
#   When the same folder is selected multiple times via the dropdowns,
#   each run MUST get a distinct _effective_bid (555.1, 555.2, 555.3 —
#   v3.19.62) applied consistently to: the wrapper folder name, the
#   subfolder name (specific-folders mode), AND the strung filename
#   itself. If only one of these three locations uses _effective_bid
#   while the others use plain args.bundle_id, duplicate runs silently
#   overwrite each other on disk (this exact bug occurred — v3.19.58).
#
# ============================================================================
# END CRITICAL FEATURES
# ============================================================================


# HELPER FUNCTIONS
# ============================================================================

def _combo_fp_sig(fp, i=0):
    """
    Build a deterministic signature fragment for one element of a combination slot.
    - Regular files (Path objects): use filename directly.
    - Nested combo dicts: recursively extract inner filenames so every unique
      inner combination produces a unique outer signature.
      Without this, ALL nested combos produce "nested_0", causing the history
      tracker to think only 1 unique combination exists and breaking the while
      loop after the very first cycle (Feature 39 / Feature 41 interaction fix).
    """
    if hasattr(fp, 'name'):
        return fp.name
    if isinstance(fp, dict) and fp.get('_nested'):
        parts = []
        for _ifn, _ifl in fp.get('combo', []):
            for _ifp in (_ifl if isinstance(_ifl, list) else [_ifl]):
                parts.append(_combo_fp_sig(_ifp, i))
        return 'N(' + '+'.join(parts) + ')' if parts else f'nested_{i}'
    return f'nested_{i}'


def format_ms_precise(ms):
    """Format milliseconds as Xm Ys"""
    total_sec = int(ms / 1000)
    minutes = total_sec // 60
    seconds = total_sec % 60
    return f"{minutes}m {seconds}s"

def get_file_duration_ms(filepath):
    """Get file duration in milliseconds"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            events = json.load(f)
        if not events:
            return 0
        times = [e.get('Time', 0) for e in events]
        return max(times) - min(times)
    except:
        return 0

def filter_problematic_keys(events: list) -> list:
    """
    CRITICAL: Filter out keys that could stop macro playback.
    Removes: HOME(36), END(35), PAGE_UP(33), PAGE_DOWN(34), PAUSE(19), PRINT_SCREEN(44)
    NOTE: ESC(27) kept - it is a valid in-game key (e.g. closing menus).
    """
    problematic_codes = {19, 33, 34, 35, 36, 44}  # ESC(27) removed - valid in-game action
    filtered = []
    
    for event in events:
        keycode = event.get('KeyCode')
        if keycode in problematic_codes:
            continue
        filtered.append(event)
    
    return filtered

def parse_optional_chance(folder_name: str) -> float:
    """
    Parse the inclusion probability from an 'optional'-tagged folder name.

    Rules:
      - No number after 'optional'  -> random default 24.0-33.0% (float)
      - Number found (integer OR decimal) -> used as centre of +/-2% random range.
        e.g. optional23 -> rng.uniform(21.0, 25.0)%
        This adds variety so the same folder doesn't always hit the exact same
        threshold. Range is clamped so it never goes below 1% or above 99%.

    Accepted formats (all case-insensitive):
      "3 optional- bank/"           -> random 0.24-0.33
      "3 optional50- bank/"         -> random 0.48-0.52
      "3 optional50.5- bank/"       -> random 0.485-0.525
      "3 optional23-4- booth/"      -> random 0.21-0.25
      "3 optional33.3+end- logout/" -> random 0.313-0.353

    Returns a float in (0, 1).
    """
    import re
    # Capture integer OR decimal number after 'optional' (e.g. 50, 50.5, 33.3)
    match = re.search(r'optional[^-\d]*?(\d+(?:\.\d+)?)', folder_name, re.IGNORECASE)
    if match:
        centre = float(match.group(1))
        lo = max(1.0, centre - 2.0)
        hi = min(99.0, centre + 2.0)
        return random.uniform(lo, hi) / 100.0
    # No number -> default random range (float, never rounded)
    return random.uniform(0.24, 0.33)


def parse_max_files(folder_name: str):
    """
    Parse max-files count from folder name.
    Formats (case-insensitive, all combinations):
      "F3 optional58-6-"  -> max 6  (58% chance)
      "F3 optional-6-"    -> max 6  (default chance)
      "F1-4-"             -> max 4  (always included)
      "F3 optional58-"    -> max 1  (no max-files number = default 1)
      "F1- mine rock/"    -> max 1  (no number = default 1)

    The max-files number is the LAST standalone integer before a trailing dash,
    not the folder number or the optional-chance percentage.
    Returns int >= 1 if found, else None.
    """
    import re
    # Pattern: dash, then digits (the max-files count), then dash or end
    # We look for a bare integer surrounded by dashes that isn't the folder number
    # (folder number is at the very start) and isn't the optional-chance percentage
    # (which directly follows "optional").
    # Strategy: strip the leading folder number, strip optional-chance, then find
    # a remaining -N- or -N/ pattern.
    name = folder_name.strip('/').strip()
    # Remove folder number prefix (e.g. "3", "3.5", "F3")
    name = re.sub(r'^[Ff]?\d+(?:\.\d+)?\s*', '', name)
    # Remove optional-chance number (digits immediately after "optional")
    name = re.sub(r'optional\s*\d+(?:\.\d+)?', 'optional', name, flags=re.IGNORECASE)
    # Now look for -N- or -N/ or -N at end where N is 2-3 digits (1 digit would be ambiguous)
    # Actually look for any -digits- pattern remaining
    matches = re.findall(r'-(\d+)-', name)
    if matches:
        try:
            return max(1, int(matches[-1]))   # take the last one
        except ValueError:
            pass
    return None   # No pattern found


def fix_click_events(events: list) -> list:
    """
    Convert 'Click' events to LeftDown+LeftUp pairs.
    This prevents the mouse from clamping down and dragging.
    
    CRITICAL FIX from merge_macros.py!
    """
    fixed = []
    for event in events:
        if event.get('Type') == 'Click':
            # Replace Click with LeftDown + LeftUp pair
            time = event.get('Time', 0)
            x = event.get('X')
            y = event.get('Y')
            
            # LeftDown at same time
            left_down = {
                'Type': 'LeftDown',
                'Time': time,
            }
            if x is not None:
                left_down['X'] = x
            if y is not None:
                left_down['Y'] = y
            
            # LeftUp 10-20ms later (small random delay)
            left_up = {
                'Type': 'LeftUp',
                'Time': time + random.randint(10, 20),
            }
            if x is not None:
                left_up['X'] = x
            if y is not None:
                left_up['Y'] = y
            
            fixed.append(left_down)
            fixed.append(left_up)
        else:
            # Keep all other events as-is
            fixed.append(event)
    
    return fixed

def generate_human_path(start_x, start_y, end_x, end_y, duration_ms, rng):
    """
    Generate a human-like mouse path with variable speed, path styles, and wobbles.
    
    Path Styles:
    - Efficient: Direct path, few curves, faster
    - Meandering: Curved path, more wandering, varied speed
    - Hesitant: Slow start, acceleration, deceleration
    - Swift: Fast throughout, minimal curves
    
    Speed Variations:
    - Very fast: 100-200ms typical
    - Fast: 200-300ms typical
    - Normal: 300-500ms typical
    - Slow: 500-700ms typical
    - Very slow: 700-1000ms typical
    
    Returns: List of (time_ms, x, y) tuples.
    """
    if duration_ms < 100:
        return [(0, end_x, end_y)]
    
    path = []
    dx = end_x - start_x
    dy = end_y - start_y
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance < 5:
        return [(0, end_x, end_y)]
    
    # Choose path style (determines curvature and speed pattern)
    # 'swift' removed from transition style pool (v3.18.98):
    # swift uses linear constant-speed motion with no deceleration near the
    # target, leaving the cursor furthest from the destination at the penultimate
    # waypoint. This maximised click-position error before the snap fix.
    path_style = rng.choice(['efficient', 'meandering', 'hesitant'])
    
    # Determine num_steps based on distance and path style
    if path_style == 'efficient':
        # Direct, fewer steps
        num_steps = max(3, min(int(distance / 20), int(duration_ms / 60)))
    elif path_style == 'swift':
        # Very fast, few steps
        num_steps = max(2, min(int(distance / 25), int(duration_ms / 80)))
    elif path_style == 'meandering':
        # More steps for smoother curves
        num_steps = max(5, min(int(distance / 10), int(duration_ms / 40)))
    else:  # hesitant
        # Medium steps
        num_steps = max(4, min(int(distance / 15), int(duration_ms / 50)))
    
    # Add control points based on path style
    if path_style == 'efficient':
        # Few or no control points (straighter path)
        num_control = rng.choice([0, 1])
        offset_range = 0.15  # Less curve
    elif path_style == 'swift':
        # No control points (direct)
        num_control = 0
        offset_range = 0.0
    elif path_style == 'meandering':
        # More control points (curvier path)
        num_control = rng.randint(2, 4)
        offset_range = 0.4  # More curve
    else:  # hesitant
        # Medium control points
        num_control = rng.randint(1, 2)
        offset_range = 0.25
    
    control_points = []
    for _ in range(num_control):
        offset = rng.uniform(-offset_range, offset_range) * distance
        t = rng.uniform(0.2, 0.8)
        ctrl_x = start_x + dx * t + (-dy / (distance + 1)) * offset
        ctrl_y = start_y + dy * t + (dx / (distance + 1)) * offset
        control_points.append((ctrl_x, ctrl_y, t))
    
    control_points.sort(key=lambda p: p[2])
    current_time = 0
    
    for step in range(num_steps + 1):
        t_raw = step / num_steps
        
        # Apply speed profile based on path style
        if path_style == 'efficient':
            # Smooth acceleration
            t = 1 - (1 - t_raw) ** 1.8
        elif path_style == 'swift':
            # Linear (constant speed)
            t = t_raw
        elif path_style == 'meandering':
            # Variable speed with slight deceleration at end
            t = 0.5 * (1 - math.cos(t_raw * math.pi))
        else:  # hesitant
            # Slow start, fast middle, slow end
            t = 0.5 * (1 - math.cos(t_raw * math.pi))
        
        # Calculate position
        if not control_points:
            x = start_x + dx * t
            y = start_y + dy * t
        else:
            x, y = start_x, start_y
            for i, (ctrl_x, ctrl_y, ctrl_t) in enumerate(control_points):
                if t <= ctrl_t:
                    segment_t = t / ctrl_t if ctrl_t > 0 else 0
                    x = start_x + (ctrl_x - start_x) * segment_t
                    y = start_y + (ctrl_y - start_y) * segment_t
                    break
                else:
                    if i == len(control_points) - 1:
                        segment_t = (t - ctrl_t) / (1 - ctrl_t) if (1 - ctrl_t) > 0 else 0
                        x = ctrl_x + (end_x - ctrl_x) * segment_t
                        y = ctrl_y + (end_y - ctrl_y) * segment_t
                    else:
                        start_x, start_y = ctrl_x, ctrl_y
        
        # Add wobble (less for swift, more for meandering)
        if path_style == 'swift':
            wobble = rng.uniform(0, 2) if step > 0 and step < num_steps else 0
        elif path_style == 'meandering':
            wobble = rng.uniform(1, 7) if step > 0 and step < num_steps else 0
        else:
            wobble = rng.uniform(1, 5) if step > 0 and step < num_steps else 0
        
        x += rng.uniform(-wobble, wobble)
        y += rng.uniform(-wobble, wobble)
        
        # Bounds
        x = max(100, min(1800, int(x)))
        y = max(100, min(1000, int(y)))
        
        step_time = int(t * duration_ms)
        current_time = max(current_time, step_time)
        path.append((current_time, x, y))
    
    return path

# ============================================================================
# COMBINATION TRACKER
# ============================================================================


def is_in_drag_sequence(events, index, drag_indices=None):
    """
    Check if the given index is inside a drag sequence (between DragStart and DragEnd).
    Returns True if we're in the middle of a drag.

    If drag_indices (a precomputed set from build_drag_index_set) is provided,
    the check is O(1). Otherwise falls back to the original O(n) scan.
    """
    if drag_indices is not None:
        return index in drag_indices

    drag_started = False
    for j in range(index, -1, -1):
        event_type = events[j].get("Type", "")
        if event_type == "DragEnd":
            return False
        elif event_type == "DragStart":
            drag_started = True
            break
    
    if not drag_started:
        return False
    
    for j in range(index + 1, len(events)):
        event_type = events[j].get("Type", "")
        if event_type == "DragEnd":
            return True
        elif event_type == "DragStart":
            return False
    
    return False


def build_drag_index_set(events) -> set:
    """
    Return the set of all event indices that are inside a drag sequence.
    O(n) single pass - call this once, then use the result for O(1) lookups.
    """
    drag_indices = set()
    in_drag = False
    for i, e in enumerate(events):
        t = e.get("Type", "")
        if t == "DragStart":
            in_drag = True
        elif t == "DragEnd":
            in_drag = False
        if in_drag:
            drag_indices.add(i)
    return drag_indices

def detect_rapid_click_sequences(events):
    """
    Detect sequences of rapid clicks at similar coordinates.

    Detects:
    - Double clicks (2 clicks within 500ms, +/-20 pixels)
    - Spam clicks  (3+ clicks within 2 seconds, +/-20 pixels)

    Detection set: Click, DragStart, LeftDown, LeftUp, RightDown, RightUp.
    LeftDown/LeftUp are included because source files often use native button
    events instead of the high-level 'Click' type. Without them, a LeftDown
    double-click sequence could have a pause inserted between the two presses,
    widening the inter-click gap from ~200ms to 1000ms+ and ruining the pattern.

    The protected range covers the ENTIRE span from the first to the last event
    in the sequence, including any intermediate LeftUp / MouseMove events,
    so no pause can land inside the double-click window.

    Returns list of protected ranges: [(start_idx, end_idx), ...]
    These ranges should NOT have pauses/gaps inserted between them.
    """
    if not events or len(events) < 2:
        return []

    # All event types that count as a "click press" for detection purposes.
    # LeftUp/RightUp are included so that the protected range spans the full
    # press+release window — the pause exclusion covers all events between
    # the first press and the last release of a rapid sequence.
    # Includes MouseDown/MouseUp as aliases — some source files use that naming convention
    _CLICK_DETECT = {"Click", "DragStart", "LeftDown", "LeftUp", "RightDown", "RightUp",
                     "MouseDown", "MouseUp"}

    protected_ranges = []

    i = 0
    while i < len(events):
        event = events[i]

        event_type = event.get("Type")
        if event_type not in _CLICK_DETECT:
            i += 1
            continue

        # Found a click event — look ahead for nearby click events
        click_sequence = [i]
        first_time = event.get("Time", 0)
        first_x = event.get("X")
        first_y = event.get("Y")

        if first_x is None or first_y is None:
            i += 1
            continue

        j = i + 1
        while j < len(events):
            next_event = events[j]
            next_time = next_event.get("Time", 0)

            # Stop looking if too far in time (2 seconds max)
            if next_time - first_time > 2000:
                break

            next_type = next_event.get("Type")
            if next_type in _CLICK_DETECT:
                next_x = next_event.get("X")
                next_y = next_event.get("Y")

                if next_x is not None and next_y is not None:
                    dist = ((next_x - first_x) ** 2 + (next_y - first_y) ** 2) ** 0.5
                    if dist <= 20:  # 20px matches Part B soft-path tolerance
                        click_sequence.append(j)

            j += 1

        # Two or more click events within the window → protect the whole span
        if len(click_sequence) >= 2:
            # Expand the range to include ALL events between first and last click
            # (catches intermediate LeftUp / MouseMove that sit inside the gap)
            start_idx = click_sequence[0]
            end_idx   = click_sequence[-1]
            protected_ranges.append((start_idx, end_idx))
            i = end_idx + 1
        else:
            i += 1

    return protected_ranges


def is_in_protected_range(index, protected_ranges):
    """Check if an index is within any protected range."""
    for start, end in protected_ranges:
        if start <= index <= end:
            return True
    return False


def add_pre_click_jitter(events: list, rng: random.Random) -> tuple:
    """
    SMART JITTER SYSTEM v3.9.0
    
    Add realistic micro-movements to 9-21% of TOTAL file movements.
    CRITICAL: NO jitter within 1 second before/after ANY click!
    
    Rules:
    1. Jitter percentage: 9-21% of total MouseMove events
    2. Exclusion zone: 1000ms before AND after any click
    3. Only jitter MouseMove events (never Click, DragStart, RightDown, etc.)
    4. Jitter = 2-3 micro-movements (+/-1-3px) + final snap to exact position
    
    Returns (events_with_jitter, jitter_count, total_moves, jitter_percentage).
    """
    if not events or len(events) < 2:
        return events, 0, 0, 0.0
    
    # Step 1: Find ALL click times (any click-like event)
    click_types = {'Click', 'LeftDown', 'LeftUp', 'RightDown', 'RightUp', 'DragStart', 'DragEnd'}
    click_times_sorted = sorted(
        event.get('Time', 0) for event in events if event.get('Type') in click_types
    )

    import bisect
    exclusion_ms = 1000

    # Step 2: Find all MouseMove events that are SAFE to jitter
    # Safe = NOT within 1000ms before/after ANY click  (O(n log c) total)
    # AND not part of an approach trajectory converging toward an upcoming click.
    # Convergence check: a MM is approaching if it is closer to the next click
    # than the previous MM was. Jitter on approach paths causes the cursor to
    # zigzag during the recorded sweep, misplacing it near the click target.
    safe_movements = []
    total_moves = 0

    # Pre-build click position lookup for convergence check
    _click_pos_lookup = {}
    for _ev in events:
        if _ev.get('Type') in click_types and _ev.get('X') is not None:
            _click_pos_lookup[_ev['Time']] = (_ev['X'], _ev['Y'])
    _click_times_with_pos = sorted(_click_pos_lookup.keys())

    # Seed prev position from first click so convergence check
    # is active even for the very first MM in the event list.
    _first_click = next(
        (e for e in events if e.get('Type') in click_types and e.get('X') is not None),
        None)
    _prev_mm_x = _first_click['X'] if _first_click else None
    _prev_mm_y = _first_click['Y'] if _first_click else None

    for i, event in enumerate(events):
        if event.get('Type') == 'MouseMove':
            total_moves += 1
            event_time = event.get('Time', 0)
            ex, ey = event.get('X'), event.get('Y')

            # Binary search: nearest click before and after
            pos = bisect.bisect_left(click_times_sorted, event_time)
            is_safe = True
            # Check click just before
            if pos > 0 and event_time - click_times_sorted[pos - 1] <= exclusion_ms:
                is_safe = False
            # Check click at or after
            if is_safe and pos < len(click_times_sorted) and click_times_sorted[pos] - event_time <= exclusion_ms:
                is_safe = False

            # Convergence check: exclude MMs that are approaching an upcoming click.
            # A MM is converging if it is closer to the next click than the prev MM.
            # Only check within 5s look-ahead to avoid false positives on idle MMs.
            if is_safe and ex is not None and ey is not None and _prev_mm_x is not None:
                _cp = bisect.bisect_right(_click_times_with_pos, event_time)
                if _cp < len(_click_times_with_pos):
                    _nct = _click_times_with_pos[_cp]
                    if _nct - event_time <= 5000:
                        _ncx, _ncy = _click_pos_lookup[_nct]
                        _d_this = (ex - _ncx) ** 2 + (ey - _ncy) ** 2
                        _d_prev = (_prev_mm_x - _ncx) ** 2 + (_prev_mm_y - _ncy) ** 2
                        if _d_this < _d_prev:  # converging → unsafe
                            is_safe = False

            if ex is not None: _prev_mm_x = ex
            if ey is not None: _prev_mm_y = ey

            if is_safe:
                safe_movements.append((i, event))
    
    # Step 3: Calculate how many jitters to add (9-21% of TOTAL movements)
    jitter_percentage = rng.uniform(0.09, 0.21)
    target_jitters = int(total_moves * jitter_percentage)
    
    # Can't jitter more than safe movements available
    target_jitters = min(target_jitters, len(safe_movements))
    
    if target_jitters == 0:
        return events, 0, total_moves, jitter_percentage
    
    # Step 4: Randomly select which safe movements get jitter
    movements_to_jitter = rng.sample(safe_movements, target_jitters)
    
    # Sort by index (descending) so we insert from end to start
    # This prevents index shifting issues
    movements_to_jitter.sort(key=lambda x: x[0], reverse=True)
    
    # Step 5: Add jitter to selected movements
    jitter_count = 0
    
    for idx, event in movements_to_jitter:
        move_x = event.get('X')
        move_y = event.get('Y')
        move_time = event.get('Time')
        
        if move_x is None or move_y is None or move_time is None:
            continue
        
        # Generate 2-3 micro-movements
        num_jitters = rng.randint(2, 3)
        jitter_events = []
        
        # Time budget: 100-200ms total
        time_budget = rng.randint(100, 200)
        time_per_jitter = time_budget // (num_jitters + 1)
        
        # Cap time_budget so jitter events never go before t=0
        if move_time - time_budget < 0:
            time_budget = max(0, int(move_time) - 1)
        if time_budget == 0:
            continue  # Not enough room before this event - skip jitter
        current_time = move_time - time_budget
        
        # Add jitter movements (+/-1-3 pixels)
        for j in range(num_jitters):
            offset_x = rng.randint(-3, 3)
            offset_y = rng.randint(-3, 3)
            
            jitter_x = int(move_x) + offset_x
            jitter_y = int(move_y) + offset_y
            
            # Bounds check
            jitter_x = max(100, min(1800, jitter_x))
            jitter_y = max(100, min(1000, jitter_y))
            
            jitter_events.append({
                'Type': 'MouseMove',
                'Time': current_time,
                'X': jitter_x,
                'Y': jitter_y
            })
            
            current_time += time_per_jitter
        
        # Final movement: snap to EXACT target position
        jitter_events.append({
            'Type': 'MouseMove',
            'Time': current_time,
            'X': int(move_x),
            'Y': int(move_y)
        })
        
        # Insert jitter events BEFORE the original movement
        for jitter_idx, jitter_event in enumerate(jitter_events):
            events.insert(idx + jitter_idx, jitter_event)
        
        jitter_count += 1
    
    return events, jitter_count, total_moves, jitter_percentage

def insert_intra_file_pauses(events: list, rng: random.Random,
                              protected_ranges: list = None,
                              file_type: str = 'normal') -> tuple:
    """
    Insert a single within-file pause whose duration is a percentage of the
    individual file's own play time:
      Raw:         0%  - no pause inserted
      Normal:      5%  - e.g. 20s file -> 1s pause somewhere safe
      Inefficient: 15% - e.g. 20s file -> 3s pause somewhere safe

    The pause is inserted at a single randomly chosen safe point (not in a drag
    sequence, not in a rapid-click sequence, not in the first or last 10%).
    Returns (events_with_pause, total_pause_time_ms).
    """
    if not events or len(events) < 5:
        return events, 0, float('inf')

    # Raw = 0%, Normal = random in [2%, 5%], Inef = random in [10%, 15%]
    # Drawn fresh each call — decimal, never rounded (e.g. 2.14%, 3.87%, 11.6%)
    if file_type == 'raw':
        return events, 0, float('inf')
    elif file_type == 'inef':
        pct = rng.uniform(0.10, 0.15)
    else:  # normal
        pct = rng.uniform(0.02, 0.05)

    if protected_ranges is None:
        protected_ranges = []

    file_duration_ms = events[-1].get('Time', 0) - events[0].get('Time', 0)
    if file_duration_ms <= 0:
        return events, 0, float('inf')

    # Float ms - no rounding
    pause_duration = min(file_duration_ms * pct, _MAX_SINGLE_PAUSE_MS)

    protected_set = set()
    for s, e in protected_ranges:
        for k in range(s, e + 1):
            protected_set.add(k)

    drag_indices = build_drag_index_set(events)

    first_safe = max(1, int(len(events) * 0.10))
    last_safe  = min(len(events) - 1, int(len(events) * 0.90))
    # Extended exclusion: never insert a pause AT or immediately BEFORE any
    # press/release event. This prevents pauses landing between LeftDown and
    # LeftUp (which would stretch the click hold) or just before a click press.
    _PRESS_TYPES = {'DragStart', 'LeftDown', 'LeftUp', 'RightDown', 'RightUp', 'Click'}

    # Build MouseWheel exclusion list — pauses must not land within
    # _MW_EXCL_MS of any scroll event. Scroll sequences are timed to
    # specific in-game states; a pause before or during them desynchronises
    # the scroll from whatever it's responding to (inventory page, interface).
    _MW_EXCL_MS = 1000
    import bisect
    _mw_times = sorted(
        e.get('Time', 0) for e in events if e.get('Type') == 'MouseWheel'
    )

    def _near_mw(t):
        if not _mw_times:
            return False
        pos = bisect.bisect_left(_mw_times, t)
        if pos > 0 and t - _mw_times[pos - 1] <= _MW_EXCL_MS:
            return True
        if pos < len(_mw_times) and _mw_times[pos] - t <= _MW_EXCL_MS:
            return True
        return False

    # Right-click exclusion: pauses must not land within _RC_EXCL_MS of any
    # RightDown or RightUp event. Right-click sequences (RightDown -> RightUp
    # -> cursor moves to menu option -> DragStart) must play exactly as
    # recorded. A pause inserted after RightUp but before the menu-selection
    # DragStart delays cursor arrival at the menu option, potentially causing
    # the wrong option to be selected or the menu to be dismissed.
    _RC_EXCL_MS = 2000
    _rc_times = sorted(
        e.get('Time', 0) for e in events
        if e.get('Type') in ('RightDown', 'RightUp')
    )

    def _near_rc(t):
        if not _rc_times:
            return False
        pos = bisect.bisect_left(_rc_times, t)
        if pos > 0 and t - _rc_times[pos - 1] <= _RC_EXCL_MS:
            return True
        if pos < len(_rc_times) and _rc_times[pos] - t <= _RC_EXCL_MS:
            return True
        return False

    valid = [
        idx for idx in range(first_safe, last_safe)
        if idx not in protected_set
        and idx not in drag_indices
        and events[idx].get('Type') not in _PRESS_TYPES
        and (idx + 1 >= len(events) or events[idx + 1].get('Type') not in _PRESS_TYPES)
        and not _near_mw(events[idx].get('Time', 0))
        and not _near_rc(events[idx].get('Time', 0))
    ]

    if not valid:
        return events, 0, float('inf')

    pause_idx = rng.choice(valid)
    _pivot_raw_t = float(events[pause_idx].get('Time', 0))  # raw time before shift
    for j in range(pause_idx, len(events)):
        events[j]['Time'] = events[j].get('Time', 0) + pause_duration

    return events, pause_duration, _pivot_raw_t
def insert_idle_mouse_movements(events, rng, movement_percentage,
                                prebuilt_drag_index=None):
    """
    Insert realistic human-like mouse movements during idle periods (gaps > 2 seconds).
    O(n) - drag membership and click-proximity lookups are precomputed as sets.
    prebuilt_drag_index: pass cached result from apply_cycle_features to avoid
    building the drag index set twice per cycle.
    """
    if not events or len(events) < 2:
        return events, 0

    # Precompute O(n) - used for O(1) per-event checks below
    drag_indices = prebuilt_drag_index if prebuilt_drag_index is not None \
                   else build_drag_index_set(events)

    # Build set of indices that are within 3 s after a click event
    # (idle movements must not be placed in those windows)
    click_proximity = set()
    click_window = 3000
    click_types = {"Click", "LeftDown", "LeftUp", "RightDown", "RightUp", "DragStart", "DragEnd"}
    for i, e in enumerate(events):
        if e.get("Type") in click_types:
            t_click = e.get("Time", 0)
            # mark all earlier indices whose next_time lands within the window
            for j in range(i - 1, -1, -1):
                if events[j].get("Time", 0) < t_click - click_window:
                    break
                click_proximity.add(j)

    result = []
    total_idle_time = 0

    for i in range(len(events)):
        result.append(events[i])

        if i < len(events) - 1:
            current_time = int(events[i].get("Time", 0))
            next_time    = int(events[i + 1].get("Time", 0))
            gap = next_time - current_time

            if gap >= 2000:
                if i in drag_indices:
                    continue
                if i in click_proximity:
                    continue
                
                # Calculate active window
                active_duration = int(gap * movement_percentage)
                buffer_start = (gap - active_duration) // 2
                movement_start = current_time + buffer_start
                
                # Get start position
                start_x, start_y = 500, 500
                for j in range(i, -1, -1):
                    x_val = events[j].get("X")
                    y_val = events[j].get("Y")
                    if x_val is not None and y_val is not None:
                        start_x = int(x_val)
                        start_y = int(y_val)
                        break
                
                # Get next position (where we need to end up)
                next_x, next_y = start_x, start_y
                for j in range(i + 1, min(i + 20, len(events))):
                    x_val = events[j].get("X")
                    y_val = events[j].get("Y")
                    if x_val is not None and y_val is not None:
                        next_x = int(x_val)
                        next_y = int(y_val)
                        break
                
                # Reserve last 25% for smooth transition back
                transition_duration = int(active_duration * 0.25)
                pattern_duration = active_duration - transition_duration
                
                # Choose movement behavior
                behavior = rng.choice([
                    'wander',      # Random wandering around
                    'check_edge',  # Quick look at screen edge
                    'fidget',      # Small nervous movements
                    'explore',     # Move far then return
                    'drift',       # Slow meandering
                    'scan'         # Move across screen
                ])
                
                pattern_end_x, pattern_end_y = start_x, start_y
                pattern_time_used = 0
                
                if behavior == 'wander':
                    # Random wandering - multiple small moves
                    num_moves = rng.randint(3, 6)
                    move_duration = pattern_duration // num_moves
                    
                    current_x, current_y = start_x, start_y
                    
                    for move_idx in range(num_moves):
                        # Pick random nearby target
                        target_x = current_x + rng.randint(-150, 150)
                        target_y = current_y + rng.randint(-100, 100)
                        target_x = max(100, min(1800, target_x))
                        target_y = max(100, min(1000, target_y))
                        
                        # Generate human path
                        path = generate_human_path(current_x, current_y, target_x, target_y, move_duration, rng)
                        
                        for path_time, px, py in path:
                            abs_time = movement_start + pattern_time_used + path_time
                            result.append({
                                "Time": abs_time,
                                "Type": "MouseMove",
                                "X": px,
                                "Y": py
                            })
                        
                        current_x, current_y = path[-1][1], path[-1][2]
                        pattern_time_used += move_duration
                    
                    pattern_end_x, pattern_end_y = current_x, current_y
                
                elif behavior == 'check_edge':
                    # Quick look at screen edge then back
                    edges = [
                        (150, start_y),    # Left edge
                        (1750, start_y),   # Right edge
                        (start_x, 150),    # Top edge
                        (start_x, 950),    # Bottom edge
                    ]
                    edge_x, edge_y = rng.choice(edges)
                    
                    # Move to edge (60% of time, fast)
                    edge_duration = int(pattern_duration * 0.6)
                    path_to_edge = generate_human_path(start_x, start_y, edge_x, edge_y, edge_duration, rng)
                    
                    for path_time, px, py in path_to_edge:
                        abs_time = movement_start + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    # Return near start (40% of time, slower)
                    return_duration = pattern_duration - edge_duration
                    return_x = start_x + rng.randint(-40, 40)
                    return_y = start_y + rng.randint(-40, 40)
                    return_x = max(100, min(1800, return_x))
                    return_y = max(100, min(1000, return_y))
                    
                    path_return = generate_human_path(edge_x, edge_y, return_x, return_y, return_duration, rng)
                    
                    for path_time, px, py in path_return:
                        abs_time = movement_start + edge_duration + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    pattern_end_x, pattern_end_y = path_return[-1][1], path_return[-1][2]
                    pattern_time_used = pattern_duration
                
                elif behavior == 'fidget':
                    # Small rapid movements in small area
                    num_fidgets = rng.randint(5, 10)
                    fidget_duration = pattern_duration // num_fidgets
                    
                    current_x, current_y = start_x, start_y
                    
                    for fidget_idx in range(num_fidgets):
                        # Small offset
                        target_x = current_x + rng.randint(-30, 30)
                        target_y = current_y + rng.randint(-30, 30)
                        target_x = max(100, min(1800, target_x))
                        target_y = max(100, min(1000, target_y))
                        
                        path = generate_human_path(current_x, current_y, target_x, target_y, fidget_duration, rng)
                        
                        for path_time, px, py in path:
                            abs_time = movement_start + pattern_time_used + path_time
                            result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                        
                        current_x, current_y = path[-1][1], path[-1][2]
                        pattern_time_used += fidget_duration
                    
                    pattern_end_x, pattern_end_y = current_x, current_y
                
                elif behavior == 'explore':
                    # Move far away then return near start
                    away_x = start_x + rng.randint(-400, 400)
                    away_y = start_y + rng.randint(-300, 300)
                    away_x = max(100, min(1800, away_x))
                    away_y = max(100, min(1000, away_y))
                    
                    # Go away (65% of time)
                    away_duration = int(pattern_duration * 0.65)
                    path_away = generate_human_path(start_x, start_y, away_x, away_y, away_duration, rng)
                    
                    for path_time, px, py in path_away:
                        abs_time = movement_start + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    # Return (35% of time)
                    return_duration = pattern_duration - away_duration
                    return_x = start_x + rng.randint(-15, 15)
                    return_y = start_y + rng.randint(-15, 15)
                    return_x = max(100, min(1800, return_x))
                    return_y = max(100, min(1000, return_y))
                    
                    path_return = generate_human_path(away_x, away_y, return_x, return_y, return_duration, rng)
                    
                    for path_time, px, py in path_return:
                        abs_time = movement_start + away_duration + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    pattern_end_x, pattern_end_y = path_return[-1][1], path_return[-1][2]
                    pattern_time_used = pattern_duration
                
                elif behavior == 'drift':
                    # Slow continuous drift
                    target_x = start_x + rng.randint(-200, 200)
                    target_y = start_y + rng.randint(-150, 150)
                    target_x = max(100, min(1800, target_x))
                    target_y = max(100, min(1000, target_y))
                    
                    path = generate_human_path(start_x, start_y, target_x, target_y, pattern_duration, rng)
                    
                    for path_time, px, py in path:
                        abs_time = movement_start + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    pattern_end_x, pattern_end_y = path[-1][1], path[-1][2]
                    pattern_time_used = pattern_duration
                
                elif behavior == 'scan':
                    # Scan across screen
                    scan_distance = rng.randint(300, 600)
                    direction = rng.choice(['horizontal', 'vertical', 'diagonal'])
                    
                    if direction == 'horizontal':
                        target_x = start_x + (scan_distance if rng.random() < 0.5 else -scan_distance)
                        target_y = start_y + rng.randint(-50, 50)
                    elif direction == 'vertical':
                        target_x = start_x + rng.randint(-50, 50)
                        target_y = start_y + (scan_distance if rng.random() < 0.5 else -scan_distance)
                    else:  # diagonal
                        target_x = start_x + (scan_distance if rng.random() < 0.5 else -scan_distance)
                        target_y = start_y + (scan_distance if rng.random() < 0.5 else -scan_distance)
                    
                    target_x = max(100, min(1800, target_x))
                    target_y = max(100, min(1000, target_y))
                    
                    path = generate_human_path(start_x, start_y, target_x, target_y, pattern_duration, rng)
                    
                    for path_time, px, py in path:
                        abs_time = movement_start + path_time
                        result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                    
                    pattern_end_x, pattern_end_y = path[-1][1], path[-1][2]
                    pattern_time_used = pattern_duration
                
                # Smooth transition back to next recorded position
                transition_path = generate_human_path(
                    pattern_end_x, pattern_end_y,
                    next_x, next_y,
                    transition_duration,
                    rng
                )
                
                for path_time, px, py in transition_path:
                    abs_time = movement_start + pattern_duration + path_time
                    result.append({"Time": abs_time, "Type": "MouseMove", "X": px, "Y": py})
                
                total_idle_time += active_duration
    
    return result, total_idle_time

class QueueFileSelector:
    def __init__(self, rng, all_files, durations_cache):
        self.rng = rng
        self.durations = durations_cache
        self.efficient = [f for f in all_files if "??" not in f.name]
        self.inefficient = [f for f in all_files if "??" in f.name]
        self.eff_pool = list(self.efficient)
        self.ineff_pool = list(self.inefficient)
        self.rng.shuffle(self.eff_pool)
        self.rng.shuffle(self.ineff_pool)

    def get_sequence(self, target_minutes, force_inef=False, is_time_sensitive=False):
        seq, cur_ms = [], 0.0
        target_ms = target_minutes * 60000
        # Add +/-5% margin for flexibility
        margin = int(target_ms * 0.05)
        target_min = target_ms - margin
        target_max = target_ms + margin
        actual_force = force_inef if not is_time_sensitive else False
        
        # Keep adding files until we reach target
        # Stop conditions:
        # 1. Reached target OR
        # 2. Adding next file would overshoot by more than 4 minutes
        
        while cur_ms < target_max:
            # Try to get next file
            if actual_force and self.ineff_pool: pick = self.ineff_pool.pop(0)
            elif self.eff_pool: pick = self.eff_pool.pop(0)
            elif self.efficient:
                self.eff_pool = list(self.efficient); self.rng.shuffle(self.eff_pool)
                pick = self.eff_pool.pop(0)
            elif self.ineff_pool and not is_time_sensitive: pick = self.ineff_pool.pop(0)
            else: break  # No more files
            
            file_duration = self.durations.get(pick, 500)
            
            # File selector multiplier - CRITICAL for accuracy
            # 1.0x = too many files (overshoot 11-18 min)
            # 1.8x = too few files (undershoot 10-13 min)
            # 1.35x = sweet spot (target ?+/-2-4 min)
            if is_time_sensitive:
                estimated_time = file_duration * 1.05  # TIME SENSITIVE: minimal overhead
            else:
                estimated_time = file_duration * 1.35  # NORMAL: balanced estimate
            
            # Check if adding would overshoot too much
            potential_total = cur_ms + estimated_time
            overshoot = potential_total - target_ms
            
            if overshoot > margin:  # Would overshoot beyond acceptable margin
                # Only skip if we're already reasonably close to target
                if cur_ms >= (target_ms - (4 * 60000)):  # Within 4 min of target
                    break  # Close enough, stop
                else:
                    # Still far from target, add it anyway
                    seq.append(pick)
                    cur_ms += estimated_time
            else:
                # Safe to add (won't overshoot by more than 4 min)
                seq.append(pick)
                cur_ms += estimated_time
            
            # Safety limits
            if len(seq) > 800: break
            if cur_ms > target_ms * 3: break
        
        return seq



def insert_massive_pause(events: list, rng: random.Random, mult: float = 1.0) -> tuple:
    """
    Insert one massive pause (500-2900ms x multiplier) at random point.
    For INEFFICIENT files only.
    
    EXCLUDES pause from:
    - Drag sequences (between DragStart and DragEnd)
    - Rapid click sequences (double-clicks, spam clicks)
    - First/last 10% of file (for safety)
    
    Returns (events_with_pause, pause_duration_ms, split_index)
    """
    if not events or len(events) < 10:
        return events, 0, 0
    
    # Generate massive pause: 4-7 minutes (240000-420000ms) x multiplier
    pause_duration = min(int(rng.uniform(240000.0, 420000.0)), _MAX_SINGLE_PAUSE_MS)  # no mult — flat 4-7 min, hard cap applied
    
    # Detect protected ranges (rapid clicks, double-clicks)
    protected_ranges = detect_rapid_click_sequences(events)
    
    # Precompute drag membership O(n) -> O(1) lookups
    drag_indices = build_drag_index_set(events)

    # Find safe split points (not in drag, not in rapid click, not in first/last 10%)
    safe_indices = []
    first_safe = int(len(events) * 0.1)  # Skip first 10%
    last_safe = int(len(events) * 0.9)   # Skip last 10%
    
    for i in range(first_safe, last_safe):
        if i in drag_indices:
            continue
        if is_in_protected_range(i, protected_ranges):
            continue
        # Don't insert right before a DragStart
        if i + 1 < len(events) and events[i + 1].get("Type") == "DragStart":
            continue
        if i + 1 < len(events) and (i + 1) in drag_indices:
            continue
        safe_indices.append(i)
    
    # If no safe indices found, return original events
    if not safe_indices:
        return events, 0, 0
    
    # Pick random safe split point
    split_index = rng.choice(safe_indices)
    
    # Shift all events after split point
    for i in range(split_index + 1, len(events)):
        events[i]["Time"] += pause_duration
    
    return events, pause_duration, split_index

# ============================================================================
# STRING PARTS WITH ANTI-DETECTION
# ============================================================================

def _pick_af_al(pool, rng):
    """Pick one always_first/last file randomly from a list/pool.
    Returns None if pool is empty or None. Accepts a single Path for backwards compat."""
    if not pool:
        return None
    if not isinstance(pool, list):
        return pool   # already a single Path (nested dicts etc.)
    return rng.choice(pool)

def string_cycle(subfolder_files, combination, rng,
                 distraction_files=None, distraction_chance=0.0,
                 is_click_sensitive=False,
                 play_always_first=True, play_always_last=True,
                 mult=1.0):
    """
    String one complete cycle (F1 -> F2 -> F3 -> ...) into a single unit.
    Returns raw events WITHOUT anti-detection features.
    play_always_first / play_always_last: for single-subfolder flat folders,
    always_first/last should fire only on the very first/last cycle of the whole
    strung file. Pass False for all but the first/last cycle respectively.
    Features will be applied to the ENTIRE cycle after.

    distraction_files: list of Path objects for generated distraction JSONs.
    distraction_chance: float in [0,1] - probability of inserting one distraction
                        file between each pair of folder transitions.
    is_click_sensitive: if True, skip jitter and idle wandering only. Cursor
                        transition still runs (position accuracy preserved).
    """
    
    def add_file_to_cycle(file_path, folder_num, file_label,
                          slot_is_click_sensitive=False, slot_is_random=False):
        """Helper to add a file to the cycle.
        slot_is_click_sensitive: suppresses cursor transition TO this file.
        The whole-cycle flag (is_click_sensitive) controls apply_cycle_features.
        """
        nonlocal timeline, cycle_events, file_info_list, total_pre_pause, total_transition_time, total_snap_gap_time, files_added
        
        # Load events — with two-level cache to avoid re-reading disk and
        # re-running Parts A-F for the same file across multiple versions.
        _fp_str = str(file_path)
        if _fp_str in _processed_events_cache:
            # Fast path: list-comprehension copy (14x faster than deepcopy)
            # Safe because all field values are immutable (str, int, None).
            _cached = _processed_events_cache[_fp_str]
            events = [{'Type': e['Type'], 'Time': e['Time'], 'X': e['X'],
                       'Y': e['Y'], 'Delta': e['Delta'], 'KeyCode': e['KeyCode']}
                      for e in _cached['events']]
            base_time_pre_filter = _cached['base_time']
            if not events:
                return
        else:
            # Slow path: load, filter, run Parts A-F, then cache result
            try:
                if _fp_str in _raw_file_cache:
                    events = json.loads(_raw_file_cache[_fp_str])
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        _raw = f.read()
                    _raw_file_cache[_fp_str] = _raw
                    events = json.loads(_raw)
            except Exception:
                return
            if not events:
                return
            # Capture base_time BEFORE filtering so that files where the first
            # event is a filtered key (e.g. END key at t=90ms) keep their full
            # original duration. Without this, base_time jumps to the first
            # surviving event and the entire leading gap is lost.
            base_time_pre_filter = min(e.get('Time', 0) for e in events)

            # Filter problematic keys only
            events = filter_problematic_keys(events)
            if not events:
                return

            # INTRA-FILE ZERO-GAP FIX (Feature 25)
            # Two separate checks, both shift the DragStart (and all events after it)
            # forward to enforce a minimum gap:
            #
            # Part A — MouseMove -> click-type gap < 15ms ("simultaneous arrival + click")
            #   Some recordings capture a MouseMove and DragStart/LeftDown at the same
            #   millisecond (or within 1-14ms). The macro player reads these as
            #   simultaneous - it can't distinguish "arrived THEN clicked" from "both at
            #   once" - causing a left-button clamp at that position.
            #   Threshold: 15ms  |  Target separation: 20ms
            #
            # Part B — DragEnd -> DragStart gap < 200ms ("too-fast re-press")
            #   Source recordings may contain rapid re-presses in the 0–199ms range.
            #   The macro player cannot distinguish a genuine release + re-click from
            #   a single held drag in that window, causing left-button clamp.
            #   v3.18.79: threshold 150ms. v3.18.92/93: raised to 200ms.
            #   Threshold: 200ms  |  Target separation: 200ms
            _CLICK_TYPES = {'DragStart', 'LeftDown', 'RightDown', 'Click'}
    
            # Part A: MouseMove -> click-type gap < 30ms (v3.19.06 raised from 15ms).
            # Fast source recordings often have the cursor still moving when
            # DragStart fires — the last MM is at X0 (slightly short of target X1)
            # and DragStart fires 15-29ms later, also at X0. Raising to 30ms means
            # any click with < 30ms since the last cursor movement is shifted to
            # 35ms after that MM, giving the macro player time to register the
            # cursor at its settled position before the click fires.
            _ZERO_GAP_THRESHOLD  = 35   # ms - gaps below this = cursor still moving
                                         # Raised from 30: catches borderline 30-34ms
                                         # cases (e.g. 33ms approach) where cursor may
                                         # not have fully settled before click fires.
            _ZERO_GAP_TARGET     = 35   # ms - minimum settle time to enforce
            _SETTLE_BEFORE_CLICK = 15   # ms - settling MM lands this many ms before click
            for _zi in range(1, len(events)):
                if (events[_zi].get('Type') in _CLICK_TYPES
                        and events[_zi - 1].get('Type') == 'MouseMove'):
                    _gap = events[_zi].get('Time', 0) - events[_zi - 1].get('Time', 0)
                    if 0 <= _gap < _ZERO_GAP_THRESHOLD:
                        _shift = _ZERO_GAP_TARGET - _gap
                        for _j in range(_zi, len(events)):
                            events[_j]['Time'] = events[_j].get('Time', 0) + _shift
                        # Insert a settling MouseMove at the click's own coords,
                        # timed _SETTLE_BEFORE_CLICK ms before the (now-shifted) click.
                        # This guarantees the cursor is at the correct tile when the
                        # click fires, regardless of where the last recorded MM landed.
                        _click_x = events[_zi].get('X')
                        _click_y = events[_zi].get('Y')
                        if _click_x is not None and _click_y is not None:
                            _settle_mm = {
                                'Type':    'MouseMove',
                                'Time':    events[_zi]['Time'] - _SETTLE_BEFORE_CLICK,
                                'X':       _click_x,
                                'Y':       _click_y,
                                'Delta':   None,
                                'KeyCode': None,
                            }
                            events.insert(_zi, _settle_mm)
                            # _zi now points to the settling MM; the click is at _zi+1.
                            # Part B/C loops run AFTER this loop so their indices are
                            # unaffected — they operate on the already-modified list.
            # --- Rapid pre-scan: protect intentional double/rapid clicks from Part B ---
            # Strict path:  DS[i-2] -> DE[i-1] -> DS[i]  (no MMs between, same tile <=5px)
            # Soft path:    DS -> DE -> (any MMs) -> DS     (cursor drift allowed, <=20px)
            # Both mark the second DS as protected so Part B never shifts it.
            _RAPID_POS_TOL      =  5   # px - strict: same tile, no drift
            _RAPID_POS_TOL_SOFT = 20   # px - soft: slight cursor movement between clicks
            _RAPID_WIN_MS       = 500  # ms - max total span DS1->DS2 for both paths
    
            rapid_protected       = set()   # strict rapid-click indices
            soft_double_protected = set()   # soft double-click indices (MM drift between)
    
            for _ri in range(1, len(events)):
                if events[_ri].get('Type') != 'DragStart':
                    continue
    
                # --- Strict path (existing logic, unchanged) ---
                if (_ri >= 2
                        and events[_ri - 1].get('Type') == 'DragEnd'
                        and events[_ri - 2].get('Type') == 'DragStart'):
                    _rgap   = events[_ri]['Time'] - events[_ri - 1].get('Time', 0)
                    _rtotal = events[_ri]['Time'] - events[_ri - 2].get('Time', 0)
                    if 0 <= _rgap < _RAPID_WIN_MS and 0 < _rtotal < _RAPID_WIN_MS:
                        _rx1 = events[_ri - 2].get('X') or 0
                        _ry1 = events[_ri - 2].get('Y') or 0
                        _rx2 = events[_ri].get('X') or 0
                        _ry2 = events[_ri].get('Y') or 0
                        _rdist = ((_rx2 - _rx1) ** 2 + (_ry2 - _ry1) ** 2) ** 0.5
                        if _rdist <= _RAPID_POS_TOL:
                            rapid_protected.add(_ri)
                            continue  # already handled, skip soft check
    
                # --- Soft path (new): DS -> DE -> (MMs only) -> DS ---
                # Walk backwards from _ri-1 through MouseMoves to find the preceding DragEnd
                _de_idx = None
                for _back in range(_ri - 1, max(_ri - 15, -1), -1):
                    _bt = events[_back].get('Type')
                    if _bt == 'DragEnd':
                        _de_idx = _back
                        break
                    elif _bt != 'MouseMove':
                        break   # hit a non-MM non-DE - not a clean drift pattern
    
                if _de_idx is None:
                    continue
    
                # Walk backwards from _de_idx-1 to find the DragStart that opened this DE
                _ds_idx = None
                for _back in range(_de_idx - 1, max(_de_idx - 5, -1), -1):
                    if events[_back].get('Type') == 'DragStart':
                        _ds_idx = _back
                        break
                    elif events[_back].get('Type') != 'MouseMove':
                        break
    
                if _ds_idx is None:
                    continue
    
                _rtotal = events[_ri]['Time'] - events[_ds_idx].get('Time', 0)
                if not (0 < _rtotal < _RAPID_WIN_MS):
                    continue
    
                _rx1   = events[_ds_idx].get('X') or 0
                _ry1   = events[_ds_idx].get('Y') or 0
                _rx2   = events[_ri].get('X') or 0
                _ry2   = events[_ri].get('Y') or 0
                _rdist = ((_rx2 - _rx1) ** 2 + (_ry2 - _ry1) ** 2) ** 0.5
    
                if _rdist <= _RAPID_POS_TOL_SOFT:
                    soft_double_protected.add(_ri)
            # --- end rapid pre-scan ---
    
            # Part B: DragEnd -> DragStart too-fast re-press
            # SKIP rapid-protected indices (intentional double/multi-clicks).
            _DRAG_REPRESS_THRESHOLD = 200   # ms - re-press faster than this = clamp risk
            _DRAG_REPRESS_TARGET    = 200   # ms - minimum release time to enforce
            for _zi in range(1, len(events)):
                if _zi in rapid_protected or _zi in soft_double_protected: continue
                if (events[_zi].get('Type') == 'DragStart'
                        and events[_zi - 1].get('Type') == 'DragEnd'):
                    _gap = events[_zi].get('Time', 0) - events[_zi - 1].get('Time', 0)
                    if 0 <= _gap < _DRAG_REPRESS_THRESHOLD:
                        _shift = _DRAG_REPRESS_TARGET - _gap
                        for _j in range(_zi, len(events)):
                            events[_j]['Time'] = events[_j].get('Time', 0) + _shift
    
            # Part C (v3.19.02): any button-event -> button-down gap < 200ms.
            # Catches cross-type rapid re-press patterns missed by A and B:
            #   LeftUp  -> LeftDown   (rapid double-click via LD/LU events)
            #   RightUp -> RightDown  (rapid right-click)
            #   DragEnd -> LeftDown   (cross-type re-press)
            #   LeftUp  -> DragStart  (cross-type re-press)
            #   ButtonDown -> ButtonDown (missing release = permanent hold risk)
            # DragEnd->DragStart is skipped — handled by Part B above.
            #   Threshold: 200ms  |  Target: 200ms
            _BUTTON_DOWN_TYPES = {'DragStart', 'LeftDown', 'RightDown'}
            _BUTTON_ANY_TYPES  = {'DragStart', 'DragEnd', 'LeftDown', 'LeftUp',
                                   'RightDown', 'RightUp', 'MouseDown', 'MouseUp'}
            _PART_C_THRESHOLD  = 200
            _PART_C_TARGET     = 200
            for _zi in range(1, len(events)):
                if _zi in rapid_protected: continue  # intentional rapid click
                _cur = events[_zi].get('Type')
                _prv = events[_zi - 1].get('Type')
                if _prv == 'DragEnd' and _cur == 'DragStart':
                    continue  # Part B already handled this
                if _cur in _BUTTON_DOWN_TYPES and _prv in _BUTTON_ANY_TYPES:
                    _gap = events[_zi].get('Time', 0) - events[_zi - 1].get('Time', 0)
                    if 0 <= _gap < _PART_C_THRESHOLD:
                        _shift = _PART_C_TARGET - _gap
                        for _j in range(_zi, len(events)):
                            events[_j]['Time'] = events[_j].get('Time', 0) + _shift
    
    
            # --- Part D: zero-gap DragEnd guard ---
            # A DragEnd firing at the same timestamp as the preceding MouseMove
            # causes the button-release to register mid-movement.
            # Shift it forward so the release always lands after the cursor settles.
            _DRAG_END_SETTLE_THRESHOLD = 25   # ms raised from 20 — catches 22ms recording
            _DRAG_END_SETTLE_TARGET    = 25   # artifacts where cursor barely moves during hold
    
            for _di in range(1, len(events)):
                if events[_di].get('Type') != 'DragEnd':
                    continue
                if events[_di - 1].get('Type') != 'MouseMove':
                    continue
                _de_gap = events[_di].get('Time', 0) - events[_di - 1].get('Time', 0)
                if 0 <= _de_gap < _DRAG_END_SETTLE_THRESHOLD:
                    _de_shift = _DRAG_END_SETTLE_TARGET - _de_gap
                    for _j in range(_di, len(events)):
                        events[_j]['Time'] = events[_j].get('Time', 0) + _de_shift
            # --- end Part D ---
            # --- Part E: out-of-bounds MouseMove clamp ---
            # Cursor positions outside game bounds are safe during real recording
            # (no click = no focus change) but dangerous in simulated playback
            # (OS/browser responds to cursor entering title bar / system UI area).
            # If an out-of-bounds MM is followed by a long idle (cursor parked
            # there), replace its coords with the last known safe position.
            _OOB_SAFE_Y_MIN  = 80    # raised from 50: catches cursor parking at Y=57-79
                                      # (browser chrome / top OS UI area). Only affects
                                      # cursors PARKED in idle gaps >= _OOB_IDLE_GATE --
                                      # active movement through Y<80 is never clamped.
            _OOB_SAFE_Y_MAX  = 900   # anything below this is probably off-screen
            _OOB_SAFE_X_MIN  = 0
            _OOB_SAFE_X_MAX  = 1920
            _OOB_IDLE_GATE   = 1000  # ms — only clamp MMs about to be parked here
    
            _last_safe_x, _last_safe_y = None, None
            for _ei in range(len(events)):
                _ex = events[_ei].get('X')
                _ey = events[_ei].get('Y')
                if _ex is None or _ey is None:
                    continue  # key event, skip
                _in_bounds = (_OOB_SAFE_X_MIN <= _ex <= _OOB_SAFE_X_MAX and
                              _OOB_SAFE_Y_MIN <= _ey <= _OOB_SAFE_Y_MAX)
                if _in_bounds:
                    _last_safe_x, _last_safe_y = _ex, _ey
                else:
                    # Out of bounds. Only clamp if the cursor is about to be
                    # parked here (large gap AFTER this event). Fast-moving paths
                    # that pass through unusual coords mid-sweep are left alone.
                    _gap_after = (events[_ei + 1]['Time'] - events[_ei]['Time']
                                  if _ei < len(events) - 1 else 0)
                    if _gap_after >= _OOB_IDLE_GATE and _last_safe_x is not None:
                        events[_ei]['X'] = _last_safe_x
                        events[_ei]['Y'] = _last_safe_y
            # --- end Part E ---
            # --- Part F: long-gap settling MM ---
            # When the last MM before a click is > 1000ms ago, it falls outside the
            # jitter exclusion zone and may have been modified. Insert a settling MM
            # at the click's exact coordinates 15ms before the click — this MM is
            # within 1000ms of the click and therefore jitter-protected.
            # No time shift needed (unlike Part A); cursor repositioning only.
            _LONG_GAP_SETTLE_MS = 1000   # ms — beyond this, last MM may be jitterable
    
            for _fi in range(1, len(events)):
                if events[_fi].get('Type') not in _CLICK_TYPES:
                    continue
                if events[_fi - 1].get('Type') != 'MouseMove':
                    continue
                _fg = events[_fi].get('Time', 0) - events[_fi - 1].get('Time', 0)
                if _fg <= _LONG_GAP_SETTLE_MS:
                    continue
                _fx = events[_fi].get('X')
                _fy = events[_fi].get('Y')
                if _fx is None or _fy is None:
                    continue
                _f_settle = {
                    'Type':    'MouseMove',
                    'Time':    events[_fi]['Time'] - _SETTLE_BEFORE_CLICK,
                    'X':       _fx,
                    'Y':       _fy,
                    'Delta':   None,
                    'KeyCode': None,
                }
                events.insert(_fi, _f_settle)
                # _fi now points to settling MM; click is at _fi+1.
                # Outer loop continues past both safely.
            # --- end Part F ---
    
    
    
            # Cache the fully-processed result for reuse across versions
            # (Only store on slow path — skip if this file was already cached)
            if _fp_str not in _processed_events_cache:
                import copy as _copy
                _processed_events_cache[_fp_str] = {
                    'events':    _copy.deepcopy(events),
                    'base_time': base_time_pre_filter,
                }

        # Normalize timing — use pre-filter base so leading gaps are preserved
        base_time = base_time_pre_filter
        
        # PRE-FILE PAUSE: random gap before file plays so click has time to release.
        # (random) slots: skip entirely — files play back-to-back with only cursor move.
        if cycle_events:
            if not slot_is_random:
                # Normal/click-sensitive: 500-800ms × mult pre-file pause
                pre_file_pause = rng.uniform(500.0, 800.0) * mult
                timeline += pre_file_pause
                total_pre_pause += pre_file_pause
            
            # NOW do cursor transition (AFTER pause, so click has time to release)
            # Get last position from previous file
            last_x, last_y = None, None
            for e in reversed(cycle_events):
                if e.get('X') is not None and e.get('Y') is not None:
                    last_x, last_y = int(e['X']), int(e['Y'])
                    break
            
            # Get first position of current file
            first_x, first_y = None, None
            for e in events:
                if e.get('X') is not None and e.get('Y') is not None:
                    first_x, first_y = int(e['X']), int(e['Y'])
                    break
            
            
            # CURSOR TRANSITION: runs for all folders including click-sensitive.
            # slot_is_click_sensitive: transition TO this specific subfolder is suppressed.
            # is_click_sensitive: only suppresses jitter + idle (NOT transition).
            # slot_is_random: uses 2.0-2.5x faster transition; no post-snap gap.
            if not slot_is_click_sensitive:
                if slot_is_random:
                    # (random) folders: 2.0-2.5x faster cursor movement, no post-snap gap
                    _speed_mult = rng.uniform(2.0, 2.5)
                    transition_duration = rng.uniform(200.0, 400.0) * mult / _speed_mult
                else:
                    transition_duration = rng.uniform(200.0, 400.0) * mult
                if last_x is not None and first_x is not None and (last_x != first_x or last_y != first_y):
                    transition_path = generate_human_path(
                        last_x, last_y, first_x, first_y,
                        int(transition_duration), rng
                    )
                    for rel_time, x, y in transition_path:
                        cycle_events.append({
                            'Type': 'MouseMove',
                            'Time': timeline + rel_time,
                            'X': x,
                            'Y': y
                        })
                    timeline += transition_duration
                    total_transition_time += int(transition_duration)
                    # Final snap to exact start position
                    cycle_events.append({
                        'Type': 'MouseMove',
                        'Time': timeline,
                        'X': first_x,
                        'Y': first_y
                    })
                    if not slot_is_random:
                        # POST-SNAP GAP: normal folders only
                        post_snap_gap = int(rng.uniform(80, 150))
                        timeline += post_snap_gap
                        total_snap_gap_time += post_snap_gap
        
        # Add events from current file
        if slot_is_random:
            # (random) folders: compress idle gaps and speed up cursor movement.
            # 1. Cap any inter-event gap to _RANDOM_MAX_GAP_MS (strips parked-cursor pauses).
            # 2. Divide all inter-event intervals by _RANDOM_SPEED_MULT (faster movement).
            # 3. EXCEPTION: the gap immediately before any click event (DragStart/LeftDown/
            #    Click/RightDown) is never compressed below _RANDOM_MIN_PRECLICK_MS.
            #    This ensures the cursor has fully settled at the target pixel before
            #    the click fires — prevents wrong-tile clicks from compressed approach.
            _RANDOM_MAX_GAP_MS     = 120.0   # idle gaps clamped to this
            _RANDOM_SPEED_MULT     = rng.uniform(2.5, 3.5)  # movement speed multiplier
            _RANDOM_MIN_PRECLICK_MS = 38.0   # minimum gap before any click event
            _CLICK_TYPES_R = {'DragStart', 'LeftDown', 'RightDown', 'Click'}
            _r_cursor_t = timeline  # running cursor time for (random) placement
            _prev_orig_t = base_time  # previous event's original time
            for event in events:
                new_event = {**event}
                _orig_gap = event['Time'] - _prev_orig_t  # gap in original recording
                _clamped  = min(_orig_gap, _RANDOM_MAX_GAP_MS)  # cap idle gaps
                _scaled   = _clamped / _RANDOM_SPEED_MULT       # speed up
                # Protect pre-click gap: ensure cursor has settled before click fires
                if event.get('Type') in _CLICK_TYPES_R:
                    _scaled = max(_scaled, _RANDOM_MIN_PRECLICK_MS)
                _r_cursor_t += _scaled
                new_event['Time'] = _r_cursor_t
                cycle_events.append(new_event)
                _prev_orig_t = event['Time']
        else:
            for event in events:
                new_event = {**event}
                new_event['Time'] = event['Time'] - base_time + timeline
                cycle_events.append(new_event)
        
        # Update timeline and track THIS file's end time
        if cycle_events:
            timeline = cycle_events[-1]['Time']
            file_info_list.append((folder_num, file_label, timeline))
        files_added += 1
    
    # Main cycle building
    cycle_events = []
    file_info_list = []
    # Start buffer: 5–8 seconds of silence before the first event so the macro
    # player has time to initialise before any input fires.
    timeline = rng.uniform(5000.0, 8000.0)
    
    files_added = 0  # Counts files added; guards pre-play buffer for every non-first file
    # NEW: Track pre-file pauses, post-pause delays, cursor transitions, and distraction durations
    total_pre_pause = 0
    total_transition_time = 0
    total_snap_gap_time = 0      # cumulative post-snap gaps (80-150ms per file transition)
    total_distraction_pause = 0  # cumulative duration of all inserted distraction files
    
    # SINGLE-SUBFOLDER MODE: if only one subfolder exists, always_first/last
    # should bracket the ENTIRE strung file (once at the very start, once at
    # the very end) rather than wrapping every single selected file.
    single_subfolder = len(subfolder_files) == 1
    if single_subfolder:
        # There is only one folder_num - grab its always_first/last once
        only_folder_num = next(iter(subfolder_files))
        only_folder_data = subfolder_files[only_folder_num]
        single_always_first = _pick_af_al(only_folder_data.get('always_first', []), rng)
        single_always_last  = _pick_af_al(only_folder_data.get('always_last',  []), rng)
        # Play always_first only when flagged (outer loop controls first-cycle)
        if single_always_first and play_always_first:
            add_file_to_cycle(single_always_first, only_folder_num,
                              f"[ALWAYS FIRST] {single_always_first.name}")
    
    def _maybe_insert_distraction(cur_folder_num):
        """Roll the chance and insert one distraction file at the current timeline.
        Uses VirtualDistQueue so all 50 files play before any repeats."""
        nonlocal total_distraction_pause
        if not distraction_files or distraction_chance <= 0.0:
            return
        if rng.random() < distraction_chance:
            # distraction_files is a VirtualDistQueue when called from main()
            dist_path = (distraction_files.next()
                         if hasattr(distraction_files, 'next')
                         else rng.choice(distraction_files))
            t_before  = timeline
            add_file_to_cycle(dist_path, cur_folder_num,
                               f"[DISTRACTION] {dist_path.name}")
            total_distraction_pause += (timeline - t_before)

    def _play_nested_loop(nested_item, parent_folder_num=None):
        """Play ONE loop of the nested sub-cycle: F1->F2->F3->F4->optional.
        AF/AL are NOT included here - they wrap ALL loops, called once by the caller.
        parent_folder_num: when set (for _random_single items), use it as the
        manifest folder_num so files show as F6- instead of F1-, F2-, etc."""
        _sub_combo  = nested_item['combo']
        _nsf        = nested_item['nested_sf']
        _is_random_single = nested_item.get('_random_single', False)
        for _sfn, _sfl in _sub_combo:
            _sfd = _nsf.get(_sfn, {})
            if not isinstance(_sfl, list):
                _sfl = [_sfl]
            # For (random) items use parent F-number in manifest; sub-subfolder number otherwise
            _manifest_fn = parent_folder_num if (_is_random_single and parent_folder_num is not None) else _sfn
            _saf = _pick_af_al(_sfd.get('always_first', []), rng)
            _sal = _pick_af_al(_sfd.get('always_last',  []), rng)
            if _saf:
                add_file_to_cycle(_saf, _manifest_fn, f"[ALWAYS FIRST] {_saf.name}")
            for _fp in _sfl:
                if isinstance(_fp, dict) and _fp.get('_nested'):
                    _play_nested_loop(_fp)
                else:
                    add_file_to_cycle(_fp, _manifest_fn, _fp.name,
                                      slot_is_random=_is_random_single)
            if _sal:
                add_file_to_cycle(_sal, _manifest_fn, f"[ALWAYS LAST] {_sal.name}")

    def _play_nested_group(nested_items_list):
        """Play all loops for a nested folder slot.
        AF fires ONCE before all loops; AL fires ONCE after all loops.
        Pattern: [AF] -> loop1 -> loop2 -> ... -> [AL]
        (random) items: no AF/AL wrapping — each is a single file from one sub-subfolder,
        played directly in the pre-shuffled order.
        """
        if not nested_items_list:
            return
        # (random) slots: items are individual files, not looped combos — skip AF/AL
        if nested_items_list[0].get('_random_single'):
            for _ni in nested_items_list:
                _play_nested_loop(_ni, parent_folder_num=_ni.get('_parent_folder_num'))
            return
        _naf = _pick_af_al(nested_items_list[0].get('nested_root_af', []), rng)
        _nal = _pick_af_al(nested_items_list[0].get('nested_root_al', []), rng)
        if _naf:
            add_file_to_cycle(_naf, 0.0, f"[ALWAYS FIRST] {_naf.name}")
        for _ni in nested_items_list:
            _play_nested_loop(_ni)
        if _nal:
            add_file_to_cycle(_nal, 0.0, f"[ALWAYS LAST] {_nal.name}")

    for idx_combo, (folder_num, file_list) in enumerate(combination):
        folder_data = subfolder_files.get(folder_num, {})
        if not isinstance(file_list, list):
            file_list = [file_list]

        # DISTRACTION: maybe insert BEFORE this folder's files
        _maybe_insert_distraction(folder_num)

        # Separate nested dicts from regular file paths in this slot
        _nested_items = [it for it in file_list if isinstance(it, dict) and it.get('_nested')]
        _regular_items = [it for it in file_list if not (isinstance(it, dict) and it.get('_nested'))]

        if _nested_items:
            # Nested folder: AF once -> all loops -> AL once
            _play_nested_group(_nested_items)
        elif single_subfolder:
            # Single-subfolder: always_first/last already played above/below loop
            for item in _regular_items:
                add_file_to_cycle(item, folder_num, item.name)
        else:
            # Multi-subfolder: always_first/last wrap ONLY the files of their OWN folder.
            # slot_cs: True if this specific subfolder is click-sensitive (per-slot flag).
            _slot_cs = folder_data.get('is_click_sensitive', False)
            af = _pick_af_al(folder_data.get('always_first', []), rng)
            al = _pick_af_al(folder_data.get('always_last',  []), rng)
            if af:
                add_file_to_cycle(af, folder_num, f"[ALWAYS FIRST] {af.name}",
                                  slot_is_click_sensitive=_slot_cs)
            for item in _regular_items:
                add_file_to_cycle(item, folder_num, item.name,
                                  slot_is_click_sensitive=_slot_cs)
            if al:
                add_file_to_cycle(al, folder_num, f"[ALWAYS LAST] {al.name}",
                                  slot_is_click_sensitive=_slot_cs)

    # DISTRACTION: maybe insert AFTER the very last folder
    if combination:
        last_folder_num = combination[-1][0]
        _maybe_insert_distraction(last_folder_num)

    if single_subfolder and single_always_last and play_always_last:
        add_file_to_cycle(single_always_last, only_folder_num,
                          f"[ALWAYS LAST] {single_always_last.name}")

    return {
        'events': cycle_events,
        'file_info': file_info_list,
        'pre_pause_total': total_pre_pause,
        'transition_total': total_transition_time,
        'snap_gap_total': total_snap_gap_time,
        'distraction_pause_total': total_distraction_pause,
    }


# ============================================================================
# DISTRACTION FILE GENERATION
# ============================================================================

# Windows Virtual Key codes for keyboard events
# (must be integers - the macro player does NOT accept strings)
_VK = {
    'a':8  # placeholder - built dynamically below
}
_VK = {}
for _c in 'abcdefghijklmnopqrstuvwxyz':
    _VK[_c] = ord(_c.upper())   # A=65 ? Z=90
_VK.update({
    '0': 48, '1': 49, '2': 50, '3': 51, '4': 52,
    '5': 53, '6': 54, '7': 55, '8': 56, '9': 57,
    'Back': 8,         # Backspace
    '.': 190, ',': 188, ';': 186, '/': 191,
    "'": 222, '[': 219, ']': 221, '\\': 220,
    '-': 189, '=': 187,
})


def _evt(type_, time, x=None, y=None, delta=None, keycode=None) -> dict:
    """
    Build a properly-structured macro event with ALL 6 required fields.
    The macro player expects Type, Time, X, Y, Delta, KeyCode on EVERY event.
    Keyboard events:  X=None, Y=None, Delta=None, KeyCode=<int VK code>
    Mouse events:     X=<int>, Y=<int>, Delta=None, KeyCode=None
    """
    return {
        'Type':    type_,
        'Time':    time,
        'X':       x,
        'Y':       y,
        'Delta':   delta,
        'KeyCode': keycode,
    }


# Common words / phrases a player might idly type then delete
_DISTRACTION_WORDS = [
    "nice", "lol", "gg", "hey", "ok", "sure", "brb", "back", "sec",
    "wait", "almost", "done", "yes", "no", "maybe", "idk", "nah",
    "yeah", "yep", "nope", "omg", "wow", "thanks", "ty", "np",
    "haha", "lmao", "ez", "rip", "oof", "yo", "kk",
    "cya", "afk", "gtg", "bbl", "wb", "ggwp", "niceone",
]

# Keys that players accidentally spam then erase (letters + symbols with VK mappings)
_SPAM_KEYS = list("asdfghjklqwertyuiopzxcvbnm/.,;'[]-=")


def _human_interval(rng, lo_ms: float, hi_ms: float) -> float:
    return rng.uniform(lo_ms, hi_ms)


def _safe_gap(rng) -> float:
    """Minimum advance so no two events share a timestamp."""
    return _human_interval(rng, 30.0, 120.0)


def _add_mouse_wander(events, timeline, rng, cur_x, cur_y):
    """
    Move cursor to 2-7 random destinations.
    Per-call: number of moves, speed envelope, and inter-move pause
    range are all re-randomised so no two wanders feel the same.
    Returns (timeline, x, y).
    """
    t = timeline + _safe_gap(rng)
    x, y = cur_x, cur_y
    # Randomise both envelope bounds so the RANGE of speeds varies per call
    spd_lo = rng.uniform(150.0, 500.0)
    spd_hi = rng.uniform(spd_lo + 200.0, spd_lo + 1200.0)
    gap_lo = rng.uniform(30.0, 150.0)
    gap_hi = rng.uniform(gap_lo + 100.0, gap_lo + 600.0)
    n_moves = rng.randint(2, 7)
    for _ in range(n_moves):
        tx = rng.randint(150, 950)
        ty = rng.randint(120, 620)
        seg_dur = _human_interval(rng, spd_lo, spd_hi)
        path = generate_human_path(x, y, tx, ty, int(seg_dur), rng)
        for rel, px, py in path:
            events.append(_evt('MouseMove', t + rel, px, py))
        t += seg_dur
        x, y = tx, ty
        t += _human_interval(rng, gap_lo, gap_hi)
    return t, x, y


def _add_cursor_pause(events, timeline, rng, cur_x, cur_y):
    """
    Stay still (or drift slightly) for a randomised duration.
    Drift probability, drift magnitude, and pause length all vary per call.
    Returns (timeline, x, y).
    """
    # Duration envelope randomised per call: 0.3s-4s range, but the actual
    # bounds shift so some calls are twitchy-short and some are long
    dur_lo = rng.uniform(300.0, 800.0)
    dur_hi = rng.uniform(dur_lo + 400.0, dur_lo + 2500.0)
    duration = _human_interval(rng, dur_lo, dur_hi)
    t_start  = timeline + _safe_gap(rng)
    # Drift: random probability AND random magnitude per call
    drift_prob = rng.uniform(0.20, 0.65)
    if rng.random() < drift_prob:
        drift_mag = rng.randint(3, 18)
        dx = max(100, min(1800, cur_x + rng.randint(-drift_mag, drift_mag)))
        dy = max(100, min(1000, cur_y + rng.randint(-drift_mag, drift_mag)))
        mid = t_start + duration * rng.uniform(0.2, 0.8)
        events.append(_evt('MouseMove', mid,              dx,    dy))
        events.append(_evt('MouseMove', t_start+duration, cur_x, cur_y))
    return t_start + duration, cur_x, cur_y


def _add_right_click(events, timeline, rng, cur_x, cur_y):
    """
    Move to a safe neutral zone far from recorded macro cursor positions,
    then right-click there. The target is always in the minimap or
    interface panel area (top-right / bottom-right of OSRS screen) —
    far from the game viewport where macro actions occur.
    Approach speed, hover time, and hold duration all vary per call.
    Returns (timeline, x, y).
    """
    t = timeline + _safe_gap(rng)
    # Safe zone: minimap area (top-right) or interface panel (bottom-right).
    # These regions are inert to right-click in OSRS and far from game viewport.
    # Two safe zones picked randomly per call so the pattern stays varied.
    _SAFE_ZONES = [
        (548, 620, 10,  80),   # minimap top-right
        (548, 700, 81, 160),   # minimap lower
        (548, 730, 340, 430),  # interface panel top
        (548, 730, 431, 500),  # interface panel mid
    ]
    zone = rng.choice(_SAFE_ZONES)
    tx = rng.randint(zone[0], zone[1])
    ty = rng.randint(zone[2], zone[3])
    spd_lo = rng.uniform(100.0, 300.0)
    move_dur = _human_interval(rng, spd_lo, spd_lo + rng.uniform(200.0, 700.0))
    path = generate_human_path(cur_x, cur_y, tx, ty, int(move_dur), rng)
    for rel, px, py in path:
        events.append(_evt('MouseMove', t + rel, px, py))
    t += move_dur
    cur_x, cur_y = tx, ty
    # Hover time randomised per call
    t += _human_interval(rng, 30.0, rng.uniform(100.0, 350.0))
    hold_lo = rng.uniform(40.0, 100.0)
    hold = _human_interval(rng, hold_lo, hold_lo + rng.uniform(80.0, 250.0))
    events.append(_evt('RightDown', t,        cur_x, cur_y))
    events.append(_evt('RightUp',   t + hold, cur_x, cur_y))
    # Post-click linger: sometimes brief, sometimes longer
    t += hold + _human_interval(rng, 80.0, rng.uniform(300.0, 900.0))
    return t, cur_x, cur_y


def _add_typing(events, timeline, rng, cur_x, cur_y):
    """
    Type a random word then erase it character by character.
    Typing speed, erasing speed, and hesitation pause all re-randomised
    per call so every typing event has its own rhythm.
    KeyCode = integer VK code, X/Y = None.
    """
    word = rng.choice(_DISTRACTION_WORDS)
    t    = timeline + _safe_gap(rng)
    # Per-call speed envelopes
    type_hold_lo = rng.uniform(40.0, 90.0)
    type_hold_hi = rng.uniform(type_hold_lo + 30.0, type_hold_lo + 120.0)
    type_gap_lo  = rng.uniform(50.0, 130.0)
    type_gap_hi  = rng.uniform(type_gap_lo + 40.0, type_gap_lo + 180.0)
    erase_hold_lo = rng.uniform(40.0, 100.0)
    erase_hold_hi = rng.uniform(erase_hold_lo + 30.0, erase_hold_lo + 110.0)
    erase_gap_lo  = rng.uniform(45.0, 110.0)
    erase_gap_hi  = rng.uniform(erase_gap_lo + 30.0, erase_gap_lo + 140.0)
    hesitation    = rng.uniform(100.0, rng.uniform(500.0, 3000.0))

    for ch in word:
        vk = _VK.get(ch, _VK.get(ch.lower()))
        if vk is None:
            continue
        hold = _human_interval(rng, type_hold_lo, type_hold_hi)
        events.append(_evt('KeyDown', t,        keycode=vk))
        events.append(_evt('KeyUp',   t + hold, keycode=vk))
        t += hold + _human_interval(rng, type_gap_lo, type_gap_hi)
    t += hesitation
    bk = _VK['Back']
    for _ in word:
        hold = _human_interval(rng, erase_hold_lo, erase_hold_hi)
        events.append(_evt('KeyDown', t,        keycode=bk))
        events.append(_evt('KeyUp',   t + hold, keycode=bk))
        t += hold + _human_interval(rng, erase_gap_lo, erase_gap_hi)
    return t


def _add_key_spam(events, timeline, rng, cur_x, cur_y):
    """
    Accidentally spam a key 2-9x, then erase with Backspace.
    Spam speed, erase speed, and the 'oh no' pause all re-randomised per call.
    KeyCode = integer VK code.
    """
    key   = rng.choice(_SPAM_KEYS)
    vk    = _VK.get(key)
    if vk is None:
        return timeline
    count = rng.randint(2, 9)
    t     = timeline + _safe_gap(rng)
    bk    = _VK['Back']
    # Spam envelope: sometimes key-repeat fast, sometimes deliberate
    spam_hold_lo = rng.uniform(25.0, 80.0)
    spam_hold_hi = rng.uniform(spam_hold_lo + 20.0, spam_hold_lo + 100.0)
    spam_gap_lo  = rng.uniform(15.0, 60.0)
    spam_gap_hi  = rng.uniform(spam_gap_lo + 15.0, spam_gap_lo + 80.0)
    # "Oh no" reaction: anywhere from a quick twitch to a long freeze
    ohno_pause = rng.uniform(150.0, rng.uniform(500.0, 1800.0))
    # Erase envelope: typically slower than spam (deliberate)
    erase_hold_lo = rng.uniform(45.0, 100.0)
    erase_hold_hi = rng.uniform(erase_hold_lo + 20.0, erase_hold_lo + 90.0)
    erase_gap_lo  = rng.uniform(40.0, 100.0)
    erase_gap_hi  = rng.uniform(erase_gap_lo + 20.0, erase_gap_lo + 110.0)

    for _ in range(count):
        hold = _human_interval(rng, spam_hold_lo, spam_hold_hi)
        events.append(_evt('KeyDown', t,        keycode=vk))
        events.append(_evt('KeyUp',   t + hold, keycode=vk))
        t += hold + _human_interval(rng, spam_gap_lo, spam_gap_hi)
    t += ohno_pause
    for _ in range(count):
        hold = _human_interval(rng, erase_hold_lo, erase_hold_hi)
        events.append(_evt('KeyDown', t,        keycode=bk))
        events.append(_evt('KeyUp',   t + hold, keycode=bk))
        t += hold + _human_interval(rng, erase_gap_lo, erase_gap_hi)
    return t


def _add_shape_movement(events, timeline, rng, cur_x, cur_y):
    """
    Trace a geometric shape: circle/donut (3-5 laps), triangle, square,
    rectangle, or star. Each shape has per-point jitter and varied speed
    so it reads human, not robotic.

    Returns (new_timeline, new_x, new_y).
    """
    shape = rng.choice(['circle', 'triangle', 'square', 'rectangle', 'star'])
    t     = timeline + _safe_gap(rng)

    # Speed factor: how long each segment between waypoints takes (ms).
    # Drawn once per shape so the whole shape is consistently fast or slow.
    ms_per_seg = rng.uniform(80.0, 400.0)   # fast (~80ms) to leisurely (~400ms)
    jitter_px  = rng.uniform(3.0, 10.0)     # positional jitter magnitude

    def _trace_waypoints(wpts):
        """Move through a list of (x, y) waypoints with jitter and human paths."""
        nonlocal t, cur_x, cur_y
        px, py = cur_x, cur_y
        for wx, wy in wpts:
            # Jitter: slightly randomise each target point
            wx = int(max(100, min(1800, wx + rng.uniform(-jitter_px, jitter_px))))
            wy = int(max(100, min(1000, wy + rng.uniform(-jitter_px, jitter_px))))
            # Per-segment time varies +/-40% for natural rhythm
            seg = ms_per_seg * rng.uniform(0.6, 1.4)
            path = generate_human_path(px, py, wx, wy, int(seg), rng)
            for rel, ex, ey in path:
                events.append(_evt('MouseMove', t + rel, ex, ey))
            t  += seg
            px, py = wx, wy
        return px, py

    # ------------------------------------------------------------------ circle
    if shape == 'circle':
        radius = rng.randint(60, 180)
        # Keep center so shape stays fully on screen
        cx = int(max(100 + radius, min(1800 - radius, cur_x + rng.randint(-120, 120))))
        cy = int(max(100 + radius, min(1000 - radius, cur_y + rng.randint(-100, 100))))
        laps   = rng.randint(3, 5)
        steps  = rng.randint(20, 36)   # points per lap (10-18 degree increments)
        wpts   = []
        for lap in range(laps):
            for s in range(steps):
                angle = (s / steps) * 2 * math.pi
                wpts.append((
                    cx + radius * math.cos(angle),
                    cy + radius * math.sin(angle),
                ))
        last_x, last_y = _trace_waypoints(wpts)

    # --------------------------------------------------------------- triangle
    elif shape == 'triangle':
        spread = rng.randint(80, 220)
        # Generate 3 vertices roughly equilateral around current position
        vertices = []
        for k in range(3):
            angle = (k / 3) * 2 * math.pi + rng.uniform(-0.3, 0.3)
            vx = cur_x + spread * math.cos(angle)
            vy = cur_y + spread * math.sin(angle)
            vertices.append((vx, vy))
        laps = rng.randint(1, 3)
        wpts = vertices * laps + [vertices[0]]   # close the last lap
        last_x, last_y = _trace_waypoints(wpts)

    # ----------------------------------------------------------------- square
    elif shape == 'square':
        side = rng.randint(80, 200)
        x0   = int(max(100, min(1800 - side, cur_x - side // 2)))
        y0   = int(max(100, min(1000 - side, cur_y - side // 2)))
        corners = [(x0, y0), (x0 + side, y0),
                   (x0 + side, y0 + side), (x0, y0 + side)]
        laps = rng.randint(1, 3)
        wpts = corners * laps + [corners[0]]
        last_x, last_y = _trace_waypoints(wpts)

    # -------------------------------------------------------------- rectangle
    elif shape == 'rectangle':
        w  = rng.randint(120, 280)
        h  = rng.randint(60,  160)
        x0 = int(max(100, min(1800 - w, cur_x - w // 2)))
        y0 = int(max(100, min(1000 - h, cur_y - h // 2)))
        corners = [(x0, y0), (x0 + w, y0),
                   (x0 + w, y0 + h), (x0, y0 + h)]
        laps = rng.randint(1, 3)
        wpts = corners * laps + [corners[0]]
        last_x, last_y = _trace_waypoints(wpts)

    # ------------------------------------------------------------------- star
    else:   # star
        outer_r = rng.randint(80, 160)
        inner_r = int(outer_r * rng.uniform(0.35, 0.55))
        points  = 5
        laps    = rng.randint(1, 2)
        wpts    = []
        for lap in range(laps):
            for k in range(points * 2):
                # Alternate outer/inner radius
                r     = outer_r if k % 2 == 0 else inner_r
                angle = (k / (points * 2)) * 2 * math.pi - math.pi / 2
                wpts.append((
                    cur_x + r * math.cos(angle),
                    cur_y + r * math.sin(angle),
                ))
        wpts.append(wpts[0])   # close shape
        last_x, last_y = _trace_waypoints(wpts)

    return t, int(last_x), int(last_y)




def _add_backspace_hold(events, timeline, rng, cur_x, cur_y):
    """
    Hold the Backspace key for a random duration between 1 and 3 seconds
    (chosen in milliseconds, float, never rounded).
    Simulates a player accidentally holding Backspace to delete a long string
    or holding it while distracted. The cursor stays still throughout.

    Duration: rng.uniform(1000.0, 3000.0) ms — full millisecond precision.
    Returns new_timeline (cur_x and cur_y unchanged).
    """
    bk       = _VK['Back']
    hold_ms  = rng.uniform(1000.0, 3000.0)   # 1–3 s, float ms, never rounded
    t        = timeline + _safe_gap(rng)
    events.append(_evt('KeyDown', t,               keycode=bk))
    events.append(_evt('KeyUp',   t + hold_ms,     keycode=bk))
    return t + hold_ms


def generate_distraction_files(distractions_src_folder, out_folder, rng,
                                count: int = 50,
                                bundle_id: int = 0) -> int:
    """
    Generate `count` distraction files.
    Each file uses exactly 3 randomly-chosen features from {wander, pause,
    right_click, type, key_spam, shapes, backspace}.
    All events follow the exact 6-field macro schema:
      Type, Time, X, Y, Delta, KeyCode  (Delta/KeyCode None where unused)
    KeyCode values are Windows VK integers, never strings.
    No left clicks. Duration 1-3 min (float ms, rounded only at save).
    Per-feature cooldown: 17-40 s between successive triggers of the same
    feature, calculated in float ms, unique per feature per file.
    """
    from pathlib import Path as _Path
    out_folder = _Path(out_folder)
    out_folder.mkdir(parents=True, exist_ok=True)

    # 7 features - each file picks 3 at random.
    ACTION_WEIGHTS = [
        ('wander',      20),
        ('pause',       14),
        ('right_click', 20),
        ('type',        18),
        ('key_spam',    11),
        ('shapes',      19),
        ('backspace',   10),   # hold Backspace 1-3 s (Feature 33 addition v3.18.83)
    ]
    action_names = [a[0] for a in ACTION_WEIGHTS]
    action_wts   = [a[1] for a in ACTION_WEIGHTS]

    written = 0
    for i in range(count):
        file_rng = random.Random(rng.random())
        target   = file_rng.uniform(30000.0, 120000.0)

        # Pick exactly 3 features for this file
        chosen     = file_rng.sample(action_names, 3)
        chosen_wts = [w for a, w in ACTION_WEIGHTS if a in chosen]

        events   = []
        timeline = 0.0
        cur_x    = file_rng.randint(300, 700)
        cur_y    = file_rng.randint(250, 450)
        last_act = None

        # Shared cooldown: after any action fires, ALL features are locked out
        # for a single random window of 17 000-30 000 ms (float ms, never rounded).
        # A fresh cooldown is drawn each time any feature triggers, so the gap
        # between every pair of consecutive actions is independently randomised.
        next_allowed_any = 0.0   # earliest ms any action may next fire

        # OVERLAP CONTROL
        # Sequential fraction: random decimal in [90.0, 95.0] percent.
        # For that share of triggers, the next action must wait until the
        # previous one has fully finished playing (action_busy_until).
        # For the remaining (100 - sequential_pct)% of triggers, the new action
        # may start while the previous is still playing (overlap allowed).
        sequential_pct  = file_rng.uniform(90.0, 95.0)   # e.g. 92.47%
        sequential_frac = sequential_pct / 100.0          # e.g. 0.9247
        action_busy_until = 0.0   # absolute ms when last action's events end

        # Opening move
        tx       = file_rng.randint(150, 950)
        ty       = file_rng.randint(120, 620)
        open_dur = _human_interval(file_rng, 350.0, 950.0)
        path     = generate_human_path(cur_x, cur_y, tx, ty, int(open_dur), file_rng)
        for rel, px, py in path:
            events.append(_evt('MouseMove', timeline + rel, px, py))
        timeline += open_dur
        action_busy_until = timeline
        cur_x, cur_y = tx, ty

        while timeline < target:
            # Wait for the shared cooldown window to expire
            if timeline < next_allowed_any:
                timeline = next_allowed_any + _human_interval(file_rng, 10.0, 80.0)
                action_busy_until = max(action_busy_until, timeline)

            # Actions available = chosen set minus consecutive-pause block
            available = [
                a for a in chosen
                if not (a == 'pause' and last_act == 'pause')
            ]

            if not available:
                # Only happens if all 3 chosen features are 'pause' (impossible
                # with sample(3)), but guard anyway
                last_act = None
                continue

            avail_wts = [w for a, w in ACTION_WEIGHTS if a in available]
            action    = file_rng.choices(available, weights=avail_wts, k=1)[0]

            # Decide: sequential (wait for previous to finish) or overlap?
            if file_rng.random() < sequential_frac:
                start_t = max(timeline, action_busy_until) + _safe_gap(file_rng)
            else:
                start_t = timeline + _safe_gap(file_rng)

            timeline = start_t

            if action == 'wander':
                timeline, cur_x, cur_y = _add_mouse_wander(events, timeline, file_rng, cur_x, cur_y)
            elif action == 'pause':
                timeline, cur_x, cur_y = _add_cursor_pause(events, timeline, file_rng, cur_x, cur_y)
            elif action == 'right_click':
                timeline, cur_x, cur_y = _add_right_click(events, timeline, file_rng, cur_x, cur_y)
            elif action == 'type':
                timeline = _add_typing(events, timeline, file_rng, cur_x, cur_y)
            elif action == 'key_spam':
                timeline = _add_key_spam(events, timeline, file_rng, cur_x, cur_y)
            elif action == 'shapes':
                timeline, cur_x, cur_y = _add_shape_movement(events, timeline, file_rng, cur_x, cur_y)
            elif action == 'backspace':
                timeline = _add_backspace_hold(events, timeline, file_rng, cur_x, cur_y)

            action_busy_until = timeline

            # Draw a fresh shared cooldown after every trigger (float ms, never rounded)
            cooldown = file_rng.uniform(17000.0, 30000.0)
            next_allowed_any = timeline + cooldown

            last_act = action
            if timeline <= 0:
                timeline = 1.0

        if not events:
            continue

        # Normalise times and enforce no zero-gaps
        base = min(e['Time'] for e in events)
        for e in events:
            e['Time'] = max(0, int(round(e['Time'] - base)))
        events.sort(key=lambda e: e['Time'])
        for j in range(1, len(events)):
            if events[j]['Time'] <= events[j-1]['Time']:
                events[j]['Time'] = events[j-1]['Time'] + 1

        # Trim any events that spilled past target due to cooldown overshoot.
        target_ms_int = int(round(target))
        events = [e for e in events if e['Time'] <= target_ms_int]
        if not events:
            continue

        # Ensure the file's duration matches its target (within 1s tolerance).
        # Cursor idle time during cooldown gaps produces no events, so the last
        # event may land well before target. A final anchor MouseMove captures
        # "cursor held still" and gives the file the correct playback length.
        if events[-1]['Time'] < target_ms_int - 1000:
            last_x = next((e['X'] for e in reversed(events) if e.get('X') is not None), cur_x)
            last_y = next((e['Y'] for e in reversed(events) if e.get('Y') is not None), cur_y)
            events.append({
                'Type': 'MouseMove', 'Time': target_ms_int,
                'X': int(last_x), 'Y': int(last_y),
                'Delta': None, 'KeyCode': None,
            })

        total_ms  = events[-1]['Time']
        total_min = total_ms // 60000
        total_sec = (total_ms % 60000) // 1000
        fname     = f"DISTRACTION_{str(i+1).zfill(2)}_{total_min}m{total_sec}s.json"
        (out_folder / fname).write_text(json.dumps(events, separators=(',', ':')))
        written += 1

    return written

def apply_cycle_features(cycle_events, rng, is_raw, is_inef=False,
                          is_click_sensitive=False, mult=1.0):
    """
    Apply anti-detection features to a complete cycle.

    Args:
        cycle_events: Events from one complete cycle
        rng: Random generator
        is_raw:  If True, 0% within-file pause (no pauses inserted)
        is_inef: If True, 15% within-file pause; False = 5% (normal)
        is_click_sensitive: If True, skip jitter and idle mouse movements
                            (no coordinate-changing features applied)

    Returns:
        (processed_events, stats)
    """
    stats = {
        'jitter_count': 0,
        'total_moves': 0,
        'jitter_percentage': 0.0,
        'intra_pauses': 0,
        'idle_movements': 0,
        'pause_pivots': [],  # [(raw_pivot_time, amount)] for manifest correction
    }

    # Step 1: Jitter - SKIPPED for click-sensitive folders
    if not is_click_sensitive:
        events_with_jitter, jitter_count, move_count, jitter_pct = add_pre_click_jitter(cycle_events, rng)
        stats['jitter_count'] = jitter_count
        stats['total_moves'] = move_count
        stats['jitter_percentage'] = jitter_pct
    else:
        events_with_jitter = cycle_events

    # Step 2: Rapid click detection
    protected_ranges = detect_rapid_click_sequences(events_with_jitter)

    # pause_pivots: list of (raw_pivot_time, amount) for manifest end-time correction.
    # Only time-shifting features (intra pause, mid-event pause) contribute entries.
    # Jitter and idle only INSERT events — they never shift existing event times.
    _pause_pivots = []

    # Step 3: Within-file pause (percentage-based, range chosen per call)
    #   Raw: 0%   Normal: 2-5%   Inefficient: 10-15%
    #   Click-sensitive (incl. (random)): forced to 0% — treat as raw
    if is_click_sensitive:
        file_type = 'raw'
    else:
        file_type = 'raw' if is_raw else ('inef' if is_inef else 'normal')
    events_with_pauses, pause_time, _intra_pivot_t = insert_intra_file_pauses(
        events_with_jitter, rng, protected_ranges, file_type=file_type
    )
    stats['intra_pauses'] = pause_time
    if pause_time > 0:
        _pause_pivots.append((_intra_pivot_t, float(pause_time)))

    # Step 3b: Multiplier-driven random mid-event pause (50% chance per cycle)
    # The multiplier can express itself as a short natural hesitation inserted
    # directly between recorded events rather than only making buffers longer.
    # Duration: rng.uniform(200, 800) * mult ms. Skipped for raw + click-sensitive.
    _drag_idx_cache = None  # initialized here so Step 4 can reuse it if built
    if not is_raw and not is_click_sensitive and rng.random() < 0.50:
        _mid_ms = min(rng.uniform(200.0, 800.0) * mult, _MAX_SINGLE_PAUSE_MS)
        # Reuse drag index if already built; avoid building twice per cycle
        _drag_idx_cache = build_drag_index_set(events_with_pauses)
        _drag_idx = _drag_idx_cache
        _p_set = set()
        for _s, _e in protected_ranges:
            for _k in range(_s, _e + 1):
                _p_set.add(_k)
        _fs = max(1, int(len(events_with_pauses) * 0.10))
        _ls = min(len(events_with_pauses) - 1, int(len(events_with_pauses) * 0.90))
        _PRESS_TYPES_MID = {'DragStart', 'LeftDown', 'LeftUp', 'RightDown', 'RightUp', 'Click'}
        _valid = [
            _i for _i in range(_fs, _ls)
            if _i not in _p_set and _i not in _drag_idx
            and events_with_pauses[_i].get('Type') not in _PRESS_TYPES_MID
            and (_i + 1 >= len(events_with_pauses)
                 or events_with_pauses[_i + 1].get('Type') not in _PRESS_TYPES_MID)
        ]
        if _valid:
            _ins = rng.choice(_valid)
            # Capture mid-event pivot in raw (pre-all-shifts) space.
            # events_with_pauses[_ins].Time is in post-intra-pause space.
            # Un-shift to raw space if the intra pause already moved this point.
            _mid_t_shifted = float(events_with_pauses[_ins].get('Time', 0))
            _mid_pivot_raw = (
                _mid_t_shifted - pause_time
                if (pause_time > 0 and _mid_t_shifted >= _intra_pivot_t + pause_time)
                else _mid_t_shifted
            )
            for _j in range(_ins, len(events_with_pauses)):
                events_with_pauses[_j]['Time'] = events_with_pauses[_j].get('Time', 0) + _mid_ms
            stats['intra_pauses'] += _mid_ms
            _pause_pivots.append((_mid_pivot_raw, float(_mid_ms)))

    # Step 4: Idle movements - SKIPPED for click-sensitive folders
    if not is_click_sensitive:
        movement_pct = rng.uniform(0.40, 0.50)
        events_with_idle, idle_time = insert_idle_mouse_movements(
            events_with_pauses, rng, movement_pct,
            prebuilt_drag_index=_drag_idx_cache
        )
        stats['idle_movements'] = idle_time
    else:
        events_with_idle = events_with_pauses

    # Expose pause pivot data for manifest end-time accuracy correction
    stats['pause_pivots'] = _pause_pivots

    return events_with_idle, stats



# ============================================================================
# FOLDER SCANNING
# ============================================================================

def scan_choose1_hub_children(hub_path):
    """
    Enumerate the children of a (choose1) hub folder, regardless of naming
    convention. Each child becomes one entry in the returned dict, keyed by
    a synthetic index (NOT parsed from the folder name) so children can be
    named anything (workflow_01, cut_long, default, ...).

    If a child is itself tagged (random), its own sub-subfolders are
    expected to follow the normal numbered-folder convention, and are
    scanned with scan_for_numbered_subfolders so the existing (random)
    selection logic in the scenario selector keeps working unchanged.

    Returns: (children_dict, non_json_files)
    """
    hub = Path(hub_path)
    children = {}
    non_json_files = []

    child_dirs = []
    for d in sorted(hub.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir():
            continue
        d_lower = d.name.lower()
        if d_lower == 'session_end, wait, in' or d.name.startswith('@'):
            continue
        if d_lower in ("don't use features on me", "dont mess with me"):
            continue
        child_dirs.append(d)

    for idx, child in enumerate(child_dirs):
        child_lower = child.name.lower()

        json_files = sorted(child.glob("*.json"))
        always_first = []
        always_last = []
        regular_files = []
        for jf in json_files:
            name_lower = jf.name.lower()
            if 'always first' in name_lower or 'alwaysfirst' in name_lower:
                always_first.append(jf)
            elif 'always last' in name_lower or 'alwayslast' in name_lower:
                always_last.append(jf)
            else:
                regular_files.append(jf)

        random_match = re.search(r'\(random(\d*)\)', child.name, re.IGNORECASE)
        is_random = bool(random_match)
        random_max = int(random_match.group(1)) if (is_random and random_match.group(1)) else None

        is_optional = 'optional' in child_lower
        optional_chance = parse_optional_chance(child.name) if is_optional else None
        is_end = bool(re.search(r'\bend\b', child.name, re.IGNORECASE))
        is_optional_end = is_optional and is_end

        is_time_sensitive = 'time sensitive' in child_lower
        is_click_time = ('click/time sensitive' in child_lower or
                         'click+time sensitive' in child_lower or
                         'click time sensitive' in child_lower)
        is_click = 'click sensitive' in child_lower
        if is_click_time:
            is_time_sensitive = True
            is_click = True

        nested_subfolder_files = None
        if is_random:
            # Random children keep using the normal numbered convention
            # for their own sub-subfolders (the "slots" to combine).
            nf, nnj, naf, nal = scan_for_numbered_subfolders(child)
            non_json_files.extend(nnj)
            if nf:
                nested_subfolder_files = nf

        for f in child.iterdir():
            if f.is_file() and not f.name.endswith('.json'):
                non_json_files.append(f)

        children[idx] = {
            'files': regular_files,
            'is_optional': is_optional,
            'optional_chance': optional_chance,
            'is_end': is_end,
            'is_optional_end': is_optional_end,
            'is_time_sensitive': is_time_sensitive,
            'is_click_sensitive': is_click,
            'max_files': parse_max_files(child.name),
            'always_first': always_first,
            'always_last': always_last,
            'nested_subfolder_files': nested_subfolder_files,
            'nested_root_always_first': None,
            'nested_root_always_last': None,
            'is_random': is_random,
            'random_max': random_max,
            'is_choose1': False,
            'folder_name': child.name,
            'folder_path': child,
        }

    return children, non_json_files


def scan_for_numbered_subfolders(base_path):
    """
    Scans folder for subfolders with numbers in their names.
    Also checks for "dont mess with me" subfolder and "optional" folders.
    
    NEW: Checks main folder name for "time sensitive" tag.
    If main folder is tagged, ALL subfolders become time_sensitive!
    
    Accepts: "1", "part1", "step2", "3-action", "3 optional- walk", "3.5- insert", etc.
    DECIMAL SUPPORT: "3.5" will be placed after "3" and before "4"
    
    Returns tuple: (numbered_folders_dict, non_json_files_list, root_always_first, root_always_last)
    """
    base = Path(base_path)
    numbered_folders = {}
    non_json_files = []
    
    # Check if MAIN FOLDER is tagged - propagates to ALL subfolders
    _base_lower = base.name.lower()
    main_folder_time_sensitive  = 'time sensitive'  in _base_lower
    main_folder_click_sensitive = (
        'click sensitive'      in _base_lower or   # plain: "click sensitive"
        'click/time sensitive' in _base_lower or   # slash: "click/time sensitive"
        'click+time sensitive' in _base_lower or   # plus:  "click+time sensitive"
        'click time sensitive' in _base_lower      # space: "click time sensitive"
    )

    if main_folder_time_sensitive:
        print(f"  ??  MAIN FOLDER is TIME SENSITIVE - All subfolders will skip inefficient files!")
    if main_folder_click_sensitive:
        print(f"  ?  MAIN FOLDER is CLICK SENSITIVE - All subfolders will skip cursor/jitter/idle/distraction features!")
    
    for item in base.iterdir():
        if not item.is_dir():
            # Collect non-JSON files in root
            if not item.name.endswith('.json'):
                non_json_files.append(item)
            continue
        
        # Check for "Don't use features on me" folder (case-insensitive)
        # Also accepts old name "dont mess with me" for backward compatibility
        folder_name_lower = item.name.lower()
        # Skip skill-specific logout folder — handled separately by build_logout_sequence
        if folder_name_lower == 'logout, wait, in' or item.name.startswith('@'):
            continue

        if folder_name_lower == "don't use features on me" or folder_name_lower == "dont mess with me":
            # Add all JSON files from this folder as unmodified
            dmwm_files = sorted(item.glob("*.json"))
            # These files are placed into numbered_folders[0] later
            # We just collect them for now; no separate variable needed
            print(f"  [!]?  Found 'Don't use features on me' folder: {len(dmwm_files)} unmodified files")
            continue
        
        # Extract folder number - prefer explicit F<N> prefix (F1, F2, F3.5, etc.)
        # so that other numbers in the name (e.g. 'press 1', 'optional-2-') are ignored.
        _f_match = re.match(r'^[Ff](\d+(?:\.\d+)?)', item.name.strip())
        if _f_match:
            folder_num = float(_f_match.group(1))   # e.g. F3.5 -> 3.5
        else:
            # Fall back: first number anywhere (handles '1- mine', '3.5 optional- ...')
            _n_match = re.search(r'\d+\.?\d*', item.name)
            folder_num = float(_n_match.group()) if _n_match else None
        if folder_num is not None:
            all_json_files = sorted(item.glob("*.json"))
            
            # Separate "always first", "always last", and regular files
            # Collect ALL always_first/last variants into pools — one is chosen randomly per run
            always_first_pool = []
            always_last_pool  = []
            regular_files = []

            for json_file in all_json_files:
                filename_lower = json_file.name.lower()
                if 'always first' in filename_lower or 'alwaysfirst' in filename_lower:
                    always_first_pool.append(json_file)
                    print(f"   Found 'always first' in folder {folder_num}: {json_file.name}")
                elif 'always last' in filename_lower or 'alwayslast' in filename_lower:
                    always_last_pool.append(json_file)
                    print(f"   Found 'always last' in folder {folder_num}: {json_file.name}")
                else:
                    regular_files.append(json_file)
            always_first = always_first_pool  # store list; caller picks one randomly
            always_last  = always_last_pool
            
            # Check if folder is "optional" (default 24-33%, or custom % from tag)
            is_optional = 'optional' in item.name.lower()
            optional_chance = parse_optional_chance(item.name) if is_optional else None
            
            # Check if folder is "end" (becomes definitive end point)
            is_end = bool(re.search(r'\bend\b', item.name, re.IGNORECASE))
            
            # Check if folder is "time sensitive" (1:1 raw:normal, no inef, minimal overhead)
            # Priority: Main folder tag > Individual subfolder tag
            if main_folder_time_sensitive:
                is_time_sensitive = True  # Main folder overrides all
            else:
                is_time_sensitive = 'time sensitive' in item.name.lower()

            # Check if folder is "click sensitive" (no cursor pathing between files)
            item_lower = item.name.lower()
            is_click_time_sensitive = ('click/time sensitive' in item_lower
                                       or 'click+time sensitive' in item_lower
                                       or 'click time sensitive' in item_lower)
            is_click_sensitive      = (('click sensitive' in item_lower)
                                       and not is_click_time_sensitive)
            # click/time sensitive implies both flags
            if is_click_time_sensitive:
                is_time_sensitive    = True
                is_click_sensitive   = True
            # Main folder tag propagates to all subfolders
            if main_folder_click_sensitive:
                is_click_sensitive = True

            # "optional+end" combo: optional folder that ends loop if chosen
            is_optional_end = is_optional and is_end

            # Check if folder is "(random)" or "(randomN)":
            # (random)  -> pick 1 file from ALL sub-subfolders in random order.
            # (random10) -> pick 1 file from 10 randomly chosen sub-subfolders.
            # Sub-subfolders are detected by leading digit OR bracketed number e.g. (1).
            _random_match = re.search(r'\(random(\d*)\)', item.name, re.IGNORECASE)
            is_random = bool(_random_match)
            random_max = int(_random_match.group(1)) if (is_random and _random_match.group(1)) else None
            # (random) folders are implicitly click-sensitive: no pauses, jitter,
            # idle movements or other timing features — only cursor movement between files.
            if is_random:
                is_click_sensitive = True

            # Check if folder is "(choose1)" hub folder:
            # Hub folder contains child folders (each with their own files).
            # Each cycle: choose ONE child folder at random, then pick ONE file from it.
            # This gives each child folder equal probability regardless of file count,
            # unlike same-number pooling which weights by file count.
            # Coexists with same-number pooling: flat child folders still pool normally
            # if they share an F-number; hub folder itself is a distinct F-slot.
            is_choose1 = bool(re.search(r'\(choose1\)', item.name, re.IGNORECASE))

            # Detect nested numbered subfolders (e.g. F5 that has its own F1/F2/F3 inside)
            # Accepts: leading digit/F-prefix OR bracketed number anywhere in name e.g. '(1)'
            nested_subfolder_files = None
            nested_root_af = None
            nested_root_al = None

            if is_choose1:
                # Hub folders enumerate ALL child directories
                hub_children, hub_nnj = scan_choose1_hub_children(item)
                non_json_files.extend(hub_nnj)
                if hub_children:
                    nested_subfolder_files = hub_children
            elif not regular_files:
                # No direct JSON files — check if there are numbered sub-subfolders
                _nested_subdirs = [
                    d for d in item.iterdir()
                    if d.is_dir() and (
                        re.search(r'^[Ff]?\d', d.name.strip())  # leading digit/F-prefix
                        or re.search(r'\(\d+\)', d.name)       # bracketed number e.g. (1)
                    )
                ]
                if _nested_subdirs:
                    # Recursively scan the nested folder
                    _nf, _nnj, _naf, _nal = scan_for_numbered_subfolders(item)
                    non_json_files.extend(_nnj)
                    if _nf:
                        nested_subfolder_files = _nf
                        nested_root_af = _naf
                        nested_root_al = _nal
                        if is_random:
                            _rlabel = f'random{random_max}' if random_max else 'random'
                            print(f"  Nested folder detected: {item.name} has {len(_nf)} "
                                  f"sub-folders [({_rlabel}) — pick {'up to '+str(random_max) if random_max else 'all'}, shuffled]")
                        elif is_choose1:
                            print(f"  Nested folder detected: {item.name} has {len(_nf)} "
                                  f"sub-folders [(choose1) — pick 1 folder at random, then 1 file from it]")
                        else:
                            print(f"  Nested folder detected: {item.name} has {len(_nf)} sub-folders inside")

            if regular_files or nested_subfolder_files:
                # SAME-NUMBER POOLING (Feature 41):
                # Multiple physical subfolders can share the same F-number
                # (e.g. "F2- Click anvil", "F2- Click anvil - Copy", "F2- dance").
                # They are merged into a single logical slot: files are pooled,
                # always_first/last pools are combined, and boolean tags are OR-ed.
                # Scalar tags (optional_chance, max_files) use the first non-None value
                # encountered across all merged folders with that number.
                _new_entry = {
                    'files': regular_files,
                    'is_optional': is_optional,
                    'optional_chance': optional_chance,
                    'is_end': is_end,
                    'is_optional_end': is_optional_end,
                    'is_time_sensitive': is_time_sensitive,
                    'is_click_sensitive': is_click_sensitive,
                    'max_files': parse_max_files(item.name),
                    'always_first': always_first,
                    'always_last': always_last,
                    'nested_subfolder_files': nested_subfolder_files,
                    'nested_root_always_first': nested_root_af,
                    'nested_root_always_last': nested_root_al,
                    'is_random': is_random,
                    'random_max': random_max,
                    'is_choose1': is_choose1,
                    'folder_name': item.name,   # stored for name-lookup in specific-folders
                    'folder_path': item,
                }
                if folder_num not in numbered_folders:
                    # First folder with this number — store as-is
                    numbered_folders[folder_num] = _new_entry
                else:
                    # Additional folder with the same number — merge into existing slot
                    _ex = numbered_folders[folder_num]
                    _ex['files']        = _ex['files'] + regular_files
                    _ex['always_first'] = _ex['always_first'] + always_first
                    _ex['always_last']  = _ex['always_last']  + always_last
                    # Boolean tags: OR (if any contributing folder has the tag, slot gets it)
                    _ex['is_optional']      = _ex['is_optional']      or is_optional
                    _ex['is_end']           = _ex['is_end']           or is_end
                    _ex['is_optional_end']  = _ex['is_optional_end']  or is_optional_end
                    _ex['is_time_sensitive'] = _ex['is_time_sensitive'] or is_time_sensitive
                    _ex['is_click_sensitive'] = _ex['is_click_sensitive'] or is_click_sensitive
                    # Scalar tags: keep first non-None value
                    if _ex['optional_chance'] is None and optional_chance is not None:
                        _ex['optional_chance'] = optional_chance
                    if _ex['max_files'] is None and _new_entry['max_files'] is not None:
                        _ex['max_files'] = _new_entry['max_files']
                    # Nested subfolder files: merge the dicts if both have nested content,
                    # otherwise use whichever is non-None
                    if nested_subfolder_files:
                        if _ex['nested_subfolder_files'] is None:
                            _ex['nested_subfolder_files']  = nested_subfolder_files
                            _ex['nested_root_always_first'] = nested_root_af
                            _ex['nested_root_always_last']  = nested_root_al
                        else:
                            # Both have nested: merge their inner subfolder dicts
                            for _inner_num, _inner_data in nested_subfolder_files.items():
                                if _inner_num not in _ex['nested_subfolder_files']:
                                    _ex['nested_subfolder_files'][_inner_num] = _inner_data
                                else:
                                    _in = _ex['nested_subfolder_files'][_inner_num]
                                    _in['files'] = _in['files'] + _inner_data.get('files', [])
                                    _in['always_first'] = _in['always_first'] + _inner_data.get('always_first', [])
                                    _in['always_last']  = _in['always_last']  + _inner_data.get('always_last', [])
                            _ex['nested_root_always_first'] = (_ex.get('nested_root_always_first') or []) + (nested_root_af or [])
                            _ex['nested_root_always_last']  = (_ex.get('nested_root_always_last')  or []) + (nested_root_al or [])
                    print(f"   [Pool] F{int(folder_num) if folder_num == int(folder_num) else folder_num}: "
                          f"merged '{item.name}' into slot "
                          f"({len(_ex['files'])} files total)")

            # Also collect non-JSON files from numbered folders
            for file in item.iterdir():
                if file.is_file() and not file.name.endswith('.' + 'json'):
                    non_json_files.append(file)
    
    # FLAT FOLDER SUPPORT:
    # If no numbered subfolders were found, check if there are JSON files
    # sitting directly in the folder itself. If so, treat the folder as a
    # single virtual subfolder (number 1.0) so everything downstream works
    # without any changes.
    if not numbered_folders:
        direct_json = sorted(base.glob('*.json'))
        
        # Exclude logout files from the pool
        logout_names = {'logout.json', '- logout.json', '-logout.json'}
        direct_json = [f for f in direct_json if f.name.lower() not in logout_names]
        
        if direct_json:
            # Separate always_first / always_last from regular files
            always_first_pool = []
            always_last_pool  = []
            regular_files = []
            for json_file in direct_json:
                name_lower = json_file.name.lower()
                if 'always first' in name_lower or 'alwaysfirst' in name_lower:
                    always_first_pool.append(json_file)
                    print(f"   Found 'always first': {json_file.name}")
                elif 'always last' in name_lower or 'alwayslast' in name_lower:
                    always_last_pool.append(json_file)
                    print(f"   Found 'always last': {json_file.name}")
                else:
                    regular_files.append(json_file)
            always_first = always_first_pool
            always_last  = always_last_pool
            
            if regular_files:
                print(f"   Flat folder detected - {len(regular_files)} file(s) treated as single pool (subfolder 1.0)")
                numbered_folders[1.0] = {
                    'files': regular_files,
                    'is_optional': False,
                    'optional_chance': None,
                    'is_end': False,
                    'is_optional_end': False,
                    'is_time_sensitive': main_folder_time_sensitive,
                    'is_click_sensitive': main_folder_click_sensitive,
                    'always_first': always_first,
                    'always_last': always_last
                }

    # Scan root-level JSON files for always_first / always_last even when
    # numbered subfolders exist. These wrap the ENTIRE strung file once —
    # not per cycle, not per subfolder. Separate from subfolder-level always tags.
    root_always_first = []
    root_always_last  = []
    # Gate: skip root scan if this is a flat-folder (synthetic key 1.0 only).
    # Flat folders store always_last in subfolder 1.0's pool; running the root
    # scan too would put the same files into root_always_last, causing a double play.
    _is_flat_scan = (
        set(numbered_folders.keys()) == {1.0}
        and not any(
            re.match(r'(?i)^[Ff]?\d', d.name)
            for d in base.iterdir() if d.is_dir()
        )
    ) if numbered_folders else False
    if numbered_folders and not _is_flat_scan:
        for _rf in sorted(base.glob('*.json')):
            _name = _rf.name.lower()
            if 'always first' in _name or 'alwaysfirst' in _name:
                root_always_first.append(_rf)
                print(f"  Found root-level 'always first': {_rf.name}")
            elif 'always last' in _name or 'alwayslast' in _name:
                root_always_last.append(_rf)
                print(f"  Found root-level 'always last': {_rf.name}")

    return numbered_folders, non_json_files, root_always_first, root_always_last

# ============================================================================
# SIMPLE PERSISTENT HISTORY (Like Bundle Counter!)
# ============================================================================


class ManualHistoryTracker:
    """
    Manual combination history - YOU upload combination files!
    
    Folder: input_macros/combination_history/
    
    Code reads ALL .txt files in that folder and ensures no duplicate combinations.
    You manually dump combination files from each bundle's output to this folder.
    
    Files can be named anything, code reads them all:
    - COMBINATION_HISTORY_39.txt
    - combos_from_bundle_40.txt
    - anything.txt
    
    All will be read and combined into one set of used combinations.
    """
    def __init__(self, subfolder_files, rng, folder_name, input_dir):
        self.subfolder_files = subfolder_files
        self.rng = rng
        self.folder_name = folder_name
        self.input_dir = input_dir
        
        # History folder (not a single file!)
        self.history_dir = input_dir / "combination_history"
        
        # Load ALL combinations from ALL files in the folder
        self.used_combinations = self._load_all_combinations()
        self._sequence_reused = False  # Set True when the 500-attempt fallback fires

        # Compute total possible unique combinations (product of pool sizes).
        # Use recursive pool size calculation that handles hubs and nested folders.
        pool_sizes = [self._pool_size(fd) for fd in subfolder_files.values()]
        _total_possible = 1
        for _ps in pool_sizes:
            _total_possible *= max(1, _ps)
        self._total_possible_combos = _total_possible

        # Detect single-slot folders (flat folders, no F-subfolders).
        # For these, per-cycle used_combinations tracking is meaningless:
        #   - Only 1 slot → signature = just one filename
        #   - Space = pool_size (e.g. 118), exhausted in one run
        #   - The actual version sequence is P(118,6)=2.37 trillion unique;
        #     files repeat naturally after one full rotation — that's fine.
        # _next_file queue (Fisher-Yates per refill) handles non-repeat correctly.
        # SEQUENCE REUSED should only fire for multi-slot F1×F2×F3 combos.
        self._is_single_slot = (
            len(subfolder_files) == 1
            and not any(
                fd.get('nested_subfolder_files')
                for fd in subfolder_files.values()
            )
        )

        # FIX A (v3.19.07 kept): if history already covers ALL possible
        # combinations AND this is a multi-slot folder, reset.
        # For single-slot folders, used_combinations is bypassed entirely.
        if (not self._is_single_slot
                and len(self.used_combinations) >= _total_possible
                and _total_possible > 0):
            print(f"   [combo reset] All {_total_possible} combination(s) used; "
                  f"resetting history for fresh rotation.")
            self.used_combinations.clear()

        # Per-subfolder virtual queues: each subfolder gets its own shuffled
        # queue so no file repeats until all files in that subfolder are used.
        self._file_queues = {}   # {folder_num: [shuffled file paths]}
        for fn, fd in self.subfolder_files.items():
            pool = list(fd.get('files', []))
            self.rng.shuffle(pool)
            self._file_queues[fn] = pool

        # Nested trackers: for subfolders that contain their own sub-subfolders,
        # maintain a separate ManualHistoryTracker for each.
        # Skip for (choose1) and (random) folders because they are handled
        # directly by the scenario selector, not by a nested tracker.
        self._nested_trackers = {}
        for fn, fd in self.subfolder_files.items():
            nsf = fd.get('nested_subfolder_files')
            if nsf and not fd.get('is_choose1') and not fd.get('is_random'):
                self._nested_trackers[fn] = ManualHistoryTracker(
                    nsf, self.rng, f"{self.folder_name}_nested_{fn}", self.input_dir
                )
        
        print(f"   {len(self.used_combinations)} combinations loaded from history")
        print(f"   History folder: {self.history_dir}")

    def _pool_size(self, folder_data):
        """
        Estimate the number of distinct file choices a folder/hub can produce.
        """
        files = folder_data.get('files') or []
        nsf = folder_data.get('nested_subfolder_files')

        if not nsf:
            return len(files)

        child_sizes = [max(1, self._pool_size(child)) for child in nsf.values()]

        if folder_data.get('is_choose1'):
            # Pick exactly one child -> combos add up
            return sum(child_sizes)

        if folder_data.get('is_random'):
            rmax = folder_data.get('random_max')
            if rmax and rmax < len(child_sizes):
                # Approximation: bound the product using largest pools
                child_sizes = sorted(child_sizes, reverse=True)[:rmax]
            total = 1
            for s in child_sizes:
                total *= s
            return total

        # Plain nested steps -> combos multiply
        total = 1
        for s in child_sizes:
            total *= s
        return total
    
    def _load_all_combinations(self):
        """Read ALL .txt files in history folder and build set of used combos"""
        all_used = set()
        
        if not self.history_dir.exists():
            print(f"   No history folder found (will skip tracking)")
            return all_used
        
        # Read ALL .txt files
        txt_files = list(self.history_dir.glob("*.txt"))
        if not txt_files:
            print(f"   History folder empty (no .txt files)")
            return all_used
        
        print(f"   Reading {len(txt_files)} history file(s)...")
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        
                        # Skip empty lines and headers
                        if not line or line.startswith('[') or line.startswith('='):
                            continue
                        
                        # Check if line is a combination (has F1=, F2=, etc.)
                        if 'F' in line and '=' in line and '|' in line:
                            # Extract just the folder name part if it's in [Folder: ...] format
                            if line.startswith('[') and ']' in line:
                                continue  # Skip section headers
                            
                            # This is a combination line
                            # Check if it matches current folder
                            # Format could be: F1=F1 (22).json|F2=F2 (39).json|F3=F3 (1).json
                            all_used.add(line)
                
                print(f"    [OK] {txt_file.name}: Loaded")
                
            except Exception as e:
                print(f"    [!]?  {txt_file.name}: Error - {e}")
        
        return all_used
    
    def _next_file(self, folder_num):
        """Return the next file from this subfolder's virtual queue.
        Refills and reshuffles when exhausted - no file repeats until all used.
        Boundary guard prevents the last file of one pass from being the first
        of the next pass (cross-boundary consecutive repeat)."""
        q = self._file_queues.get(folder_num)
        if not q:
            pool = list(self.subfolder_files.get(folder_num, {}).get('files', []))
            if not pool:
                return None
            self.rng.shuffle(pool)
            # Boundary guard: if the last item would repeat the previous pick,
            # swap it with a random other position
            last_key = f"_last_{folder_num}"
            last = getattr(self, last_key, None)
            if last is not None and len(pool) > 1 and pool[-1] == last:
                swap = self.rng.randint(0, len(pool) - 2)
                pool[-1], pool[swap] = pool[swap], pool[-1]
            self._file_queues[folder_num] = pool
            q = self._file_queues[folder_num]
        item = q.pop()
        setattr(self, f"_last_{folder_num}", item)
        return item

    def get_next_combination(self):
        """Get next unused combination (with end folder support)"""
        # Determine if ALL slots are purely nested (no direct files).
        # When every outer slot is a nested folder, the outer tracker's own
        # used_combinations check becomes harmful: the 500-attempt retry loop
        # calls each inner tracker's get_next_combination() on every attempt,
        # consuming inner queue slots even when the outer sig is rejected.
        # For a doubly-nested folder (e.g. FM+COOK where F1=FM, F2=Cook),
        # this exhausts inner trackers (e.g. FM's F6-Wait with 38 files) far
        # faster than expected, causing F6 to silently disappear from cycles.
        # Fix: if all slots are nested, skip the outer used_combinations guard
        # entirely — uniqueness is already enforced by the inner trackers.
        _all_nested = all(
            fd.get('nested_subfolder_files') and not fd.get('files')
            for fd in self.subfolder_files.values()
        )

        max_attempts = 500 if not _all_nested else 1

        for _attempt in range(max_attempts):
            # Pick random combination
            combination = []

            for folder_num in sorted(self.subfolder_files.keys()):
                folder_data = self.subfolder_files[folder_num]
                
                # Check for "optional+end" combo (optional folder that ends loop if chosen)
                if folder_data.get('is_optional_end', False):
                    optional_chance = folder_data.get('optional_chance', 0.50)
                    if self.rng.random() < optional_chance:
                        _f = self._next_file(folder_num)
                        if _f: combination.append((folder_num, [_f]))
                        break
                    else:
                        continue
                
                # Check for regular "end" folder (always included, always ends loop)
                if folder_data.get('is_end', False) and not folder_data.get('is_optional', False):
                    _f = self._next_file(folder_num)
                    if _f: combination.append((folder_num, [_f]))
                    break
                
                # Regular optional folder check
                if folder_data.get('is_optional', False):
                    optional_chance = folder_data.get('optional_chance', 0.50)
                    if self.rng.random() >= optional_chance:
                        continue
                
                # Nested folder: delegate to the inner tracker
                _nsf = folder_data.get('nested_subfolder_files')
                _max = folder_data.get('max_files', 1) or 1   # FIX: convert None to 1
                _n = self.rng.randint(1, _max) if _max > 1 else 1
                if _nsf:
                    # Use tracker only if it exists (i.e., not choose1/random)
                    tracker = self._nested_trackers.get(folder_num)
                    _picked_nested = []
                    if folder_data.get('is_choose1'):
                        # (choose1) hub: pick ONE child folder at random (equal prob
                        # per folder regardless of file count), then:
                        # - If chosen child is tagged (random)/(randomN): run full
                        #   random multi-pick on its sub-subfolders (all shuffled,
                        #   1 file each, up to random_max if set).
                        # - Otherwise: pick 1 file from the chosen folder.
                        _sub_nums = sorted(_nsf.keys())
                        if _sub_nums:
                            _chosen_sn = self.rng.choice(_sub_nums)
                            _sf_data = _nsf[_chosen_sn]
                            if _sf_data.get('is_random'):
                                # Chosen child is (random)/(randomN) — run its full logic
                                _child_nsf = _sf_data.get('nested_subfolder_files', {})
                                if _child_nsf:
                                    _child_nums = sorted(_child_nsf.keys())
                                    self.rng.shuffle(_child_nums)
                                    _rmax = _sf_data.get('random_max')
                                    if _rmax and _rmax < len(_child_nums):
                                        _child_nums = _child_nums[:_rmax]
                                    for _csn in _child_nums:
                                        _csf_files = _child_nsf[_csn].get('files', [])
                                        if _csf_files:
                                            _f = self.rng.choice(_csf_files)
                                            _picked_nested.append({
                                                '_nested': True,
                                                '_random_single': True,
                                                '_parent_folder_num': folder_num,
                                                'combo': [(_csn, [_f])],
                                                'nested_sf': _child_nsf,
                                                'nested_root_af': folder_data.get('nested_root_always_first'),
                                                'nested_root_al': folder_data.get('nested_root_always_last'),
                                            })
                            else:
                                # Normal child — pick 1 file
                                _sf_files = _sf_data.get('files', [])
                                if _sf_files:
                                    _f = self.rng.choice(_sf_files)
                                    _picked_nested.append({
                                        '_nested': True,
                                        '_random_single': True,
                                        '_parent_folder_num': folder_num,
                                        'combo': [(_chosen_sn, [_f])],
                                        'nested_sf': _nsf,
                                        'nested_root_af': folder_data.get('nested_root_always_first'),
                                        'nested_root_al': folder_data.get('nested_root_always_last'),
                                    })
                    elif folder_data.get('is_random'):
                        # (random) / (randomN) tag:
                        # Shuffle all sub-subfolder keys, then pick up to random_max
                        # (or all if random_max is None). Pick 1 file from each chosen.
                        _sub_nums = sorted(_nsf.keys())
                        self.rng.shuffle(_sub_nums)
                        _rmax = folder_data.get('random_max')  # None = all
                        if _rmax and _rmax < len(_sub_nums):
                            _sub_nums = _sub_nums[:_rmax]
                        for _sn in _sub_nums:
                            _sf_data = _nsf[_sn]
                            _sf_files = _sf_data.get('files', [])
                            if _sf_files:
                                _f = self.rng.choice(_sf_files)
                                _picked_nested.append({
                                    '_nested': True,
                                    '_random_single': True,
                                    '_parent_folder_num': folder_num,  # manifest uses parent F-number
                                    'combo': [(_sn, [_f])],
                                    'nested_sf': _nsf,
                                    'nested_root_af': folder_data.get('nested_root_always_first'),
                                    'nested_root_al': folder_data.get('nested_root_always_last'),
                                })
                    else:
                        # Plain nested folder: use tracker if it exists
                        if tracker is not None:
                            for _ in range(_n):
                                _sub_combo = tracker.get_next_combination()
                                if _sub_combo:
                                    _picked_nested.append({
                                        '_nested': True,
                                        'combo': _sub_combo,
                                        'nested_sf': _nsf,
                                        'nested_root_af': folder_data.get('nested_root_always_first'),
                                        'nested_root_al': folder_data.get('nested_root_always_last'),
                                    })
                    if _picked_nested:
                        combination.append((folder_num, _picked_nested))
                else:
                    # Regular folder: pick files from virtual queue
                    _picked = []
                    for _ in range(_n):
                        _f = self._next_file(folder_num)
                        if _f:
                            _picked.append(_f)
                    if _picked:
                        combination.append((folder_num, _picked))
            
            if not combination:
                continue
            
            if _all_nested:
                # All slots are nested — inner trackers enforce uniqueness.
                # Return immediately without outer used_combinations check.
                return combination

            # Create signature (format folder numbers cleanly)
            signature = "|".join(
                f"F{int(fn) if fn == int(fn) else fn}=" +
                "+".join(_combo_fp_sig(fp, i) for i, fp in enumerate(fl if isinstance(fl, list) else [fl]))
                for fn, fl in combination
            )
            
            # Single-slot (flat) folders: skip used_combinations entirely.
            # The _next_file queue handles non-repeat; sequence space is vast.
            if self._is_single_slot:
                return combination

            # Multi-slot: reset if all possible combinations exhausted mid-run.
            if (self._total_possible_combos > 0
                    and len(self.used_combinations) >= self._total_possible_combos):
                self.used_combinations.clear()

            # Check if unused
            if signature not in self.used_combinations:
                self.used_combinations.add(signature)
                return combination
        
        # Fallback: return random (may repeat)
        print(f"  [!]?  Using random combination (may repeat)")
        self._sequence_reused = True  # Flag so output folder gets SEQUENCE REUSED prefix
        combination = []
        for folder_num in sorted(self.subfolder_files.keys()):
            folder_data = self.subfolder_files[folder_num]
            
            # Handle optional+end
            if folder_data.get('is_optional_end', False):
                optional_chance = folder_data.get('optional_chance', 0.50)
                if self.rng.random() < optional_chance:
                    _f = self._next_file(folder_num)
                    if _f: combination.append((folder_num, [_f]))
                    break
                else:
                    continue
            
            # Handle regular end
            if folder_data.get('is_end', False) and not folder_data.get('is_optional', False):
                files = folder_data['files']
                _f = self._next_file(folder_num)
                if _f: combination.append((folder_num, [_f]))
                break
            
            # Handle regular optional
            if folder_data.get('is_optional', False):
                optional_chance = folder_data.get('optional_chance', 0.50)
                if self.rng.random() >= optional_chance:
                    continue
            
            _f = self._next_file(folder_num)
            if _f: combination.append((folder_num, [_f]))
        
        return combination if combination else None


class VirtualDistQueue:
    """
    Virtual queue for distraction file selection (Feature 23).
    Works identically to the virtual queue used for macro file selection:
    - All 50 distraction files are shuffled into a queue at construction
    - Files are popped one at a time; no file repeats until ALL have been used
    - When the queue is exhausted it re-shuffles the full pool and starts again
    - Boundary guard: the first item of a new shuffle is never the same as
      the last item of the previous pass, preventing cross-boundary repeats
    - Each shuffle uses the shared rng so order varies per bundle
    """
    def __init__(self, files: list, rng):
        self._pool = list(files)
        self._rng  = rng
        self._queue: list = []
        self._last: object = None
        self._refill()

    def _refill(self):
        self._queue = list(self._pool)
        self._rng.shuffle(self._queue)
        # Prevent cross-boundary consecutive repeat
        if self._last is not None and len(self._queue) > 1 and self._queue[-1] == self._last:
            # Swap the would-be-first item with a random other position
            swap_idx = self._rng.randint(0, len(self._queue) - 2)
            self._queue[-1], self._queue[swap_idx] = self._queue[swap_idx], self._queue[-1]

    def next(self):
        if not self._queue:
            self._refill()
        item = self._queue.pop()
        self._last = item
        return item




# ============================================================================
# LOGOUT SEQUENCE BUILDER (Feature 40)
# ============================================================================

def build_logout_sequence(profile_folder_path, rng, out_path,
                          wait_range_ms=(7200000.0, 16200000.0)):
    """
    Build a strung logout sequence from a profile in @ logout_profiles/.

    profile_folder_path : Path — skill profile folder containing numerically
                          prefixed .json files (0-, 1-, 2-, 3-, etc.).
    wait_range_ms       : (lo, hi) — random wait injected AFTER the last 2.x
                          file plays (break files). None = no wait (fixed file).

    Files are loaded in numeric-prefix order. Random wait fires after the
    last slot with prefix >= 2 and < 3. All other slots are unchanged.

    Returns (out_path, slot_seq_str) on success, (None, None) on failure.
    slot_seq_str: compact digit string e.g. '0123' or '01234'.
    """
    _json_files = sorted(profile_folder_path.glob('*.json'))
    if not _json_files:
        print(f"  [!] Profile '{profile_folder_path.name}': no .json files — logout skipped")
        return None, None

    def _slot_num(fname):
        _m = re.match(r'^(\d+(?:\.\d+)?)\s*[-\s]', fname.lower())
        return float(_m.group(1)) if _m else None

    _numbered = {}
    for _f in _json_files:
        _n = _slot_num(_f.name)
        if _n is None:
            continue
        if _n not in _numbered:
            _numbered[_n] = _f

    if not _numbered:
        print(f"  [!] Profile '{profile_folder_path.name}': no numerically-prefixed files — skipped")
        return None, None

    _sorted_nums = sorted(_numbered.keys())
    _pre  = [n for n in _sorted_nums if n < 2.0]
    _wait = [n for n in _sorted_nums if 2.0 <= n < 3.0]
    _post = [n for n in _sorted_nums if n >= 3.0]
    _miss = []
    if not _pre:  _miss.append("slot < 2")
    if not _wait: _miss.append("slot 2.x")
    if not _post: _miss.append("slot >= 3")
    if _miss:
        print(f"  [!] Profile '{profile_folder_path.name}' missing: {';'.join(_miss)} — skipped")
        return None, None

    _wait_after = max(_wait)

    def _load(path):
        try:
            _evts = json.loads(path.read_text(encoding='utf-8'))
        except Exception as _exc:
            print(f"  [!] LOGOUT: failed to load {path.name}: {_exc}")
            return None
        if not _evts:
            return None
        _evts = filter_problematic_keys(_evts)
        if not _evts:
            return None
        _bt = min(e.get('Time', 0) for e in _evts)
        return [{**e, 'Time': e['Time'] - _bt} for e in _evts]

    _loaded = {}
    for _n in _sorted_nums:
        _evts = _load(_numbered[_n])
        if _evts is None:
            print(f"  [!] Profile '{profile_folder_path.name}': slot {_n} failed — skipped")
            return None, None
        _loaded[_n] = _evts

    _merged   = []
    _timeline = 0.0
    _wait_ms  = 0.0

    def _append(evts):
        nonlocal _timeline
        _dur = max(e.get('Time', 0) for e in evts)
        for e in evts:
            _merged.append({**e, 'Time': e['Time'] + _timeline})
        _timeline += _dur

    for _i, _n in enumerate(_sorted_nums):
        _append(_loaded[_n])
        if _n == _wait_after and wait_range_ms is not None:
            _wait_ms   = rng.uniform(*wait_range_ms)
            _timeline += _wait_ms
        if _i < len(_sorted_nums) - 1:
            _timeline += rng.uniform(500.0, 800.0)

    for e in _merged:
        e['Time'] = max(0, int(round(e['Time'])))
    _merged.sort(key=lambda e: e.get('Time', 0))

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(_merged, separators=(',', ':')))
    except Exception as _exc:
        print(f"  [!] LOGOUT: failed to write {out_path.name}: {_exc}")
        return None, None

    _slot_seq = ''.join(
        str(int(_n)) if _n == int(_n) else str(_n)
        for _n in _sorted_nums
    )
    _tot_min = int(_timeline / 60000)
    _tot_sec = int((_timeline % 60000) / 1000)
    _w_min   = int(_wait_ms  / 60000)
    _w_sec   = int((_wait_ms  % 60000) / 1000)
    print(f"  Built logout (profile: '{profile_folder_path.name}', slots: {_slot_seq}):")
    for _n in _sorted_nums:
        _sfx = f"  (+{_w_min}m {_w_sec}s random wait)" if _n == _wait_after and wait_range_ms else ""
        print(f"    {_n}. {_numbered[_n].name}{_sfx}")
    print(f"    Total: {_tot_min}m {_tot_sec}s  |  -> {out_path.name}")
    return out_path, _slot_seq

def main():
    parser = argparse.ArgumentParser(description="String Macros v3.1.0")
    parser.add_argument("input_root", type=str)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--versions", type=int, default=12, help="Total versions (default: 12 = 3 Raw + 3 Inef + 6 Normal)")
    parser.add_argument("--target-minutes", type=int, default=35)
    parser.add_argument("--bundle-id", type=int, required=True)
    parser.add_argument("--no-chat", action="store_true", help="Disable chat inserts")
    parser.add_argument("--specific-folders", type=str, help="Path to file with specific folder names to include (one per line)")
    parser.add_argument("--group-subfolders", action="store_true", default=False,
                        help="Wrap group-child folders inside (bundle_id) skill_name/ in output (default: off)")
    args = parser.parse_args()
    
    print("="*70)
    print(f"STRING MACROS v{VERSION}")
    print("="*70)
    print(f"Bundle ID: {args.bundle_id}")
    print(f"Target: {args.target_minutes} minutes per file")
    print(f"Versions: {args.versions} total (3 Raw + 3 Inef + 6 Normal)")
    print(f"Chat: {'DISABLED' if args.no_chat else 'ENABLED (20% of files, post-save)'}")
    print("="*70)
    
    # Setup
    search_base = Path(args.input_root).resolve()
    if not search_base.exists():
        print(f"[X] Input root not found: {search_base}")
        return
    
    output_root = Path(args.output_root).resolve()
    bundle_dir = output_root / f"stringed_bundle_{args.bundle_id}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    
    # Load chat files
    chat_files = []
    if not args.no_chat:
        chat_dir = Path(args.input_root).parent / "chat inserts"
        if chat_dir.exists() and chat_dir.is_dir():
            chat_files = list(chat_dir.glob("*.json"))
            if chat_files:
                print(f"? Found {len(chat_files)} chat insert files")
    
    # Scan for DISTRACTIONS trigger - accepts either:
    #   A) A folder named "DISTRACTIONS" (case-insensitive) containing >=1 .json
    #   B) A single file named "distraction_file.json" (or similar) at root level
    # Either presence activates the feature; the trigger content is irrelevant.
    distractions_src = None

    # Option A: folder-based trigger (original behaviour)
    for candidate in [search_base / "DISTRACTIONS",
                       search_base / "distractions",
                       search_base / "Distractions"]:
        if candidate.exists() and candidate.is_dir():
            distractions_src = candidate
            break
    if distractions_src is None:
        for candidate in [search_base.parent / "DISTRACTIONS",
                           search_base.parent / "distractions"]:
            if candidate.exists() and candidate.is_dir():
                distractions_src = candidate
                break

    # Option B: single trigger file at root level
    # Any .json file whose name contains "distraction" (case-insensitive) works
    if distractions_src is None:
        for candidate_dir in [search_base, search_base.parent]:
            for f in candidate_dir.glob("*.json"):
                if "distraction" in f.name.lower():
                    distractions_src = f.parent   # treat parent as the trigger dir
                    break
            if distractions_src:
                break

    if distractions_src:
        trigger_files = list(distractions_src.glob("*.json")) if distractions_src.is_dir() else []
        if not distractions_src.is_dir():
            # single-file trigger: src is the parent folder, just confirm the file is there
            trigger_files = [f for f in distractions_src.iterdir()
                             if f.suffix == '.json' and 'distraction' in f.name.lower()]
        if trigger_files:
            print(f"? Distraction trigger found - 50 distraction files will be generated")
        else:
            print(f"  Distraction trigger found but empty - feature disabled")
            distractions_src = None
    else:
        print(f"  No distraction trigger found - distraction generation disabled")
    
    # LOGOUT SEQUENCE FOLDER (Feature 40) — detect folder; build per output folder.
    # Long break (2h–4.5h) and Short break (30–90min) are generated fresh per
    # output folder so every folder gets a different random wait duration.
    # @ logout_profiles/ — single source of truth for all logout sequences.
    # Each skill has a matching subfolder: @ logout_profiles/<skill_folder_name>/
    # Matching uses exact name first, then leading-number fallback.
    _logout_profiles_root = search_base / "@ logout_profiles"
    if _logout_profiles_root.is_dir():
        _profiles = [d.name for d in sorted(_logout_profiles_root.iterdir()) if d.is_dir()]
        print(f"  Found @ logout_profiles/ with {len(_profiles)} profile(s): {_profiles}")
    else:
        _logout_profiles_root = None
        print(f"  No '@ logout_profiles' folder found — logout files will not be generated.")

    # @ Final logout X client.json — copied from input_macros/ into every output skill folder.
    _final_client_src = search_base / "@ Final logout X client.json"
    if not _final_client_src.exists():
        _final_client_src = None
        print(f"  No '@ Final logout X client.json' found in input_macros/ — will not be copied.")
    else:
        print(f"  Found: @ Final logout X client.json")

    print()

    # ── Folder scan — supports GROUP FOLDERS (organizer dirs one level above macros)
    # Structure: input_macros/GroupName/MacroFolder1, MacroFolder2, ...
    # Group children auto-flatten into main_folders for ALL FOLDERS mode.
    # _group_registry maps group_name_lower -> [child_folder_data, ...]
    # so the filter loop can expand a group name into all its children.
    main_folders   = []
    _group_registry = {}   # {group_name_lower: [child_fd, ...]}
    _SCAN_SKIP = {'distractions', 'logout, wait, in', 'combination_history',
                  '@ logout_profiles', '@ logout_sequence'}

    def _register_macro_folder(fd, indent=""):
        """Add fd to main_folders and print its summary line."""
        main_folders.append(fd)
        _ns = fd['subfolders']
        nums = sorted(k for k in _ns if k != 0)
        print(f"{indent}  Found: {fd['name']}")
        if nums:
            print(f"{indent}    Subfolders: {nums}")
            _sp = []
            for _n in nums:
                _fi = _ns.get(_n, {})
                if _fi.get('is_optional_end'): _sp.append(f"{_n} (optional+end)")
                elif _fi.get('is_end'):         _sp.append(f"{_n} (end)")
                elif _fi.get('is_optional'):    _sp.append(f"{_n} (optional)")
                if _fi.get('is_time_sensitive'): _sp.append(f"{_n} (time-sensitive)")
            if _sp: print(f"{indent}    Special: {', '.join(_sp)}")
        if fd.get('non_json'):   print(f"{indent}    Non-JSON:   {len(fd['non_json'])} files")

    def _has_f_prefix_subdir(d):
        """Return True if directory d has any DIRECT child dir starting with
        the explicit F+digit pattern (F1-, F2, F3.5, etc.).
        Used for condition-1 of _looks_like_group: if the candidate folder
        already has F-prefix direct children it is a normal macro folder.
        """
        _re = re.compile(r'(?i)^[Ff]\d')
        try:
            for _it in d.iterdir():
                if _it.is_dir() and _re.match(_it.name):
                    return True
        except (PermissionError, OSError):
            pass
        return False

    def _has_numbered_subdir(d):
        """Return True if directory d has any DIRECT child dir whose name starts
        with a digit (with or without F prefix: F1-, 1-, F3.5, 3.5-optional...).
        Matches the same number-detection logic as scan_for_numbered_subfolders.
        Used for condition-2 of _looks_like_group: at least one child of the
        candidate folder contains numbered subdirs → that child is a macro folder.
        """
        _re = re.compile(r'^[Ff]?\d')
        try:
            for _it in d.iterdir():
                if _it.is_dir() and _re.match(_it.name):
                    return True
        except (PermissionError, OSError):
            pass
        return False

    def _looks_like_group(folder):
        """Return True if folder is an organizer group folder.

        Two-condition heuristic (both must hold):
          1. folder has NO direct F+digit children.
             If it does, it is a normal macro folder (e.g. FM+COOK has F1-, F2-).
          2. At least one direct child of folder CONTAINS numbered subdirectories
             (F-prefix or plain-digit prefix).
             This makes the child itself a macro folder inside a group.

        Examples:
          6- smithing files/ : no F-children (✓), 61-smth-var HAS 1-,2- (✓) → GROUP
          Test/              : no F-children (✓), test1 HAS F1-,F2- (✓) → GROUP
          FM+COOK/           : HAS F1-,F2- direct children (✗) → MACRO
          22- Craft Dia/     : HAS F1-,F2- direct children (✗) → MACRO

        Must run BEFORE scan_for_numbered_subfolders so that child dirs whose
        names contain digits are never mis-extracted as F-subfolders.
        """
        # Condition 1: parent must have NO direct F+digit children
        if _has_f_prefix_subdir(folder):
            return False
        # Condition 2: at least one direct child must contain numbered subdirs
        try:
            for _ch in folder.iterdir():
                if not _ch.is_dir(): continue
                if _has_numbered_subdir(_ch):
                    return True
        except (PermissionError, OSError):
            pass
        return False

    def _scan_as_macro(folder, group_name=None):
        """Run scan_for_numbered_subfolders on folder. If the scan returns empty
        but the folder has children with numbered subdirs one level deeper (the
        child/container/F1 pattern), scan those intermediate containers too.
        Returns a valid folder_data dict or None.
        """
        _cn, _cnj, _craf, _cral = scan_for_numbered_subfolders(folder)
        if not _cn:
            # Try one level deeper: child/container/F1-... pattern
            for _sub in sorted(folder.iterdir()):
                if not _sub.is_dir(): continue
                if _has_numbered_subdir(_sub):
                    _sn, _snj, _sraf, _sral = scan_for_numbered_subfolders(_sub)
                    # Merge non-JSON files from deeper scan
                    _cnj.extend(_snj)
                    if _sn:
                        _cn.update(_sn)
                        _craf = _craf or _sraf
                        _cral = _cral or _sral
        if not _cn:
            return None
        fd = {
            'path':              folder,
            'name':              folder.name,
            'root_always_first': _craf,
            'root_always_last':  _cral,
            'subfolders':        _cn,
            'non_json':          _cnj,
        }
        if group_name is not None:
            fd['_group_name'] = group_name
        return fd

    for folder in sorted(search_base.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name.lower() in _SCAN_SKIP:
            continue

        # ── GROUP FOLDER pre-check ───────────────────────────────────────
        # Must happen BEFORE scan_for_numbered_subfolders: the fallback number
        # regex would extract digits from child names like "test1"→1, mis-
        # treating the organizer as a macro folder with numbered subfolders.
        if _looks_like_group(folder):
            _children = []
            for _child in sorted(folder.iterdir()):
                if not _child.is_dir(): continue
                # Skip @ asset folders — logout profiles, sequences, etc.
                if _child.name.startswith('@'):
                    continue
                _cfd = _scan_as_macro(_child, group_name=folder.name)
                if _cfd:
                    _children.append(_cfd)
            if _children:
                print(f"  [GROUP] '{folder.name}' contains {len(_children)} macro folder(s):")
                for _cfd in _children:
                    _register_macro_folder(_cfd, indent="  ")
                _group_registry[folder.name.lower()] = _children
            continue  # do NOT fall through to normal scan below

        # ── Normal macro folder ──────────────────────────────────────────
        numbered_subfolders, non_json_files, root_always_first, root_always_last = scan_for_numbered_subfolders(folder)

        if numbered_subfolders:
            _register_macro_folder({
                'path':              folder,
                'name':              folder.name,
                'root_always_first': root_always_first,
                'root_always_last':  root_always_last,
                'subfolders':        numbered_subfolders,
                'non_json':          non_json_files,
            })
        else:
            # Folder has no F-subfolders and doesn't look like a group.
            # Could be an empty/non-macro folder — silently skip.
            pass

    if not main_folders:
        print("[X] No folders with numbered subfolders found!")
        return
    
    # Filter by specific folders (and optionally specific subfolders) if provided
    # File format (one entry per line):
    #   FolderName                     -> include that folder, ALL its subfolders
    #   FolderName: F1, F3, F4         -> include that folder, ONLY listed subfolders
    #   FolderName: F1, F3-F5          -> include that folder, subfolders F1 and F3..F5 range
    # Matching is case-insensitive and whitespace-stripped.
    if args.specific_folders:
        try:
            with open(args.specific_folders, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            # Parse lines — each line is either "FolderName" or "FolderName: F1, F2"
            # GitHub Actions may collapse newlines; handle commas-as-separators only
            # when there is NO colon present (legacy behaviour).
            # DUPLICATE SUPPORT: entries_list is an ORDERED LIST of (name, sf_filter)
            # tuples. The same folder name may appear multiple times — each occurrence
            # produces one independent output folder, suffixed " (2)", " (3)", etc.
            entries_list = []   # [(folder_name_lower, sf_filter_or_None), ...]
            for raw_line in raw_text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                if ':' in line:
                    # "FolderName: F1, F2, F3" — split on first colon only
                    folder_part, sf_part = line.split(':', 1)
                    folder_key = folder_part.strip().lower()
                    # Parse subfolder numbers from "F1, F2, F3-F5" etc.
                    sf_nums = set()
                    for tok in re.split(r'[,\s]+', sf_part.strip()):
                        tok = tok.strip()
                        if not tok:
                            continue
                        # Range: F3-F5 (note: only meaningful if written as "F3-F5" not "F3,F5")
                        range_m = re.match(r'^[Ff]?(\d+(?:\.\d+)?)-[Ff]?(\d+(?:\.\d+)?)$', tok)
                        if range_m:
                            lo, hi = float(range_m.group(1)), float(range_m.group(2))
                            # Add all integer steps between lo and hi
                            v = lo
                            while v <= hi + 0.001:
                                sf_nums.add(round(v, 4))
                                v += 1.0
                        else:
                            # Single: F1, F3, 2, 3.5
                            single_m = re.match(r'^[Ff]?(\d+(?:\.\d+)?)$', tok)
                            if single_m:
                                sf_nums.add(float(single_m.group(1)))
                    entries_list.append((folder_key, sf_nums if sf_nums else None))
                else:
                    # No colon — legacy comma-separated folder names (no subfolder filter)
                    for name in line.replace(',', '\n').splitlines():
                        name = name.strip()
                        if name:
                            entries_list.append((name.lower(), None))

            if entries_list:
                print(f"\n Filtering to specific folders only:")
                for name, sfs in entries_list:
                    sf_str = f" (subfolders: {sorted(sfs)})" if sfs else " (all subfolders)"
                    print(f"  - {name}{sf_str}")

                filtered_folders = []
                _name_run_count = {}  # {name_lower: run_count} — tracks duplicates

                for _req_name, _sf_filter in entries_list:
                    # ── GROUP FOLDER: expand name → all children ────────────────────────
                    if _req_name in _group_registry:
                        _name_run_count[_req_name] = _name_run_count.get(_req_name, 0) + 1
                        _grun = _name_run_count[_req_name]
                        # Effective bundle id: 555 for run 1, 555.1 for run 2, 555.2 for run 3
                        _g_ebid = f"{args.bundle_id}.{_grun}"
                        _gsufx = f" (run {_grun}, bid={_g_ebid})" if _grun > 1 else ""
                        print(f"  [group] '{_req_name}' → {len(_group_registry[_req_name])} child folder(s){_gsufx}")
                        for _gchild in _group_registry[_req_name]:
                            _gfd = dict(_gchild)
                            _gfd['_run_suffix'] = ''  # no suffix on folder name — bid carries the distinction
                            _gfd['_effective_bid'] = _g_ebid
                            filtered_folders.append(_gfd)
                        continue

                    # ── Normal single macro folder ─────────────────────────────────────
                    _matched_fd = None
                    for _fd in main_folders:
                        if _fd['name'].lower() == _req_name:
                            _matched_fd = _fd
                            break
                    if _matched_fd is None:
                        continue  # not found as top-level; caught by subfolder fallback

                    # Assign effective bundle id for duplicates: 555, 555.1, 555.2
                    _name_run_count[_req_name] = _name_run_count.get(_req_name, 0) + 1
                    _nrun = _name_run_count[_req_name]
                    _rsuffix = ''  # no longer used for naming — _effective_bid carries distinction
                    _effective_bid = f"{args.bundle_id}.{_nrun}"

                    if _sf_filter:
                        original_subs = _matched_fd['subfolders']
                        filtered_subs = {}
                        for num, data in original_subs.items():
                            if round(num, 4) in _sf_filter or num == 0:
                                forced = dict(data)
                                forced['is_optional']     = False
                                forced['is_end']          = False
                                forced['is_optional_end'] = False
                                filtered_subs[num] = forced
                        if not filtered_subs:
                            print(f"  [!] No matching subfolders found in '{_matched_fd['name']}'")
                            print(f"      Requested: {sorted(_sf_filter)}")
                            print(f"      Available: {sorted(k for k in original_subs if k != 0)}")
                            continue
                        filtered_fd = dict(_matched_fd)
                        filtered_fd['subfolders'] = filtered_subs
                        filtered_fd['_run_suffix'] = _rsuffix
                        filtered_fd['_effective_bid'] = _effective_bid
                        filtered_folders.append(filtered_fd)
                    else:
                        # Shallow-copy folder_data so each duplicate run has its own
                        # _effective_bid without sharing it with other runs of the same folder.
                        filtered_fd = dict(_matched_fd)
                        filtered_fd['_run_suffix'] = _rsuffix
                        filtered_fd['_effective_bid'] = _effective_bid
                        filtered_folders.append(filtered_fd)

                if not filtered_folders:
                    # Fallback A: expand any group names
                    _req_names_set = {n for n, _ in entries_list}
                    for _gn, _gchildren in _group_registry.items():
                        if _gn in _req_names_set:
                            for _gcfd in _gchildren:
                                _gcfd2 = dict(_gcfd)
                                _gcfd2['_run_suffix'] = ''
                                filtered_folders.append(_gcfd2)
                    # Fallback B: search by subfolder name
                    _req_names_set = {n for n, _ in entries_list}
                    for folder_data in main_folders:
                        for sf_num, sf_data in folder_data['subfolders'].items():
                            sf_name = sf_data.get('folder_name', '')
                            if sf_name.lower() in _req_names_set:
                                print(f"  [->] '{sf_name}' matched as subfolder of '{folder_data['name']}'")
                                forced_sf = dict(sf_data)
                                forced_sf['is_optional']     = False
                                forced_sf['is_end']          = False
                                forced_sf['is_optional_end'] = False
                                forced_sf['max_files']       = 1

                                nsf = sf_data.get('nested_subfolder_files')
                                if nsf:
                                    synthetic = {
                                        'path': sf_data.get('folder_path', folder_data['path']),
                                        'name': sf_name,
                                        'root_always_first': sf_data.get('nested_root_always_first'),
                                        'root_always_last':  sf_data.get('nested_root_always_last'),
                                        'subfolders': nsf,
                                        'non_json':   folder_data.get('non_json', []),
                                    }
                                else:
                                    synthetic = {
                                        'path': sf_data.get('folder_path', folder_data['path']),
                                        'name': sf_name,
                                        'root_always_first': sf_data.get('always_first'),
                                        'root_always_last':  sf_data.get('always_last'),
                                        'subfolders': {sf_num: forced_sf},
                                        'non_json':   folder_data.get('non_json', []),
                                    }
                                synthetic['_run_suffix'] = ''
                                filtered_folders.append(synthetic)

                if not filtered_folders:
                    print(f"\n[X] None of the specified folders were found!")
                    print(f"   Looking for: {[n for n, _ in entries_list]}")
                    print(f"   Available main folders: {[f['name'] for f in main_folders]}")
                    print(f"   TIP: You can also write a subfolder name directly:")
                    print(f"     F0.5 optional-7- CAM2       <- auto-found inside any main folder")
                    print(f"   Or use colon format to specify parent:")
                    print(f"     22- Craft Dia: F0.5         <- explicit parent + subfolder")
                    sys.exit(1)

                main_folders = filtered_folders
                for _dn, _dc in _name_run_count.items():
                    if _dc > 1:
                        print(f"  [dup] '{_dn}' selected {_dc}x -- {_dc} separate output folders")
                print(f"[OK] Filtered to {len(main_folders)} folder(s)")
            else:
                print(f"\n[!]?  Specific folders file is empty, processing ALL folders")
        
        except FileNotFoundError:
            print(f"\n[X] Specific folders file not found: {args.specific_folders}")
            return
        except Exception as e:
            print(f"\n[X] Error reading specific folders file: {e}")
            return
    
    print(f"\n Total folders to process: {len(main_folders)}")
    print("="*70)
    
    # Initialize global chat queue
    rng = random.Random(args.bundle_id * 42)
    global_chat_queue = list(chat_files) if chat_files else []
    if global_chat_queue:
        rng.shuffle(global_chat_queue)
        print(f" Initialized global chat queue with {len(global_chat_queue)} files")
        print()
    
    # Track ALL combinations for the bundle (one file at root level)
    bundle_combinations = {}  # {folder_name: [combination_signatures]}

    # Generate DISTRACTIONS now (before folder loop) so files are available
    # for inline insertion during stringing.
    # Files are written to a TEMP folder (not inside the bundle) - they are used
    # only as in-memory splice sources and are NOT included in the final output.
    import tempfile as _tempfile
    _dist_tmpdir = None
    distraction_files = []   # list of Path objects to pick from during stringing
    dist_queue = None        # VirtualDistQueue - cycles through all files before repeating
    if distractions_src:
        print("\n" + "="*70)
        print(" Generating DISTRACTION files (inline splice only, not saved to bundle)...")
        _dist_tmpdir = _tempfile.mkdtemp(prefix="string_macros_dist_")
        dist_tmp = Path(_dist_tmpdir) / "distractions"
        n_written = generate_distraction_files(distractions_src, dist_tmp, rng, count=50, bundle_id=args.bundle_id)
        print(f"  [OK] Generated {n_written} distraction files (virtual queue: no repeats until all used)")
        distraction_files = sorted(dist_tmp.glob("*.json"))
        dist_queue = VirtualDistQueue(distraction_files, rng)

    # Process each folder
    for folder_data in main_folders:
        folder_name = folder_data['name']
        subfolder_files = folder_data['subfolders']
        non_json_files = folder_data['non_json']
        root_always_first = folder_data.get('root_always_first')
        root_always_last  = folder_data.get('root_always_last')

        # Per-folder distraction insertion chances (float decimal, drawn once per folder):
        # - Normal files:      7.0-10.0%  (tighter window, more controlled)
        # - Inefficient files: 7.0-14.0%  (wider window, more varied)
        # - Raw files:         0%          (never)
        folder_dist_chance_normal = rng.uniform(3.5,  5.0) / 100.0 if distraction_files else 0.0
        folder_dist_chance_inef   = rng.uniform(3.5,  7.0) / 100.0 if distraction_files else 0.0
        
        # D_ REMOVAL
        cleaned_folder_name = re.sub(r'[Dd]_', '', folder_name)
        
        # Extract folder number
        folder_num_match = re.search(r'\d+', cleaned_folder_name)
        folder_number = int(folder_num_match.group()) if folder_num_match else 0
        
        
        # Create output folder - append bundle ID in specific folders mode
        # _run_suffix (" (2)", " (3)") is set when the same folder is selected
        # multiple times via the dropdowns, giving each run a distinct output name.
        output_folder_name = cleaned_folder_name
        _group_name = folder_data.get('_group_name')  # set for group children in ALL FOLDERS and specific-folders mode
        _run_suffix = folder_data.get('_run_suffix', '')
        # _effective_bid: 555 for run 1, 555.1 for run 2, 555.2 for run 3
        # Makes it easy to identify which repeat of a folder a file belongs to.
        _effective_bid = folder_data.get('_effective_bid', str(args.bundle_id))
        if _group_name:
            # Group child: always wrap inside (effective_bid) skill_name/ subfolder
            _skill_out = bundle_dir / f"({_effective_bid}) {_group_name}"
            _skill_out.mkdir(parents=True, exist_ok=True)
            out_folder = _skill_out / output_folder_name
            print(f"  [group] _group_name={_group_name!r} → {out_folder.relative_to(bundle_dir)}")
        elif args.specific_folders:
            # Specific-folders mode, non-group: batch prefix on the subfolder name itself
            output_folder_name = f"({_effective_bid}) {output_folder_name}{_run_suffix}"
            out_folder = bundle_dir / output_folder_name
        else:
            # ALL FOLDERS mode, standalone folder: flat, no batch prefix
            out_folder = bundle_dir / output_folder_name
        print(f"\n Processing: {out_folder.relative_to(bundle_dir)}")
        out_folder.mkdir(parents=True, exist_ok=True)
        
        # --- Logout profile lookup + 3-file generation ---
        # Checks every plausible location for @ logout_sequence/, printing
        # each path so the console shows exactly what was found or missed.
        _fd_path   = folder_data['path']          # actual path object (may be subfolder in specific-folders mode)
        _fd_name   = folder_data['name']          # skill folder name string
        _profile_folder = None

        # Build candidate paths to check — covers every nesting scenario
        _candidates = []
        _candidates.append(('fd_path',          _fd_path / "@ logout_sequence"))
        _candidates.append(('fd_path_parent',   _fd_path.parent / "@ logout_sequence"))
        _candidates.append(('search/name',      search_base / _fd_name / "@ logout_sequence"))

        print(f"  [LOGOUT] Checking '{_fd_name}' (path={_fd_path.name}):")
        for _clabel, _cpath in _candidates:
            _exists = _cpath.is_dir()
            print(f"    {'OK' if _exists else '--'} [{_clabel}] {_cpath}")
            if _exists and _profile_folder is None:
                _profile_folder = _cpath
                print(f"  Logout: MATCHED @ logout_sequence/ via [{_clabel}]")

        # Level 2 — @ logout_profiles/ hub if no @ logout_sequence/ found
        if _profile_folder is None and _logout_profiles_root:
            _fn_m   = re.match(r'^(\d+)', _fd_name)
            _fn_num = _fn_m.group(1) if _fn_m else None
            _exact  = _logout_profiles_root / _fd_name
            if _exact.is_dir():
                _profile_folder = _exact
            elif _fn_num:
                for _pd in sorted(_logout_profiles_root.iterdir()):
                    if _pd.is_dir():
                        _pm = re.match(r'^(\d+)', _pd.name)
                        if _pm and _pm.group(1) == _fn_num:
                            _profile_folder = _pd
                            break
            if _profile_folder:
                print(f"  Logout: using hub profile '{_profile_folder.name}'")

        # Level 3 — global LOGOUT, wait, in/ fallback
        if _profile_folder is None:
            _global_dir = search_base / "LOGOUT, wait, in"
            if _global_dir.is_dir():
                _profile_folder = _global_dir
                print(f"  Logout: using global LOGOUT, wait, in/ fallback")

        if _profile_folder is None:
            print(f"  [!] No logout source found for '{_fd_name}' — skipped.")
        else:
            _fl_rng = random.Random()

            _lo_fixed_p = Path(args.output_root) / "_tmp_logout_fixed.json"
            _lo_short_p = Path(args.output_root) / "_tmp_logout_short.json"
            _lo_long_p  = Path(args.output_root) / "_tmp_logout_long.json"

            _lk = str(_profile_folder)
            if _lk in _fixed_logout_cache:
                _fixed_slots  = _fixed_logout_cache[_lk]['slots']
                _fixed_dest   = out_folder / f"@ {_fixed_slots}.json"
                _fixed_dest.write_text(_fixed_logout_cache[_lk]['json'], encoding='utf-8')
                print(f"  \u2713 Built (cached): {_fixed_dest.name}")
                _fixed_built = _fixed_dest
            else:
                _fixed_built, _fixed_slots = build_logout_sequence(
                    _profile_folder, _fl_rng, _lo_fixed_p, wait_range_ms=None)
                if _fixed_built and _fixed_slots:
                    try:
                        shutil.copy2(_fixed_built, out_folder / f"@ {_fixed_slots}.json")
                        print(f"  \u2713 @ {_fixed_slots}.json")
                        _fixed_logout_cache[_lk] = {
                            'slots': _fixed_slots,
                            'json':  (out_folder / f"@ {_fixed_slots}.json").read_text(encoding='utf-8'),
                        }
                    except Exception as _e:
                        print(f"  [!] Error writing fixed logout: {_e}")

            _short_built, _ = build_logout_sequence(
                _profile_folder, _fl_rng, _lo_short_p,
                wait_range_ms=(1800000.0, 5400000.0))
            if _short_built:
                try:
                    shutil.copy2(_short_built, out_folder / "@ LOGOUT SHORT BREAK.json")
                    print(f"  \u2713 @ LOGOUT SHORT BREAK.json")
                except Exception as _e:
                    print(f"  [!] Error writing short break: {_e}")

            _long_built, _ = build_logout_sequence(
                _profile_folder, _fl_rng, _lo_long_p,
                wait_range_ms=(7200000.0, 16200000.0))
            if _long_built:
                try:
                    shutil.copy2(_long_built, out_folder / "@ LOGOUT LONG BREAK.json")
                    print(f"  \u2713 @ LOGOUT LONG BREAK.json")
                except Exception as _e:
                    print(f"  [!] Error writing long break: {_e}")

        # @ Final logout X client.json
        if _final_client_src:
            try:
                shutil.copy2(_final_client_src, out_folder / _final_client_src.name)
                print(f"  \u2713 Copied: {_final_client_src.name}")
            except Exception as _e:
                print(f"  [!] Error copying final client: {_e}")

        # Repo-root fixed logout files
        for _repo_fixed in [
            "- Final logout.json",
            "- Quick logout wait RELOGIN.json",
        ]:
            _rf_src = search_base.parent / _repo_fixed
            if not _rf_src.exists():
                continue
            _rf_dest = "@ " + _repo_fixed[1:].lstrip()
            try:
                shutil.copy2(_rf_src, out_folder / _rf_dest)
                print(f"  \u2713 Copied: {_rf_dest}")
            except Exception as _e:
                print(f"  [!] Error copying {_repo_fixed}: {_e}")
        # Copy non-JSON files with @ prefix (images, txt, etc — not temp/part files)
        _NONJSON_SKIP_EXTS = {".part", ".tmp", ".bak", ".swp", ".ds_store"}
        for non_json_file in non_json_files:
            if non_json_file.suffix.lower() in _NONJSON_SKIP_EXTS:
                continue
            try:
                original_name = non_json_file.name
                if original_name.startswith("-"):
                    new_name = f"@ {folder_number} {original_name[1:].strip()}"
                else:
                    new_name = f"@ {folder_number} {original_name}"
                shutil.copy2(non_json_file, out_folder / new_name)
                print(f"  ✓ Copied non-JSON: {new_name}")
            except Exception as e:
                print(f"  ? Error copying {non_json_file.name}: {e}")
        
        if not subfolder_files:
            print("  [!]?  No numbered subfolders to process")
            continue
        
        # Use bundle-organized tracker
        tracker = ManualHistoryTracker(
            subfolder_files, rng, cleaned_folder_name, search_base
        )
        target_ms = args.target_minutes * 60000
        
        _base_target_ms = target_ms  # base for per-version +-15min variance
        # Track all combinations used in THIS RUN for this folder
        folder_combinations_used = []
        
        # Calculate total original duration
        # Detect "copied" subfolders: subfolders whose file-name sets are identical
        # (e.g. F1-mine and F2-mine with same files). Count their files only once
        # so the duration reflects unique content, not duplicated repetitions.
        # Count each unique filename only once across ALL subfolders.
        # Copied folders (F1-mine, F2-mine) may share file names - count once.
        _seen_filenames = set()   # filenames already counted (by name, not path)
        total_original_files = 0
        total_original_ms = 0
        # Count subfolders whose *entire* file-name set is a duplicate of another
        _seen_filesets = []
        num_copied_folders = 0

        def _count_files_recursive(subfolder_dict):
            """Recursively count files in a subfolder dict, descending into nested_subfolder_files."""
            for _sdata in subfolder_dict.values():
                _files = _sdata.get('files', [])
                fileset = frozenset(f.name for f in _files)
                if fileset and fileset in _seen_filesets:
                    num_copied_folders_box[0] += 1
                elif fileset:
                    _seen_filesets.append(fileset)
                for f in _files:
                    if f.name not in _seen_filenames:
                        _seen_filenames.add(f.name)
                        total_box[0] += 1
                        total_ms_box[0] += get_file_duration_ms(f)
                # Recurse into nested subfolders (e.g. FM nested → F1-F6 inner)
                _nsf = _sdata.get('nested_subfolder_files')
                if _nsf:
                    _count_files_recursive(_nsf)

        # Use mutable boxes so the nested helper can update them
        total_box            = [0]
        total_ms_box         = [0]
        num_copied_folders_box = [0]
        _count_files_recursive(subfolder_files)
        total_original_files = total_box[0]
        total_original_ms    = total_ms_box[0]
        num_copied_folders   = num_copied_folders_box[0]

        
        # Build subfolder file count lines for manifest
        _subfolder_lines = []
        for _fn in sorted(subfolder_files.keys()):
            _fd = subfolder_files[_fn]
            _fn_label = str(int(_fn) if _fn == int(_fn) else _fn)
            _file_count = len(_fd.get('files', []))
            _always_note = ""
            # always_first/last are now pools (lists) — show count if > 1
            _af_pool = _fd.get('always_first', [])
            _al_pool = _fd.get('always_last',  [])
            if _af_pool:
                _af_count = len(_af_pool) if isinstance(_af_pool, list) else 1
                _always_note += f" + always_first({_af_count})" if _af_count > 1 else " + always_first"
            if _al_pool:
                _al_count = len(_al_pool) if isinstance(_al_pool, list) else 1
                _always_note += f" + always_last({_al_count})" if _al_count > 1 else " + always_last"
            # Nested subfolder: show sub-folder count instead of 0 files
            _nsf = _fd.get('nested_subfolder_files')
            if _nsf:
                _nested_count = len(_nsf)
                # Show per-sub-subfolder file counts
                _nested_parts = []
                for _nfn in sorted(_nsf.keys()):
                    _nfd = _nsf[_nfn]
                    _nfn_label = str(int(_nfn) if _nfn == int(_nfn) else _nfn)
                    _nfile_count = len(_nfd.get('files', []))
                    _nested_parts.append(f"F{_nfn_label}:{_nfile_count}")
                _subfolder_lines.append(f"  F{_fn_label}: nested ({', '.join(_nested_parts)}){_always_note}")
            else:
                _subfolder_lines.append(f"  F{_fn_label}: {_file_count} file(s){_always_note}")

        # Manifest header
        manifest_lines = [
            f"MANIFEST FOR FOLDER: {cleaned_folder_name}",
            "=" * 40,
            f"Script Version: {VERSION}",
            f"Stringed Bundle: stringed_bundle_{args.bundle_id}",
            f"Total Original Files: {total_original_files}",
            (f"Total Original Files Duration: {format_ms_precise(total_original_ms)} ({num_copied_folders} copied folder(s))"
             if num_copied_folders > 0
             else f"Total Original Files Duration: {format_ms_precise(total_original_ms)}"),
        ] + _subfolder_lines + [""]
        
        # Check if any folders are 'time sensitive' (no inefficient files)
        has_time_sensitive = any(
            folder_data.get('is_time_sensitive', False) 
            for folder_data in subfolder_files.values()
        )
        
        # Debug: Show which folders are time_sensitive
        if has_time_sensitive:
            time_sensitive_folders = [
                str(int(num) if num == int(num) else num)
                for num, data in subfolder_files.items() 
                if data.get('is_time_sensitive', False)
            ]
            print(f"  ??  TIME SENSITIVE folders detected: {', '.join(time_sensitive_folders)}")
        
        # Version loop: 3 Raw + 3 Inef + 6 Normal = 12 total
        # OR: 3 Raw + 0 Inef + 9 Normal = 12 total (if time_sensitive)
        def get_version_letter(idx):
            """
            Generate version letter for any index, repeating letters after Z.
            0=A, 1=B, ..., 25=Z, 26=AA, 27=BB, ..., 51=ZZ, 52=AAA, etc.
            """
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            repeat = (idx // 26) + 1   # how many chars: 1 for 0-25, 2 for 26-51, etc.
            letter = letters[idx % 26]
            return letter * repeat
        # VERSION DISTRIBUTION - 2:3:7 ratio (raw:inefficient:normal)
        # Scaled from the 12-file base using round() so it stays proportional
        # for any --versions value, with remainder going to normal files.
        # Time-sensitive folders replace all inefficient slots with normal.
        _total_parts = 12  # ratio denominator
        if has_time_sensitive:
            # 1:1 ratio for time-sensitive: half raw, half normal, zero inefficient
            num_raw    = max(1, round(args.versions / 2))
            num_inef   = 0
            num_normal = args.versions - num_raw
            print(f"   File distribution: {num_raw} Raw + 0 Inef + {num_normal} Normal (time sensitive - 1:1 ratio)")
        else:
            num_raw   = max(1, round(args.versions * 2 / _total_parts))
            num_inef  = max(1, round(args.versions * 3 / _total_parts))
            num_normal = args.versions - num_raw - num_inef
            if num_normal < 1:
                num_normal = 1
                num_inef = max(1, args.versions - num_raw - num_normal)
            print(f"   File distribution: {num_raw} Raw + {num_inef} Inef + {num_normal} Normal ({num_raw}:{num_inef}:{num_normal} ratio, target 2:3:7)")
        
        # CHAT INSERT applied post-save (see post-loop block below the version loop).
        
        for v_idx in range(args.versions):
            v_letter = get_version_letter(v_idx)
            
            # Determine file type
            is_raw = (v_idx < num_raw)
            is_inef = (num_raw <= v_idx < num_raw + num_inef)
            is_normal = (v_idx >= num_raw + num_inef)
            
            # DEBUG: Show file type determination
            if v_idx == 0:  # First file
                print(f"\n   File Type Assignments:")
            
            file_type_str = "RAW" if is_raw else ("INEFFICIENT" if is_inef else "NORMAL")
            prefix_str = "^" if is_raw else ("\u00ac\u00ac" if is_inef else "none")
            print(f"     {v_letter}: {file_type_str:12s} (prefix: {prefix_str})")
            
            # Set multiplier — continuous random range (not rounded), giving decimal values
            # e.g. Normal picks anywhere in [1.3, 1.5] so 1.31, 1.44, 1.49, etc.
            if is_raw:
                # Raw: range 1.0 – 1.1  (e.g. 1.03, 1.07)
                mult = round(rng.uniform(1.1, 1.2), 4)
            elif is_inef:
                # Inefficient: range 2.0 – 3.0  (e.g. 2.14, 2.87)
                mult = round(rng.uniform(2.0, 3.0), 4)
            else:  # normal
                # Normal: range 1.3 – 1.5  (e.g. 1.33, 1.47)
                mult = round(rng.uniform(1.5, 1.7), 4)
            
            # Per-version target: ±5 minutes random variance around base target
            # Each version independently drawn — decimal ms, never rounded
            _variance_ms = rng.uniform(-15 * 60000, 15 * 60000)
            target_ms = max(60000, _base_target_ms + _variance_ms)
            _t_min = int(target_ms // 60000)
            _t_sec = int((target_ms % 60000) / 1000)
            _var_actual = (target_ms - _base_target_ms) / 60000
            _var_sign   = "+" if _var_actual >= 0 else ""
            print(f"     {v_letter}: target = {_t_min}m {_t_sec}s (base {args.target_minutes}m, var {_var_sign}{_var_actual:.1f}m)")

            # Build cycles until target reached
            stringed_events = []
            all_file_info_with_times = []  # List of (folder_num, filename, end_time) tuples
            total_intra = 0
            total_inter = 0
            total_idle = 0
            total_normal_pauses = 0
            massive_pause_ms = 0
            jitter_pct = 0

            # NEW: Track pre-file pauses, post-pause delays, cursor transitions, distraction pauses
            total_pre_file = 0
            total_transitions = 0
            total_snap_gap = 0     # cumulative post-snap transition gaps (80-150ms each)
            total_dist_pause = 0   # cumulative distraction file duration inserted into this version

            # For flat/single-subfolder folders, always_first fires on the FIRST cycle
            # only and always_last fires once AFTER the whole loop.
            _is_flat_folder = (len(subfolder_files) == 1)
            _cycle_count = 0   # tracks which cycle we are on

            # INEF: reserve budget for the massive pause so the loop doesn't
            # overshoot target_ms once the pause is inserted after the loop.
            # Pre-sample the pause duration using the same formula as insert_massive_pause.
            # The loop uses (target_ms - massive_pause_budget) as its effective ceiling.
            if is_inef:
                _expected_massive_ms = int(rng.uniform(240000.0, 420000.0))  # no mult
                _effective_target = max(target_ms - _expected_massive_ms, target_ms // 4)
            else:
                _expected_massive_ms = 0
                _effective_target = target_ms

            # ROOT-LEVEL always_first: play ONCE before all cycles (not per cycle)
            _picked_raf = _pick_af_al(root_always_first, rng)
            if _picked_raf:
                try:
                    _raf_events = json.load(open(_picked_raf, encoding='utf-8'))
                    _raf_events = filter_problematic_keys(_raf_events)
                    if _raf_events:
                        _raf_base = min(e.get('Time', 0) for e in _raf_events)
                        for _e in _raf_events:
                            _ne = {**_e}
                            _ne['Time'] = _e['Time'] - _raf_base
                            stringed_events.append(_ne)
                        _raf_end = stringed_events[-1]['Time']
                        all_file_info_with_times.append(
                            (0.0, f"[ALWAYS FIRST] {_picked_raf.name}", _raf_end)
                        )
                        # Advance timeline tracker so first cycle gets proper buffer
                        total_pre_file += rng.uniform(500.0, 800.0) * mult
                except Exception as _e:
                    print(f"  [!] Root always_first load error: {_e}")

            while True:
                combo = tracker.get_next_combination()
                if not combo:
                    break
                
                # Track this combination signature (format folder numbers cleanly)
                combo_signature = "|".join(
                    f"F{int(fn) if fn == int(fn) else fn}=" +
                    "+".join(_combo_fp_sig(fp, i) for i, fp in enumerate(fl if isinstance(fl, list) else [fl]))
                    for fn, fl in combo
                )
                folder_combinations_used.append(combo_signature)
                
                # BUILD CYCLE (F1 -> F2 -> F3) WITHOUT features
                # Folder is click-sensitive if ANY subfolder in this folder is tagged,
                # OR if the main folder name contains a click-sensitive tag.
                # Belt-and-suspenders: check the name directly so that if the
                # is_click_sensitive flag ever fails to propagate through the subfolder
                # dicts (e.g. after specific-folders filtering), the feature is still
                # correctly suppressed for all cycles in this folder.
                _fn_lower = folder_name.lower()
                _name_click_sensitive = (
                    'click sensitive'      in _fn_lower or
                    'click/time sensitive' in _fn_lower or
                    'click+time sensitive' in _fn_lower or
                    'click time sensitive' in _fn_lower
                )
                # folder_is_click_sensitive = ONLY the main folder name tag.
                # Per-subfolder click-sensitivity is handled slot-by-slot inside
                # add_file_to_cycle (slot_is_click_sensitive). This prevents one
                # click-sensitive subfolder (e.g. F6) from suppressing features
                # for all other normal subfolders (F1-F5, F7-F8) in the same cycle.
                folder_is_click_sensitive = _name_click_sensitive
                # Distractions: Raw and click-sensitive folders never get any
                if is_raw or folder_is_click_sensitive:
                    cycle_dist_chance = 0.0
                elif is_inef:
                    cycle_dist_chance = folder_dist_chance_inef
                else:
                    cycle_dist_chance = folder_dist_chance_normal
                # Flat/single-subfolder: always_first only on cycle 0,
                # always_last suppressed here (injected once after loop ends)
                # If root_always_first/last are set, they fire in the outer loop
                # (before/after the while True). Suppress subfolder-level always_first/last
                # to prevent double-firing for flat folders where both scanners find the
                # same files.
                _has_root_af = bool(root_always_first)
                _has_root_al = bool(root_always_last)
                _play_af = ((not _is_flat_folder) or (_cycle_count == 0)) and not _has_root_af
                _play_al = (not _is_flat_folder) and not _has_root_al   # always_last injected after loop
                cycle_result = string_cycle(
                    subfolder_files, combo, rng,
                    distraction_files=dist_queue,
                    distraction_chance=cycle_dist_chance,
                    is_click_sensitive=folder_is_click_sensitive,
                    play_always_first=_play_af,
                    play_always_last=_play_al,
                    mult=mult
                )
                _cycle_count += 1
                
                cycle_events = cycle_result['events']
                file_info = cycle_result['file_info']
                
                if not cycle_events:
                    break
                
                # APPLY FEATURES to ENTIRE cycle
                cycle_with_features, stats = apply_cycle_features(
                    cycle_events, rng, is_raw, is_inef=is_inef,
                    is_click_sensitive=folder_is_click_sensitive, mult=mult
                )
                
                # Check if adding would exceed target
                current_duration = stringed_events[-1]['Time'] if stringed_events else 0
                cycle_duration = cycle_with_features[-1]['Time'] if cycle_with_features else 0
                
                # Add INEFFICIENT Before File Pause (only for inefficient files, only if file >= 25 sec)
                inter_cycle_pause = 0
                if stringed_events:
                    # PRE-PLAY BUFFER BETWEEN CYCLES (all file types)
                    # The intra-cycle add_file_to_cycle buffer fires for files WITHIN a cycle,
                    # but the very first file of each new cycle has files_added=0 so gets no buffer.
                    # Without this, the last DragEnd of cycle N and the cursor transition of cycle
                    # N+1 share the same timestamp -> the game reads them as simultaneous ->
                    # cursor teleports while button is still held -> drag-click at wrong position.
                    _cycle_gap = rng.uniform(500.0, 800.0)
                    inter_cycle_pause += int(_cycle_gap)
                    total_pre_file += _cycle_gap

                    # Add cursor transition for raw/normal file types during the inter-cycle gap.
                    # Inef skips this block — its transition is handled below in the inef block,
                    # which covers the full 10-30s pause with a slow drift. Running both blocks
                    # would: (1) move cursor to destination immediately in block 1, then (2) find
                    # distance≈0 in block 2, generating no drift at all during the long pause.
                    if not folder_is_click_sensitive and not is_inef:
                        _ic_last_x, _ic_last_y = None, None
                        for _e in reversed(stringed_events):
                            if _e.get('X') is not None and _e.get('Y') is not None:
                                _ic_last_x, _ic_last_y = int(_e['X']), int(_e['Y'])
                                break
                        _ic_first_x, _ic_first_y = None, None
                        for _e in cycle_with_features:
                            if _e.get('X') is not None and _e.get('Y') is not None:
                                _ic_first_x, _ic_first_y = int(_e['X']), int(_e['Y'])
                                break
                        if (_ic_last_x is not None and _ic_first_x is not None
                                and (_ic_last_x != _ic_first_x or _ic_last_y != _ic_first_y)):
                            _ic_base = stringed_events[-1]['Time']
                            _ic_path = generate_human_path(
                                _ic_last_x, _ic_last_y, _ic_first_x, _ic_first_y,
                                int(_cycle_gap), rng
                            )
                            _IC_SNAP_ADVANCE = 50  # ms: snap lands this far before cycle start
                            for _rt, _px, _py in _ic_path[:-1]:
                                if _rt < int(_cycle_gap) - _IC_SNAP_ADVANCE:
                                    stringed_events.append({
                                        'Type': 'MouseMove',
                                        'Time': _ic_base + _rt,
                                        'X': _px, 'Y': _py
                                    })
                            # SNAP: explicit final position so cursor is exactly
                            # on the click target before the new cycle begins.
                            # Mirrors the within-cycle snap in add_file_to_cycle.
                            stringed_events.append({
                                'Type': 'MouseMove',
                                'Time': _ic_base + int(_cycle_gap) - _IC_SNAP_ADVANCE,
                                'X': _ic_first_x,
                                'Y': _ic_first_y
                            })
                            total_transitions += int(_cycle_gap)

                if stringed_events and is_inef:
                    # Check file length: Only apply if file is >= 25 seconds (25000ms)
                    file_duration = cycle_duration  # Current cycle duration in ms
                    if file_duration >= 25000:
                        # INEFFICIENT Before File Pause: 10-30 seconds (10000-30000ms)
                        # Random, not rounded, no multiplier applied
                        inter_cycle_pause = min(int(rng.uniform(10000.0, 30000.0)), _MAX_SINGLE_PAUSE_MS)
                        total_inter += inter_cycle_pause

                    # Add slow cursor drift covering the full inef pause.
                    # FIX (v3.18.75): _trans_base uses current_duration (real end of previous
                    # cycle content), not stringed_events[-1]['Time']. The old code pointed to
                    # the tail of any idle-movement events that extend beyond current_duration,
                    # causing drift events to start late and overlap with the next cycle after
                    # sort. Using current_duration anchors the drift correctly at the cycle
                    # boundary. Block-1 is now skipped for inef (see above), so
                    # stringed_events[-1] is still at current_duration when we arrive here —
                    # but using current_duration explicitly is safer and self-documenting.
                    last_x, last_y = None, None
                    for e in reversed(stringed_events):
                        if e.get('X') is not None and e.get('Y') is not None:
                            last_x, last_y = int(e['X']), int(e['Y'])
                            break

                    first_x, first_y = None, None
                    for e in cycle_with_features:
                        if e.get('X') is not None and e.get('Y') is not None:
                            first_x, first_y = int(e['X']), int(e['Y'])
                            break

                    if last_x is not None and first_x is not None and (last_x != first_x or last_y != first_y):
                        _trans_base = current_duration  # FIX: anchor at cycle boundary, not after idle events
                        _INEF_SNAP_ADVANCE = 200  # ms: snap well before cycle start (inef gap is 10-30s)
                        transition_path = generate_human_path(
                            last_x, last_y, first_x, first_y,
                            inter_cycle_pause, rng
                        )
                        for rel_time, x, y in transition_path[:-1]:
                            if rel_time < inter_cycle_pause - _INEF_SNAP_ADVANCE:
                                stringed_events.append({
                                    'Type': 'MouseMove',
                                    'Time': _trans_base + rel_time,
                                    'X': x,
                                    'Y': y
                                })
                        # SNAP: cursor settles exactly on the next cycle's first
                        # click target 200ms before the new cycle begins.
                        if inter_cycle_pause > _INEF_SNAP_ADVANCE:
                            stringed_events.append({
                                'Type': 'MouseMove',
                                'Time': _trans_base + inter_cycle_pause - _INEF_SNAP_ADVANCE,
                                'X': first_x,
                                'Y': first_y
                            })
                
                potential_total = current_duration + inter_cycle_pause + cycle_duration
                margin = int(_effective_target * 0.05)
                if potential_total > _effective_target + margin and stringed_events:
                    break
                
                # Add cycle to merged events
                offset = current_duration + inter_cycle_pause
                for e in cycle_with_features:
                    new_event = {**e}
                    new_event['Time'] = e['Time'] + offset
                    stringed_events.append(new_event)
                
                # Track file info with cumulative timeline.
                # Correct end times for pauses added by apply_cycle_features:
                # each pause_pivot (raw_t, amount) shifts all files whose raw end
                # time >= raw_t forward by amount. Both pivots are in cycle-raw space.
                _pp = stats.get('pause_pivots', [])
                for folder_num, filename, end_time_in_cycle in file_info:
                    _corr = end_time_in_cycle + sum(
                        _pa for _pt, _pa in _pp if _pt <= end_time_in_cycle
                    )
                    actual_end_time = _corr + offset
                    all_file_info_with_times.append((folder_num, filename, actual_end_time))
                
                # Update stats
                total_intra += stats['intra_pauses']
                total_idle += stats['idle_movements']
                jitter_pct = stats['jitter_percentage']
                
                # NEW: Accumulate pre-file pause, post-pause, and transition times
                total_pre_file += cycle_result.get('pre_pause_total', 0)
                total_transitions += cycle_result.get('transition_total', 0)
                total_snap_gap += cycle_result.get('snap_gap_total', 0)
                total_dist_pause += cycle_result.get('distraction_pause_total', 0)
                
                if len(all_file_info_with_times) > 2000:  # Safety limit (increased from 150)
                    break
            
            # Flat/single-subfolder: inject always_last once at the very end
            if _is_flat_folder and stringed_events:
                _only_fn  = next(iter(subfolder_files))
                _only_fd  = subfolder_files[_only_fn]
                _al_file  = _pick_af_al(_only_fd.get('always_last', []), rng)
                if _al_file:
                    _al_events = json.load(open(_al_file, encoding='utf-8'))
                    _al_events = filter_problematic_keys(_al_events)
                    if _al_events:
                        _al_base  = min(e.get('Time', 0) for e in _al_events)
                        _al_start = stringed_events[-1]['Time'] if stringed_events else 0
                        # Pre-play buffer before always_last
                        _al_buf   = rng.uniform(500.0, 800.0)
                        _al_start += _al_buf
                        total_pre_file += _al_buf
                        for _e in _al_events:
                            _ne = {**_e}
                            _ne['Time'] = _e['Time'] - _al_base + _al_start
                            stringed_events.append(_ne)
                        _al_end = stringed_events[-1]['Time']
                        all_file_info_with_times.append(
                            (_only_fn, f"[ALWAYS LAST] {_al_file.name}", _al_end)
                        )

            # ROOT-LEVEL always_last: play ONCE after all cycles
            _picked_ral = _pick_af_al(root_always_last, rng)
            if _picked_ral and stringed_events:
                try:
                    _ral_events = json.load(open(_picked_ral, encoding='utf-8'))
                    _ral_events = filter_problematic_keys(_ral_events)
                    if _ral_events:
                        _ral_base  = min(e.get('Time', 0) for e in _ral_events)
                        _ral_buf   = rng.uniform(500.0, 800.0) * mult
                        _ral_start = stringed_events[-1]['Time'] + _ral_buf
                        total_pre_file += _ral_buf
                        for _e in _ral_events:
                            _ne = {**_e}
                            _ne['Time'] = _e['Time'] - _ral_base + _ral_start
                            stringed_events.append(_ne)
                        _ral_end = stringed_events[-1]['Time']
                        all_file_info_with_times.append(
                            (0.0, f"[ALWAYS LAST] {_picked_ral.name}", _ral_end)
                        )
                except Exception as _e:
                    print(f"  [!] Root always_last load error: {_e}")

            if not stringed_events:
                print(f"  [!]?  Version {v_letter}: no events built (all combos exceeded target or no valid combo) - skipping")
                continue
            
            # Add massive pause for INEFFICIENT
            if is_inef and len(stringed_events) > 1:
                stringed_events, massive_pause_ms, split_idx = insert_massive_pause(stringed_events, rng)  # mult not applied
                
                # FIX (v3.19.03): Correct file end-times after massive pause.
                # CRITICAL: read split_time BEFORE the shift by recovering the
                # pre-shift timestamp: events[split_idx].Time is now post-shift,
                # so subtract massive_pause_ms to get the original split point.
                # The old code used the post-shift split_time directly, so every
                # file end-time (pre-shift values) compared as less-than the
                # inflated split_time and received zero correction.
                if massive_pause_ms > 0 and 0 <= split_idx < len(stringed_events):
                    split_time_pre_shift = (
                        stringed_events[split_idx]['Time'] - massive_pause_ms
                    )
                    updated_file_info = []
                    for folder_num, filename, end_time in all_file_info_with_times:
                        if end_time >= split_time_pre_shift:
                            # File ends at or after the split → shift forward
                            updated_file_info.append(
                                (folder_num, filename, end_time + massive_pause_ms)
                            )
                        else:
                            # File ends before the split → unaffected
                            updated_file_info.append(
                                (folder_num, filename, end_time)
                            )
                    all_file_info_with_times = updated_file_info
            
            # Calculate total duration
            total_duration = stringed_events[-1]['Time']
            total_min = int(total_duration / 60000)
            total_sec = int((total_duration % 60000) / 1000)
            
            # File prefix and name
            if is_raw:
                prefix = "^"
            elif is_inef:
                prefix = "\u00ac\u00ac"
            else:
                prefix = ""
            
            v_code = f"{folder_number}_{v_letter}"
            fname = f"{prefix}{v_code}_{total_min}m{total_sec}s_({_effective_bid}).json"
            
            # CRITICAL FIXES before saving:
            # 1. Convert Click events to LeftDown+LeftUp pairs (prevents clamp)
            # 2. Sort all events by Time (prevents out-of-order gaps)
            stringed_events = fix_click_events(stringed_events)
            # Round all Times to int (rng.uniform() produces floats) and ensure non-negative
            for e in stringed_events:
                if 'Time' in e:
                    e['Time'] = max(0, int(round(e['Time'])))
            stringed_events = sorted(stringed_events, key=lambda e: e.get('Time', 0))
            
            # Save file
            (out_folder / fname).write_text(json.dumps(stringed_events, separators=(',', ':')))
            
            # DEBUG: Show created file
            type_label = "RAW" if is_raw else ("INEF" if is_inef else "NORM")
            print(f"     ? Created: {fname:<30s} [{type_label}]")
            
            # Build manifest entry
            separator = "=" * 40
            version_label = f"Version {prefix}{v_code}_{total_min}m{total_sec}s:"
            
            # Compute totals for all three types
            if is_raw:
                _intra_show = 0; _inter_show = 0; _massive_show = 0
            elif is_inef:
                original_inter = int(total_inter / mult) if mult > 0 else total_inter
                _intra_show = total_intra; _inter_show = total_inter; _massive_show = massive_pause_ms
            else:  # normal
                _intra_show = total_intra; _inter_show = 0; _massive_show = 0

            total_pause = (total_intra + total_pre_file + total_transitions
                           + total_snap_gap + total_dist_pause
                           + _inter_show + _massive_show)

            file_type_label = "Raw" if is_raw else ("Inefficient" if is_inef else "Normal")
            manifest_entry = [
                separator,
                "",
                version_label,
                f"FILE TYPE: {file_type_label}",
                f"  Total PAUSE ADDED: {format_ms_precise(total_pause)} (x{mult} Multiplier)",
                "",
                f"BREAKDOWN (x = mult applied, - = flat no mult):",
                f"                x PRE-Play Buffer: {format_ms_precise(total_pre_file)}",
                f"                x Within File Pauses: {format_ms_precise(_intra_show)}",
                f"                x CURSOR to Start Point: {format_ms_precise(total_transitions)}",
                f"                - POST-SNAP GAP: {format_ms_precise(total_snap_gap)}",
                f"                - DISTRACTION File Pause: {format_ms_precise(total_dist_pause)}",
                f"                - INEFFICIENT Before File Pause: {format_ms_precise(_inter_show)}",
                f"                - INEFFICIENT MASSIVE PAUSE: {format_ms_precise(_massive_show)}",
                ""
            ]
            
            # Add file list with F-number prefix and cumulative timeline
            for folder_num, filename, end_time in all_file_info_with_times:
                # F-number prefix: skip for root-level (folder_num==0) and
                # bracket-tagged entries ([ALWAYS FIRST], [DISTRACTION], etc.)
                if folder_num and folder_num != 0.0 and not filename.startswith('['):
                    _fn_label = str(int(folder_num) if folder_num == int(folder_num) else folder_num)
                    f_prefix = f"F{_fn_label}- "
                else:
                    f_prefix = ""
                manifest_entry.append(f"  * {f_prefix}{filename} (Ends at {format_ms_precise(end_time)})")
            
            manifest_lines.extend(manifest_entry)
        
        # ── POST-LOOP CHAT INSERT ─────────────────────────────────────────
        # All strung .json files are now saved. Pick floor(total * 0.20) at
        # random — all file types eligible — and splice one chat file into each.
        if chat_files and not args.no_chat:
            _strung = sorted(
                p for p in out_folder.iterdir()
                if p.suffix == '.json'
                and not p.name.startswith('!')
                and not p.name.startswith('@')
                and not p.name.startswith('-')
            )
            _n_chat = int(len(_strung) * 0.20)  # floor(20%)
            if _n_chat > 0:
                _targets = rng.sample(_strung, _n_chat)
                print(f"   Chat inserts: {_n_chat}/{len(_strung)} file(s) selected")
                for _ct in _targets:
                    try:
                        _cevs = json.loads(_ct.read_text(encoding='utf-8'))
                        _csrc = rng.choice(chat_files)
                        _rchat = json.loads(_csrc.read_text(encoding='utf-8'))
                        if not _cevs or not _rchat:
                            continue
                        _cb = min(e.get('Time', 0) for e in _rchat)
                        _cdur = max(e.get('Time', 0) for e in _rchat) - _cb
                        if len(_cevs) >= 6:
                            _ins = rng.randint(len(_cevs) // 3, (2 * len(_cevs)) // 3)
                        else:
                            _ins = len(_cevs) // 2
                        _it = _cevs[_ins]['Time']
                        for _e in _cevs[_ins:]:
                            _e['Time'] += _cdur
                        _merged = sorted(
                            _cevs[:_ins]
                            + [{**_e, 'Time': _it + (_e.get('Time', 0) - _cb)} for _e in _rchat]
                            + _cevs[_ins:],
                            key=lambda _e: _e.get('Time', 0)
                        )
                        _ct.write_text(json.dumps(_merged, separators=(',', ':')))
                        print(f"     +CHAT {_ct.name} <- {_csrc.name}"
                              f" at ~{_it//60000}m{(_it%60000)//1000}s")
                        # Update manifest end-times for this file:
                        # any all_file_info entry whose name contains this file's
                        # stem gets its end time extended by the chat duration.
                        _ct_name = _ct.name
                        all_file_info_with_times = [
                            (fn, fnm,
                             et + _cdur if _ct_name in fnm else et)
                            for fn, fnm, et in all_file_info_with_times
                        ]
                    except Exception as _ce:
                        print(f"     [!] Chat insert failed ({_ct.name}): {_ce}")
            else:
                print(f"   Chat: 0 inserts ({len(_strung)} file(s), floor(20%)=0)")

        # Write manifest
        manifest_path = out_folder / f"!_MANIFEST_{folder_number}_!.txt"
        manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")
        print(f"\n   Manifest written: {manifest_path.name}")

        # SEQUENCE REUSED: now that tracker exists and all versions + manifest are written,
        # rename the output folder on disk if the combination fallback fired at any point.
        # Must happen AFTER manifest write so the path is valid before we rename.
        if tracker._sequence_reused:
            _reused_name = f"SEQUENCE REUSED {output_folder_name}"
            _new_out_folder = bundle_dir / _reused_name
            try:
                out_folder.rename(_new_out_folder)
                out_folder = _new_out_folder
                output_folder_name = _reused_name
                print(f"  [!] SEQUENCE REUSED — folder renamed to: {_reused_name}")
            except Exception as _re:
                print(f"  [!] SEQUENCE REUSED — could not rename folder: {_re}")

        # Collect combinations for this folder (for bundle-level file)
        # Use the combinations we tracked during THIS RUN
        if folder_combinations_used:
            bundle_combinations[cleaned_folder_name] = folder_combinations_used
        files_written = len(folder_combinations_used)
        print(f"  [OK] Folder done: {output_folder_name} - {files_written} version(s) written")
    
    # Write ONE combination file at SAME LEVEL as bundle folder
    if bundle_combinations:
        combo_file = output_root / f"COMBINATION_HISTORY_{args.bundle_id}.txt"
        try:
            with open(combo_file, 'w') as f:
                f.write(f"=== BUNDLE {args.bundle_id} COMBINATION HISTORY ===\n\n")
                
                for folder_name in sorted(bundle_combinations.keys()):
                    combos = bundle_combinations[folder_name]
                    f.write(f"[{folder_name}]\n")
                    for combo in combos:
                        f.write(f"{combo}\n")
                    f.write(f"\n")
            
            total_combos = sum(len(c) for c in bundle_combinations.values())
            print(f"\n Combination file written: {combo_file.name}")
            print(f"   Total combinations: {total_combos} across {len(bundle_combinations)} folders")
        except Exception as e:
            print(f"\n[!]?  Could not write combination file: {e}")

    # Clean up temporary distraction files (used only for inline splicing, not saved to bundle)
    if _dist_tmpdir:
        import shutil as _shutil
        try:
            _shutil.rmtree(_dist_tmpdir, ignore_errors=True)
        except Exception:
            pass

    print("\n" + "="*70)
    print(f"[OK] STRING MACROS COMPLETE - Bundle {args.bundle_id}")
    print(f" Output: {bundle_dir}")
    print(f"\n To track combinations:")
    print(f"   1. Upload COMBINATION_HISTORY_{args.bundle_id}.txt to:")
    print(f"      input_macros/combination_history/")
    print(f"   2. Code will read ALL .txt files and avoid duplicates")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
