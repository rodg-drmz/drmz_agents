import argparse
from morpheus_crew import MorpheusCrew

def main():
    parser = argparse.ArgumentParser(description="Run a CrewAI crew.")
    parser.add_argument("--crew", type=str, required=True, help="The crew name from crews.yaml")
    parser.add_argument("--input", type=str, required=True, help="Task input or prompt")
    args = parser.parse_args()

    crew = MorpheusCrew()
    result = crew.run_crew(crew_name=args.crew, task_input=args.input)

    print("\n📦 Final Result:")
    print(result)

if __name__ == "__main__":
    main()