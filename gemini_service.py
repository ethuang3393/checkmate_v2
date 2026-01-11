import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_subtasks(todo_title):
    """
    Returns a list of 5 string subtasks.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = (
            f"I have a to-do list item titled: '{todo_title}'. "
            "Please break this down into exactly 5 actionable, concrete sub-tasks. "
            "Return the response ONLY as a raw JSON array of strings. "
            "Example format: [\"Step 1\", \"Step 2\", ...]"
        )

        response = model.generate_content(prompt)
        text_response = response.text

        # Clean up potential markdown formatting (```json ... ```)
        clean_text = text_response.replace('```json', '').replace('```', '').strip()
        
        tasks_list = json.loads(clean_text)
        
        # Ensure we just take the first 5 if model hallucinates more
        return tasks_list[:5]
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Fallback if API fails
        return [
            "Define requirements", 
            "Research options", 
            "Draft initial version", 
            "Review and refine", 
            "Finalize execution"
        ]