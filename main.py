# import streamlit as st
# import pytesseract
# from PIL import Image, ImageOps
# import json
# import os
# import urllib.parse
# from datetime import datetime, timedelta

# st.set_page_config(page_title="AI Secretary", page_icon="", layout="centered")

# st.title("AI Secretary")
# st.write("Upload an image flyer, schedule, or poster to parse details and generate a calendar event invite.")

# api_key = st.secrets.get("GROQ_API_KEY", "")
# client = None

# if not api_key:
#     st.warning("Configure your GROQ_API_KEY inside Streamlit's Secrets manager.")
# else:
#     try:
#         from groq import Groq
#         client = Groq(api_key=api_key)
#     except Exception as e:
#         st.error(f"Failed to load Groq library: {str(e)}")

# def generate_google_calendar_link(data):
#     base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
#     text = data.get('program_name', 'Education Course')

#     start_date = datetime.now() + timedelta(days=7)
#     end_date = start_date + timedelta(days=90)
#     dates_str = f"{start_date.strftime('%Y%m%dT090000')}/{end_date.strftime('%Y%m%dT170000')}"

#     eligibility = data.get('eligibility', {})
#     details = data.get('other_important_details', {})

#     description_lines = [
#         f"Eligibility: {eligibility.get('education', 'N/A')} (Age: {eligibility.get('age_limit', 'N/A')})",
#         f"Fee: {data.get('certification_fee', 'N/A')}",
#         f"Contacts: {', '.join(data.get('contact_numbers', []))}",
#         f"Certificate: {details.get('certification_type', 'N/A')}",
#         f"Initiative: {details.get('initiative', 'N/A')}",
#         "\\nGenerated automatically by AI Secretary"
#     ]
#     description = "\\n".join(description_lines)
#     location = "NAVTTC Multan / Tech Heaven"

#     params = {
#         "text": text,
#         "dates": dates_str,
#         "details": description,
#         "location": location,
#         "sf": "true",
#         "output": "xml"
#     }
#     return f"{base_url}&{urllib.parse.urlencode(params)}"

# uploaded_file = st.file_uploader("Choose a poster image", type=["jpg", "jpeg", "png"])

# if uploaded_file is not None:
#     img = Image.open(uploaded_file)
#     st.image(img, caption="Uploaded Image", use_container_width=True)

#     if client is not None:
#         with st.spinner("Processing OCR and Extraction"):
#             resized_img = img.resize((img.width * 2, img.height * 2))
#             grayscale_img = ImageOps.grayscale(resized_img)
#             ocr_text = pytesseract.image_to_string(grayscale_img)

#             prompt = "Analyze the following messy OCR text from an informational poster and extract the key details in a clean JSON format.\\n"
#             prompt += "You MUST respond with only valid JSON matching this structure: "
#             prompt += '{"program_name": "", "eligibility": {"education": "", "age_limit": ""}, "duration": "", "certification_fee": "", "contact_numbers": [], "other_important_details": {"certification_type": "", "initiative": ""}}\\n\\n'
#             prompt += "OCR Text:\\n" + ocr_text

#             try:
#                 response = client.chat.completions.create(
#                     model="openai/gpt-oss-120b",
#                     messages=[
#                         {"role": "system", "content": "You are a precise JSON extractor. Output ONLY JSON, no markdown formatting, no backticks, no introduction."},
#                         {"role": "user", "content": prompt}
#                     ],
#                     temperature=0.1
#                 )
                
#                 raw_text = response.choices[0].message.content.strip()
#                 # Safety clean in case markdown code blocks are returned
#                 if raw_text.startswith("```"):
#                     raw_text = raw_text.split("```json")[-1].split("```")[0].strip()
                
#                 structured_data = json.loads(raw_text)
#                 gcal_url = generate_google_calendar_link(structured_data)

#                 st.success("Parsing Completed")

#                 st.markdown(f"### {structured_data.get('program_name')}")
#                 st.write(f"**Duration:** {structured_data.get('duration')}")
#                 st.write(f"**Course Fee:** {structured_data.get('certification_fee')}")

#                 eligibility = structured_data.get('eligibility', {})
#                 st.markdown(f"**Eligibility:** {eligibility.get('education', 'N/A')} (Age: {eligibility.get('age_limit', 'N/A')})")

#                 contacts = ", ".join(structured_data.get('contact_numbers', []))
#                 st.write(f"**Contact Info:** {contacts}")

#                 st.markdown(f"[Add directly to Google Calendar]({gcal_url})")

#             except Exception as e:
#                 st.error(f"Error processing extraction: {str(e)}")

import streamlit as st
import pytesseract
from PIL import Image, ImageOps
import json
import urllib.parse

st.set_page_config(page_title="AI Secretary", page_icon="", layout="centered")

st.title("AI Secretary")
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


def generate_google_calendar_link(data):
    dates = data.get("dates", {})

    start = dates.get("start")
    end = dates.get("end")

    if not start:
        return None

    if not end:
        end = start

    params = {
        "action": "TEMPLATE",
        "text": data.get("title", "Event"),
        "dates": f"{start}/{end}",
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

            if raw.startswith("```"):
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

            if dates.get("start"):
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

            calendar_url = generate_google_calendar_link(data)

            if calendar_url:
                st.markdown(
                    f"[Add directly to Google Calendar]({calendar_url})"
                )

        except Exception as e:
            st.error(f"Error processing extraction: {e}")
