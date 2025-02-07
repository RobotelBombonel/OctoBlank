import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from gpt4all import GPT4All
import pygame

# Pygame GUI Setup
pygame.init()
WIDTH, HEIGHT = 800, 600
FONT = pygame.font.SysFont("Arial", 18)
INPUT_FONT = pygame.font.SysFont("Arial", 20)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 120, 215)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("OctoBlank v1.2 Chat")

class ConversationManager:
    """Manages conversation history storage and retrieval"""
    
    def __init__(self, storage_path: str = 'dtb.json'):
        self.storage_path = storage_path
        self.history: List[Dict[str, Any]] = []
        self._load_history()
        
        # Initialize model with context-aware parameters
        self.model = GPT4All('orca-mini-3b-gguf2-q4_0.gguf')
        self.context_window = 2048  # Context window size in tokens
        self.max_history_messages = 20  # Maximum messages to keep in memory
        
    def _load_history(self) -> None:
        """Load conversation history from JSON storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history = []
            
    def _save_history(self) -> None:
        """Save conversation history to JSON storage"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
            
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        self.history.append(message)
        self._save_history()
        
    def delete_all_history(self) -> None:
        """Delete all conversation history"""
        self.history = []
        self._save_history()
        print("All conversation history deleted.")
        
    def delete_specific_entry(self, keyword: str) -> None:
        """Delete specific entries containing a keyword"""
        self.history = [msg for msg in self.history if keyword.lower() not in msg['content'].lower()]
        self._save_history()
        print(f"All entries containing '{keyword}' have been deleted.")
        
    def get_context_prompt(self) -> str:
        """Generate context-aware prompt from conversation history"""
        context = "You are OctoBlank v1.2, an AI created with Python scripts and a JSON database. Previous conversation:\n"
        for msg in self.history[-self.max_history_messages:]:
            context += f"{msg['role'].capitalize()}: {msg['content']}\n"
        context += "\nAssistant:"
        return context[:self.context_window]
    
    def generate_response(self, user_input: str) -> str:
        """Generate intelligent response using conversation context"""
        self.add_message('user', user_input)
        
        prompt = self.get_context_prompt()
        
        try:
            with self.model.chat_session():
                response = self.model.generate(
                    prompt=prompt,
                    temp=0.7,  # Temperature for creativity
                    top_k=40,  # Diversity control
                    max_tokens=500,  # Response length limit
                    streaming=False
                )
                
            # Post-process response
            response = response.strip()
            if 'Assistant:' in response:
                response = response.split('Assistant:')[-1].strip()
                
            self.add_message('assistant', response)
            return response
            
        except Exception as e:
            return f"Error generating response: {e}"


def wrap_text(text: str, font, max_width: int) -> List[str]:
    """Wrap text to fit within a specified width"""
    words = text.split(' ')
    lines = []
    current_line = ''
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_chat(screen, messages: List[str], input_text: str):
    """Draw the chat interface"""
    screen.fill(WHITE)
    y_offset = 20
    
    # Display messages with text wrapping
    for msg in messages:
        wrapped_lines = wrap_text(msg, FONT, WIDTH - 40)
        for line in wrapped_lines:
            text_surface = FONT.render(line, True, BLACK)
            screen.blit(text_surface, (20, y_offset))
            y_offset += 30
    
    # Input box
    pygame.draw.rect(screen, GRAY, (20, HEIGHT - 60, WIDTH - 140, 40))
    input_surface = INPUT_FONT.render(input_text, True, BLACK)
    screen.blit(input_surface, (30, HEIGHT - 55))
    
    # Send button
    pygame.draw.rect(screen, BLUE, (WIDTH - 110, HEIGHT - 60, 90, 40))
    send_text = FONT.render("Send", True, WHITE)
    screen.blit(send_text, (WIDTH - 90, HEIGHT - 50))
    
    pygame.display.flip()


def main():
    bot = ConversationManager()
    messages = []
    input_text = ""
    clock = pygame.time.Clock()
    
    print("OctoBlank v1.2 - Advanced AI Chatbot")
    print("Type '/exit' to quit, '/deldtb' to delete all history, or '/costumdeldtb' to delete specific entries.")
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Add a new line instead of sending the message
                    input_text += '\n'
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if WIDTH - 110 <= mouse_pos[0] <= WIDTH - 20 and HEIGHT - 60 <= mouse_pos[1] <= HEIGHT - 20:
                    # Send button clicked
                    if input_text.strip().lower() == '/exit':
                        pygame.quit()
                        sys.exit()
                    elif input_text.strip().lower() == '/deldtb':
                        bot.delete_all_history()
                        messages.append("System: All conversation history deleted.")
                    elif input_text.strip().lower() == '/costumdeldtb':
                        messages.append("OctoBlank: What do you want to delete from the memory?")
                        draw_chat(screen, messages, "")
                        pygame.display.flip()
                        
                        # Wait for user input
                        deleting = True
                        while deleting:
                            for ev in pygame.event.get():
                                if ev.type == pygame.KEYDOWN:
                                    if ev.key == pygame.K_RETURN:
                                        bot.delete_specific_entry(input_text.strip())
                                        messages.append(f"System: Entries containing '{input_text.strip()}' have been deleted.")
                                        deleting = False
                                        input_text = ""
                                    elif ev.key == pygame.K_BACKSPACE:
                                        input_text = input_text[:-1]
                                    else:
                                        input_text += ev.unicode
                            draw_chat(screen, messages, input_text)
                            pygame.display.flip()
                            clock.tick(30)
                    else:
                        response = bot.generate_response(input_text.strip())
                        messages.append(f"You: {input_text.strip()}")
                        messages.append(f"OctoBlank: {response}")
                    input_text = ""
        
        draw_chat(screen, messages, input_text)
        clock.tick(30)


if __name__ == "__main__":
    main()
