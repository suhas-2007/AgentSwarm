from dotenv import load_dotenv

load_dotenv()

from graph.workflow import app


goal = input("Enter your goal: ")


initial_state = {
    "user_goal": goal,
    "plan": "",
    "research": "",
    "code": "",
    "evaluation": "",
    "final_answer": "",

    "revision_count": 0,

    "human_approval": "",
    "human_feedback": "",

    "revision_reason": "INITIAL",

    "status": "STARTING"
}


result = app.invoke(initial_state)


print("\n--- STATUS ---")
print(result["status"])

print("\n--- PLAN ---")
print(result["plan"])

print("\n--- RESEARCH ---")
print(result["research"])

print("\n--- CODE ---")
print(result["code"])

print("\n--- EVALUATION ---")
print(result["evaluation"])

print("\n--- HUMAN APPROVAL ---")
print(result["human_approval"])

print("\n--- HUMAN FEEDBACK ---")
print(result["human_feedback"])

print("\n--- REVISION COUNT ---")
print(result["revision_count"])

print("\n--- REVISION REASON ---")
print(result["revision_reason"])

print("\n--- FINAL ANSWER ---")
print(result["final_answer"])