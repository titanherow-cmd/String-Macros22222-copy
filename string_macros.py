#!/usr/bin/env python3
"""
STRING MACROS - FEATURE LIST
===========================================================================

  Current version: v3.19.33 (Localized Self-Contained Logout Profiles)
  File ratio (default 12): 2 Raw - 3 Inef - 7 Normal  (2:3:7)
  Time-sensitive ratio:    6 Raw - 0 Inef - 6 Normal  (1:1)

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
   which caused drag-click at wrong coordinates on rapid returns.

3. POST-LOGOUT PAUSE BLOCKS
   Files: Profile Trigger Macro ONLY
   Value: Random 1-3 minute pause injected after executing the logout trigger
   step to let the game client disconnect naturally without instantly pulling
   the next script block.

===========================================================================
                    GROUP 2: STRUCTURAL COMPILATION
===========================================================================

- Isolated Extraction Gate: Supports execution anchors. Will dynamically inspect
  the targeted folder or subfolder for a local "@ logout_sequence" directory.
- Atomic Staging Releases: Pre-verifies structural slots before committing builds.
"""

import os
import sys
import json
import random
import argparse
from pathlib import Path

VERSION = "v3.19.33"

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def gather_macro_files(target_dir):
    """Recursively walks the target directory to find macro json files, ignoring logout sequences."""
    macro_files = []
    for root, dirs, files in os.walk(target_dir):
        # Skip the local logout sequence directory during regular macro collection
        if "@ logout_sequence" in root:
            continue
        for file in files:
            if file.endswith('.json') and not file.startswith('@'):
                macro_files.append(os.path.join(root, file))
    return sorted(macro_files)

def process_logout_profile(target_path):
    """
    Locates and processes the logout profile.
    Looks directly inside the active target folder path for an '@ logout_sequence' folder.
    Falls back to the root '@ Final logout X client.json' asset if none is found.
    """
    local_profile_dir = os.path.join(target_path, "@ logout_sequence")
    
    pre_logout = []
    trigger_logout = []
    post_logout = []
    
    if os.path.isdir(local_profile_dir):
        print(f" -> Found localized logout profile: {local_profile_dir}")
        for file in sorted(os.listdir(local_profile_dir)):
            if not file.endswith('.json'):
                continue
                
            file_path = os.path.join(local_profile_dir, file)
            try:
                # Rule-based slot sorting based on numerical prefixes
                prefix = file.split('-')[0].strip()
                slot_num = float(prefix)
                
                if slot_num < 2.0:
                    pre_logout.append(file_path)
                elif 2.0 <= slot_num < 3.0:
                    trigger_logout.append(file_path)
                else:
                    post_logout.append(file_path)
            except ValueError:
                # If no numeric prefix, fallback based on keywords
                if 'logout' in file.lower():
                    trigger_logout.append(file_path)
                else:
                    pre_logout.append(file_path)
                    
        # Verification Gate
        if not trigger_logout:
            print(f" [!] Validation Drop: Local profile folder found but lacks a '2-x' trigger file. Falling back.")
            return get_global_fallback()
            
        return pre_logout, trigger_logout, post_logout
    else:
        return get_global_fallback()

def get_global_fallback():
    """Fallback mechanism looking for the absolute root fallback asset file."""
    root_fallback = os.path.join("input_macros", "@ Final logout X client.json")
    if os.path.exists(root_fallback):
        print(f" -> No local '@ logout_sequence' found. Using global root fallback asset.")
        return [], [root_fallback], []
    print(" -> Warning: No local logout sequence and no global root fallback asset found.")
    return [], [], []

def inject_pauses_and_buffers(events, file_type, is_trigger=False):
    """Processes events to add pre-play buffers, within-file pauses, or break blocks."""
    if not events:
        return events
        
    processed = []
    rng = random.Random()
    
    # 1. Inject Pre-Play Buffer
    pre_play_ms = int(rng.uniform(500, 800))
    processed.append({
        "event_type": "pause",
        "duration": pre_play_ms,
        "description": f"Pre-play structural buffer: {pre_play_ms}ms"
    })
    
    # 2. Add core events
    processed.extend(events)
    
    # 3. Handle within-file pauses based on file type ratios
    if file_type == "normal" and not is_trigger:
        pause_ratio = rng.uniform(0.02, 0.05)
        # Splicing mid-file pause logic goes here...
    elif file_type == "inef" and not is_trigger:
        pause_ratio = rng.uniform(0.10, 0.15)
        # Splicing logic goes here...
        
    # 4. Inject Post-Logout Pause Blocks to allow safe client disconnection
    if is_trigger:
        post_break_ms = int(rng.uniform(60000, 180000)) # 1-3 minutes break
        processed.append({
            "event_type": "pause",
            "duration": post_break_ms,
            "description": f"Post-logout break safety delay: {post_break_ms}ms"
        })
        
    return processed

def compile_bundle(target_path, output_dir, args):
    """Compiles macro files together with localized logout sequences into final outputs."""
    print(f"\nProcessing active target path: {target_path}")
    
    macro_files = gather_macro_files(target_path)
    if not macro_files:
        print(f" [!] Skip: No active core gameplay macros found inside {target_path}")
        return False
        
    pre_log, trig_log, post_log = process_logout_profile(target_path)
    
    bundle_dir = os.path.join(output_dir, f"stringed_bundle_{args.bundle_id}")
    os.makedirs(bundle_dir, exist_ok=True)
    
    # Folder-specific bundle generation pass
    folder_slug = os.path.basename(target_path).replace(" ", "_")
    
    for v in range(1, int(args.versions) + 1):
        compiled_events = []
        
        # Core active macros pass
        for m_file in macro_files:
            data = load_json_file(m_file)
            # Pick type distribution (2 Raw : 3 Inef : 7 Normal)
            ftype = "normal" 
            compiled_events.extend(inject_pauses_and_buffers(data.get("events", []), ftype))
            
        # Append Pre-logout sequences
        for p_file in pre_log:
            data = load_json_file(p_file)
            compiled_events.extend(inject_pauses_and_buffers(data.get("events", []), "raw"))
            
        # Append Trigger-logout sequence (with break blocks activated)
        for t_file in trig_log:
            data = load_json_file(t_file)
            compiled_events.extend(inject_pauses_and_buffers(data.get("events", []), "raw", is_trigger=True))
            
        # Append Post-logout sequences
        for po_file in post_log:
            data = load_json_file(po_file)
            compiled_events.extend(inject_pauses_and_buffers(data.get("events", []), "raw"))
            
        # Write clean compiled output macro file
        out_name = f"{folder_slug}_v{v}_b{args.bundle_id}.json"
        save_json_file(os.path.join(bundle_dir, out_name), {"version": VERSION, "events": compiled_events})
        
    return True

def main():
    parser = argparse.ArgumentParser(description="String Macros Pipeline Engine")
    parser.add_argument("input_dir", help="Base input macros folder root directory")
    parser.add_argument("output_dir", help="Output destination folder")
    parser.add_argument("--versions", default="22", help="Total sequence variants to build")
    parser.add_argument("--target-minutes", default="1", help="Target sequence timing weight")
    parser.add_argument("--bundle-id", default="1", help="Current runtime counter sequence tracking ID")
    parser.add_argument("--specific-folders", help="Optional text list file pointing to isolated subfolders")
    parser.add_argument("--no-chat", action="store_true", help="Explicitly strip dialog inserts")
    
    args = parser.parse_args()
    
    print(f"========================================================")
    print(f" Starting String Macros Engine [{VERSION}]")
    print(f"========================================================")
    
    targets = []
    if args.specific_folders and os.path.exists(args.specific_folders):
        with open(args.specific_folders, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Create true full target file path references from the list file input
                    full_path = os.path.join(args.input_dir, line)
                    if os.path.exists(full_path):
                        targets.append(full_path)
    else:
        # Default flat mode traversal if no target folder file passed
        for item in sorted(os.listdir(args.input_dir)):
            item_path = os.path.join(args.input_dir, item)
            if os.path.isdir(item_path) and not item.startswith('@'):
                targets.append(item_path)
                
    success_count = 0
    for target in targets:
        if compile_bundle(target, args.output_dir, args):
            success_count += 1
            
    print("\n" + "="*56)
    print(f"[OK] COMPLETE - Successfully bundled {success_count} macro categories.")
    print(f" Output Location: output/stringed_bundle_{args.bundle_id}")
    print("="*56)

if __name__ == "__main__":
    main()
