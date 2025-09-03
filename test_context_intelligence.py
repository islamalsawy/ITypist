#!/usr/bin/env python3
"""
Test the new intelligent context-driven field analysis
"""
from openai import OpenAI

# Configure OpenAI
api_key = ("sk-proj-h-a4m2ytlim46bq2Hj7XLsJ0P_shBPjVTAWE3OwqVw4ycDFDCGvPuL"
           "Y7IZmheSjFOM9O3oGIbLT3BlbkFJZ_DejDQN9aX0boJMYacQQq1gFCo3lx"
           "n4jnu_eY0CbAF2WeQh_u7ShNNfJJkreFe4tQhw1pCs4A")
client = OpenAI(api_key=api_key)

def test_context_analysis():
    """Test intelligent context analysis without explicit if-else"""
    
    test_contexts = [
        {
            "description": "Email field in Gmail app",
            "context": ("Analyze this Android form field and generate appropriate sample data. "
                       "App Context: This is a gmail app. "
                       "Field Details: The purpose of this input component may be 'email address'. "
                       "Surrounding Elements: There is a component on the same vertical line as this input component. "
                       "Its type is Button and its text is 'Sign In'. "
                       "Instructions: Based on the app name, field labels, surrounding UI elements, "
                       "and field ID, intelligently determine what type of data this field expects "
                       "and generate a realistic example that a real user would type. "
                       "Respond with ONLY the sample data - no explanations or quotes.")
        },
        {
            "description": "First name field in registration",
            "context": ("Analyze this Android form field and generate appropriate sample data. "
                       "App Context: This is a signup app. "
                       "Field Details: The label of this component is 'First Name'. "
                       "The purpose of this input component may be 'first name input'. "
                       "Surrounding Elements: There is a component on the same vertical line as this input component. "
                       "Its text is 'Last Name'. Another component says 'Create Account'. "
                       "Instructions: Based on the app name, field labels, surrounding UI elements, "
                       "and field ID, intelligently determine what type of data this field expects "
                       "and generate a realistic example that a real user would type. "
                       "Respond with ONLY the sample data - no explanations or quotes.")
        },
        {
            "description": "Password field",
            "context": ("Analyze this Android form field and generate appropriate sample data. "
                       "App Context: This is a banking app. "
                       "Field Details: The purpose of this input component may be 'password field'. "
                       "Surrounding Elements: There is a component on the same horizontal line as this input component. "
                       "Its text is 'Show'. There is also a 'Login' button nearby. "
                       "Instructions: Based on the app name, field labels, surrounding UI elements, "
                       "and field ID, intelligently determine what type of data this field expects "
                       "and generate a realistic example that a real user would type. "
                       "Respond with ONLY the sample data - no explanations or quotes.")
        }
    ]
    
    for test in test_contexts:
        print(f"\n🧪 Testing: {test['description']}")
        print(f"📝 Context: {test['context'][:100]}...")
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": ("You are an expert Android UI analyst. Analyze form field "
                                   "context (app name, labels, surrounding elements, field IDs) "
                                   "to intelligently determine what data type is expected. "
                                   "Generate realistic sample data that real users would type. "
                                   "Examples: emails (john.doe@gmail.com), names (John Smith), "
                                   "phones (+1234567890), passwords (MyPass123), addresses, etc. "
                                   "Respond with ONLY the sample data, no explanations.")
                    },
                    {
                        "role": "user",
                        "content": test['context']
                    }
                ],
                max_tokens=50,
                temperature=0.2,
                stop=["\n", ".", ",", ";", "\"", "'"]
            )
            
            if response.choices and response.choices[0].message.content:
                result = response.choices[0].message.content.strip()
                result = result.replace('"', '').replace("'", '').strip()
                print(f"✅ AI Generated: '{result}'")
                
                # Analyze if it made smart choices
                if "gmail" in test['description'].lower() and "@" in result:
                    print("🎯 Correctly identified email field!")
                elif "first name" in test['description'].lower() and any(name in result for name in ["John", "Jane", "Mike", "Sarah"]):
                    print("🎯 Correctly identified name field!")
                elif "password" in test['description'].lower() and len(result) > 6:
                    print("🎯 Correctly identified password field!")
                else:
                    print("🤔 Let's see if this makes sense for the context...")
            else:
                print("❌ No response")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_context_analysis()
