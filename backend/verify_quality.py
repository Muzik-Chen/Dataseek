"""
数据质量验证 — 检查 3 套方案的天数/完整性。
"""
import asyncio
import json
import time
import sys
sys.path.insert(0, ".")

from ai.trip_agent import generate_three_plans

async def test():
    params = {
        "origin": "北京",
        "days": 3,
        "crowd_type": "family",
        "interests": ["food", "culture"],
        "budget": "mid",
    }
    print(f"Params: {json.dumps(params, ensure_ascii=False)}")
    print("Generating 3 plans...")
    t0 = time.time()
    plans = await generate_three_plans(params)
    elapsed = time.time() - t0
    print(f"\n=== {len(plans)} plans in {elapsed:.1f}s ===\n")

    all_good = True
    for p in plans:
        pid = p.get("plan_id", "?")
        title = p.get("title", "?")
        error = p.get("error", False)
        days = p.get("days", [])
        hotels = p.get("hotels", [])
        tips = p.get("tips", [])

        issues = []
        # Day count check
        if len(days) != params["days"]:
            issues.append(f"DAYS: expected {params['days']}, got {len(days)}")
        # Empty activities check
        for d in days:
            if not d.get("activities"):
                issues.append(f"Day {d.get('day','?')}: no activities")
            elif len(d["activities"]) < 2:
                issues.append(f"Day {d.get('day','?')}: only {len(d['activities'])} activities")
        # Hotels check
        if len(hotels) < 2:
            issues.append(f"HOTELS: only {len(hotels)} tiers")
        # Tips check
        if len(tips) < 2:
            issues.append(f"TIPS: only {len(tips)}")

        status = "PASS" if not issues and not error else "FAIL"
        if status == "FAIL":
            all_good = False
        print(f"[{status}] Plan {pid}: {title}")
        print(f"  Days: {len(days)} | Hotels: {len(hotels)} | Tips: {len(tips)} | Error: {error}")
        for d in days:
            n_acts = len(d.get("activities", []))
            print(f"    Day {d.get('day','?')}: {d.get('title','?')} ({n_acts} activities)")
        if issues:
            for i in issues:
                print(f"  [ISSUE] {i}")
        print()

    print("=" * 40)
    print("OVERALL: PASS" if all_good else "OVERALL: FAIL - some plans have issues")

asyncio.run(test())
