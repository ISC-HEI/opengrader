import json

with open('/home/pmudry/git/opengrader/pregrade/inputs_clean/Question4_batch0.json', 'r') as f:
    data = json.load(f)

for i, student in enumerate(data['students']):
    print(f"--- Student {i}: {student['firstname']} {student['lastname']} ---")
    print(student['answer'])
    print("\n" + "="*50 + "\n")
