import json
import logging
import math
import os
import re
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

AI_TIMEOUT_SECONDS = 5

LOCAL_PROVIDER_CATALOG = [
    {"name": "CityCare General Hospital", "type": "hospital", "lat": 28.6139, "lon": 77.2090, "address": "Connaught Place, New Delhi"},
    {"name": "Apollo Community Clinic", "type": "clinic", "lat": 13.0827, "lon": 80.2707, "address": "Anna Salai, Chennai"},
    {"name": "MedPlus Pharmacy", "type": "pharmacy", "lat": 12.9716, "lon": 77.5946, "address": "MG Road, Bengaluru"},
    {"name": "Sunrise Multispeciality Hospital", "type": "hospital", "lat": 19.0760, "lon": 72.8777, "address": "Dadar, Mumbai"},
    {"name": "Green Cross Clinic", "type": "clinic", "lat": 17.3850, "lon": 78.4867, "address": "Banjara Hills, Hyderabad"},
    {"name": "LifeLine Pharmacy", "type": "pharmacy", "lat": 22.5726, "lon": 88.3639, "address": "Park Street, Kolkata"},
]


@dataclass(frozen=True)
class LocalSymptomRule:
    keywords: tuple[str, ...]
    disease: str
    probability: float
    specialization: str
    medication: str
    dosage: str
    priority: str = "Normal"


SYMPTOM_RULES = [
    LocalSymptomRule(
        keywords=("chest pain", "shortness of breath"),
        disease="Possible Cardiac Event",
        probability=88.0,
        specialization="Cardiologist",
        medication="Immediate emergency evaluation",
        dosage="Do not self-medicate. Seek emergency care right away.",
        priority="Emergency",
    ),
    LocalSymptomRule(
        keywords=("chest pain",),
        disease="Cardiac Chest Pain",
        probability=76.0,
        specialization="Cardiologist",
        medication="Aspirin 81mg (only if already advised by a clinician)",
        dosage="Urgent medical review is recommended today.",
        priority="Emergency",
    ),
    LocalSymptomRule(
        keywords=("fever", "cough"),
        disease="Flu or Viral Upper Respiratory Infection",
        probability=84.0,
        specialization="General Physician",
        medication="Paracetamol 500mg",
        dosage="1 tablet after food every 6 to 8 hours if needed. Hydrate well.",
        priority="Urgent",
    ),
    LocalSymptomRule(
        keywords=("headache", "vision"),
        disease="Migraine Episode",
        probability=74.0,
        specialization="Neurologist",
        medication="Paracetamol 500mg",
        dosage="1 tablet after food if needed. Avoid bright light and get rest.",
        priority="Urgent",
    ),
    LocalSymptomRule(
        keywords=("stomach", "acidity"),
        disease="Acid Peptic Irritation",
        probability=69.0,
        specialization="Gastroenterologist",
        medication="Antacid suspension",
        dosage="10 ml after meals for temporary relief. Avoid spicy food.",
        priority="Normal",
    ),
    LocalSymptomRule(
        keywords=("stomach",),
        disease="Gastritis",
        probability=65.0,
        specialization="Gastroenterologist",
        medication="Omeprazole 20mg",
        dosage="1 capsule before breakfast for short-term relief.",
        priority="Normal",
    ),
    LocalSymptomRule(
        keywords=("rash", "itching"),
        disease="Allergic Skin Reaction",
        probability=71.0,
        specialization="Dermatologist",
        medication="Cetirizine 10mg",
        dosage="1 tablet in the evening if it is safe for you to take antihistamines.",
        priority="Normal",
    ),
]


def _remote_ai_enabled():
    return os.getenv("ENABLE_REMOTE_AI", "").lower() in {"1", "true", "yes", "on"}


def _live_provider_lookup_enabled():
    raw_value = os.getenv("ENABLE_LIVE_PROVIDER_LOOKUP", "true").lower()
    return raw_value in {"1", "true", "yes", "on"}


def _request_remote_chat(messages, response_format=None):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or not _remote_ai_enabled():
        return None

    session = requests.Session()
    session.trust_env = False
    payload = {
        "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        "messages": messages,
    }
    if response_format:
        payload["response_format"] = response_format

    try:
        response = session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=AI_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("Remote AI unavailable, falling back to local logic: %s", exc)
        return None


def _normalize_text(value):
    return (value or "").strip()


def _person_snapshot(person):
    return {
        "id": person.id,
        "name": person.full_name,
        "gender": person.gender or "Unknown",
        "blood_group": person.blood_group or "Unknown",
        "city": person.city or "Unknown",
        "status": person.status or "Unknown",
        "mobile_number": person.mobile_number or "Unavailable",
        "email": person.email or "Unavailable",
    }


def _match_people_by_name(persons, name):
    lookup = _normalize_text(name).lower()
    if not lookup:
        return []
    return [person for person in persons if lookup in _normalize_text(person.full_name).lower()]


def _format_people_list(people):
    return ", ".join(person.full_name for person in people)


def _unique_names(people, limit=10):
    seen = []
    for person in people:
        if person.full_name not in seen:
            seen.append(person.full_name)
        if len(seen) >= limit:
            break
    return ", ".join(seen)


def _extract_name_after_phrase(question, phrase):
    lowered = question.lower()
    if phrase not in lowered:
        return ""
    start = lowered.index(phrase) + len(phrase)
    return question[start:].strip(" ?.")


def _normalize_blood_group_token(token):
    cleaned = _normalize_text(token).upper()
    cleaned = cleaned.replace("BLOOD GROUP", "")
    cleaned = cleaned.replace("GROUP", "")
    cleaned = cleaned.replace("TYPE", "")
    cleaned = cleaned.replace("POSITIVE", "+")
    cleaned = cleaned.replace("NEGATIVE", "-")
    cleaned = cleaned.replace("PLUS", "+")
    cleaned = cleaned.replace("MINUS", "-")
    cleaned = cleaned.replace("VE", "")
    cleaned = cleaned.replace("POS", "+")
    cleaned = cleaned.replace("NEG", "-")
    cleaned = cleaned.replace(" ", "")

    blood_groups = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
    return cleaned if cleaned in blood_groups else ""


def _extract_blood_group_query(question):
    patterns = [
        r"blood\s+group\s+(?:is|are|=)?\s*([abo]{1,2}\s*(?:\+|-|positive|negative|plus|minus|pos|neg)?\s*(?:ve)?)",
        r"group\s+(?:is|are|=)?\s*([abo]{1,2}\s*(?:\+|-|positive|negative|plus|minus|pos|neg)?\s*(?:ve)?)",
        r"\b([abo]{1,2}\s*(?:\+|-|positive|negative|plus|minus|pos|neg)\s*(?:ve)?)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match:
            normalized = _normalize_blood_group_token(match.group(1))
            if normalized:
                return normalized
    return ""


def _find_doctors():
    from .models import Doctor

    return list(Doctor.objects.select_related("user").all())


def _find_appointments():
    from .models import Appointment

    return list(Appointment.objects.select_related("patient", "doctor__user").all())


def _find_reports():
    from .models import MedicalReport

    return list(MedicalReport.objects.select_related("patient").all())


def _find_invoices():
    from .models import Invoice

    return list(Invoice.objects.select_related("patient").all())


def _find_inventory():
    from .models import InventoryItem

    return list(InventoryItem.objects.all())


def _handle_patient_question(question, person_list):
    qa = question.lower()

    blood_group_query = _extract_blood_group_query(question)
    if blood_group_query and any(
        phrase in qa for phrase in (
            "who are all", "who all", "which patients", "show patients", "list patients",
            "blood group", "group is", "group are"
        )
    ):
        matches = [
            person for person in person_list
            if _normalize_text(person.blood_group).upper() == blood_group_query
        ]
        if matches:
            return f"Patients with blood group {blood_group_query}: {_unique_names(matches, limit=20)}."
        return f"No patients found with blood group {blood_group_query}."

    if "blood group of" in qa:
        name = _extract_name_after_phrase(question, "blood group of")
        matches = _match_people_by_name(person_list, name)
        if matches:
            person = matches[0]
            return f"{person.full_name}'s blood group is {person.blood_group or 'Unknown'}."
        return "I couldn't find that person in the database."

    if qa.startswith("who is") or qa.startswith("who was"):
        raw_name = question[6:] if qa.startswith("who is") else question[7:]
        matches = _match_people_by_name(person_list, raw_name.strip(" ?."))
        if matches:
            person = matches[0]
            return (
                f"{person.full_name} is recorded as {person.gender or 'Unknown gender'}, blood group "
                f"{person.blood_group or 'Unknown'}, city {person.city or 'not specified'}, "
                f"status {person.status or 'Unknown'}, contact {person.mobile_number or 'N/A'}."
            )
        return "I couldn't find that person in the database."

    if "details of" in qa or "show patient" in qa or "patient details for" in qa:
        phrase = "details of" if "details of" in qa else "show patient" if "show patient" in qa else "patient details for"
        name = _extract_name_after_phrase(question, phrase)
        matches = _match_people_by_name(person_list, name)
        if matches:
            person = matches[0]
            return (
                f"{person.full_name}: gender {person.gender or 'Unknown'}, age {person.age or 'Unknown'}, "
                f"blood group {person.blood_group or 'Unknown'}, city {person.city or 'not specified'}, "
                f"email {person.email or 'N/A'}, mobile {person.mobile_number or 'N/A'}, "
                f"status {person.status or 'Unknown'}."
            )
        return "I couldn't find that patient record."

    if "which people live in" in qa or "who live in" in qa or "patients in" in qa:
        match = re.search(r"(?:live in|patients in)\s+([a-zA-Z\s]+)", question, flags=re.IGNORECASE)
        city = match.group(1).strip(" ?.") if match else question.split()[-1].strip(" ?.")
        matches = [person for person in person_list if city.lower() in _normalize_text(person.city).lower()]
        if matches:
            return f"People found in {city}: {_unique_names(matches)}."
        return f"No people found in {city}."

    if "active records" in qa or "show me all active" in qa or "active patients" in qa:
        matches = [person for person in person_list if _normalize_text(person.status).lower() == "active"]
        if matches:
            return f"Active records: {_unique_names(matches, limit=20)}."
        return "No active records found."

    if "inactive patients" in qa or "inactive records" in qa:
        matches = [person for person in person_list if _normalize_text(person.status).lower() == "inactive"]
        if matches:
            return f"Inactive records: {_unique_names(matches, limit=20)}."
        return "No inactive records found."

    if "total patients" in qa or "how many patients" in qa or "patient count" in qa:
        return f"There are {len(person_list)} patient records in the system."

    if "list patients" in qa or "show all patients" in qa or "patient names" in qa:
        if person_list:
            return f"Patients in the system: {_unique_names(person_list, limit=20)}."
        return "No patient records are available."

    return None


def _handle_doctor_question(question):
    qa = question.lower()
    doctors = _find_doctors()

    if "how many doctors" in qa or "doctor count" in qa:
        return f"There are {len(doctors)} doctors in the system."

    if "list doctors" in qa or "available doctors" in qa or "show doctors" in qa:
        if not doctors:
            return "No doctor records are available."
        names = []
        for doctor in doctors[:15]:
            name = doctor.user.get_full_name() or doctor.user.username
            names.append(f"Dr. {name} ({doctor.specialization}, {doctor.availability_status})")
        return "Doctors in the system: " + ", ".join(names) + "."

    if "cardiologist" in qa or "neurologist" in qa or "gastroenterologist" in qa or "pediatrician" in qa or "general physician" in qa:
        specializations = [doctor for doctor in doctors if doctor.specialization and doctor.specialization.lower() in qa]
        if specializations:
            matches = [f"Dr. {doctor.user.get_full_name() or doctor.user.username}" for doctor in specializations]
            return "Matching doctors: " + ", ".join(matches) + "."
        return "I couldn't find a doctor matching that specialization."

    return None


def _handle_appointment_question(question):
    qa = question.lower()
    appointments = _find_appointments()

    if "how many appointments" in qa or "appointment count" in qa:
        return f"There are {len(appointments)} appointments in the system."

    if "today appointments" in qa or "appointments today" in qa:
        from django.utils import timezone

        today_date = timezone.localdate()
        today = [
            item for item in appointments
            if item.appointment_date and timezone.localtime(item.appointment_date).date() == today_date
        ]
        return f"There are {len(today)} appointments scheduled for today."

    if "scheduled appointments" in qa or "pending appointments" in qa:
        scheduled = [item for item in appointments if (item.status or "").lower() == "scheduled"]
        return f"There are {len(scheduled)} scheduled appointments."

    if "list appointments" in qa or "recent appointments" in qa:
        if not appointments:
            return "No appointments are available."
        recent = sorted(
            [item for item in appointments if item.appointment_date],
            key=lambda item: item.appointment_date,
            reverse=True,
        )[:5]
        parts = []
        for item in recent:
            doctor_name = item.doctor.user.get_full_name() or item.doctor.user.username
            parts.append(
                f"{item.patient.full_name} with Dr. {doctor_name} on {item.appointment_date.strftime('%d %b %Y %I:%M %p')} ({item.status})"
            )
        return "Recent appointments: " + "; ".join(parts) + "."

    return None


def _handle_report_question(question):
    qa = question.lower()
    reports = _find_reports()

    if "how many reports" in qa or "report count" in qa or "medical reports" in qa:
        return f"There are {len(reports)} medical reports in the system."

    if "pending reports" in qa:
        pending = [report for report in reports if (report.status or "").lower() == "pending"]
        return f"There are {len(pending)} pending reports."

    if "reviewed reports" in qa:
        reviewed = [report for report in reports if (report.status or "").lower() == "reviewed"]
        return f"There are {len(reviewed)} reviewed reports."

    return None


def _handle_billing_question(question):
    qa = question.lower()
    invoices = _find_invoices()

    if "how many invoices" in qa or "invoice count" in qa or "billing count" in qa:
        return f"There are {len(invoices)} invoices in the system."

    if "paid invoices" in qa:
        paid = [invoice for invoice in invoices if (invoice.status or "").lower() == "paid"]
        total = sum(float(invoice.total_amount or 0) for invoice in paid)
        return f"There are {len(paid)} paid invoices totaling {total:.2f}."

    if "unpaid invoices" in qa or "pending revenue" in qa:
        unpaid = [invoice for invoice in invoices if (invoice.status or "").lower() == "unpaid"]
        total = sum(float(invoice.total_amount or 0) for invoice in unpaid)
        return f"There are {len(unpaid)} unpaid invoices totaling {total:.2f}."

    if "total revenue" in qa or "revenue" in qa:
        paid = [invoice for invoice in invoices if (invoice.status or "").lower() == "paid"]
        total = sum(float(invoice.total_amount or 0) for invoice in paid)
        return f"Total paid revenue is {total:.2f}."

    return None


def _handle_inventory_question(question):
    qa = question.lower()
    items = _find_inventory()

    if "inventory count" in qa or "how many inventory items" in qa:
        return f"There are {len(items)} inventory items in the system."

    if "low stock" in qa or "low inventory" in qa:
        low_stock = [item for item in items if item.quantity <= item.threshold]
        if low_stock:
            item_names = ", ".join(f"{item.name} ({item.quantity})" for item in low_stock[:10])
            return f"Low-stock items: {item_names}."
        return "No items are currently below their stock threshold."

    if "list inventory" in qa or "show inventory" in qa:
        if items:
            item_names = ", ".join(f"{item.name} ({item.quantity})" for item in items[:10])
            return f"Inventory items: {item_names}."
        return "No inventory items are available."

    return None


def get_ai_response(question, persons):
    question = _normalize_text(question)
    person_list = list(persons)
    if not question:
        return "Please ask a question."

    remote_answer = _request_remote_chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are EHR AssistAI, a hospital database assistant. "
                    "Answer using the database context only."
                ),
            },
            {
                "role": "user",
                "content": "DATABASE CONTEXT:\n"
                + "\n".join(
                    f"ID: {item['id']}, Name: {item['name']}, Gender: {item['gender']}, "
                    f"Blood Group: {item['blood_group']}, City: {item['city']}, Status: {item['status']}"
                    for item in (_person_snapshot(person) for person in person_list)
                )
                + f"\n\nUSER QUESTION: {question}",
            },
        ]
    )
    if remote_answer:
        return remote_answer

    handlers = [
        lambda: _handle_patient_question(question, person_list),
        lambda: _handle_doctor_question(question),
        lambda: _handle_appointment_question(question),
        lambda: _handle_report_question(question),
        lambda: _handle_billing_question(question),
        lambda: _handle_inventory_question(question),
    ]

    for handler in handlers:
        result = handler()
        if result:
            return result

    sample_names = _format_people_list(person_list[:5])
    if sample_names:
        return (
            "I couldn't map that exact question yet, but I can answer patient, doctor, appointment, report, "
            f"billing, and inventory questions. Recent patient records include: {sample_names}."
        )
    return "I can help with database questions, but I could not find any patient records yet."


def predict_disease_from_symptoms(symptoms):
    symptoms = _normalize_text(symptoms)
    if not symptoms:
        return (
            "General Consultation",
            50.0,
            "General Physician",
            "Medical review required",
            "Please describe symptoms in more detail.",
        )

    remote_content = _request_remote_chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI symptom checker. Return only JSON with disease, probability, "
                    "specialization, medication, and dosage."
                ),
            },
            {"role": "user", "content": f"Symptoms: {symptoms}"},
        ],
        response_format={"type": "json_object"},
    )

    if remote_content:
        try:
            cleaned = remote_content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            content = json.loads(cleaned)
            return (
                content.get("disease", "Condition Analyzed"),
                float(content.get("probability", 70.0)),
                content.get("specialization", "General Physician"),
                content.get("medication", "Consult Pharmacist"),
                content.get("dosage", "Follow pharmacist instructions"),
            )
        except Exception as exc:
            logger.warning("Remote symptom payload invalid, using local logic: %s", exc)

    return predict_disease_from_symptoms_local(symptoms)


def predict_disease_from_symptoms_local(symptoms):
    symptoms_lower = symptoms.lower()
    for rule in SYMPTOM_RULES:
        if all(keyword in symptoms_lower for keyword in rule.keywords):
            return (
                rule.disease,
                rule.probability,
                rule.specialization,
                rule.medication,
                rule.dosage,
            )

    if "fever" in symptoms_lower:
        return (
            "Feverish Viral Illness",
            62.0,
            "General Physician",
            "Paracetamol 500mg",
            "1 tablet after food if needed for fever. Rest and stay hydrated.",
        )

    return (
        "General Consultation",
        50.0,
        "General Physician",
        "Supportive care only",
        "Hydrate well and book a doctor consultation if symptoms continue or worsen.",
    )


def detect_appointment_priority(reason, symptoms):
    text = f"{_normalize_text(reason)} {_normalize_text(symptoms)}".lower()
    remote_answer = _request_remote_chat(
        messages=[
            {
                "role": "system",
                "content": "Return only one word: Normal, Urgent, or Emergency.",
            },
            {"role": "user", "content": text},
        ]
    )
    if remote_answer in {"Normal", "Urgent", "Emergency"}:
        return remote_answer

    if any(flag in text for flag in ("chest pain", "unconscious", "bleeding", "shortness of breath")):
        return "Emergency"
    if any(flag in text for flag in ("fever", "severe", "persistent vomiting", "dizziness")):
        return "Urgent"
    return "Normal"


def _distance_km(lat1, lon1, lat2, lon2):
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _normalize_overpass_element(element):
    tags = element.get("tags", {})
    lat = element.get("lat") or element.get("center", {}).get("lat")
    lon = element.get("lon") or element.get("center", {}).get("lon")
    if lat is None or lon is None or not tags.get("amenity"):
        return None
    return {
        "id": element.get("id"),
        "name": tags.get("name") or "Healthcare Center",
        "type": tags.get("amenity"),
        "address": tags.get("addr:street") or tags.get("addr:full") or "Address not listed",
        "lat": lat,
        "lon": lon,
        "distance_km": None,
    }


def get_nearby_healthcare(lat, lon, radius_m=10000):
    lat = float(lat)
    lon = float(lon)

    if _live_provider_lookup_enabled():
        session = requests.Session()
        session.trust_env = False
        query = f"""
        [out:json];
        (
          node["amenity"~"hospital|clinic|pharmacy|doctors|dentist"](around:{int(radius_m)},{lat},{lon});
          way["amenity"~"hospital|clinic|pharmacy|doctors|dentist"](around:{int(radius_m)},{lat},{lon});
          relation["amenity"~"hospital|clinic|pharmacy|doctors|dentist"](around:{int(radius_m)},{lat},{lon});
        );
        out center;
        """
        for endpoint in (
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.openstreetmap.fr/api/interpreter",
        ):
            try:
                response = session.get(endpoint, params={"data": query}, timeout=AI_TIMEOUT_SECONDS)
                response.raise_for_status()
                raw_items = response.json().get("elements", [])
                providers = []
                seen_keys = set()
                for element in raw_items:
                    normalized = _normalize_overpass_element(element)
                    if normalized:
                        normalized["distance_km"] = round(
                            _distance_km(lat, lon, normalized["lat"], normalized["lon"]), 2
                        )
                        key = (
                            normalized["name"].strip().lower(),
                            normalized["type"],
                            round(normalized["lat"], 5),
                            round(normalized["lon"], 5),
                        )
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        providers.append(normalized)
                if providers:
                    return sorted(providers, key=lambda item: item["distance_km"])[:25]
            except Exception as exc:
                logger.warning("Provider lookup endpoint failed, trying fallback: %s", exc)

    providers = []
    for index, provider in enumerate(LOCAL_PROVIDER_CATALOG, start=1):
        distance_km = _distance_km(lat, lon, provider["lat"], provider["lon"])
        providers.append(
            {
                "id": provider.get("id", f"local-{index}"),
                "name": provider["name"],
                "type": provider["type"],
                "address": provider["address"],
                "lat": provider["lat"],
                "lon": provider["lon"],
                "distance_km": round(distance_km, 2),
            }
        )
    return sorted(providers, key=lambda item: item["distance_km"])[:8]
