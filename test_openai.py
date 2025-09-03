#!/usr/bin/env python3
"""
Test script to verify OpenAI integration
"""
from openai import OpenAI

# Configure OpenAI with your API key
api_key = ("sk-proj-h-a4m2ytlim46bq2Hj7XLsJ0P_shBPjVTAWE3OwqVw4ycDFDCGvPuL"
           "Y7IZmheSjFOM9O3oGIbLT3BlbkFJZ_DejDQN9aX0boJMYacQQq1gFCo3lx"
           "n4jnu_eY0CbAF2WeQh_u7ShNNfJJkreFe4tQhw1pCs4A")
client = OpenAI(api_key=api_key)

def test_openai():
    try:
        print("Testing OpenAI GPT-4 Mini integration...")
        
        # Test question similar to what the main app would ask
        question = ("Generate sample data for an Android email input field. "
                   "The field has ID 'email_input' and hint 'Enter your email'. "
                   "Provide only a realistic email address.")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": ("Generate realistic sample data for Android "
                                "form fields. Provide only the sample data, "
                                "nothing else. Keep it short and realistic.")
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=50,
            temperature=0.3,
            stop=["\n", "."]
        )
        
        if response.choices and response.choices[0].message.content:
            result = response.choices[0].message.content.strip()
            print(f"✅ OpenAI API working! Generated: {result}")
            return True
        else:
            print("❌ Empty response from OpenAI API")
            return False
            
    except Exception as e:
        print(f"❌ Error with OpenAI API: {e}")
        return False

if __name__ == "__main__":
    test_openai()
