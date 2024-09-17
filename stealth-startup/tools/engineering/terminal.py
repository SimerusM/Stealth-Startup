import subprocess
import os
from groq import Groq

# Initialize Groq client
client = Groq(api_key="groq api key")

def execute_command(command):
    """Execute a shell command and return the output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

def edit_file(filename, content):
    """Edit a file using direct file writing."""
    with open(filename, 'w') as f:
        f.write(content)
    return f"File {filename} has been created/updated."

def ai_agent(task, context=""):
    """AI agent to interpret tasks, suggest actions, and evaluate completion."""
    prompt = f"""Task: {task}
Previous Context: {context}

Suggest the next step to complete the task. Provide a single, executable command or a short description of an action.
If the task is complete, respond with 'TASK COMPLETED'.

Suggested action:"""
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an AI assistant that suggests executable commands or simple actions to accomplish tasks step by step. Provide one command or action at a time."},
            {"role": "user", "content": prompt}
        ],
        model="llama3-70b-8192",
        max_tokens=100
    )
    
    return response.choices[0].message.content.strip()

def execute_action(action):
    """Execute the suggested action and return the result."""
    if action.startswith("edit:"):
        _, filename, content = action.split(":", 2)
        return edit_file(filename, content.strip())
    else:
        output, error = execute_command(action)
        return output if output else error

def get_human_approval(action):
    """Ask for human approval before executing an action."""
    while True:
        response = input(f"Approve this action? (y/n/m): '{action}'\n(y = yes, n = no, m = modify): ").lower()
        if response == 'y':
            return True, action
        elif response == 'n':
            return False, action
        elif response == 'm':
            modified_action = input("Enter the modified action: ")
            return True, modified_action
        else:
            print("Invalid input. Please enter 'y', 'n', or 'm'.")

def main():
    task = input("Enter a task: ")
    context = ""
    
    while True:
        action = ai_agent(task, context)
        
        if action == "TASK COMPLETED":
            print("AI suggests the task is completed. Do you agree?")
            approved, _ = get_human_approval("Mark task as completed")
            if approved:
                print("Task completed successfully!")
                break
            else:
                context += "\nHuman disagreed with task completion."
                continue
        
        approved, action_to_execute = get_human_approval(action)
        
        if approved:
            print(f"Executing: {action_to_execute}")
            result = execute_action(action_to_execute)
            print(f"Result: {result}")
            context += f"\nAction: {action_to_execute}\nResult: {result}"
        else:
            print("Action skipped.")
            context += f"\nAction suggested but skipped: {action}"

if __name__ == "__main__":
    main()