from groq import Groq
from config import GROQ_API_KEY

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Store conversation history
conversation_history = []

def chat(user_message):
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Send to Groq API
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant named Aria. You are friendly, smart, and concise."
            }
        ] + conversation_history
    )
    
    # Get response
    assistant_message = response.choices[0].message.content
    
    # Add to history
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    return assistant_message

def main():
    print("="*45)
    print("  🤖 ARIA - AI Chatbot powered by Groq")
    print("="*45)
    print("  Type 'quit' or 'exit' to stop")
    print("  Type 'clear' to clear history")
    print("="*45)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ["quit", "exit"]:
            print("\nAria: Goodbye! Have a great day! 👋")
            break
        
        if user_input.lower() == "clear":
            conversation_history.clear()
            print("\n✅ Conversation history cleared!")
            continue
        
        print("\nAria: ", end="", flush=True)
        response = chat(user_input)
        print(response)

if __name__ == "__main__":
    main()