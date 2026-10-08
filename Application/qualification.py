"""
Qualification flags for the attorney (the `qualify` step in MVP Flow Design.md). Pure rules, no model, nothing spoken.

Flags only inform the attorney's review; intake never declines on them. The caller never hears a computed
deadline (RF Key takeaway 11).

Sources (Research Findings.md):
- Fla. Stat. 95.11(5)(a) via HB 837: 2-year negligence limit for causes accruing after 2023-03-24, 4 years on or
  before (RF 4.1). Whether the boundary day itself is "after" is unsettled, so it's flagged for review.
- Fla. Stat. 627.736(1)(a): PIP requires initial treatment within 14 days of a motor vehicle accident (RF 1.5).
- Government defendants need written pre-suit notice within 3 years (RF Key takeaway 6).
- M&M routes medical malpractice and nursing-home claims to RN screeners (RF 1.1 #7).
"""

from datetime import date, timedelta

HB_837_EFFECTIVE = date(2023, 3, 24)
SOL_URGENT_DAYS = 90
PIP_TREATMENT_DAYS = 14


def as_date(value) -> date | None:
    """Guava date fields arrive as {"year", "month", "day"}."""
    try:
        return date(value["year"], value["month"], value["day"])
    except (TypeError, KeyError, ValueError):
        return None


def add_years(start: date, years: int) -> date:
    try:
        return start.replace(year=start.year + years)
    except ValueError:  # Feb 29 -> Feb 28
        return start.replace(year=start.year + years, day=28)


def limitation_flags(incident: date, today: date) -> set[str]:
    flags = set()
    if abs((incident - HB_837_EFFECTIVE).days) <= 1:
        flags.add("sol_boundary_case")

    years = 2 if incident > HB_837_EFFECTIVE else 4
    days_left = (add_years(incident, years) - today).days
    if days_left < 0:
        flags.add("sol_expired_likely")
    elif days_left < SOL_URGENT_DAYS:
        flags.add("sol_urgent")
    return flags


def flags(fields: dict, today: date) -> set[str]:
    """`fields` maps field keys to Guava field values (missing keys / None are fine)."""
    result = set()
    incident = as_date(fields.get("incident_date"))
    first_treatment = as_date(fields.get("first_treatment_date"))
    incident_type = fields.get("incident_type")

    if incident:
        result |= limitation_flags(incident, today)

    if fields.get("treatment") == "none_yet":
        result.add("no_treatment")

    if incident_type == "motor_vehicle" and incident:
        untreated_too_long = fields.get("treatment") == "none_yet" and (today - incident).days > PIP_TREATMENT_DAYS
        treated_late = first_treatment is not None and (first_treatment - incident).days > PIP_TREATMENT_DAYS
        if untreated_too_long or treated_late:
            result.add("pip_14_day_risk")

    if incident_type == "medical_or_nursing_home":
        result.add("route_nurse_intake")
    if incident_type in ("slip_and_fall", "other"):
        result.add("non_mva_case_type")
    if fields.get("government_involved") == "yes":
        result.add("government_defendant")
    if fields.get("incident_state") == "other_state":
        result.add("out_of_state")
    return result
