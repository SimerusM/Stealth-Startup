import os
import subprocess
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class SWEAgent:
    def __init__(self, project_path):
        self.project_path = project_path
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.project_map = {}

    def map_directory(self):
        print("Mapping app/ and components/ directories...")
        self.project_map = {
            'app': self._scan_directory(os.path.join(self.project_path, 'app')),
            'components': self._scan_directory(os.path.join(self.project_path, 'components'))
        }
        return self.project_map

    def _scan_directory(self, directory):
        if not os.path.exists(directory):
            return {}
        
        structure = {}
        for item in os.listdir(directory):
            path = os.path.join(directory, item)
            if os.path.isdir(path):
                structure[item] = self._scan_directory(path)
            elif os.path.isfile(path):
                structure[item] = self._read_file(path)
        return structure

    def _read_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return {
                'content': content,
                'size': len(content),
                'extension': os.path.splitext(file_path)[1]
            }
        except Exception as e:
            return {
                'error': str(e),
                'size': 0,
                'extension': os.path.splitext(file_path)[1]
            }

    def _extract_json(self, text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Attempt to extract JSON object from the text
            json_text = re.search(r'\{.*\}', text, re.DOTALL)
            if json_text:
                try:
                    return json.loads(json_text.group())
                except json.JSONDecodeError as e:
                    print("Failed to parse JSON:", e)
            raise

    def generate_changes(self, task_description):
        if not self.project_map:
            self.map_directory()

        project_context = json.dumps(self.project_map)
        few_shot_example = '''
Example task: Update the header to mention a cooking app

Example changes:
{
  "app/page.js": {
    "original": "export default function Home() {\\n  return (\\n    <main className=\\"flex min-h-screen flex-col items-center justify-between p-24\\">\\n      <h1 className=\\"text-4xl font-bold\\">Welcome to Our App</h1>\\n    </main>\\n  )\\n}",
    "updated": "export default function Home() {\\n  return (\\n    <main className=\\"flex min-h-screen flex-col items-center justify-between p-24\\">\\n      <h1 className=\\"text-4xl font-bold\\">Welcome to Our Cooking App</h1>\\n    </main>\\n  )\\n}"
  }
}

Example task: Add a new footer component with contact information

Example changes:
{
  "components/Footer.js": {
    "original": "",
    "updated": "export default function Footer() {\\n  return (\\n    <footer className=\\"bg-gray-800 text-white p-4\\">\\n      <p>Contact us at contact@example.com</p>\\n    </footer>\\n  )\\n}"
  },
  "app/page.js": {
    "original": "export default function Home() {\\n  return (\\n    <main>\\n      {/* Content */}\\n    </main>\\n  )\\n}",
    "updated": "import Footer from '../components/Footer';\\n\\nexport default function Home() {\\n  return (\\n    <>\\n      <main>\\n        {/* Content */}\\n      </main>\\n      <Footer />\\n    </>\\n  )\\n}"
  }
}
'''

        prompt = f"""You are a skilled software engineer working on a Next.js project. Analyze the given project structure and file contents, then generate the necessary code changes based on the task.

- **Output Format**: Provide the changes in a JSON format where keys are file paths and values are objects with "original" and "updated" keys.
- **Instructions**:
  - Only include files that need to be changed or created.
  - For new files, the "original" content should be an empty string.
  - Ensure the JSON is valid and properly escaped.
  - Do not include any explanations or additional text.

Project structure and contents:
{project_context}

Few-shot examples:
{few_shot_example}

Task:
{task_description}

Provide the code changes to implement this task in the same format as the examples above."""

        chat_completion = self.groq.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            temperature=0.2,
            max_tokens=4000,
        )

        response = chat_completion.choices[0].message.content
        print("Raw response from Groq:")
        print(response)
        changes = self._extract_json(response)
        return changes

    def propose_changes(self, task_description):
        changes = self.generate_changes(task_description)
        print("\nProposed changes:")
        for file_path, content in changes.items():
            print(f"File: {file_path}")
            print("Original Content:")
            print(content['original'])
            print("\nUpdated Content:")
            print(content['updated'])
            print("-" * 50)
        return changes

    def implement_feature(self, code_snippets):
        for file_path, content in code_snippets.items():
            full_path = os.path.join(self.project_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            if os.path.exists(full_path):
                self._modify_file(full_path, content['original'], content['updated'])
            else:
                self._create_new_file(full_path, content['updated'])
    
    def _create_new_file(self, file_path, code):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(code)
        print(f"Created new file: {file_path}")
    
    def _modify_file(self, file_path, original_code, new_code):
        with open(file_path, 'r', encoding='utf-8') as file:
            current_code = file.read()

        if current_code.strip() != original_code.strip():
            print(f"Warning: Current content of {file_path} does not match the expected original content.")
            return

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_code)
        print(f"Modified file: {file_path}")
    
    def run_tests(self):
        result = subprocess.run(["npm", "test"], cwd=self.project_path, capture_output=True, text=True)
        print(result.stdout)
        return result.returncode == 0
    
    def commit_changes(self):
        try:
            print("trace1")
            subprocess.run(["git", "add", "."], cwd=self.project_path)
            print("trace2")
            subprocess.run(["git", "commit", "-m", "Implemented new feature"], cwd=self.project_path)
            print("trace3")
        except:
            print("could not add and commit")

# if __name__ == "__main__":
#     agent = SWEAgent("../../stealth-startup-dev/landing")
#     project_map = agent.map_directory()
#     print("Project structure and file contents mapped.")

#     task = "Fix the formatting and improve the design. Make it more modern."
#     proposed_changes = agent.propose_changes(task)

#     user_input = input("Do you want to implement the proposed changes? (Y/N): ")
#     if user_input.strip().upper() == 'Y':
#         agent.implement_feature(proposed_changes)
#         agent.commit_changes()
#     else:
#         print("Changes were not implemented.")
