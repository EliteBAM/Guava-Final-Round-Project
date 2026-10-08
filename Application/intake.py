"""
The intake sheet and the attorney's intake record, as schemas. One FieldSpec drives both the Guava field the agent
fills and where the value lands in the record.

Spec: Documents/Legal Intake Specialist Agent Notes/Story Stage Schema and Plan.md (fields, tiers, record shape).
Research: PI Intake Research.md (why each field is asked on the call, and what's deferred to the questionnaire).

Kept free of guava imports so it can be unit tested without credentials or a network.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

# Two tiers only. PIR 5 also has "opportunistic" (record if volunteered, never ask), but Guava resolves an optional
# field only by a value or the caller declining it, so a never-asked field has no way to resolve and once kept the
# task from completing live. Volunteered details are in the narrative; the rest go on the questionnaire (DEFERRED).
CRITICAL, IMPORTANT = "critical", "important"
UNSURE = ("yes", "no", "not_sure")

# the subset of Guava's FieldTypes the intake uses; a Literal so a typo is a type error, not a mid-call failure
FieldKind = Literal["text", "multiple_choice", "date"]


@dataclass(frozen=True)
class FieldSpec:
    key: str
    kind: FieldKind
    ask: str  # what to collect, in plain words (the Guava field description)
    tier: str
    section: str  # record section: incident | liability | injuries | coverage | parties
    choices: tuple[str, ...] = ()
    optional: bool = False  # a critical field that can legitimately stay empty (only applies sometimes)


NARRATIVE = FieldSpec(
    "narrative", "text",
    "Their account of what happened, in their own words. Let them finish before asking anything else, and "
    "acknowledge any injuries with care.",
    CRITICAL, "incident",
)

# common core, every case type: critical first, then important (PIR 2.1)
CORE = (
    FieldSpec("incident_type", "multiple_choice", "What kind of incident it was.", CRITICAL, "incident",
              ("motor_vehicle", "slip_and_fall", "medical_or_nursing_home", "other")),
    FieldSpec("incident_state", "multiple_choice", "Whether it happened in Florida or another state.", CRITICAL,
              "incident", ("florida", "other_state")),
    FieldSpec("incident_location", "text",
              "Where it happened: the city or county, and the street or intersection if they know it.",
              CRITICAL, "incident"),
    FieldSpec("injuries", "text", "Their injuries and symptoms, in their own words. Don't press for diagnoses.",
              CRITICAL, "injuries"),
    FieldSpec("treatment", "multiple_choice", "The medical care they've had so far, if any.", CRITICAL, "injuries",
              ("er_or_hospital", "doctor_or_urgent_care", "none_yet")),
    FieldSpec("first_treatment_date", "date", "The date they were first treated. Only ask if they've had treatment.",
              CRITICAL, "injuries", optional=True),
    FieldSpec("police_report", "multiple_choice", "Whether the police came or a police report was made.", CRITICAL,
              "liability", UNSURE),
    FieldSpec("government_involved", "multiple_choice",
              "Whether a government vehicle or property was involved, such as a city bus, police car, or public "
              "property.", CRITICAL, "parties", UNSURE),
    FieldSpec("other_parties", "text",
              "Anyone else involved whom they haven't already named, such as the other driver's employer, a "
              "business, or the property owner. Leave it empty if there's no one.", CRITICAL, "parties",
              optional=True),
    FieldSpec("still_treating", "multiple_choice", "Whether they're still getting treatment for their injuries.",
              IMPORTANT, "injuries", UNSURE),
    FieldSpec("missed_work", "multiple_choice", "Whether they've missed any work because of their injuries.",
              IMPORTANT, "injuries", ("yes", "no", "not_working")),
    FieldSpec("witnesses", "multiple_choice", "Whether anyone saw what happened.", IMPORTANT, "liability", UNSURE),
    FieldSpec("photos", "multiple_choice", "Whether anyone took photos or video of the scene, vehicles or injuries.",
              IMPORTANT, "liability", UNSURE),
    FieldSpec("insurer_contact", "multiple_choice",
              "Whether the other side's insurance company has contacted them, and if so whether they gave a "
              "statement.", IMPORTANT, "coverage", ("gave_statement", "contacted_only", "no_contact", "not_sure")),
    FieldSpec("prior_similar_injury", "multiple_choice",
              "Whether they've had a previous injury or injury claim involving the same part of the body. Ask gently "
              "and plainly; it's routine.", IMPORTANT, "injuries", UNSURE),
)

# motor-vehicle module (PIR 2.2, 3)
MVA = (
    FieldSpec("vehicle_role", "multiple_choice", "Their role in the accident.", CRITICAL, "incident",
              ("driver", "passenger", "pedestrian", "cyclist", "motorcyclist")),
    FieldSpec("other_vehicle", "multiple_choice",
              "What kind of vehicle hit them or caused the accident: a personal vehicle, a commercial or work "
              "vehicle such as a truck or van, a rideshare such as Uber or Lyft, or a driver who left the scene.",
              CRITICAL, "parties", ("personal", "commercial_or_work", "rideshare", "hit_and_run", "not_sure")),
    FieldSpec("on_the_job", "multiple_choice", "Whether they were working or driving for work at the time.",
              CRITICAL, "parties", ("yes", "no")),
    FieldSpec("seat_belt", "multiple_choice",
              "Whether they were wearing a seat belt. Ask it plainly, with no commentary on what it means.",
              IMPORTANT, "liability", ("yes", "no", "not_sure", "not_applicable")),
    FieldSpec("ambulance", "multiple_choice", "Whether they left the scene in an ambulance.", IMPORTANT, "injuries",
              ("yes", "no")),
    FieldSpec("other_insurer", "text", "The other driver's insurance company, if they know it.", IMPORTANT,
              "coverage"),
    FieldSpec("own_insurer", "text",
              "Their own auto insurance company. If they don't have auto insurance, write \"none\".", IMPORTANT,
              "coverage"),
    FieldSpec("um_coverage", "multiple_choice", "Whether their own policy includes uninsured motorist coverage.",
              IMPORTANT, "coverage", UNSURE),
)

# stub modules: the minimum the attorney needs; full questionnaires are a later phase (PIR 2.3, 2.4)
PREMISES = (
    FieldSpec("property_type", "multiple_choice", "What kind of property they were on.", CRITICAL, "parties",
              ("business", "residence", "government", "other")),
    FieldSpec("hazard", "text", "What caused them to fall, such as a spill, a broken step, or poor lighting.",
              CRITICAL, "liability"),
    FieldSpec("reported_to_staff", "multiple_choice", "Whether they told staff or the owner about the fall.",
              IMPORTANT, "liability", UNSURE),
    FieldSpec("incident_report", "multiple_choice", "Whether an incident report was made.", IMPORTANT, "liability",
              UNSURE),
)

MEDICAL = (
    FieldSpec("provider_name", "text", "The doctor, hospital, or facility involved.", CRITICAL, "parties"),
    # text, not date: callers give approximate times ("mid-October"), and a date field can't take them
    FieldSpec("discovery_date", "text",
              "Roughly when they first realized something had gone wrong. An approximate time is fine.", IMPORTANT,
              "injuries"),
)

# incident_type -> (Guava task id, module fields); "other" has no module
MODULES = {
    "motor_vehicle": ("details_mva", MVA),
    "slip_and_fall": ("details_premises", PREMISES),
    "medical_or_nursing_home": ("details_medical", MEDICAL),
}

# fields collected by earlier tasks that belong in the record
HEADER_KEYS = (
    "caller_name", "caller_full_name", "recording_consent", "recording_consent_final", "caller_type", "on_behalf_of",
    "adverse_parties", "incident_date", "represented",
)

ALL_SPECS = (NARRATIVE, *CORE, *MVA, *PREMISES, *MEDICAL)
ALL_KEYS = HEADER_KEYS + tuple(spec.key for spec in ALL_SPECS)

# collected after signing, on the client questionnaire, never on this call (PIR 1, 5)
DEFERRED = (
    "insurance policy numbers, limits and claim numbers",
    "resident relatives' auto insurance",
    "full list of medical providers, dates and bills",
    "employer and lost wages",
    "health insurance, Medicare and Medicaid",
    "prior accidents, claims and medical history in detail",
    "police agency and report number",
    "vehicle damage, towing and airbags",
    "date of birth",
    "photos, crash report and other documents",
)


# other_parties answers that mean "nobody else" or "don't know" rather than a name. Kept deliberately narrow: a name
# wrongly matched here would skip a conflict re-check, while a missed phrase only costs a pointless lookup.
NO_PARTY = re.compile(
    r"no|none|nobody|no one|noone|nothing|n/?a|unknown|not sure|(i )?don'?t know"
    r"|(none|nobody else|no one else|no other|there (was|were) no one)\b.*"
)


def named_parties(value) -> str:
    """The other_parties answer as a name to re-check, or "" when it means nobody or unknown."""
    text = " ".join((value or "").split())
    return "" if NO_PARTY.fullmatch(text.lower().strip(" .!,")) else text


def specs_for(incident_type) -> tuple[FieldSpec, ...]:
    """The fields asked on this call: narrative, core, and the matching module."""
    module = MODULES.get(incident_type, (None, ()))[1]
    return (NARRATIVE, *CORE, *module)


def _filled(value) -> bool:
    return value not in (None, "", {}, [])


def completeness(fields: dict, specs) -> dict:
    """Code-side audit: which fields the call didn't collect. "not_sure" / "unknown" count as collected."""
    def missing(tier):
        return [s.key for s in specs if s.tier == tier and not s.optional and not _filled(fields.get(s.key))]
    return {"critical_missing": missing(CRITICAL), "important_missing": missing(IMPORTANT)}


def _plain(value):
    """Guava date fields arrive as {"year", "month", "day"}; the record stores ISO dates."""
    if isinstance(value, dict) and {"year", "month", "day"} <= value.keys():
        return f"{value['year']:04d}-{value['month']:02d}-{value['day']:02d}"
    return value


def build_record(fields: dict, state: dict, call_id: str, created_at: datetime) -> dict:
    """The intake record for attorney review, grouped by what the attorney decides on (PIR takeaway 4)."""
    specs = specs_for(fields.get("incident_type"))
    sections = {name: {} for name in ("incident", "liability", "injuries", "coverage", "parties")}
    for spec in specs:
        if _filled(fields.get(spec.key)):
            sections[spec.section][spec.key] = _plain(fields[spec.key])
    sections["incident"]["date"] = _plain(fields.get("incident_date"))
    sections["parties"]["adverse"] = fields.get("adverse_parties")

    return {
        "call_id": call_id,
        "created_at": created_at.isoformat(timespec="seconds"),
        "disposition": state.get("disposition") or "partial_intake",
        "caller": {
            "name": fields.get("caller_full_name") or fields.get("caller_name"),
            "recording_consent": fields.get("recording_consent_final") or fields.get("recording_consent"),
            "caller_type": fields.get("caller_type"),
            "represented": fields.get("represented"),
        },
        "conflicts": {
            "status": state.get("conflict_status"),
            "names_checked": list(state.get("conflict_names", [])),
            "recheck": state.get("recheck_status", "not_needed"),
        },
        **sections,
        "flags": sorted(state.get("flags", ())),
        # the signing packet as sent on the call (main.send_documents); None when it wasn't sent
        "documents": state.get("documents"),
        "completeness": completeness(fields, specs),
        "deferred_to_questionnaire": list(DEFERRED),
    }
