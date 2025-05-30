# DeepSeek CLI Chat Application

A robust command-line interface application for interacting with DeepSeek AI models, featuring conversation history management, configuration options, multilingual support, and a user-friendly dashboard.

![DeepSeek CLI Chat](https://img.shields.io/badge/DeepSeek-CLI%20Chat-blue)
![Python Version](https://img.shields.io/badge/python-3.7%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Languages](https://img.shields.io/badge/languages-English%20%7C%20French%20%7C%20Arabic-brightgreen)

## 🌟 Features

- **Interactive CLI Interface**: Chat with DeepSeek AI models directly from your terminal
- **Conversation History**: All chats are saved as Markdown files with timestamps
- **Dashboard Management**: Easy-to-use dashboard for managing conversations and settings
- **Secure Configuration**: API keys stored in environment variables, not in source code
- **Customizable Settings**: Adjust model parameters, temperature, max tokens, etc.
- **Color-coded Interface**: Enhanced readability with ANSI color formatting
- **Streaming Responses**: Real-time streaming of AI responses for natural interaction
- **Multilingual Support**: Available in English, French, and Arabic

## 📋 Requirements

- Python 3.7+
- OpenAI Python package
- python-dotenv package

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd deepseek_api
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Required Packages

```bash
pip install openai python-dotenv
```

### 4. Set Up Environment Variables

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit the `.env` file and replace `your_api_key_here` with your actual DeepSeek API key.

## 🔧 Configuration

The application uses two configuration mechanisms:

1. **Environment Variables** (recommended for sensitive data):
   - `DEEPSEEK_API_KEY`: Your DeepSeek API key
   - `DEEPSEEK_BASE_URL`: Base URL for the DeepSeek API
   - `DEEPSEEK_MODEL`: Model name to use
   - `DEEPSEEK_LANGUAGE`: Default language (en, fr, ar)

2. **Configuration File** (`config.json`):
   - Contains model parameters and application settings
   - Can be modified through the configuration menu
   - Environment variables take precedence over config file values

## 💻 Usage

### Starting the Application

```bash
./main.py
```

or

```bash
python main.py
```

### Dashboard Options

The main dashboard provides the following options:

1. **Start New Chat**: Begin a new conversation with DeepSeek AI
2. **View Chat History**: Browse and review past conversations
3. **Configure Settings**: Adjust API settings, model parameters, and application preferences
4. **Change Language**: Switch between English, French, and Arabic interfaces
5. **Exit**: Close the application

### Chat Commands

During a chat session, you can use the following commands:

- Type `exit`, `quit`, or `bye` to end the current conversation
- Type `dashboard` to return to the main menu

## 📝 Conversation History

Conversations are automatically saved as Markdown files in the `chat_history` directory. Each file includes:

- Timestamp-based filename for easy sorting
- Conversation title
- Creation and last updated timestamps
- Conversation ID for reference
- Complete message history with timestamps

Example:
```
# My Conversation

**Created:** 2023-09-15T10:30:45.123456
**Last Updated:** 2023-09-15T10:35:12.654321
**Conversation ID:** a1b2c3d4-e5f6-7890-abcd-1234567890ab

---

### You (2023-09-15T10:30:45.123456)

Hello, how can you help me today?

---

### DeepSeek AI (2023-09-15T10:31:02.987654)

I can assist you with a variety of tasks...

---
```

## 🔒 Security

- API keys are stored in `.env` file (excluded from git repository)
- The `.gitignore` file prevents sensitive data from being committed
- Configuration with sensitive information is stored locally only

## 🧪 Testing

A test script is included to verify core functionality:

```bash
python test_chat.py
```

This will test:
- Conversation creation and saving
- Loading conversations from files
- API client configuration

## 📁 Project Structure

```
deepseek_api/
├── main.py              # Main application script
├── test_chat.py         # Test script
├── config.json          # Configuration settings
├── .env                 # Environment variables (not in repo)
├── .env.example         # Example environment file
├── .gitignore           # Git ignore rules
├── locales/             # Translation files directory
│   ├── en.json          # English translations
│   ├── fr.json          # French translations
│   └── ar.json          # Arabic translations
└── chat_history/        # Directory for conversation files
    └── *.md             # Saved conversations
```

## 🌐 Language Support

The application supports the following languages:

- **English**: Default language
- **French**: Full translation of UI elements and messages
- **Arabic**: Full translation with right-to-left (RTL) text support

You can change the language from the dashboard or by setting the `DEEPSEEK_LANGUAGE` environment variable.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- OpenAI for their Python client library
- DeepSeek AI for their powerful language models