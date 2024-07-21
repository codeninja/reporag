import autogen
from .code_context import get_code_context

class DocstringGenerator:
    def __init__(self, openai_api_key: str):
        self.config_list = [
            {
                'model': 'gpt-4o',
                'api_key': openai_api_key,
            },
        ]
        self.llm_config = {
            "config_list": self.config_list,
            "seed": 42,
        }

    def generate_docstring(self, file_path: str, method_name: str, start_line: int):
        context = get_code_context(file_path, start_line)
        
        assistant = autogen.AssistantAgent(
            name="DocstringWriter",
            llm_config=self.llm_config,
            system_message="You are an expert Python and Javascript developer. Your task is to write clear and concise docstrings for Python and Javascript methods."
        )

        user_proxy = autogen.UserProxyAgent(
            name="CodeAnalyzer",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config={"work_dir": "coding"},
            llm_config=self.llm_config,
            system_message="You are a code analyzer. Your task is to provide method context to the DocstringWriter and ask for a docstring.",
        )

        user_proxy.initiate_chat(
            assistant,
            message=f"Please write a docstring for the following method:\n\n{context}\n\nProvide only the docstring, nothing else. TERMINATE"
        )

        # Extract the generated docstring from the conversation
        for message in user_proxy.chat_messages[assistant]:
            if "content" in message:
                return message["content"].strip()

        return "Unable to generate docstring."

# Add more methods as needed for docstring generation