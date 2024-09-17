import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from agent import CEO, CTOAgent, Marketer
from dictator import Dictator
import time

# Load environment variables from .env file
load_dotenv()

# Initialize the Slack WebClient with Bot User OAuth Token

# Initialize the agent
cohere_api_key = os.getenv("COHERE_API_KEY")
slack_token = os.getenv("IAN_K_SLACK_BOT_TOKEN")
cto_slack_token = os.getenv("ELIJAH_K_SLACK_BOT_TOKEN")
marketer_slack_token = os.getenv("MARKETER_SLACK_BOT_TOKEN")
replicate_api_token = os.getenv("REPLICATE_API_TOKEN")  # Ensure Replicate API token is loaded
repo_path = "../stealth-startup-dev"  # Path to the external repo
PAT = os.getenv("GITHUB_PAT")
ceo_slack_id = "U07M0K20NB1"
cto_slack_id = "U07MUQUCU6M"
client = WebClient(token=slack_token)
#ceo_slack_id = os.getenv("CEO_SLACK_ID")  # The Slack ID for the CEO

# Initialize agents
ceo_agent = CEO(name="Ian Korovinsky", id=ceo_slack_id, cohere_api_key=cohere_api_key, slack_token=slack_token)
cto_agent = CTOAgent(name="Elijah Kurien", id=cto_slack_id, cohere_api_key=cohere_api_key, slack_token=cto_slack_token, github_repo_path=repo_path, github_token=PAT)
# Initialize the Marketer agent
marketer_agent = Marketer(
    name="Lily Zhang", 
    id="U07MVBVPXB3",  # Replace with your marketer's Slack ID
    role="Marketing Specialist", 
    cohere_api_key=cohere_api_key, 
    slack_token=marketer_slack_token,
    flux_token=replicate_api_token
)

employees = {
    ceo_agent.id: ceo_agent,
    cto_agent.id: cto_agent,
    marketer_agent.id: marketer_agent
}

roles_to_agents = {
    "CEO": ceo_agent,
    "CTO": cto_agent,
    "Marketer": marketer_agent
}

print("\n\nVERY START:", employees)
#print(employees)
dictator = Dictator(name="Dictator", cohere_api_key=cohere_api_key, employees=employees, channel_id="C07MF3WH7UJ", slack_client=client, roles_to_agents=roles_to_agents)

# CEO executes a task (e.g., setting up company goals)
# ceo_agent.take_instruction("the AI-driven healthcare market")

channel_id = "C07MF3WH7UJ"  # Replace with your actual Slack channel ID
messages = []

for event in dictator.events:
    time.sleep(5)
    dictator.process_event(event, channel_id)
