import streamlit as st
import pytesseract
from PIL import Image, ImageOps
import json
import urllib.parse
import re

st.set_page_config(page_title="AI Secretary", page_icon="", layout="centered")

st.title("AI Secretary")

# Configure Sidebar / Settings
with st.sidebar:
    st.markdown("### Settings")
    show_ocr_output = st.checkbox("Show Raw OCR Debugger", value=True)

st.write("Upload an image and extract all useful information from it.")

api_key = st.secrets.get("GROQ_API_KEY", "")

if not api_key:
    st.warning("Configure your GROQ_API_KEY inside Streamlit's Secrets manager.")
    st.stop()

try:
    from groq import Groq
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"Failed to load Groq library: {e}")
    st.stop()


def clean_date_for_calendar(date_str):
    """Helper to normalize various date styles to Basic Google Calendar format (YYYYMMDD)."""
    if not date_str:
        return ""
    
    # Strip non-alphanumeric chars for easy matching
    clean_str = re.sub(r'[^a-zA-Z0-9\s-]', '', str(date_str)).strip()
    
    # Attempt standard YYYY-MM-DD format extraction
    iso_match = re.search(r'(\d{4})[-\s]?(\d{2})[-\s]?(\d{2})', clean_str)
    if iso_match:
        return f"{iso_match.group(1)}{iso_match.group(2)}{iso_match.group(3)}"
        
    # If it is natural language, we try to let Google Calendar API parse or use a standard default formatting.
    # Replace spaces/hyphens for formatting compatibility
    return urllib.parse.quote(clean_str)


def generate_google_calendar_link(data):
    dates = data.get("dates", {})
    start_raw = dates.get("start", "").strip() if dates else ""
    end_raw = dates.get("end", "").strip() if dates else ""

    if not start_raw:
        # Check details list for dates/deadlines if none in 'dates' key
        for item in data.get("details", []):
            label = item.get("label", "").lower()
            if "date" in label or "deadline" in label:
                start_raw = item.get("value", "")
                break

    if not start_raw:
        return None

    start_clean = clean_date_for_calendar(start_raw)
    end_clean = clean_date_for_calendar(end_raw) if end_raw else start_clean

    params = {
        "action": "TEMPLATE",
        "text": data.get("title", "Event"),
        "dates": f"{start_clean}/{end_clean}",
        "details": data.get("description", ""),
        "location": data.get("location", "")
    }

    return (
        "https://calendar.google.com/calendar/render?"
        + urllib.parse.urlencode(params)
    )


uploaded_file = st.file_uploader(
    "Choose an image",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file:

    img = Image.open(uploaded_file)

    st.image(
        img,
        caption="Uploaded Image",
        use_container_width=True
    )

    if st.button("Extract Information", type="primary"):

        with st.spinner("Reading image..."):

            resized = img.resize(
                (img.width * 2, img.height * 2)
            )

            grayscale = ImageOps.grayscale(resized)

            ocr_text = pytesseract.image_to_string(grayscale)

        if not ocr_text.strip():
            st.error("No readable text was found in the image.")
            st.stop()

        # OCR Debugger Expander
        if show_ocr_output:
            with st.expander("🔍 Show Raw OCR Output", expanded=False):
                st.text_area("OCR Output", ocr_text, height=250)

        prompt = f"""
Analyze the following OCR text from an image.

The image can be ANYTHING: a course, certification,
event, job advertisement, scholarship, admission notice,
business advertisement, announcement, schedule, flyer,
poster, invitation, product advertisement, or anything else.

Extract EVERY useful piece of information that actually
appears in the image.

Do NOT assume what type of image this is.

Do NOT invent information.

Do NOT create fields for information that does not exist.

For example, if there is no duration, do not return duration.
If there is no fee, do not return fee.
If there is no eligibility, do not return eligibility.

Use natural labels based on the actual image.

Return ONLY valid JSON in this format:

{{
    "title": "",
    "description": "",
    "location": "",
    "dates": {{
        "start": "",
        "end": ""
    }},
    "details": [
        {{
            "label": "",
            "value": ""
        }}
    ],
    "contacts": [],
    "links": []
}}

Rules:

- title = main heading/name of the poster.
- description = useful overall description if one exists.
- location = only if a location/venue/address is present.
- dates = only if actual event/program dates are present.
- details = ALL other useful information found.
- Use natural labels such as Duration, Fee, Eligibility,
  Age Limit, Requirements, Benefits, Organization,
  Deadline, Qualification, Experience, etc. ONLY when
  those things actually appear.
- contacts = all phone numbers and email addresses.
- links = all websites, URLs, registration links, etc.
- Preserve important wording and values.
- Do not summarize away useful information.
- Do not add information that is not present.

OCR TEXT:
{ocr_text}
"""

        try:

            response = client.chat.completions.create( 
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise OCR information "
                            "extractor. Return only valid JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0
            )

            raw = response.choices[0].message.content.strip()

            # Robust clean-up of markdown fences and JSON wrapper anomalies
            if "```" in raw:
                matches = re.findall(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
                if matches:
                    raw = matches[0].strip()
                else:
                    raw = raw.replace("```json", "").replace("```", "").strip()

            data = json.loads(raw)

            st.success("Information extracted")

            if data.get("title"):
                st.markdown(f"## {data['title']}")

            if data.get("description"):
                st.write(data["description"])

            if data.get("location"):
                st.markdown(
                    f"**Location:** {data['location']}"
                )

            dates = data.get("dates", {})
            has_date = False

            if dates and dates.get("start"):
                has_date = True
                label = "Date"

                if dates.get("end") and dates["end"] != dates["start"]:
                    label = "Dates"

                value = dates["start"]

                if dates.get("end") and dates["end"] != dates["start"]:
                    value += f" - {dates['end']}"

                st.markdown(f"**{label}:** {value}")

            for item in data.get("details", []):
                label = item.get("label", "").strip()
                value = item.get("value", "").strip()

                if label and value:
                    st.markdown(f"**{label}:** {value}")

            if data.get("contacts"):
                st.markdown(
                    f"**Contact:** {', '.join(data['contacts'])}"
                )

            for link in data.get("links", []):
                st.markdown(f"[{link}]({link})")

            # Generate Google Calendar link safely
            calendar_url = generate_google_calendar_link(data)

            if calendar_url:
                st.markdown("---")
                st.markdown(
                    f"**Add this to schedule:** [Add directly to Google Calendar]({calendar_url})"
                )

        except json.JSONDecodeError as jde:
            st.error(f"Failed to parse model output. Raw output was: {raw[:200]}... Error details: {jde}")
        except Exception as e:
            st.error(f"Error processing extraction: {e}")
