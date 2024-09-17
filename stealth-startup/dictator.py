import os
import cohere
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from agent import CEO
import json
import math
import random
import time

""" 
load_dotenv()

# Initialize the Slack WebClient with Bot User OAuth Token
slack_token = os.getenv("IAN_K_SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

# Initialize the agent
cohere_api_key = os.getenv("COHERE_API_KEY")
ceo_agent = Agent(name="Alice", role="CEO", cohere_api_key=cohere_api_key) """

class Event:
    def __init__(self, name, roles, tool_used=False, metadata=None):
        self.name = name  # The event's name, e.g., "Conduct market research"
        self.roles = roles  # A tuple or list of roles involved in the event, e.g., ("CEO", "CTO")
        self.tool_used = tool_used  # A flag indicating if a tool (like SWEAgent) is needed
        self.metadata = metadata or {}  # Optional additional metadata for the event

    def __repr__(self):
        return f"Event(name={self.name}, roles={self.roles}, tool_used={self.tool_used}, metadata={self.metadata})"


class Dictator:
    def __init__(self, name, cohere_api_key, employees, channel_id, slack_client, roles_to_agents):
        self.current_event_index = 0
        self.cohere_api_key = cohere_api_key
        self.channel_id = channel_id
        self.employees = employees
        #self.channel_id = channel_id  # Replace with your actual Slack channel ID
        self.slack = slack_client
        self.roles_to_agents = roles_to_agents

         # Define events with metadata, assign roles and tool usage flags
        self.events = [
            #Event(name="Conduct market research", roles=("CEO",), tool_used=False),
            #Event(name="Discuss different viewpoints of the product derived from the market research step", roles=("CEO", "CTO"), tool_used=False),
            Event(name="Make changes to the website", roles=("CTO",), tool_used=True, metadata={"task": "Fix the formatting and improve the design. Make it more modern."}),
            Event(name="Design a new logo", roles=("Marketer",), tool_used=True, metadata={"task": "Design a new company logo"}),
            Event(name="Discuss thoughts about the logo design", roles=("CTO", "CEO", "Marketer"), metadata={"CEO": "Your viewpoint should be that you don't like it.", "CTO": "Your viewpoint should be that you like it.", "Marketer": "Your viewpoint should be that you like it"}),
            Event(name="Add the logo to the website", roles=("CTO",), tool_used=True, metadata={"task": "Integrate new logo into homepage"})
        ]

        # Initialize Cohere Client
        self.cohere_client = cohere.Client(self.cohere_api_key, log_warning_experimental_features=False)

    # Employees = {id: ID, agent: Agent}
    def process_event(self, event, channel_id):
        """Processes a single event by assigning tasks to agents based on roles and tool flags."""
        print(f"Processing Event: {event.name}")

        # Fetch the latest messages from Slack for context
        #self.fetch_slack_messages()

        # If there are multiple agents, initiate a discussion between them
        if len(event.roles) > 1:
            print(f"Initiating a discussion between: {', '.join(event.roles)}")
            self.initiate_discussion(event, channel_id)
        else:
            # Single agent task handling
            for role in event.roles:
                if role in self.roles_to_agents:
                    agent = self.roles_to_agents[role]
                    print(f"Assigning task to {agent.name} ({agent.role})")

                    if event.tool_used:
                        if role == "CTO":
                            agent.take_instruction(event.metadata.get("task", ""))
                        elif role == "Marketer":
                            agent.create_logo()
                    else:
                        # Call the regular agent method to participate in the conversation
                        agent.take_instruction(event.name)

    

    def initiate_discussion(self, event, channel_id):
        counter = 0
        while counter < 8:
            time.sleep(5)
            try:
                response = self.slack.conversations_history(channel=channel_id, limit=6)
                #print(response)
                messages = response['messages']
                if len(messages) > 0:
                    self.process_message(messages)
            except SlackApiError as e:
                print(f"Error retrieving messages: {e.response['error']}")
                messages = []
                return
            counter += 1

    def process_message(self, messages):
        prompt = self.build_prompt(messages)
        response = self.cohere_client.chat(
            message=prompt,
            temperature=0.5,
            max_tokens=600,
            response_format={
  "type": "json_object",
  "schema": {
    "type": "object",
    "properties": {
      "progress": {
        "type": "integer"
      },
      "value": {
        "type": "string"
      },
      "employees": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string"
            },
            "response_type": {
              "type": "string"
            }
          },
          "required": ["id", "response_type"]
        }
      }
    },
    "required": ["employees", "progress", "value"]
  }
}
        )
        
        response_json = json.loads(response.text)
        print("\n\n\n\n")
        print(response_json)
        print("\n\n\n\n")
    
        # Access the "employees" key to retrieve the list of objects
        employees = response_json.get("employees", [])
        progress = response_json.get("progress", 0)
        topic = response_json.get("value", "")

        # Now you can iterate over the employees and handle the data
        #print(self.employees)
       # print(self.employees['U07M0K20NB1'].id)
        for employee in employees:
            employee_id = employee.get("id")
            response_type = employee.get("response_type")
            #print(f"Employee ID: {employee_id}, Response Type: {response_type}")
            # Process the employee's information
            print(f"CURRENTLY AT {self.get_employee_name(employee_id)}")
            if employee_id in self.employees and employee_id != messages[0]['user']:
                prompt = f"""You are {self.get_employee_name(employee_id)}, the {self.employees[employee_id].role} of Echo. Echo is a 911 dispatching service that uses AI to help manage emergency calls. You are responding to a message from a team member. You are a technical person with management of the codebase. Your current goal is to do Market Research and evaluate (1) Customers (2) Industry and (3) Market insights and the conversation should NOT stray away from this topic. If it does, take initiative to come back to it until it is complete."""
                
                prompt += "\n\nThis is the previous conversation. Continue on after the last message"
                for message in messages[::-1]:
                    prompt += f"\n{self.get_employee_name(message['user'])}: {message['text']}"
                
                prompt += f"""\n\nMake your message short and informal. Only write the response text without quotations and do not give any prefix. 
                Remember that you are the employee of Echo, an AI-driven service to help manage dispatching. Do not repeat from the past message. Only provide a response for the person, do not include any preamble describing the response. Do not add comments, it is very important that you only provide the final output without any additional comments or remarks. Do not meeting or dicussing. Speak casually, you are close with everyone as you are already all on the team. Do not use the word Great in your response."""
                print("\n\n", prompt)
                self.employees[employee_id].generate_message(prompt)
                break
            else:
                print(f"Employee with ID {employee_id} not found.")
            

        
    def build_prompt(self, messages):
        prompt = """You are the manager of a startup. Based on the input provided, determine the top 3 employees that should respond. The employee can have either a tool response or a message response, determine which response that this should be.""" 

        prompt += "\n\nThe following messages were received:"
        for message in messages:
            prompt += f"\n{self.get_employee_name(message['user'])}: \"{message['text']}\"\n"

        prompt += "Determine the IDs of the to 3 employees in order that they should respond and the response they should provide (tool or message). Ensure they are in the right JSON format. Pick from the following employees:"
        employees_list = list(self.employees.values())
        random.shuffle(employees_list)
        print(employees_list)
        for employee in employees_list:
            prompt += f"\n- ID: {employee.id}"
        
        prompt += f"\n\Regarding this event {self.events[self.current_event_index]}, give a specific topic that was not used before for continuation of the conversation to discuss and store it in \"value\". Give a \"progress\" of 1 to end the conversation. Otherwise, give a 0 to continue this conversation."
        return prompt

    def get_employee_name(self, employee_id):
        #print("\n\nLOOKING FOR ", employee_id)
        #print(self.employees)
        if employee_id in self.employees:
            return self.employees[employee_id].name
        else:
            return employee_id