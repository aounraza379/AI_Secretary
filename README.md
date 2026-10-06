# AI Secretary

AI Secretary is an automated assistant that processes messy informational flyers, schedules, and posters via local OCR, extracts clean structured JSON parameters using Google Gemini, and generates 1-click calendar invite links.

---

## Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## About the Project

### Problem

Important event schedules, program flyers, and academic circulars are often shared as unstructured images or raw OCR outputs where row data is visually merged, making manual scheduling tedious and error-prone.

### Solution

This project extracts structured fields from noisy layout text using advanced language models, format-validates the output, and directly compiles downloadable calendar events alongside active pre-populated calendar URLs.

### Goals

- Enable seamless local OCR text extraction from document images.
- Ensure robust semantic structure extraction using modern API structures.
- Facilitate instant workflow integration with 1-click calendar additions.

---

## Features

- Intelligent text parsing with layout awareness.
- Validated semantic JSON structuring.
- Dynamic 1-click Google Calendar template links.
- Offline iCalendar file compiler.
- Production-ready Streamlit dashboard.

---

## Tech Stack

### Frontend / UI
- Streamlit

### AI Engine
- Google GenAI SDK (gemini-3.8-flash)
- Tesseract OCR Engine

---

## Project Structure

```text
ai-secretary/
├── main.py              # Main Streamlit application entrypoint
├── requirements.txt     # Python package dependencies
└── README.md            # Project overview and documentation
```

---

## Prerequisites

Ensure you have the following installed on your system:
- Python >= 3.10
- Tesseract OCR Engine
- Git

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/username/ai-secretary.git
cd ai-secretary
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
streamlit run main.py
```

---

## Environment Variables

Create your environment secret variables on your local environment or within your hosting service:

| Variable | Required | Description | Example |
| --- | --- | --- | --- |
| GEMINI_API_KEY | Yes | Google GenAI SDK key | AIzaSy... |

---

## Usage

### Local Execution
```bash
streamlit run main.py
```

---

## Deployment

### Deployment on Streamlit Community Cloud
1. Host this repository on GitHub.
2. Log into Streamlit Share and import your repository.
3. Add `GEMINI_API_KEY` under Advanced Settings -> Secrets.
4. Deploy your application.

---

## Contributing

1. Fork this repository.
2. Create a development feature branch: `git checkout -b feature/improvement`.
3. Commit your modifications: `git commit -m "feat: added improvements"`.
4. Push changes: `git push origin feature/improvement`.
5. Submit a pull request.

---

## License

This project is licensed under the MIT License.

---

## Author

- GitHub: https://github.com/username