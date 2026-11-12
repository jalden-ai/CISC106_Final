"""
Course Difficulty Finder
------------------------
Helps students gauge how hard a future course will be, using ratings that
earlier students entered (professor difficulty, concept difficulty, workload,
overall difficulty, and hours of work per week).

Built with Drafter for the CS1 Final Project.
Run with:  python main.py
Unit tests live in test_main.py.
"""
from dataclasses import dataclass
from drafter import *

# Global constants are allowed (these never change while the site runs).
MIN_RATING = 1
MAX_RATING = 10
HARD_CUTOFF = 7
MODERATE_CUTOFF = 4


# --------------------------------------------------------------------------
# Dataclasses
# --------------------------------------------------------------------------
@dataclass
class Course:
    """One student's rating of one course (ratings are 1-10)."""
    course_name: str
    professor: str
    professor_difficulty: int
    concept_diff: int
    workload: int
    difficulty_rating: int
    hours_per_week: int


@dataclass
class State:
    """Everything the site remembers between pages."""
    user_name: str
    univ_name: str
    course_list: list[Course]
    message: str
    current_course: str  # the course the user is currently searching for


# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------
def normalize(text: str) -> str:
    """Make names comparable by ignoring case and extra spaces."""
    return " ".join(text.strip().lower().split())


def clamp_rating(value: int) -> int:
    """Keep a rating inside the MIN_RATING to MAX_RATING range."""
    if value < MIN_RATING:
        return MIN_RATING
    if value > MAX_RATING:
        return MAX_RATING
    return value


def find_matches(courses: list[Course], course_name: str,
                 professor: str) -> list[Course]:
    """Find loop: return every stored Course matching the course name (and
    the professor, unless the professor is blank, meaning any professor)."""
    matches = []
    for course in courses:
        if normalize(course.course_name) == normalize(course_name):
            if normalize(professor) == "":
                matches.append(course)
            elif normalize(course.professor) == normalize(professor):
                matches.append(course)
    return matches


def professors_for(courses: list[Course], course_name: str) -> list[str]:
    """Return the unique professor names that have ratings for a course."""
    names = []
    for course in find_matches(courses, course_name, ""):
        if course.professor not in names:
            names.append(course.professor)
    return names


def average_ratings(matches: list[Course]) -> list[float]:
    """Average the matching ratings. Returns, in order: professor difficulty,
    concept difficulty, workload, overall difficulty, hours per week.
    The list of matches must not be empty."""
    totals = [0, 0, 0, 0, 0]
    for course in matches:
        totals[0] += course.professor_difficulty
        totals[1] += course.concept_diff
        totals[2] += course.workload
        totals[3] += course.difficulty_rating
        totals[4] += course.hours_per_week
    averages = []
    for total in totals:
        averages.append(round(total / len(matches), 1))
    return averages


def difficulty_verdict(overall: float) -> str:
    """Turn an overall difficulty average into a short sentence."""
    if overall >= HARD_CUTOFF:
        return "This course is considered HARD."
    if overall >= MODERATE_CUTOFF:
        return "This course is considered MODERATE."
    return "This course is considered EASY."


def all_whole_numbers(values: list[str]) -> bool:
    """Return True if every string in the list is a whole number."""
    for value in values:
        if not value.strip().isdigit():
            return False
    return True


def make_course(course: str, professor: str, ratings: list[str]) -> Course:
    """Build a Course from form text. ratings holds, in order: professor
    difficulty, concept difficulty, workload, overall difficulty (each
    clamped to 1-10) and hours per week."""
    return Course(
        course.strip().upper(),
        professor.strip().title(),
        clamp_rating(int(ratings[0])),
        clamp_rating(int(ratings[1])),
        clamp_rating(int(ratings[2])),
        clamp_rating(int(ratings[3])),
        int(ratings[4]),
    )


def starting_courses() -> list[Course]:
    """Sample ratings so the site has data the first time it runs."""
    return [
        Course("CISC106", "Dr. Smith", 4, 5, 6, 5, 8),
        Course("CISC108", "Dr. Smith", 3, 4, 5, 4, 6),
        Course("CISC108", "Dr. Lee", 6, 5, 7, 6, 10),
        Course("MATH241", "Dr. Patel", 7, 8, 8, 8, 12),
        Course("PHYS207", "Dr. Garcia", 6, 7, 7, 7, 10),
    ]


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@route
def index(state: State) -> Page:
    """Home page: welcome the user, collect name and university."""
    content = [
        Header("Course Difficulty Finder", 1),
        "Find out how hard a course will be before you sign up, based on "
        "ratings from students who already took it.",
    ]
    if state.message != "":
        content.append(state.message)
    content.extend([
        LineBreak(),
        "Your name:",
        TextBox("user_name", state.user_name),
        "Your university:",
        TextBox("univ_name", state.univ_name),
        LineBreak(),
        Button("Search for a Course", search_course),
        Button("Input Rating", add_rating),
        Button("About", about),
    ])
    return Page(state, content)


@route
def search_course(state: State, user_name: str, univ_name: str) -> Page:
    """Search page: save the user's info and ask which course to look up."""
    state.user_name = user_name.strip()
    state.univ_name = univ_name.strip()
    state.message = ""

    greeting = "Which course are you looking for?"
    if state.user_name != "":
        greeting = ("Hi " + state.user_name +
                    "! Which course are you looking for?")

    return Page(state, [
        Header("Search for a Course", 1),
        greeting,
        TextBox("course", state.current_course),
        LineBreak(),
        Button("Search", select_professor),
        Button("Home", index),
    ])


@route
def select_professor(state: State, course: str) -> Page:
    """Professor page: ask which professor the user has for this course."""
    if normalize(course) == "":
        state.message = "Please type a course name to search."
        return index(state)

    state.current_course = course.strip()
    known = professors_for(state.course_list, state.current_course)

    if len(known) == 0:
        state.message = ("No ratings found for '" + state.current_course +
                         "' yet. Be the first to add one!")
        return index(state)

    return Page(state, [
        Header("Who is your professor?", 1),
        "Course: " + state.current_course,
        "Professors with ratings for this course: " + ", ".join(known),
        "Type your professor's name (leave blank to see all professors):",
        TextBox("professor", ""),
        LineBreak(),
        Button("Continue", course_results),
        Button("Home", index),
    ])


@route
def course_results(state: State, professor: str) -> Page:
    """Results page: show the averaged ratings for the course/professor."""
    matches = find_matches(state.course_list, state.current_course, professor)

    if len(matches) == 0:
        state.message = ("No ratings found for '" + professor.strip() +
                         "' in " + state.current_course + ".")
        return select_professor(state, state.current_course)

    prof_avg, concept_avg, workload_avg, overall_avg, hours_avg = \
        average_ratings(matches)

    who = professor.strip()
    if who == "":
        who = "all professors"

    return Page(state, [
        Header("Results: " + state.current_course, 1),
        "Professor: " + who,
        "Based on " + str(len(matches)) + " student rating(s)",
        LineBreak(),
        "Professor difficulty: " + str(prof_avg) + " / 10",
        "Concept difficulty: " + str(concept_avg) + " / 10",
        "Workload: " + str(workload_avg) + " / 10",
        "Overall difficulty: " + str(overall_avg) + " / 10",
        "Average work per week: " + str(hours_avg) + " hours",
        LineBreak(),
        difficulty_verdict(overall_avg),
        LineBreak(),
        Button("Search Another Course", search_course),
        Button("Home", index),
    ])


@route
def add_rating(state: State) -> Page:
    """Add-rating page: collect a new course review from the user."""
    content = [
        Header("Input a Rating", 1),
        "Rate your course from 1 (easiest) to 10 (hardest).",
    ]
    if state.message != "":
        content.append(state.message)
    content.extend([
        "Course name:",
        TextBox("course", ""),
        "Professor:",
        TextBox("professor", ""),
        "Professor difficulty (1-10):",
        TextBox("professor_difficulty", ""),
        "Concept difficulty (1-10):",
        TextBox("concept_diff", ""),
        "Workload (1-10):",
        TextBox("workload", ""),
        "Overall difficulty (1-10):",
        TextBox("difficulty_rating", ""),
        "Average hours of work per week:",
        TextBox("hours_per_week", ""),
        LineBreak(),
        Button("Submit Rating", submit_rating),
        Button("Home", index),
    ])
    return Page(state, content)


@route
def submit_rating(state: State, course: str, professor: str,
                  professor_difficulty: str, concept_diff: str,
                  workload: str, difficulty_rating: str,
                  hours_per_week: str) -> Page:
    """Validate the form, store a new Course in state, and go home."""
    if normalize(course) == "" or normalize(professor) == "":
        state.message = "Please fill in both the course and the professor."
        return add_rating(state)

    ratings = [professor_difficulty, concept_diff, workload,
               difficulty_rating, hours_per_week]
    if not all_whole_numbers(ratings):
        state.message = "All ratings and hours must be whole numbers."
        return add_rating(state)

    new_course = make_course(course, professor, ratings)
    state.course_list.append(new_course)
    state.message = ("Thanks! Your rating for " + new_course.course_name +
                     " was added.")
    return index(state)


@route
def about(state: State) -> Page:
    """About page: explain what the site does."""
    return Page(state, [
        Header("About", 1),
        "Course Difficulty Finder helps students estimate how hard a "
        "future course will be. Ratings come from earlier students and "
        "are averaged for each course and professor: professor difficulty, "
        "concept difficulty, workload, overall difficulty, and weekly hours.",
        LineBreak(),
        Button("Home", index),
    ])


# --------------------------------------------------------------------------
# Start the site (only when this file is run directly, not when imported
# by test_main.py). The __name__ check is documented here because it may not
# have been covered in class: Python sets __name__ to "__main__" only for
# the file you run, so importing this file for tests will not start a server.
# --------------------------------------------------------------------------
if __name__ == "__main__":
    set_site_information(
        author="John Alden",
        description="Estimate how hard a course will be using ratings from "
                    "earlier students.",
        sources=["Ratings entered by students using this site"],
        planning="CS1_Final_Project_Design.docx",
        links=["https://github.com/jalden-ai/CISC106"],
    )
    start_server(State("", "", starting_courses(), "", ""))

