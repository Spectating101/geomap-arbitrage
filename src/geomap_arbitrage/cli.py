from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .catalog import load_catalog, load_profile
from .citation_bridge import record_assessment
from .engine import rank_opportunities
from .geojson import ranked_to_geojson
from .planner import build_livelihood_plan

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE = REPO_ROOT / "examples" / "fixtures" / "profile.json"
DEFAULT_CATALOG = REPO_ROOT / "examples" / "fixtures" / "opportunities.json"
DEFAULT_AS_OF = "2026-08-24"


def _trace_summary(trace: dict[str, Any], include_bundle: bool) -> dict[str, Any]:
    if include_bundle:
        return trace
    return {key: value for key, value in trace.items() if key != "bundle"}


def _run(profile_path: str | Path, catalog_path: str | Path, as_of: str, *, cited: bool, include_bundle: bool):
    profile = load_profile(profile_path)
    catalog = load_catalog(catalog_path)
    ranked = rank_opportunities(profile, catalog, as_of=as_of)
    rows = []
    for row in ranked:
        body = row.as_dict()
        if cited:
            body["citation_engine"] = _trace_summary(record_assessment(profile, row.opportunity, row.assessment), include_bundle=include_bundle)
        rows.append(body)
    return profile, ranked, rows


def _human(rows: list[dict[str, Any]]) -> str:
    lines = []
    for index, row in enumerate(rows, start=1):
        opportunity = row["opportunity"]
        assessment = row["assessment"]
        surplus = assessment["estimated_monthly_surplus"]
        lines.append(f"{index:>2}. [{assessment['status']}] {opportunity['title']} — score {assessment['score']:.1f}")
        lines.append(f"    surplus range: {surplus['low']:.0f}-{surplus['high']:.0f} {surplus['currency']}/month; distance: {assessment['distance_km']:.1f} km")
        if assessment["blockers"]:
            lines.append("    blockers: " + " | ".join(assessment["blockers"]))
        if assessment["research_questions"]:
            lines.append("    research: " + assessment["research_questions"][0])
        trace = row.get("citation_engine")
        if trace:
            lines.append(f"    receipt: {trace.get('receiptRef')} bundle={trace.get('bundleFingerprint')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geomap", description="Map evidence-backed local economic opportunities to person/place constraints.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--profile", default=str(DEFAULT_PROFILE))
        p.add_argument("--catalog", default=str(DEFAULT_CATALOG))
        p.add_argument("--as-of", default=DEFAULT_AS_OF)

    demo = sub.add_parser("demo", help="Run the synthetic demonstration catalog.")
    add_common(demo)
    demo.add_argument("--json", action="store_true", dest="as_json")
    demo.add_argument("--uncited", action="store_true", help="Debug only: skip Citation Engine receipts.")
    demo.add_argument("--include-bundle", action="store_true")

    assess = sub.add_parser("assess", help="Rank one profile against an opportunity catalog.")
    add_common(assess)
    assess.add_argument("--json", action="store_true", dest="as_json")
    assess.add_argument("--uncited", action="store_true", help="Debug only: skip Citation Engine receipts.")
    assess.add_argument("--include-bundle", action="store_true")

    geojson = sub.add_parser("geojson", help="Export ranked opportunities as GeoJSON.")
    add_common(geojson)
    geojson.add_argument("--output", required=True)

    plan = sub.add_parser("plan", help="Build a small livelihood action plan from ranked opportunities.")
    add_common(plan)
    plan.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args(argv)

    if args.command in {"demo", "assess"}:
        _, _, rows = _run(args.profile, args.catalog, args.as_of, cited=not args.uncited, include_bundle=args.include_bundle)
        if args.as_json:
            print(json.dumps({"as_of": args.as_of, "results": rows}, indent=2, default=str))
        else:
            print(_human(rows))
        return 0

    if args.command == "geojson":
        profile = load_profile(args.profile)
        ranked = rank_opportunities(profile, load_catalog(args.catalog), as_of=args.as_of)
        body = ranked_to_geojson(ranked)
        Path(args.output).write_text(json.dumps(body, indent=2), encoding="utf-8")
        print(args.output)
        return 0

    if args.command == "plan":
        profile = load_profile(args.profile)
        ranked = rank_opportunities(profile, load_catalog(args.catalog), as_of=args.as_of)
        body = build_livelihood_plan(profile.id, ranked).as_dict()
        if args.as_json:
            print(json.dumps(body, indent=2))
        else:
            print(f"primary: {body['primary_opportunity_id']}")
            print(f"secondary: {body['secondary_opportunity_id']}")
            print("next actions:")
            for action in body["next_actions"]:
                print(f"- {action}")
        return 0

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
