"""Pure local validation policy v0.1; no credentials, cloud calls, or Ground Truth."""
from datetime import date
from decimal import Decimal, InvalidOperation
import re
import unicodedata

POLICY_VERSION = "0.1"
REQUIRED_FIELDS = ("VendorName", "InvoiceId", "InvoiceDate", "DueDate",
                   "SubTotal", "TotalTax", "InvoiceTotal")
AMOUNT_FIELDS = ("SubTotal", "TotalTax", "InvoiceTotal")
DATE_FIELDS = ("InvoiceDate", "DueDate")


def clean_text(value):
    return " ".join(unicodedata.normalize("NFC", value).split())


def absent(value):
    return value is None or isinstance(value, str) and not value.strip()


def amount(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("invalid amount type")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("invalid amount") from None
    if not result.is_finite():
        raise ValueError("nonfinite amount")
    return result


def normalized(field, value):
    if absent(value):
        return None
    if field in AMOUNT_FIELDS:
        try:
            return amount(value)
        except ValueError:
            return ("invalid_amount", str(value))
    return clean_text(value) if isinstance(value, str) else ("invalid_text_type", type(value).__name__)


def evaluate_records(records):
    """Return decisions in input order without changing records.

    Each record supplies unique nonempty record_id, raw/refined value dictionaries,
    and source_grounding_validated=True only after separate source checks.
    Unknown metadata is ignored. All seven fields are mandatory. Both members of
    a duplicate group are flagged. Results never constitute automatic approval.
    """
    identifiers = [record.get("record_id") for record in records]
    if (any(not isinstance(value, str) or not value.strip() for value in identifiers)
            or len(set(identifiers)) != len(identifiers)):
        raise ValueError("unique nonempty record IDs required")
    results = []
    duplicate_groups = {}
    for record in records:
        raw, refined = record.get("raw"), record.get("refined")
        if not isinstance(raw, dict) or not isinstance(refined, dict):
            raise ValueError("raw and refined dictionaries required")
        reasons = []
        if record.get("source_grounding_validated") is not True:
            reasons.append({"code": "source_grounding_not_validated"})
        amounts = {}
        for field in REQUIRED_FIELDS:
            value = refined.get(field)
            if absent(value):
                reasons.append({"code": "required_field_missing", "field": field})
            elif field in AMOUNT_FIELDS:
                try:
                    amounts[field] = amount(value)
                except ValueError:
                    reasons.append({"code": "invalid_amount", "field": field})
            elif not isinstance(value, str):
                reasons.append({"code": "invalid_text_type", "field": field})
            elif field in DATE_FIELDS:
                try:
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                        raise ValueError("non ISO date")
                    date.fromisoformat(value)
                except ValueError:
                    reasons.append({"code": "invalid_date", "field": field})
            if normalized(field, raw.get(field)) != normalized(field, value):
                reasons.append({"code": "raw_refined_disagreement", "field": field})
        if len(amounts) == 3 and amounts["SubTotal"] + amounts["TotalTax"] != amounts["InvoiceTotal"]:
            reasons.append({"code": "totals_inconsistent"})
        result = {"record_id": record["record_id"], "policy_version": POLICY_VERSION,
                  "status": "review_required" if reasons else "checks_passed",
                  "review_reasons": reasons, "automatic_approval": False}
        results.append(result)
        supplier, invoice_id = refined.get("VendorName"), refined.get("InvoiceId")
        if (record.get("source_grounding_validated") is True
                and isinstance(supplier, str) and not absent(supplier)
                and isinstance(invoice_id, str) and not absent(invoice_id)):
            # Conservative exact key: normalize Unicode/whitespace, preserve case/punctuation.
            key = (clean_text(supplier), clean_text(invoice_id))
            duplicate_groups.setdefault(key, []).append(result)
    for group in duplicate_groups.values():
        if len(group) > 1:
            for result in group:
                result["review_reasons"].append({
                    "code": "suspected_duplicate",
                    "matching_record_ids": [other["record_id"] for other in group
                                            if other["record_id"] != result["record_id"]],
                })
                result["status"] = "review_required"
    return results
