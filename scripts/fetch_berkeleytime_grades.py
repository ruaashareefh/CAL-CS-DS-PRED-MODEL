import requests
import json
import time
from pathlib import Path

URL = "https://berkeleytime.com/api/graphql"
OUTPUT_DIR = Path("data/raw/berkeleytime")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CS_COURSES = [
    # Intro / Lower Division
    "10",
    "61A",
    "61B",
    "61C",
    "70",

    # Upper Division Core Systems / Theory
    "161",
    "162",
    "170",
    "186",

    # Upper Division AI / ML / Data
    "188",
    "189",
    "182",

    # Upper Division Software / Design
    "169A",
    "160",

    # Upper Division Electives (popular)
    "168",
    "164",
    "176",
    "184",
    "180"
]


DATA_COURSES = [
    # Lower Division
    "4AC",
    "6",
    "C8",      # Foundations of Data Science
    "C88C",    # Computational Structures in DS
    "C88S",    # Probability & Math Stats for DS

    # Upper Division Core
    "C100",    # Principles & Techniques of DS
    "C101",    # Data Engineering
    "C102",    # Data Inference & Decisions
    "C104",    # Ethics of Data

    # Upper Division Electives
    "88E",     # Economic Models
    "C131A",   # Statistical Methods for DS
    "C140",    # Probability for DS
    "144"      # Data Mining & Analytics
]

EECS_COURSES = [
    # Lower Division Core
    "16A",     # Designing Information Devices and Systems I
    "16B",     # Designing Information Devices and Systems II

    # Upper Division - Systems & Architecture
    "151",     # Introduction to Digital Design
    "149",     # Embedded Systems

    # Upper Division - Theory & Math
    "126",     # Probability and Random Processes
    "127",     # Optimization Models

    # Upper Division - Signal Processing & Communications
    "120",     # Signals and Systems
    "123",     # Digital Signal Processing

    # Upper Division - Security & Networking
    "122",     # Introduction to Communication Networks
]


QUERY = """
query GetCourseGrades($subject: String!, $number: CourseNumber!) {
  course(subject: $subject, number: $number) {
    courseId
    subject
    number
    gradeDistribution {
      average
      distribution {
        letter
        count
      }
    }
  }
}
"""

def fetch_course(subject, number):
    payload = {
        "query": QUERY,
        "variables": {
            "subject": subject,
            "number": number
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "berkeley-grade-predictor/1.0 (academic)"
    }

    response = requests.post(URL, json=payload, headers=headers)

    # Helpful debugging if it fails again
    if response.status_code != 200:
        print("Status:", response.status_code)
        print("Response:", response.text)

    response.raise_for_status()
    return response.json()


def save_course_data(subject, number, data):
    filename = OUTPUT_DIR / f"{subject}_{number}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def run():
    for subject, courses in {
        "COMPSCI": CS_COURSES,
        "DATA": DATA_COURSES,
        "EECS": EECS_COURSES
    }.items():
        for number in courses:
            print(f"Fetching {subject} {number}...")
            try:
                data = fetch_course(subject, number)
                if data.get("data", {}).get("course"):
                    save_course_data(subject, number, data)
                else:
                    print(f"  ⚠️ No data for {subject} {number}")
            except Exception as e:
                print(f"  ❌ Failed {subject} {number}: {e}")

            time.sleep(0.5)  # polite rate limiting

if __name__ == "__main__":
    run()
