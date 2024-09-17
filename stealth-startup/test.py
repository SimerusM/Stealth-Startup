import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from agent import CEO, CTO
from dictator import Dictator
import time

# Load environment variables from .env file
load_dotenv()

# Initialize the Slack WebClient with Bot User OAuth Token

# Initialize the agent
cohere_api_key = os.getenv("COHERE_API_KEY")
slack_token = os.getenv("IAN_K_SLACK_BOT_TOKEN")
ceo_slack_id = "U07M0K20NB1"
client = WebClient(token=slack_token)

# Initialize the CEO agent
#ceo_agent = CEO(name="Alice", id=ceo_slack_id, cohere_api_key=cohere_api_key, slack_token=slack_token)

repo_path = "../stealth-startup-dev"  # Path to the external repo

# Initialize CEO and CTO agents
ceo_agent = CEO(name="Alice", id=ceo_slack_id, cohere_api_key=cohere_api_key, slack_token=slack_token)
cto_agent = CTO(name="Bob", id=ceo_slack_id, cohere_api_key=cohere_api_key, slack_token=slack_token, github_repo_path=repo_path, github_token=os.getenv("GITHUB_PAT"))

# Define the coding task
task_description = "Fix the formatting and improve the design. Make it more modern."

# Run the CTO agent to code based on CEO's memory and push changes to GitHub
cto_agent.take_instruction(task_description)