import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def categorize_expense(description: str) -> str:
    if not model:
        return "Uncategorized"
    
    prompt = f"Categorize the following expense description into a single short category word (e.g., Food, Travel, Rent, Utilities, Entertainment, Health, Shopping, Others): '{description}'. Return ONLY the category name."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Error (Categorize): {e}")
        return "Uncategorized"

def generate_insights(expenses: list) -> str:
    if not model:
        return "AI insights are unavailable without an API key."
    
    if not expenses:
        return "No expenses to analyze."
        
    expense_data = ", ".join([f"{e['description']}: ₹{e['amount']}" for e in expenses])
    prompt = f"Analyze the following spending patterns and provide a 1-2 sentence insightful summary (e.g., 'You spent mostly on food this week. Try cooking at home!'). Expenses: {expense_data}"
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Error (Insights): {e}")
        return "Could not generate insights."

def generate_suggested_reply(settlement_message: str) -> str:
    if not model:
        return "Sure, I'll pay you back soon."
        
    prompt = f"Generate a friendly, short 1-sentence reply to the following settlement message: '{settlement_message}'"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Error (Reply): {e}")
        return "Sure, I'll pay you back soon."
