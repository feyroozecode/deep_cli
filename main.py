#!/usr/bin/env python3
import os
import json
import datetime
import argparse
import time
import dotenv
from pathlib import Path
from typing import List, Dict, Optional, Union
import textwrap
from openai import OpenAI
import uuid
import locale

# Load environment variables from .env file
dotenv.load_dotenv()

# Constants
HISTORY_DIR = Path("chat_history")
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://inference.baseten.co/v1")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-ai/DeepSeek-R1-0528")
CONFIG_FILE = Path("config.json")
LOCALES_DIR = Path("locales")
SUPPORTED_LANGUAGES = ["en", "fr", "ar"]
DEFAULT_LANGUAGE = "en"

# ANSI Colors for better UX
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Ensure directories exist
if not HISTORY_DIR.exists():
    HISTORY_DIR.mkdir(parents=True)
if not LOCALES_DIR.exists():
    LOCALES_DIR.mkdir(parents=True)

def load_translations(lang_code: str) -> Dict:
    """Load translation strings for the specified language."""
    if lang_code not in SUPPORTED_LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    
    try:
        with open(LOCALES_DIR / f"{lang_code}.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to English if translation file is missing or invalid
        try:
            with open(LOCALES_DIR / "en.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If even English fails, return a basic dictionary with minimal text
            return {"app_name": "DeepSeek CLI Chat"}

def load_config() -> Dict:
    """Load configuration from file or create default."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Always use environment variables for sensitive data if available
            if API_KEY:
                config["api_key"] = API_KEY
            if BASE_URL:
                config["base_url"] = BASE_URL
            if MODEL:
                config["model"] = MODEL
            
            # Set default language if not present
            if "language" not in config:
                config["language"] = DEFAULT_LANGUAGE
            
            return config
    else:
        if not API_KEY:
            print(f"{Colors.RED}Warning: DEEPSEEK_API_KEY not found in environment variables.{Colors.ENDC}")
            print(f"{Colors.RED}Please set it in the .env file or through the configuration menu.{Colors.ENDC}")
            
        default_config = {
            "api_key": API_KEY,
            "base_url": BASE_URL,
            "model": MODEL,
            "temperature": 0.7,
            "max_tokens": 1000,
            "save_history": True,
            "show_timestamps": True,
            "language": DEFAULT_LANGUAGE
        }
        save_config(default_config)
        return default_config

def save_config(config: Dict) -> None:
    """Save configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

class Conversation:
    def __init__(self, id: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.messages: List[Dict] = []
        self.title = f"Conversation-{self.id[:8]}"
        self.created_at = datetime.datetime.now().isoformat()
        self.last_updated = self.created_at
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        timestamp = datetime.datetime.now().isoformat()
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": timestamp
        })
        self.last_updated = timestamp
    
    def to_dict(self) -> Dict:
        """Convert conversation to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "messages": self.messages
        }
    
    def save(self) -> Path:
        """Save conversation to a Markdown file."""
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{self.title}.md"
        filepath = HISTORY_DIR / filename
        
        # Format conversation as Markdown
        with open(filepath, 'w') as f:
            f.write(f"# {self.title}\n\n")
            f.write(f"**Created:** {self.created_at}\n")
            f.write(f"**Last Updated:** {self.last_updated}\n")
            f.write(f"**Conversation ID:** {self.id}\n\n")
            f.write("---\n\n")
            
            for msg in self.messages:
                role_display = "You" if msg["role"] == "user" else "DeepSeek AI"
                f.write(f"### {role_display} ({msg['timestamp']})\n\n")
                f.write(f"{msg['content']}\n\n")
                f.write("---\n\n")
        
        return filepath
    
    @classmethod
    def from_file(cls, filepath: Path) -> 'Conversation':
        """Load conversation from a Markdown file."""
        conv = cls()
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Parse basic metadata
        conv.title = lines[0].strip('# \n')
        
        # Simplified parsing - in a real app, this would be more robust
        current_role = None
        current_content = []
        current_timestamp = None
        
        for line in lines[5:]:  # Skip header lines
            if line.startswith('### '):
                # Save previous message if exists
                if current_role and current_content:
                    conv.messages.append({
                        "role": "user" if "You" in current_role else "assistant",
                        "content": ''.join(current_content).strip(),
                        "timestamp": current_timestamp or datetime.datetime.now().isoformat()
                    })
                    current_content = []
                
                # Parse new message header
                header = line.strip('### \n')
                current_timestamp = header.split('(')[1].split(')')[0] if '(' in header else None
                current_role = "user" if "You" in header else "assistant"
            elif line.strip() != "---" and current_role:
                current_content.append(line)
        
        # Add the last message if exists
        if current_role and current_content:
            conv.messages.append({
                "role": "user" if "You" in current_role else "assistant",
                "content": ''.join(current_content).strip(),
                "timestamp": current_timestamp or datetime.datetime.now().isoformat()
            })
        
        return conv

def list_conversation_history() -> List[Path]:
    """List all conversation history files."""
    if not HISTORY_DIR.exists():
        return []
    return sorted(HISTORY_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)

def display_conversations(files: List[Path], strings: Dict) -> None:
    """Display a list of conversation files."""
    if not files:
        print(f"{Colors.YELLOW}{strings['history']['empty']}{Colors.ENDC}")
        return
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{strings['history']['title']}{Colors.ENDC}\n")
    for i, file in enumerate(files, 1):
        # Extract timestamp and title from filename
        parts = file.stem.split('_', 1)
        if len(parts) > 1:
            timestamp, title = parts
            date_format = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
        else:
            date_format = "Unknown date"
            title = parts[0]
        
        print(f"{Colors.BOLD}{i}.{Colors.ENDC} [{date_format}] {Colors.CYAN}{title}{Colors.ENDC}")

def view_conversation(filepath: Path, strings: Dict) -> None:
    """View the content of a conversation file."""
    if not filepath.exists():
        print(f"{Colors.RED}Conversation file not found.{Colors.ENDC}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Simple formatting for CLI display
    print(f"\n{Colors.BOLD}{Colors.HEADER}" + "="*60 + f"{Colors.ENDC}")
    lines = content.split("\n")
    print(f"{Colors.BOLD}{Colors.BLUE}{lines[0]}{Colors.ENDC}")
    
    in_message = False
    role = None
    
    for line in lines[1:]:
        if line.startswith("### You"):
            role = "user"
            in_message = True
            print(f"\n{Colors.BOLD}{Colors.GREEN}{strings['chat']['you']}:{Colors.ENDC}")
        elif line.startswith("### DeepSeek AI"):
            role = "assistant"
            in_message = True
            print(f"\n{Colors.BOLD}{Colors.CYAN}{strings['chat']['ai']}:{Colors.ENDC}")
        elif line.strip() == "---":
            in_message = False
        elif in_message and role:
            if role == "user":
                print(f"{Colors.GREEN}{line}{Colors.ENDC}")
            else:
                print(f"{Colors.CYAN}{line}{Colors.ENDC}")
        elif line.startswith("**"):
            print(f"{Colors.YELLOW}{line}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}" + "="*60 + f"{Colors.ENDC}\n")

def setup_client(config: Dict) -> OpenAI:
    """Setup and return OpenAI client."""
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"]
    )

def chat_with_model(client: OpenAI, messages: List[Dict], config: Dict, strings: Dict) -> str:
    """Send messages to the model and stream the response."""
    api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    
    response = client.chat.completions.create(
        model=config["model"],
        messages=api_messages,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        stop=[],
        stream=True,
        stream_options={
            "include_usage": True,
            "continuous_usage_stats": True
        },
        top_p=1,
        presence_penalty=0,
        frequency_penalty=0
    )
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{strings['chat']['ai']}:{Colors.ENDC} ", end="", flush=True)
    full_response = ""
    
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(f"{Colors.CYAN}{content}{Colors.ENDC}", end="", flush=True)
            full_response += content
            # Add small delay for more natural feeling
            time.sleep(0.01)
    
    print("\n")
    return full_response

def configure_settings(config: Dict, strings: Dict) -> Dict:
    """Allow user to configure application settings."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{strings['settings']['title']}{Colors.ENDC}\n")
    
    api_key_display = f"{config['api_key'][:5]}...{config['api_key'][-5:]}" if config['api_key'] and len(config['api_key']) > 10 else "[Not Set]"
    print(f"1. {strings['settings']['api_key']}: {api_key_display}")
    print(f"2. {strings['settings']['base_url']}: {config['base_url']}")
    print(f"3. {strings['settings']['model']}: {config['model']}")
    print(f"4. {strings['settings']['temperature']}: {config['temperature']}")
    print(f"5. {strings['settings']['max_tokens']}: {config['max_tokens']}")
    print(f"6. {strings['settings']['save_history']}: {config['save_history']}")
    print(f"7. {strings['settings']['show_timestamps']}: {config['show_timestamps']}")
    print(f"8. {strings['settings']['language']}: {strings['languages'][config['language']]}")
    print(f"9. {strings['settings']['save_return']}")
    
    choice = input(f"\n{Colors.BOLD}{strings['settings']['select_prompt']}{Colors.ENDC} ")
    
    if choice == '1':
        new_key = input(f"{strings['settings']['enter_new']} {strings['settings']['api_key']}: ")
        config['api_key'] = new_key
        print(f"{Colors.YELLOW}{strings['settings']['note_config_only']}{Colors.ENDC}")
        print(f"{Colors.YELLOW}{strings['settings']['note_env_persist']} DEEPSEEK_API_KEY.{Colors.ENDC}")
    elif choice == '2':
        new_url = input(f"{strings['settings']['enter_new']} {strings['settings']['base_url']}: ")
        config['base_url'] = new_url
        print(f"{Colors.YELLOW}{strings['settings']['note_env_persist']} DEEPSEEK_BASE_URL.{Colors.ENDC}")
    elif choice == '3':
        new_model = input(f"{strings['settings']['enter_new']} {strings['settings']['model']}: ")
        config['model'] = new_model
        print(f"{Colors.YELLOW}{strings['settings']['note_env_persist']} DEEPSEEK_MODEL.{Colors.ENDC}")
    elif choice == '4':
        temp = input(f"{strings['settings']['enter_new']} {strings['settings']['temperature']} (0.0-1.0): ")
        try:
            config['temperature'] = float(temp)
        except ValueError:
            print(f"{Colors.RED}{strings['warnings']['invalid_value']}{Colors.ENDC}")
    elif choice == '5':
        tokens = input(f"{strings['settings']['enter_new']} {strings['settings']['max_tokens']}: ")
        try:
            config['max_tokens'] = int(tokens)
        except ValueError:
            print(f"{Colors.RED}{strings['warnings']['invalid_value']}{Colors.ENDC}")
    elif choice == '6':
        save = input(f"{strings['settings']['save_history']} ({strings['settings']['yes_no']}): ").lower()
        config['save_history'] = save.startswith(strings['settings']['yes_no'][0])
    elif choice == '7':
        timestamps = input(f"{strings['settings']['show_timestamps']} ({strings['settings']['yes_no']}): ").lower()
        config['show_timestamps'] = timestamps.startswith(strings['settings']['yes_no'][0])
    elif choice == '8':
        print("\n" + "-"*40)
        for i, lang in enumerate(SUPPORTED_LANGUAGES, 1):
            print(f"{i}. {strings['languages'][lang]}")
        print("-"*40)
        lang_choice = input(f"{strings['settings']['enter_new']} {strings['settings']['language']}: ")
        try:
            lang_idx = int(lang_choice) - 1
            if 0 <= lang_idx < len(SUPPORTED_LANGUAGES):
                config['language'] = SUPPORTED_LANGUAGES[lang_idx]
                print(f"{Colors.GREEN}{strings['languages'][config['language']]} {strings['settings']['saved']}{Colors.ENDC}")
                # Return config early to reload translations
                save_config(config)
                return config
            else:
                print(f"{Colors.RED}{strings['settings']['invalid_choice']}{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}{strings['settings']['invalid_choice']}{Colors.ENDC}")
    elif choice == '9':
        save_config(config)
        print(f"{Colors.GREEN}{strings['settings']['saved']}{Colors.ENDC}")
    else:
        print(f"{Colors.RED}{strings['settings']['invalid_choice']}{Colors.ENDC}")
    
    return config

def display_dashboard(config: Dict, strings: Dict):
    """Display the main application dashboard."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}" + "="*60)
    print(f"            🤖  {strings['dashboard']['title']}  🤖")
    print("="*60 + f"{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}1.{Colors.ENDC} {Colors.GREEN}{strings['dashboard']['options']['new_chat']}{Colors.ENDC}")
    print(f"{Colors.BOLD}2.{Colors.ENDC} {Colors.CYAN}{strings['dashboard']['options']['view_history']}{Colors.ENDC}")
    print(f"{Colors.BOLD}3.{Colors.ENDC} {Colors.YELLOW}{strings['dashboard']['options']['settings']}{Colors.ENDC}")
    print(f"{Colors.BOLD}4.{Colors.ENDC} {Colors.BLUE}{strings['dashboard']['options']['language']}{Colors.ENDC}")
    print(f"{Colors.BOLD}5.{Colors.ENDC} {Colors.RED}{strings['dashboard']['options']['exit']}{Colors.ENDC}")
    
    choice = input(f"\n{Colors.BOLD}{strings['dashboard']['prompt']}{Colors.ENDC} ")
    return choice

def change_language(config: Dict) -> Dict:
    """Change the application language."""
    # Load current language strings to display language options
    strings = load_translations(config["language"])
    
    print("\n" + "-"*40)
    print(f"{Colors.BOLD}{Colors.HEADER}Select Language / Sélectionner la langue / اختر اللغة:{Colors.ENDC}")
    print("-"*40)
    
    for i, lang in enumerate(SUPPORTED_LANGUAGES, 1):
        lang_name = strings['languages'].get(lang, lang)
        print(f"{i}. {lang_name}")
    
    print("-"*40)
    lang_choice = input("Enter choice / Entrez votre choix / أدخل اختيارك (1-3): ")
    
    try:
        lang_idx = int(lang_choice) - 1
        if 0 <= lang_idx < len(SUPPORTED_LANGUAGES):
            config['language'] = SUPPORTED_LANGUAGES[lang_idx]
            save_config(config)
            # Load new language strings to show confirmation
            new_strings = load_translations(config["language"])
            print(f"{Colors.GREEN}✓ {new_strings['settings']['saved']}{Colors.ENDC}")
        else:
            print(f"{Colors.RED}Invalid choice / Choix invalide / اختيار غير صالح{Colors.ENDC}")
    except ValueError:
        print(f"{Colors.RED}Invalid choice / Choix invalide / اختيار غير صالح{Colors.ENDC}")
    
    return config

def main():
    """Main application function."""
    # Check for API key
    if not API_KEY:
        print(f"\n{Colors.RED}Warning: No API key found in environment variables.{Colors.ENDC}")
        print(f"{Colors.YELLOW}Please set DEEPSEEK_API_KEY in .env file or configure it in the application.{Colors.ENDC}\n")
    
    config = load_config()
    strings = load_translations(config["language"])
    client = setup_client(config)
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}" + "="*60)
    print(f"            🤖  {strings['welcome']['header']}  🤖")
    print("="*60 + f"{Colors.ENDC}\n")
    
    print(f"{Colors.YELLOW}{strings['welcome']['description']}{Colors.ENDC}")
    print(f"{Colors.YELLOW}{strings['welcome']['history_info']}{Colors.ENDC}\n")
    
    while True:
        choice = display_dashboard(config, strings)
        
        if choice == '1':
            # Start new chat
            conversation = Conversation()
            print(f"\n{Colors.BOLD}{Colors.HEADER}{strings['chat']['started']}{Colors.ENDC}")
            print(f"{Colors.YELLOW}{strings['chat']['instructions']}{Colors.ENDC}\n")
            
            while True:
                user_input = input(f"{Colors.BOLD}{Colors.GREEN}{strings['chat']['you']}:{Colors.ENDC} ")
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    if config["save_history"] and conversation.messages:
                        filepath = conversation.save()
                        print(f"\n{Colors.GREEN}{strings['chat']['saved']} {filepath.name}{Colors.ENDC}")
                    break
                
                if user_input.lower() == 'dashboard':
                    if config["save_history"] and conversation.messages:
                        filepath = conversation.save()
                        print(f"\n{Colors.GREEN}{strings['chat']['saved']} {filepath.name}{Colors.ENDC}")
                    break
                
                # Add user message to conversation
                conversation.add_message("user", user_input)
                
                # Get model response
                model_response = chat_with_model(client, conversation.messages, config, strings)
                
                # Add model response to conversation
                conversation.add_message("assistant", model_response)
        
        elif choice == '2':
            # View chat history
            history_files = list_conversation_history()
            display_conversations(history_files, strings)
            
            if history_files:
                history_choice = input(f"\n{Colors.BOLD}{strings['history']['view_prompt']}{Colors.ENDC} ")
                
                if history_choice.lower() != 'b':
                    try:
                        idx = int(history_choice) - 1
                        if 0 <= idx < len(history_files):
                            view_conversation(history_files[idx], strings)
                        else:
                            print(f"{Colors.RED}{strings['history']['invalid_selection']}{Colors.ENDC}")
                    except ValueError:
                        print(f"{Colors.RED}{strings['history']['enter_valid']}{Colors.ENDC}")
        
        elif choice == '3':
            # Configure settings
            config = configure_settings(config, strings)
            strings = load_translations(config["language"])
            client = setup_client(config)
        
        elif choice == '4':
            # Change language
            config = change_language(config)
            strings = load_translations(config["language"])
            client = setup_client(config)
        
        elif choice == '5':
            # Exit
            print(f"\n{Colors.BOLD}{Colors.BLUE}{strings['exit_message']}{Colors.ENDC}\n")
            break
        
        else:
            print(f"{Colors.RED}{strings['settings']['invalid_choice']}{Colors.ENDC}")

if __name__ == "__main__":
    main()