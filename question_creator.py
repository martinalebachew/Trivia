# Trivia - TCP Quiz Game POC [1.1.0-alpha]
# By Martin Alebachew
# QUESTION_CREATOR.PY
# #####

"""
This is a side tool for creating new questions.
Server-side.
"""

import pickle
from protocol import Question, TOPICS


# Load questions file
with open('questions', 'rb') as f:
    questions = pickle.load(f)


def main():
    print("// Add Questions //\n")
    print("Available topics:")
    for t in TOPICS:
        print(t)

    print("Select topic:")
    k = input()

    if k in questions.keys():
        print("Number of questions in topic:" + str(len(questions[k])))
        print("Enter a question:")
        q = input()

        while q != "*":
            print("Enter 1st answer:")
            a1 = input()

            print("Enter 2nd answer:")
            a2 = input()

            print("Enter 3rd answer:")
            a3 = input()

            print("Enter 4th answer:")
            a4 = input()

            print("Enter correct answer number (1-4):")
            c = int(input())

            q_obj = Question(q, a1, a2, a3, a4, c)
            questions[k].append(q_obj)
            print(f"Question added. There are now {str(len(questions[k]))} questions in the topic.")

            # Update questions file
            with open('questions', 'wb') as f:
                pickle.dump(questions, f)

            print("Enter a question:")
            q = input()
    else:
        print("Invalid topic!")


if __name__ == "__main__":
    main()
