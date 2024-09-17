import os
import cohere
import replicate
import requests  # For downloading the image
import random  # Import random for selecting a random message
from io import BytesIO
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Any
from helpers import *
from swe_agent import SWEAgent

from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name, id, role, cohere_api_key, slack_token, flux_token=None):
        self.name = name  # Agent's name, e.g., "Alice"
        self.id = id
        self.role = role  # Agent's role, e.g., "CTO"
        self.cohere_client = cohere.Client(cohere_api_key, log_warning_experimental_features=False)  # Initialize Cohere client directly with API key
        self.memory = []  # Memory to store previous actions or responses
        self.slack_client = WebClient(token=slack_token)  # Initialize Slack client with token

    @abstractmethod
    def take_instruction(self, instruction):
        """Processes an instruction and generates a response using the LLM."""
        pass

    def send_message_to_slack(self, message, channel_id):
        """Send a message to Slack using the Slack SDK."""
        try:
            response = self.slack_client.chat_postMessage(
                channel=channel_id,
                text=message
            )
            #print(f"Message sent to Slack successfully: {response['message']['text']}")
        except SlackApiError as e:
            print(f"Failed to send message to Slack: {e.response['error']}")

    def store_in_memory(self, instruction, action):
        """Stores the instruction and action in memory."""
        self.memory.append({"instruction": instruction, "action": action})

    def recall_memory(self):
        """Recalls previous actions and responses from memory."""
        return self.memory
    
    def process_instruction_with_llm(self, instruction: str) -> str:
        """Uses the Cohere LLM client to process the instruction."""
        prompt = f"{instruction}" # TODO: have some way to expand on the company once the idea is fleshed out
        #print("\n\n\n")
        #print(prompt)
        #print("\n\n\n")

        response = self.cohere_client.generate(
            model="command-r-08-2024",
            prompt=prompt,
            max_tokens=150
        )
        result = response.generations[0].text.strip()
        #print(f"{self.name} processed the instruction and generated: {result}")
        return result

    def get_slack_id(self):
        """Getter method to get specific users slack ID."""
        return self.id
    
    def summarize(self, text: str) -> str:
        """Summarized thoughts for slack output."""
        prompt = f"""DO NOT USE MARKDOWN FORMATTING. Summarize the text I gave you in 3-4 bullet points. Be CONCISE. This
        will be outputted to the slack channel for a summarized version of everything you've been thinking. Talk in 1st person as if you are the CEO thinking out loud.
         Focus on the high-level stuff."""
        response = self.process_instruction_with_llm(f"{prompt}: {text}")
        return response 

    @abstractmethod
    def generate_message(self, prompt):
        pass


class CEO(BaseAgent):
    def __init__(self, name, id, cohere_api_key, slack_token):
        super().__init__(name, id, "CEO", cohere_api_key, slack_token)
        self.stages = [
            "market_research",
            "idea_creation",
            "product_creation",
            "business_plan",
        ]  # List of stages in order
        self.current_stage_index = 0  # Initial stage index

    def take_instruction(self, instruction):
        """Initial entry point for the CEO to start the feedback loop process."""
        #(f"{self.name} received instruction: {instruction}")
        self.run_stage(instruction)

    def run_stage(self, previous_output):
        """General function to handle each stage recursively."""
        if self.current_stage_index >= len(self.stages):
            print("Feedback loop complete. Business plan is ready for execution.")
            self.send_message_to_slack("Business plan is ready for execution.", "C07N3SLH5EU")
            return  # End the recursive process when all stages are done
        
        current_stage = self.stages[self.current_stage_index]
        
        # Determine the prompt based on the current stage
        if current_stage == "market_research":
            prompt = f"""DO NOT USE MARKDOWN FORMATTING. I'm the CEO of a tech startup looking to enter the AI-driven healthcare market. I need to get a clear understanding of the current market dynamics. 
            What are the key trends, challenges, and opportunities in this space? I want to find the major players, the gaps they're not addressing, and where we could make an impact. 
            Talk in 1st person as if you are the CEO thinking out loud. """
            instruction = "Market Research"
        
        elif current_stage == "idea_creation":
            prompt = f"""DO NOT USE MARKDOWN FORMATTING. Now that I've gathered valuable insights from my market research, I need to come up with a tech idea that can really make an impact. 
            Based on the trends and opportunities I uncovered—{previous_output}—what innovative solution can we develop that solves the biggest pain points in this space? 
            Talk in 1st person as if you are the CEO thinking out loud."""
            instruction = "Tech Idea Creation"
        
        elif current_stage == "product_creation":
            prompt = f"""DO NOT USE MARKDOWN FORMATTING. I've now developed a strong tech idea: {previous_output}. The next step is to conceptualize the product around this idea.
            I need to think about how we can bring this idea to life in a way that solves the problem effectively, while also creating a product that is easy to use, scalable, and marketable. 
            Talk in 1st person as if you are the CEO thinking out loud."""
            instruction = "Product Creation"
        
        elif current_stage == "business_plan":
            prompt = f"""DO NOT USE MARKDOWN FORMATTING. Now that we've conceptualized the product, it's time to finalize the business plan. The product is based on {previous_output}, and I need to think carefully about our strategy moving forward.
            What's our go-to-market strategy? How should we position ourselves against competitors, and what’s our revenue model? This business plan needs to be forward-looking and adaptable as we grow. 
            Talk in 1st person as if you are the CEO thinking out loud."""
            instruction = "Business Plan Finalization"
        
        # Process the prompt with the LLM
        response = self.process_instruction_with_llm(prompt)
        self.store_in_memory(instruction, response)
        summarized_response = self.summarize(response)
        self.send_message_to_slack(f"{instruction}: {summarized_response}", "C07N3SLH5EU")  # Send to Slack

        # Move to the next stage
        self.current_stage_index += 1

        # Recursively call the function to proceed to the next stage
        self.run_stage(response)
    
    def generate_message(self, prompt):
        response = self.process_instruction_with_llm(prompt)
        self.store_in_memory("Generate Response", response)
        self.send_message_to_slack(f"{trim_quotations(response)}", "C07MF3WH7UJ")


class Marketer(BaseAgent):
    def __init__(self, name, id, role, cohere_api_key, slack_token, flux_token):
        super().__init__(name, id, role, cohere_api_key, slack_token, flux_token)
        self.slack_client = WebClient(token=slack_token)

        # Get Replicate API token from environment variables
        self.replicate_api_token = flux_token
        self.metadata = {
            "branding_documents": [],  # Store branding documents
            "logos": []  # Store logo URLs and related metadata
        }

    def take_instruction(self, instruction):
        """Processes the instruction for branding, logo creation, or design work."""
        response = self.process_instruction_with_llm(instruction)

        if "logo" in instruction.lower():
            action = self.create_logo(instruction)
        elif "branding" in instruction.lower():
            action = self.create_branding_document()
        else:
            self.generic_message(instruction)
            action = f"{self.name} processed the instruction: {response}"

        self.store_in_memory(instruction, action)
        return action

    def generic_message(self, text) -> str:
        """General endpoint to have a conversation with the marketing agent."""
        prompt=f"""
                As the marketing lead of a fast-growing tech startup, you're known for your artistic eye. You’ve been brought into a Slack discussion where various artistic challenges are being debated. Read the following message carefully and respond with sound technical advice, thoughtful insights, and clear action points. Your tone should be confident but approachable, demonstrating strong leadership while maintaining open communication with your team.

                Avoid using markdown formatting. Instead, focus on explaining key artistic ideas in a structured, logical manner. Be sure to provide actionable next steps or solutions to address the technical issues discussed.
                The message you're responding to: {text}

                Now, respond as the marketing with creative flair. Provide creative thoughts and discuss further iterations. Focus on solutions, but keep it conversational. This is a serious matter. Focus on the task at hand.
                """
        response = self.process_instruction_with_llm(prompt)
        self.send_message_to_slack(f"{response}", "C07MF3WH7UJ")



    def create_logo(self):
        """Generates a logo using Replicate API and generates a human-like reply using Cohere, then sends it to Slack."""
        print(f"{self.name} is generating a logo with Replicate...")

        # Static prompt for the logo creation
        logo_prompt = (
            "Design a modern, minimalist logo for a tech company called 'Echo', which builds automated 911 caller systems. "
            "The logo should convey trust, reliability, and quick response. The design should incorporate clean lines, a subtle "
            "tech feel, and a symbol representing communication or emergency response (e.g., a soundwave or signal). Use colors "
            "that evoke safety, such as blue or green, but keep the overall design sleek and professional."
        )

        try:
            # Set up the input for the Replicate API to generate the logo
            input = {
                "prompt": logo_prompt,
                "guidance": 3.5  # Customize guidance if needed
            }

            # Call Replicate API to generate the image
            output = replicate.run(
                "black-forest-labs/flux-dev",
                input=input
            )
            image_url = output[0]  # The first image URL generated

            # Now, generate the human-like message using Cohere
            message_prompt = (
                "Generate a friendly, human-like message from a marketer presenting a draft of a new company logo to the team. "
                "The logo is for a tech company called 'Echo', which builds automated 911 caller systems. The message should be "
                "informal, encourage feedback, and describe the design briefly."
            )

            # Call the Cohere API to generate the message
            cohere_response = self.cohere_client.generate(
                model='command-xlarge-nightly',  # Use a large model for high-quality text
                prompt=message_prompt,
                max_tokens=100,
                temperature=0.8  # Adjust the temperature for more creativity
            )

            # Extract the generated message from Cohere's response
            generated_message = cohere_response.generations[0].text.strip()

            # Combine the generated message with the image URL
            message = f"{generated_message}\n\n{image_url}"

            # Send the Cohere-generated message with the image link to Slack
            self.send_image_link_to_slack(message)

            self.metadata["logos"].append({
                "url": image_url,
                "description": generated_message,
                "prompt": logo_prompt  # Storing the prompt for future context
            })

            action = f"{self.name} shared a draft logo: {image_url}"
            return action
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return "Failed to create a logo."

    def create_branding_document(self):
        """Generates a branding document using Cohere and formats it as structured text for Slack."""
        print(f"{self.name} is generating a branding document using Cohere...")

        try:
            # Step 1: Generate branding document using Cohere
            prompt = """
            Generate a clean and professional branding document for a tech startup called 'Stealth Startup.' 
            The document should include the following sections:
            
            1. Company Vision: Explain the long-term vision of the company and its mission to revolutionize the tech industry.
            2. Mission Statement: A short, impactful mission statement that captures the essence of the company.
            3. Brand Colors: Suggest 3 primary brand colors that reflect professionalism, innovation, and security.
            4. Typography: Recommend 2 fonts (one for headers and one for body text) that align with the brand's modern and minimalist aesthetic.
            5. Messaging Tone and Voice: Describe the tone and voice of the company's messaging (e.g., authoritative, friendly, approachable).
            6. Logo Guidelines: Provide basic guidelines for logo usage, including color variations and spacing.
            
            Format the document in a clear, professional manner.
            """

            # Call the Cohere API to generate the branding document text
            response = self.cohere_client.generate(
                model='command-xlarge-nightly',
                prompt=prompt,
                max_tokens=500,
                temperature=0.8
            )

            print("Cohere response received.")
            # Extract the generated document from the response
            branding_document = response.generations[0].text.strip()

            # Check if the branding document is valid
            if not branding_document:
                raise ValueError("Cohere API did not return a valid branding document.")

            print(f"Generated Branding Document: {branding_document[:100]}...")  # Print a preview of the document

            # Step 2: Format the branding document dynamically
            formatted_document = self.format_branding_document(branding_document)

            # Step 3: Send the formatted branding document to Slack
            self.send_text_to_slack(formatted_document)

            # Store the branding document in metadata
            self.metadata["branding_documents"].append({
                "content": branding_document,
                "formatted": formatted_document,
                "prompt": prompt
            })

            print("Branding document stored in metadata and sent to Slack successfully.")
            action = f"{self.name} created and shared a formatted branding document."

            print("Formatted branding document sent to Slack successfully.")
            action = f"{self.name} created and shared a formatted branding document."
            return action

        except Exception as e:
            print(f"An error occurred while generating the branding document: {e}")
            return "Failed to create a branding document."
    
    def send_text_to_slack(self, text):
        """Sends a text message to a Slack channel."""
        try:
            response = self.slack_client.chat_postMessage(
                channel="C07MF3WH7UJ",  # Replace with your Slack channel ID
                text=text
            )
            print("Branding document sent to Slack successfully!")
        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")

    def send_image_link_to_slack(self, message):
        """Sends the generated message along with the image link to a Slack channel."""
        try:
            response = self.slack_client.chat_postMessage(
                channel="C07MF3WH7UJ",  # Replace with your Slack channel ID
                text=message
            )
            print("Cohere-generated message with image URL sent to Slack successfully!")
        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")
    
    def format_branding_document(self, branding_document):
        """
        Formats the branding document text dynamically by applying bullet points and basic formatting
        to specific sections like 'Company Vision', 'Mission Statement', 'Brand Colors', etc.
        """
        # Example of dynamically splitting and formatting the document
        sections = branding_document.split("\n")

        formatted_document = "*Here is the latest branding document:*\n\n"

        for section in sections:
            if "Company Vision" in section:
                formatted_document += "*1. Company Vision*\n"
            elif "Mission Statement" in section:
                formatted_document += "*2. Mission Statement*\n"
            elif "Brand Colors" in section:
                formatted_document += "*3. Brand Colors*\n"
            elif "Typography" in section:
                formatted_document += "*4. Typography*\n"
            elif "Messaging Tone and Voice" in section:
                formatted_document += "*5. Messaging Tone and Voice*\n"
            elif "Logo Guidelines" in section:
                formatted_document += "*6. Logo Guidelines*\n"
            else:
                # Default case: Add bullets for content under each section
                cleaned_section = section.strip()
                if cleaned_section:  # Check if the section contains any text
                    formatted_document += f"• {cleaned_section}\n"

        formatted_document += "\n*Happy to take any suggestions!* :page_facing_up:"
        
        return formatted_document

    def execute_task(self, instruction):
        return self.take_instruction(instruction)
    
    def generate_message(self, text):
        # potentially change
        return self.take_instruction(text)



class CTOAgent(BaseAgent):
    def __init__(self, name, id, cohere_api_key, slack_token, github_repo_path, github_token):
        super().__init__(name, id, "CTO", cohere_api_key, slack_token)
        self.github_repo_path = github_repo_path  # Path to the local GitHub repository
        self.github_token = github_token  # GitHub Personal Access Token (for HTTPS authentication)
        self.swe_agent = SWEAgent(self.github_repo_path)  # Initialize the SWEAgent to handle project changes

    def take_instruction(self, instruction):
        """Process an instruction to implement code-related changes."""
        print(f"{self.name} received instruction: {instruction}")
        self.code(instruction)

    def code(self, task_description):
        """Generates code changes and pushes them to the linked repository."""
        print(f"{self.name} is executing the code function.")

        # Step 1: Map the project directory
        project_map = self.swe_agent.map_directory()

        # Step 2: Propose changes based on the task
        proposed_changes = self.swe_agent.propose_changes(task_description)

        # Step 3: Ask for confirmation to implement the changes
        """ user_input = input("Do you want to implement the proposed changes? (Y/N): ")
        if user_input.strip().upper() == 'Y': """
        self.swe_agent.implement_feature(proposed_changes)
        print("Changes implemented. Pushing to GitHub...")
        self.push_changes_to_github()
        """ else:
            print("Changes were not implemented.") """

    def push_changes_to_github(self):
        """Commit and push the changes to the linked GitHub repository."""
        self.swe_agent.commit_changes()  # Commit changes using SWEAgent
        print(f"Changes have been committed to the repository at {self.github_repo_path}.")

        # Push the committed changes to the GitHub repository
        try:
            repo_url = f"https://{self.github_token}@github.com/rajansagarwal/stealth-startup-dev.git"
            os.system(f'git -C {self.github_repo_path} push {repo_url}')
            print(f"Changes pushed to {repo_url}.")
        except Exception as e:
            print(f"Failed to push changes: {e}")

    def view_ceo_memory(self, ceo_agent):
        """View the memory/messages of the CEO (or other agent)."""
        memory = ceo_agent.recall_memory()
        if memory:
            print(f"{ceo_agent.name}'s Memory:")
            for idx, entry in enumerate(memory):
                print(f"{idx + 1}. Instruction: {entry['instruction']}")
                print(f"   Action: {entry['action']}")
        else:
            print(f"{ceo_agent.name} has no stored memory or messages.")

    def generate_message(self, text) -> str:
        """General endpoint to have a conversation with the CTO agent."""
        prompt=f"""
                As the CTO of a fast-growing tech startup, you're known for your deep technical expertise and ability to simplify complex subjects. You’ve been brought into a Slack discussion where various technical challenges are being debated. Read the following message carefully and respond with sound technical advice, thoughtful insights, and clear action points. Your tone should be confident but approachable, demonstrating strong leadership while maintaining open communication with your team.

                Avoid using markdown formatting. Instead, focus on explaining key technical ideas in a structured, logical manner. Use precise language that non-technical and technical members alike can understand. Be sure to provide actionable next steps or solutions to address the technical issues discussed.

                Example topics that might arise:
                - Architecture design decisions (e.g., microservices vs monolithic architecture)
                - Cloud infrastructure choices (e.g., AWS, Azure, GCP)
                - Software scalability challenges
                - DevOps pipelines and automation best practices
                - Implementing security protocols
                - Talking about the codebase and best practices

                The message you're responding to: {text}

                Now, respond as the CTO with sound technical knowledge. Assign another employee a task directly. Make the task specific. Focus on solutions, but keep it conversational. Be extremely serious.
                """
        response = self.process_instruction_with_llm(prompt)
        self.send_message_to_slack(f"{self.summarize(response)}", "C07MF3WH7UJ")

