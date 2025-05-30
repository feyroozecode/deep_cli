#!/usr/bin/env python3
"""
Test script for DeepSeek CLI Chat application.
This script demonstrates the core functionality without requiring user input.
"""

import os
import sys
import json
import dotenv
from pathlib import Path
from datetime import datetime

# Load environment variables
dotenv.load_dotenv()

# Import from main module - adjust import path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import Conversation, setup_client, load_config, load_translations, HISTORY_DIR

def test_conversation_creation():
    """Test creating and saving a conversation."""
    print("Testing conversation creation and saving...")
    
    # Create a test conversation
    conv = Conversation()
    conv.title = "Test Conversation"
    
    # Add some test messages
    conv.add_message("user", "Hello, this is a test message")
    conv.add_message("assistant", "Hello! I'm responding to your test message.")
    conv.add_message("user", "Can you tell me about DeepSeek?")
    conv.add_message("assistant", "DeepSeek is an AI model designed for conversational interactions...")
    
    # Save the conversation
    filepath = conv.save()
    
    print(f"Conversation saved to: {filepath}")
    
    # Verify file exists
    if filepath.exists():
        print("✅ Conversation file created successfully")
    else:
        print("❌ Failed to create conversation file")
    
    return filepath

def test_conversation_loading(filepath):
    """Test loading a conversation from a file."""
    print("\nTesting conversation loading...")
    
    # Load the conversation
    loaded_conv = Conversation.from_file(filepath)
    
    # Print basic info
    print(f"Loaded conversation: {loaded_conv.title}")
    print(f"Number of messages: {len(loaded_conv.messages)}")
    
    # Verify content
    if loaded_conv.title == "Test Conversation" and len(loaded_conv.messages) == 4:
        print("✅ Conversation loaded successfully")
    else:
        print("❌ Failed to load conversation correctly")

def test_api_connection():
    """Test connection to the DeepSeek API."""
    print("\nTesting API connection...")
    
    try:
        # Load config and set up client
        config = load_config()
        client = setup_client(config)
        
        # Just test that the client initializes without error
        api_key_display = f"{config['api_key'][:5]}...{config['api_key'][-5:]}" if config['api_key'] and len(config['api_key']) > 10 else "[Not Set]"
        print(f"Client configured with API key: {api_key_display}")
        print(f"Using model: {config['model']}")
        print("✅ API client initialized successfully")
        
        # Check if API key is set
        if not config['api_key']:
            print("⚠️ Warning: No API key configured. Set DEEPSEEK_API_KEY in .env file.")
        
        # We don't actually make an API call here to avoid unnecessary usage
        print("Note: No actual API call made to preserve quota")
    except Exception as e:
        print(f"❌ Failed to initialize API client: {str(e)}")

def test_language_support():
    """Test language support functionality."""
    print("\nTesting language support...")
    
    # Test loading translations for each supported language
    languages = ["en", "fr", "ar"]
    
    for lang in languages:
        try:
            translations = load_translations(lang)
            if translations:
                app_name = translations.get("app_name", "")
                print(f"✅ Loaded {lang} translation: {app_name}")
            else:
                print(f"❌ Failed to load {lang} translation")
        except Exception as e:
            print(f"❌ Error loading {lang} translation: {str(e)}")
    
    # Test config with language setting
    config = load_config()
    current_lang = config.get("language", "en")
    print(f"Current language setting: {current_lang}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("DEEPSEEK CLI CHAT - TEST SUITE")
    print("=" * 60)
    print(f"Running tests at: {datetime.now().isoformat()}")
    print(f"History directory: {HISTORY_DIR}")
    print(f"Environment: {'Using .env file' if os.getenv('DEEPSEEK_API_KEY') else 'No API key in environment'}")
    print("=" * 60)
    
    # Create history directory if it doesn't exist
    if not HISTORY_DIR.exists():
        HISTORY_DIR.mkdir(parents=True)
        print(f"Created history directory: {HISTORY_DIR}")
    
    # Run tests
    filepath = test_conversation_creation()
    test_conversation_loading(filepath)
    test_api_connection()
    test_language_support()
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()