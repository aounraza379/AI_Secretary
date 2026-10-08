import streamlit as st
import pytesseract
from PIL import Image, ImageOps
import json
import os
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="AI Secretary", page_icon="", layout="centered")

st.title("AI Secretary")
st.write("Upload an image flyer, schedule, or poster to parse details and generate a calendar event invite.")

api_key = st.secrets.get("GROQ_API_KEY", "")
client = None

if not api_key:
    st.warning("Configure your GROQ_API_KEY inside Streamlit's Secrets manager.")
else:
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to load Groq library: {str(e)}")

def generate_google_calendar_link(data):
    base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    text = data.get('program_name', 'Education Course')

    start_date = datetime.now() + timedelta(days=7)
    end_date = start_date + timedelta(days=90)
    dates_str = f"{start_date.strftime('%Y%m%dT090000')}/{end_date.strftime('%Y%m%dT170000')}"

    eligibility = data.get('eligibility', {})
    details = data.get('other_important_details', {})

    description_lines = [
        f"Eligibility: {eligibility.get('education', 'N/A')} (Age: {eligibility.get('age_limit', 'N/A')})",
        f"Fee: {data.get('certification_fee', 'N/A')}",
        f"Contacts: {', '.join(data.get('contact_numbers', []))}",
        f"Certificate: {details.get('certification_type', 'N/A')}",
        f"Initiative: {details.get('initiative', 'N/A')}",
        "\\nGenerated automatically by AI Secretary"
    ]
    description = "\\n".join(description_lines)
    location = "NAVTTC Multan / Tech Heaven"

    params = {
        "text": text,
        "dates": dates_str,
        "details": description,
        "location": location,
        "sf": "true",
        "output": "xml"
    }
    return f"{base_url}&{urllib.parse.urlencode(params)}"

uploaded_file = st.file_uploader("Choose a poster image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, caption="Uploaded Image", use_container_width=True)

    if client is not None:
        with st.spinner("Processing OCR and Extraction"):
            resized_img = img.resize((img.width * 2, img.height * 2))
            grayscale_img = ImageOps.grayscale(resized_img)
            ocr_text = pytesseract.image_to_string(grayscale_img)

            prompt = "Analyze the following messy OCR text from an informational poster and extract the key details in a clean JSON format.\\n"
            prompt += "You MUST respond with only valid JSON matching this structure: "
            prompt += '{"program_name": "", "eligibility": {"education": "", "age_limit": ""}, "duration": "", "certification_fee": "", "contact_numbers": [], "other_important_details": {"certification_type": "", "initiative": ""}}\\n\\n'
            prompt += "OCR Text:\\n" + ocr_text

            try:
                response = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[
                        {"role": "system", "content": "You are a precise JSON extractor. Output ONLY JSON, no markdown formatting, no backticks, no introduction."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                raw_text = response.choices[0].message.content.strip()
                # Safety clean in case markdown code blocks are returned
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```json")[-1].split("```")[0].strip()
                
                structured_data = json.loads(raw_text)
                gcal_url = generate_google_calendar_link(structured_data)

                st.success("Parsing Completed")

                st.markdown(f"### {structured_data.get('program_name')}")
                st.write(f"**Duration:** {structured_data.get('duration')}")
                st.write(f"**Course Fee:** {structured_data.get('certification_fee')}")

                eligibility = structured_data.get('eligibility', {})
                st.markdown(f"**Eligibility:** {eligibility.get('education', 'N/A')} (Age: {eligibility.get('age_limit', 'N/A')})")

                contacts = ", ".join(structured_data.get('contact_numbers', []))
                st.write(f"**Contact Info:** {contacts}")

                st.markdown(f"[Add directly to Google Calendar]({gcal_url})")

            except Exception as e:
                st.error(f"Error processing extraction: {str(e)}")
