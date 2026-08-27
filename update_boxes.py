#!/usr/bin/env python3
import json, subprocess, urllib.request, os

OWNER = "Sealshy-sol"
HUB = "DomingoHub"

def gh_json(method, path, body=None):
    cmd = ["gh", "api", "--method", method, path]
    if body is not None:
        cmd += ["--input", "-"]
        r = subprocess.run(cmd, input=json.dumps(body), capture_output=True, text=True)
    else:
        r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout) if r.stdout.strip() else {}

def bar(pct, width=25):
    filled = int(round(max(0, min(100, pct)) / 100 * width))
    return "\u2588" * filled + "\u2591" * (width - filled)

langs = gh_json("GET", "repos/%s/%s/languages" % (OWNER, HUB))
total = sum(langs.values()) or 1
# top 4 + other
items = sorted(langs.items(), key=lambda kv: -kv[1])
top = items[:4]
rest = sum(v for _, v in items[4:])
rows = [(n, v) for n, v in top]
if rest:
    rows.append(("Other", rest))

waka_lines = []
for name, n in rows:
    pct = n * 100.0 / total
    waka_lines.append("%-12s %s %5.1f %%" % (name, bar(pct), pct))
waka = "\n".join(waka_lines) + "\n"

events = gh_json("GET", "/users/%s/events?per_page=40" % OWNER)
act = []
for ev in events:
    if ev.get("type") != "PullRequestEvent":
        continue
    p = ev.get("payload") or {}
    pr = p.get("pull_request") or {}
    n = pr.get("number")
    if not n:
        continue
    action = p.get("action")
    merged = bool(pr.get("merged"))
    if action == "opened":
        line = "%d. \U0001f4aa Opened PR #%d \u00b7 DomingoHub" % (len(act) + 1, n)
    elif merged or action == "merged":
        line = "%d. \u274c Merged PR #%d \u00b7 DomingoHub" % (len(act) + 1, n)
    elif action == "closed":
        line = "%d. \u274c Closed PR #%d \u00b7 DomingoHub" % (len(act) + 1, n)
    else:
        continue
    act.append(line)
    if len(act) >= 5:
        break
activity = "\n".join(act) + "\n"

print("WAKA\n" + waka)
print("ACT\n" + activity)

# find existing boxes by filename
gists = gh_json("GET", "/gists")
waka_id = None
act_id = None
for g in gists:
    names = list((g.get("files") or {}).keys())
    joined = " ".join(names)
    if "Time programming" in joined:
        waka_id = g["id"]
    if "Last Activities" in joined:
        act_id = g["id"]

waka_file = "\U0001f4ca Time programming (last 7 days)"
act_file = "\U0001f4bb Last Activities"

def upsert(gid, filename, content, desc):
    body = {
        "description": desc,
        "files": {filename: {"content": content}},
    }
    if gid:
        return gh_json("PATCH", "/gists/" + gid, body)
    body["public"] = True
    return gh_json("POST", "/gists", body)

w = upsert(waka_id, waka_file, waka, "Time programming (last 7 days)")
a = upsert(act_id, act_file, activity, "Last Activities")
print("waka_gist", w.get("id"), w.get("html_url"))
print("act_gist", a.get("id"), a.get("html_url"))
print("waka_node", w.get("node_id"))
print("act_node", a.get("node_id"))
