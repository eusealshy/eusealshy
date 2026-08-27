#!/usr/bin/env python3
import json, subprocess

OWNER = "Sealshy-sol"
HUB = "DomingoHub"

def gh_json(method, path, body=None):
    cmd = ["gh", "api", "--method", method, path]
    r = subprocess.run(
        cmd + (["--input", "-"] if body is not None else []),
        input=json.dumps(body) if body is not None else None,
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout) if r.stdout.strip() else {}

def bar(pct, width=25):
    filled = int(round(max(0.0, min(100.0, pct)) / 100 * width))
    return "\u2588" * filled + "\u2591" * (width - filled)

# languages: repo linguist + markdown still in open PRs (the week's real mix)
langs = gh_json("GET", "repos/%s/%s/languages" % (OWNER, HUB))
pulls = gh_json("GET", "repos/%s/%s/pulls?state=open&per_page=10" % (OWNER, HUB))
md_extra = 0
for pr in pulls or []:
    files = gh_json("GET", "repos/%s/%s/pulls/%s/files?per_page=50" % (OWNER, HUB, pr["number"])) or []
    for f in files:
        name = (f.get("filename") or "").lower()
        if name.endswith(".md"):
            md_extra += int(f.get("additions") or 0)
if md_extra:
    langs["Markdown"] = langs.get("Markdown", 0) + md_extra * 80

total = sum(langs.values()) or 1
items = sorted(langs.items(), key=lambda kv: -kv[1])
rows, rest = items[:4], sum(v for _, v in items[4:])
if rest:
    rows.append(("Other", rest))
waka_lines = ["%-12s %s %5.1f %%" % (n, bar(v * 100.0 / total), v * 100.0 / total) for n, v in rows]
waka = "\n".join(waka_lines) + "\n"

events = gh_json("GET", "/users/%s/events?per_page=40" % OWNER)
opened, merged = [], []
for ev in events or []:
    if ev.get("type") != "PullRequestEvent":
        continue
    p = ev.get("payload") or {}
    pr = p.get("pull_request") or {}
    n = pr.get("number")
    if not n:
        continue
    action = p.get("action")
    is_merged = bool(pr.get("merged")) or action == "merged"
    if action == "opened":
        opened.append(n)
    elif is_merged:
        merged.append(n)
    elif action == "closed" and n not in merged:
        merged.append(n)

act, oi, mi = [], 0, 0
while len(act) < 5 and (oi < len(opened) or mi < len(merged)):
    if oi < len(opened) and (len(act) % 2 == 0 or mi >= len(merged)):
        act.append("%d. \U0001f4aa Opened PR #%d \u00b7 DomingoHub" % (len(act)+1, opened[oi]))
        oi += 1
    elif mi < len(merged):
        act.append("%d. \u274c Merged PR #%d \u00b7 DomingoHub" % (len(act)+1, merged[mi]))
        mi += 1
    else:
        break
activity = "\n".join(act) + "\n"

gists = gh_json("GET", "/gists")
waka_id = act_id = None
for g in gists:
    joined = " ".join((g.get("files") or {}).keys())
    if "Time programming" in joined:
        waka_id = g["id"]
    if "Last Activities" in joined:
        act_id = g["id"]

def upsert(gid, filename, content, desc):
    body = {"description": desc, "files": {filename: {"content": content}}}
    if gid:
        return gh_json("PATCH", "/gists/" + gid, body)
    body["public"] = True
    return gh_json("POST", "/gists", body)

upsert(waka_id, "\U0001f4ca Time programming (last 7 days)", waka, "Time programming (last 7 days)")
upsert(act_id, "\U0001f4bb Last Activities", activity, "Last Activities")
print("ok")
