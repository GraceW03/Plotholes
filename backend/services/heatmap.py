descriptors = {"cave-in", "unsafe worksite", "crash cushion defect",
        "guard rail - street", "plate condition - open",
        "blocked - construction",  "line/marking - faded",
        "line/marking - after repaving", "strip paving",
        "plate condition - anti-skid", "plate condition - noisy",
        "wear & tear", "defective hardware", "defacement",
        "dumpster - construction waste",}

def calculate_severity(descriptor):
    """Calculate severity score (1–5) based on descriptor text"""

    # Highest severity (5) — immediate hazards or unsafe conditions
    high_severity = [
        "cave-in",
        "unsafe worksite",
        "crash cushion defect",
        "guard rail - street",
        "plate condition - open",
        "blocked - construction",
    ]

    # Medium-high severity (4) — structural or major damage issues
    medium_high = [
        "pothole",
        "depression maintenance",
        "failed street repair",
        "plate condition - shifted",
        "hummock",
        "rough, pitted or cracked roads",
    ]

    # Medium severity (3) — surface or marking problems
    medium = [
        "line/marking - faded",
        "line/marking - after repaving",
        "strip paving",
        "plate condition - anti-skid",
        "plate condition - noisy",
        "wear & tear",
    ]

    # Low severity (2) — mostly cosmetic or non-urgent issues
    low = [
        "defective hardware",
        "defacement",
        "dumpster - construction waste",
    ]

    text = (descriptor or "").lower().strip()

    if any(term.lower() in text for term in high_severity):
        return 5
    elif any(term.lower() in text for term in medium_high):
        return 4
    elif any(term.lower() in text for term in medium):
        return 3
    elif any(term.lower() in text for term in low):
        return 2
    else:
        # Default minimal severity if no match
        return 1


def create_heatmap():
  '''
  Input: list of open issues
    'unique_key': row.unique_key,
    'complaint_type': row.complaint_type,
    'descriptor': row.descriptor,
    'status': row.status,
    'borough': row.borough,
    'latitude': float(row.latitude) if row.latitude else None,
    'longitude': float(row.longitude) if row.longitude else None,
    'created_date': row.created_date,
    'incident_address': row.incident_address

  '''

