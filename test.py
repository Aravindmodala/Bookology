import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from movie_script_prompt import expand_prompt
from book_generator_prompt import book_prompt
from book_generator import generate_book
from movie_script_generator import generate_movie_script

# Load your OpenAI API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_user_approval(prompt: str) -> bool:
    print("\n=== Story Outline Preview ===")
    print(prompt)
    while True:
        response = input("\nDo you like this story outline? (yes/no): ").lower()
        if response in ['yes', 'no']:
            return response == 'yes'
        print("Please answer 'yes' or 'no'")

def main():
    print("\n=== Story Generator ===")
    print("Choose your format:")
    print("1. Generate Book (Chapter 1)")
    print("2. Generate Movie Script")
    
    while True:
        try:
            choice = int(input("\nEnter your choice (1 or 2): "))
            if choice not in [1, 2]:
                print("Please enter either 1 or 2!")
                continue
            break
        except ValueError:
            print("Please enter a valid number!")
    
    story_idea = input("\nEnter your story idea: ")
    
    if choice == 1:
        # Generate initial story outline
        expanded_prompt = book_prompt(story_idea)
        
        # Keep trying new outlines until user approves or gives up
        while True:
            if get_user_approval(expanded_prompt):
                print("\nGenerating Chapter 1...\n")
                result = generate_book(story_idea)
                print("=== Your Generated Chapter 1 ===")
                break
            else:
                retry = input("\nWould you like to try another story outline? (yes/no): ").lower()
                if retry != 'yes':
                    print("\nExiting without generating story.")
                    return
                expanded_prompt = book_prompt(story_idea)
    else:
        result = generate_movie_script(story_idea)
        print("=== Your Generated Movie Script ===")
    
    print("\n" + result)

if __name__ == "__main__":
    main()
