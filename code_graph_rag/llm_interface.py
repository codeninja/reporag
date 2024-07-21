import os
import autogen
from dotenv import load_dotenv

load_dotenv()

class LLMInterface:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        self.config_list = [
            {
                'model': 'gpt-4o',
                'api_key': self.openai_api_key,
                'base_url': self.openai_base_url,
            },
            {
                'model': 'gpt-4o-mini',
                'api_key': self.openai_api_key,
                'base_url': self.openai_base_url,
            },
        ]

    def create_assistant(self, name: str, system_message: str, model: str = 'gpt-4o'):
        llm_config = {
            "config_list": [config for config in self.config_list if config['model'] == model],
            "seed": 42,
        }
        
        return autogen.AssistantAgent(
            name=name,
            llm_config=llm_config,
            system_message=system_message
        )

    def create_user_proxy(self, name: str):
        return autogen.UserProxyAgent(
            name=name,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"work_dir": "coding"},
            llm_config={"config_list": self.config_list},
        )

    def run_conversation(self, user_proxy, assistant, initial_message):
        user_proxy.initiate_chat(assistant, message=initial_message)
        return user_proxy.chat_messages[assistant]

# Add more methods as needed for LLM interactions