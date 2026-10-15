import streamlit as st
import pytesseract
from PIL import Image
import json
import urllib.parse
import re
from datetime import datetime

# Configure Streamlit UI
st.set_page_config(page_title="AI Secretary", page_icon="📅", layout="centered")

st.title("📅 AI Secretary")
st.markdown("**Your Intelligent Event & Document Organizer**")

# Configure Sidebar / Settings & Mock Testing Suite
with st.sidebar:
    st.markdown("### Developer Controls")
    show_ocr_output = st.checkbox("Show Raw OCR Debugger", value=True)

    st.markdown("---")
    st.markdown("### 🧪 Simulation & Test Suite")
    st.markdown("Simulate edge-cases from your checklist:")
    mock_scenario = st.selectbox(
        "Select a test scenario",
        [
            "None (Use Real Upload)",
            "Huawei/NAVTTC poster (No calendar dates)",
            "Event Poster (With Valid Calendar Dates)",
            "Sabzi Wala Diagram (Costs & comparisons)",
            "Seller lifecycle diagram (No omissions)",
            "Blurry relief poster (Limited information)",
            "Image with no useful text (Empty OCR)",
            "API failure or malformed output"
        ]
    )

st.write(
    "Upload an image containing flyers, event details, schedules, "
    "or diagrams, and watch AI extract perfectly structured information."
)

# Initialize default values safely
api_key = ""
try:
    api_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    pass

if not api_key and mock_scenario == "None (Use Real Upload)":
    st.warning(
        "Configure your GROQ_API_KEY inside Streamlit's Secrets "
        "manager to use live API features."
    )

try:
    from groq import Groq
    client = Groq(api_key=api_key) if api_key else None
except Exception:
    client = None


def clean_date_for_calendar(date_str):
    """Normalize date styles to YYYYMMDD."""
    if not date_str:
        return ""

    clean_str = re.sub(r"[^a-zA-Z0-9\s-]", "", str(date_str)).strip()

    match = re.search(r"(\d{4})[-\s]?(\d{2})[-\s]?(\d{2})", clean_str)
    if match:
        return f"{match.group(1)}{match.group(2)}{match.group(3)}"

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%b-%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(clean_str, fmt).strftime("%Y%m%d")
        except ValueError:
            continue

    digits = re.sub(r"\D", "", clean_str)
    if len(digits) == 8:
        return digits

    return ""


def generate_google_calendar_link(data):
    """Generate a Google Calendar event link."""
    dates = data.get("dates", {})
    if not dates or not dates.get("start"):
        return ""

    start_raw = dates.get("start", "")
    end_raw = dates.get("end", "") or start_raw

    start_clean = clean_date_for_calendar(start_raw)
    end_clean = clean_date_for_calendar(end_raw)

    if not start_clean:
        return ""

    base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    params = {
        "text": data.get("title", "New Event"),
        "dates": f"{start_clean}/{end_clean}",
        "details": data.get("description", ""),
        "location": data.get("location", "")
    }

    return f"{base_url}&{urllib.parse.urlencode(params)}"


def generate_offline_ics(data):
    """Generate an iCalendar (.ics) file."""
    dates = data.get("dates", {})
    start_raw = dates.get("start", "") if dates else ""
    end_raw = dates.get("end", "") if dates else ""

    if not start_raw:
        return None

    start_val = clean_date_for_calendar(start_raw)
    end_val = clean_date_for_calendar(end_raw) or start_val

    if not start_val:
        return None

    if len(start_val) == 8:
        start_val += "T090000"
    if len(end_val) == 8:
        end_val += "T100000"

    title = str(data.get("title", "Event"))
    description = str(data.get("description", ""))
    location = str(data.get("location", ""))

    def escape_ics(value):
        return (
            value.replace("\\", "\\\\")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\n", "\\n")
            .replace(",", "\\,")
            .replace(";", "\\;")
        )

    title_esc = escape_ics(title)
    desc_esc = escape_ics(description)
    loc_esc = escape_ics(location)

    now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Secretary//NONSGML v1.0//EN
BEGIN:VEVENT
UID:{now_str}-ai-secretary@localhost
DTSTAMP:{now_str}
DTSTART:{start_val}
DTEND:{end_val}
SUMMARY:{title_esc}
DESCRIPTION:{desc_esc}
LOCATION:{loc_esc}
END:VEVENT
END:VCALENDAR
"""
    return ics_content


def get_mock_scenario_data(scenario):
    """Simulate datasets for the functional test checklist."""

    if "Huawei" in scenario:
        return {
            "ocr": (
                "NAVTTC FREE HUAWEI TECH ESSENTIALS Multan ICT Academy "
                "16 Years of Education CS 17 SE Math 18 to 40 Years "
                "Duration 3 Months Fee FREE 0300-0741284"
            ),
            "json": {
                "title": "NAVTTC FREE Huawei Tech Essentials",
                "description": (
                    "Building Skills, Empowering Youth, Building a Digital "
                    "Pakistan - a Prime Minister's Initiative."
                ),
                "location": "Multan, Pakistan",
                "dates": {"start": "", "end": ""},
                "details": [
                    {"label": "Eligibility", "value": "16 Years of Education"},
                    {"label": "Age Limit", "value": "18 to 40 Years"},
                    {"label": "Duration", "value": "3 Months"},
                    {"label": "Fee", "value": "FREE"}
                ],
                "contacts": ["0300-0741284"],
                "links": []
            }
        }

    elif "Calendar" in scenario:
        return {
            "ocr": (
                "AI Seminar on 2026-10-15 from 10:00 to 18:00 at NIC Hall. "
                "Registration Deadline is 2026-10-14."
            ),
            "json": {
                "title": "AI Application Seminar",
                "description": "Hands-on workshop on building Streamlit applications.",
                "location": "NIC Hall",
                "dates": {"start": "2026-10-15", "end": "2026-10-15"},
                "details": [
                    {"label": "Registration Deadline", "value": "2026-10-14"}
                ],
                "contacts": [],
                "links": ["https://example.com/register"]
            }
        }

    elif "Sabzi Wala" in scenario:
        return {
            "ocr": (
                "Sabzi Wala Model: Direct farm delivery costs 20% less. "
                "Traditional stores charge high margins."
            ),
            "json": {
                "title": "Sabzi Wala Delivery Model Comparison",
                "description": (
                    "Analysis of direct farm delivery versus traditional "
                    "vegetable supply-chain structures."
                ),
                "location": "",
                "dates": {"start": "", "end": ""},
                "details": [
                    {
                        "label": "Key Finding",
                        "value": "Direct farm delivery saves up to 20% on retail margins"
                    }
                ],
                "contacts": [],
                "links": []
            }
        }

    elif "lifecycle" in scenario:
        return {
            "ocr": (
                "Seller lifecycle: Registration, Verification, Listing, "
                "Sale, Settlement. Comprehensive processes map."
            ),
            "json": {
                "title": "Seller Lifecycle Map",
                "description": (
                    "Sequential roadmap detailing critical phases for "
                    "independent seller onboarding and conversions."
                ),
                "location": "",
                "dates": {"start": "", "end": ""},
                "details": [
                    {"label": "Step 1", "value": "Registration"},
                    {"label": "Step 2", "value": "Verification"},
                    {"label": "Step 3", "value": "Listing"},
                    {"label": "Step 4", "value": "Sale"},
                    {"label": "Step 5", "value": "Settlement"}
                ],
                "contacts": [],
                "links": []
            }
        }

    elif "Blurry" in scenario:
        return {
            "ocr": "Relief Event... Oct 24... City... urgent action",
            "json": {
                "title": "Relief Support Drive",
                "description": (
                    "Community relief and disaster assistance distribution event."
                ),
                "location": "City Hall",
                "dates": {"start": "2026-10-24", "end": "2026-10-24"},
                "details": [],
                "contacts": [],
                "links": []
            }
        }

    elif "no useful" in scenario:
        return {
            "ocr": "...",
            "json": {
                "title": "Untitled Document",
                "description": (
                    "No text could be extracted or parsed from the supplied resource image."
                ),
                "location": "",
                "dates": {"start": "", "end": ""},
                "details": [],
                "contacts": [],
                "links": []
            }
        }

    else:
        return {
            "ocr": "API limits or invalid keys encountered.",
            "json": None
        }


# Dynamic Workflow Trigger
ocr_text = ""
json_parsed_data = None

if mock_scenario != "None (Use Real Upload)":
    st.info(f"Running simulated test scenario: **{mock_scenario}**")
    mock_result = get_mock_scenario_data(mock_scenario)
    ocr_text = mock_result["ocr"]
    json_parsed_data = mock_result["json"]

else:
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.image(
                image,
                caption="Uploaded Source Image",
                use_container_width=True
            )

            with st.spinner("Executing local optical character recognition..."):
                ocr_text = pytesseract.image_to_string(image)

        except Exception as e:
            st.error(f"Error reading image or executing local OCR: {e}")


if ocr_text:
    if show_ocr_output:
        st.subheader("🔍 Raw Optical Character Recognition Output")
        edited_ocr_text = st.text_area(
            "Review and make corrections to raw OCR results before compiling:",
            value=ocr_text,
            height=150
        )
        ocr_text = edited_ocr_text

    # Parse OCR using LLM or Mock
    if json_parsed_data is None and ocr_text:
        if not client:
            st.info(
                "Mocking LLM processing as no active Groq client "
                "configuration is present."
            )
            json_parsed_data = {
                "title": "Extracted Event",
                "description": f"Automatic summary: {ocr_text[:120]}...",
                "location": "Unknown",
                "dates": {"start": "", "end": ""},
                "details": [],
                "contacts": [],
                "links": []
            }

        else:
            with st.spinner("AI is parsing structured data..."):
                try:
                    prompt = (
                        "Extract structured information from the following OCR text. "
                        "Analyze dates thoroughly. If dates or deadlines exist, "
                        "output them strictly in format 'YYYY-MM-DD'. "
                        "Never fabricate info or invent values. Return raw, strict "
                        "JSON only with structure:\n"
                        "{\n"
                        '  "title": "Event/Topic title",\n'
                        '  "description": "Brief detailed description",\n'
                        '  "location": "Physical venue or online URL",\n'
                        '  "dates": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},\n'
                        '  "details": [{"label": "...", "value": "..."}],\n'
                        '  "contacts": ["phones or emails"],\n'
                        '  "links": ["links found"]\n'
                        "}\n\n"
                        f"OCR text:\n{ocr_text}"
                    )

                    response = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a precise parsing assistant. "
                                    "Return only valid JSON."
                                )
                            },
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0
                    )

                    raw_output = response.choices[0].message.content.strip()

                    if "```" in raw_output:
                        matches = re.findall(
                            r"```(?:json)?\s*(.*?)\s*```",
                            raw_output,
                            re.DOTALL
                        )
                        if matches:
                            raw_output = matches[0].strip()

                    json_parsed_data = json.loads(raw_output)

                except Exception as e:
                    st.error(f"Parsing exception encountered: {e}")

    # Display Output and enable modifications
    if json_parsed_data:
        st.success("✨ Information Processed Successfully!")

        st.subheader("📝 Live Structured Editor")
        st.markdown(
            "Edit fields dynamically to correct any remaining omissions or mismatches:"
        )

        edited_title = st.text_input(
            "Title",
            value=json_parsed_data.get("title", "")
        )
        edited_desc = st.text_area(
            "Description",
            value=json_parsed_data.get("description", "")
        )
        edited_location = st.text_input(
            "Location",
            value=json_parsed_data.get("location", "")
        )

        dates_grp = json_parsed_data.get("dates", {})
        start_d = st.text_input(
            "Start Date (YYYY-MM-DD)",
            value=dates_grp.get("start", "")
        )
        end_d = st.text_input(
            "End Date (YYYY-MM-DD)",
            value=dates_grp.get("end", "")
        )

        final_data = {
            "title": edited_title,
            "description": edited_desc,
            "location": edited_location,
            "dates": {"start": start_d, "end": end_d},
            "details": json_parsed_data.get("details", []),
            "contacts": json_parsed_data.get("contacts", []),
            "links": json_parsed_data.get("links", [])
        }

        st.markdown("### 🛠️ Actions & Exports")
        col1, col2 = st.columns(2)

        with col1:
            g_link = generate_google_calendar_link(final_data)
            if g_link:
                st.markdown(f"[🔗 Add directly to Google Calendar]({g_link})")
            else:
                st.info(
                    "Provide a valid Start Date to enable Google Calendar shortcuts."
                )

        with col2:
            ics_string = generate_offline_ics(final_data)
            if ics_string:
                st.download_button(
                    label="💾 Download .ics File Offline",
                    data=ics_string,
                    file_name="event.ics",
                    mime="text/calendar"
                )
            else:
                st.info("Provide a valid Start Date to enable .ics exports.")
