# Generate numbers for everyone who submitted on microsoft forms
import csv # Python's built in csv reader. Not Pandas related
import random
import json

def generate_integer_assignments(csv_file, output_file="lecture_4_code/assignments.json"):
    assignments = {}
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row["Email address"].strip()
            assignments[email] = random.randint(0, 10)
    
    with open(output_file, "w") as f:
        json.dump(assignments, f, indent=2)
    print(f"Saved {len(assignments)} assignments to {output_file}")

if __name__=="__main__":
    generate_integer_assignments("lecture_4_code/microsoft.csv")