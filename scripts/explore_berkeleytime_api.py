"""
Explore what metadata BerkleyTime API provides beyond grades
"""

import requests
import json

URL = "https://berkeleytime.com/api/graphql"

# GraphQL introspection query to see available fields
INTROSPECTION_QUERY = """
query IntrospectCourse {
  __type(name: "Course") {
    fields {
      name
      type {
        name
        kind
      }
    }
  }
}
"""

# Try to get full course data to see all available fields
FULL_COURSE_QUERY = """
query GetFullCourseData($subject: String!, $number: CourseNumber!) {
  course(subject: $subject, number: $number) {
    courseId
    subject
    number
    title
    description
    requirements
    finalExam
    typicallyOffered
    academicOrganization
    academicOrganizationName
    departmentNicknames
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

def introspect_api():
    """Use GraphQL introspection to see available fields"""
    print("=" * 80)
    print("BERKLEYTIME API INTROSPECTION")
    print("=" * 80)
    print()

    payload = {"query": INTROSPECTION_QUERY}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "berkeley-grade-predictor/1.0 (academic)"
    }

    response = requests.post(URL, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        fields = data.get("data", {}).get("__type", {}).get("fields", [])

        if fields:
            print("Available Course fields:")
            for field in fields:
                field_name = field["name"]
                field_type = field["type"].get("name", field["type"].get("kind", "unknown"))
                print(f"  - {field_name}: {field_type}")
        else:
            print("No fields found or introspection disabled")
    else:
        print(f"Introspection failed: {response.status_code}")
        print(response.text)

    print()

def test_full_query():
    """Test fetching full course data with all fields"""
    print("=" * 80)
    print("TEST FULL COURSE DATA (COMPSCI 61A)")
    print("=" * 80)
    print()

    payload = {
        "query": FULL_COURSE_QUERY,
        "variables": {
            "subject": "COMPSCI",
            "number": "61A"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "berkeley-grade-predictor/1.0 (academic)"
    }

    response = requests.post(URL, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        course = data.get("data", {}).get("course", {})

        print("Course data available:")
        for key, value in course.items():
            if key != "gradeDistribution":  # Skip large grade data
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: [grade distribution data]")
    else:
        print(f"Failed: {response.status_code}")
        print(response.text)

    print()
    print("Full JSON response:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    introspect_api()
    test_full_query()
