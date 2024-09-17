import os
from dotenv import load_dotenv
from agent import Marketer  # Assuming Marketer is defined in agent.py

# Load environment variables from .env file
load_dotenv()

# Initialize API keys and Slack token from environment variables
cohere_api_key = os.getenv("COHERE_API_KEY")
slack_token = os.getenv("MARKETER_SLACK_BOT_TOKEN")
replicate_api_token = os.getenv("REPLICATE_API_TOKEN")  # Ensure Replicate API token is loaded

# Check if environment variables are set properly
if not cohere_api_key or not slack_token or not replicate_api_token:
    raise EnvironmentError("Ensure that COHERE_API_KEY, MARKETER_SLACK_BOT_TOKEN, and REPLICATE_API_TOKEN are set in the .env file")

# Initialize the Marketer agent
marketer_agent = Marketer(
    name="MarketingAgent", 
    id="C07MJHRPJS0",  # Replace with your marketer's Slack ID
    role="Marketing Specialist", 
    cohere_api_key=cohere_api_key, 
    slack_token=slack_token,
    flux_token=replicate_api_token
)

# Test the image generation (logo creation)
def test_create_logo():
    # prompt = "Design a modern, minimalist logo for a tech company called 'Echo', which builds automated 911 caller systems. The logo should convey trust, reliability, and quick response. The design should incorporate clean lines, a subtle tech feel, and a symbol representing communication or emergency response (e.g., a soundwave or signal). Use colors that evoke safety, such as blue or green, but keep the overall design sleek and professional."
    print("Testing logo creation...")
    logo_result = marketer_agent.create_logo()
    print(f"Logo creation result: {logo_result}")

# Test the branding document generation
def test_create_branding_document():
    print("Testing branding document creation...")
    branding_result = marketer_agent.create_branding_document()
    print(f"Branding document result: {branding_result}")

if __name__ == "__main__":
    # Run the logo generation test
    # test_create_logo()

    # Run the branding document generation test
    test_create_branding_document()
