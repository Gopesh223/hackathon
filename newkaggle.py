import os
import csv
import time
from groq import Groq

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Fixed role instructions
role_instructions = {
    "Plaintiff": "You are the plaintiff in this case. Explain your complaint and what you expect from the court.",
    "Defendant": "You are the defendant. Present your side of the story and why you believe you are not at fault.",
    "Prosecution Lawyer": "You are the prosecution lawyer. Present the case against the defendant based on the facts.",
    "Defense Lawyer": "You are the defense lawyer. Argue in defense of your client using legal reasoning and facts.",
    "Judge": (
        "You are a fair and wise judge. Based on the opening statements and arguments from both sides, deliver a clear verdict. "
        "At the end, explicitly state either:\n"
        "'The court finds the defendant GUILTY.'\n"
        "or\n"
        "'The court finds the defendant NOT GUILTY.'"
    )
}

# Utility: Trim long summaries
def trim(text, max_chars):
    return text[:max_chars] + " ...[truncated]" if len(text) > max_chars else text

# Prompt generation
def generate_response(role, case_summary, context, phase):
    instruction = role_instructions[role]
    prompt = f"""You are participating in a courtroom simulation.

Case Summary:
{trim(case_summary, 2000)}

Phase: {phase}
Role: {role}
Instructions: {instruction}

Context so far:
{context}

{role}: What would you say next?
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Main logic
def process_csv(input_path, output_path, max_cases=50):
    results = []

    with open(input_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header if needed

        for i, row in enumerate(reader):
            if i >= max_cases:
                break
            if len(row) < 3:
                continue

            case_id = row[1].strip()
            summary = row[2].strip()

            # Simulate trial phases
            context = ""
            for role in ["Plaintiff", "Prosecution Lawyer", "Defendant", "Defense Lawyer"]:
                response = generate_response(role, summary, context, "Opening Statements")
                context += f"\n{role}: {response}\n"
                time.sleep(0.5)

            # Judge's ruling
            judge_response = generate_response("Judge", summary, context, "Judge’s Ruling")

            if "guilty" in judge_response.lower() and "not guilty" not in judge_response.lower():
                verdict = 1
            elif "not guilty" in judge_response.lower():
                verdict = 0
            else:
                # Force 0 if unclear to ensure binary outcome
                verdict = 0
                judge_response += "\n(Note: Verdict unclear, defaulting to NOT GUILTY)"

            print(f"Case {case_id} → Verdict: {verdict} | {judge_response[-60:]}")
            results.append((case_id, verdict))

    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "verdict"])
        writer.writerows(results)

    print(f"\nDone! Verdicts saved to: {output_path}")

# Example usage
if __name__ == "__main__":
    process_csv("cases.csv", "verdict_output.csv", max_cases=50)