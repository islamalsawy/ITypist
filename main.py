import os
import json
import xmltodict
import time
import win32api
import win32con
from openai import OpenAI

# Set ADB path BEFORE importing uiautomator2
android_sdk_path = r"C:\Users\islam.elafify\AppData\Local\Android\Sdk\platform-tools"
current_path = os.environ.get('PATH', '')
if android_sdk_path not in current_path:
    os.environ['PATH'] = android_sdk_path + os.pathsep + current_path
if android_sdk_path not in current_path:
    os.environ['PATH'] = android_sdk_path + os.pathsep + current_path

# Set ADB path environment variables for uiautomator2
os.environ['ANDROID_HOME'] = r"C:\Users\islam.elafify\AppData\Local\Android\Sdk"
os.environ['ANDROID_SDK_ROOT'] = r"C:\Users\islam.elafify\AppData\Local\Android\Sdk"

# Now import uiautomator2 after PATH is set
import uiautomator2 as u2
import pprint

# Configure OpenAI with your API key
api_key = ("sk-proj-h-a4m2ytlim46bq2Hj7XLsJ0P_shBPjVTAWE3OwqVw4ycDFDCGvPuL"
           "Y7IZmheSjFOM9O3oGIbLT3BlbkFJZ_DejDQN9aX0boJMYacQQq1gFCo3lx"
           "n4jnu_eY0CbAF2WeQh_u7ShNNfJJkreFe4tQhw1pCs4A")
client = OpenAI(api_key=api_key)

def getAllComponents(jsondata: dict):

    root = jsondata['hierarchy']

    queue = [root]
    res = []

    while queue:
        currentNode = queue.pop(0)

        if 'node' in currentNode:
            if type(currentNode['node']).__name__ == 'dict':
                queue.append(currentNode['node'])
            else:
                for e in currentNode['node']:
                    queue.append(e)
        else:
            if ('com.android.systemui' not in currentNode['@resource-id']) and (
                    'com.android.systemui' not in currentNode['@package']):
                res.append(currentNode)

    return res


def find_EditText(jsondata: dict):

    all_components = getAllComponents(jsondata)
    ans = []

    for e_component in all_components:
        if '@class' in e_component and (e_component['@class'] == 'android.widget.EditText' or e_component['@class'] == 'android.widget.AutoCompleteTextView'):
            ans.append(e_component)
    return ans


def get_basic_info(e_component: dict):

    key_list = ['id', 'text', 'label', 'text-hint', 'app_name']
    key_at_list = ['resource-id', 'text', 'label', 'content-desc', 'package']
    dict_info = {}

    for i in range(len(key_list)):
        dict_info[key_list[i]] = None
        for e_property in e_component:
            if key_at_list[i] in e_property.lower():
                dict_info[key_list[i]] = e_component[e_property]
                break

    return dict_info


def chooseFromPos(all_components: list, bounds: list):

    
    same_horizon_components = []
    same_vertical_components = []

    for e_component in all_components:
        e_bounds = e_component['@bounds']
        if e_bounds == bounds:
            continue
        if (e_bounds[1], e_bounds[3]) == (bounds[1], bounds[3]):
            same_horizon_components.append(e_component)
        if (e_bounds[0], e_bounds[2]) == (bounds[0], bounds[2]):
            same_vertical_components.append(e_component)

    return same_horizon_components, same_vertical_components


def turn_null_to_str(prop: str):

    if prop == None:
        return ''
    else:
        return prop


def component_basic_info(jsondata: dict):

    text_id = "The purpose of this component may be '<EditText id>'. "
    text_label = "The label of this component is '<label>'. "
    text_text = "The text on this component is '<text>'. "
    text_hint = "The hint text of this component is '<hint>'. "

    if jsondata['id'] == "" or jsondata['id'] == None:
        text_id = ""
    else:
        EditText_id = jsondata['id'].split('/')[-1]
        EditText_id = EditText_id.replace('_', ' ')
        text_id = text_id.replace('<EditText id>', EditText_id)

    if jsondata['label'] == "" or jsondata['label'] == None:
        text_label = ""
    else:
        label = jsondata['label']
        text_label = text_label.replace('<label>', label)

    if jsondata['text'] == "" or jsondata['text'] == None:
        text_text = ""
    else:
        text = jsondata['text']
        text_text = text_text.replace('<text>', text)

    if jsondata['text-hint'] == "" or jsondata['text-hint'] == None:
        text_hint = ""
    else:
        hint = jsondata['text-hint']
        text_hint = text_hint.replace('<hint>', hint)

    return text_id + text_label + text_text + text_hint + '\n'


def isEnglish(s: str):

    s = s.replace('\u2026', '')
    return s.isascii()


def use_context_info_generate_prompt(jsondata: dict):

    text_header = "Question: "
    text_app_name = "This is a <app name> app. "
    text_activity_name = "On its page, it has an input component. "
    text_label = "The label of this component is '<label>'. "
    text_text = "The text on this component is '<text>'. "
    text_context_info = "Below is the relevant prompt information of the input component:\n<context information>"
    text_id = "The purpose of this input component may be '<EditText id>'. "
    text_ask = "What is the hint text of this input component?\n"

    app_name = jsondata['app_name'].split('.')[-1]
    text_app_name = text_app_name.replace('<app name>', app_name)

    if jsondata['label'] == "" or jsondata['label'] == None:
        text_label = ""
    else:
        label = jsondata['label']
        text_label = text_label.replace('<label>', label)

    if jsondata['text'] == "" or jsondata['text'] == None:
        text_text = ""
    else:
        text = jsondata['text']
        text_text = text_text.replace('<text>', text)

    context_info = ""
    if len(jsondata['same-horizon']) > 0:
        for e in jsondata['same-horizon']:
            if not isEnglish(turn_null_to_str(e['label']) + turn_null_to_str(e['text']) + turn_null_to_str(
                    e['text-hint'])):
                continue
            context_info += "There is a component on the same horizontal line as this input component. "
            context_info += component_basic_info(e)

    if len(jsondata['same-vertical']) > 0:
        for e in jsondata['same-vertical']:
            if not isEnglish(turn_null_to_str(e['label']) + turn_null_to_str(e['text']) + turn_null_to_str(
                    e['text-hint'])):
                continue
            context_info += "There is a component on the same vertical line as this input component. "
            context_info += component_basic_info(e)

    if len(jsondata['same-horizon']) > 0 or len(jsondata['same-vertical']) > 0:
        text_context_info = text_context_info.replace('<context information>', context_info)
    else:
        text_context_info = ""

    if jsondata['id'] == "" or jsondata['id'] == None:
        text_id = ""
    else:
        EditText_id = jsondata['id'].split('/')[-1]
        EditText_id = EditText_id.replace('_', ' ')
        text_id = text_id.replace('<EditText id>', EditText_id)

    # Create an intelligent prompt that provides rich context for analysis
    question = (f"Analyze this Android form field and generate appropriate sample data. "
                f"App Context: {text_app_name}"
                f"Field Details: {text_label}{text_text}{text_id}"
                f"Surrounding Elements: {text_context_info} "
                f"Instructions: Based on the app name, field labels, surrounding UI elements, "
                f"and field ID, intelligently determine what type of data this field expects "
                f"and generate a realistic example that a real user would type. "
                f"Respond with ONLY the sample data - no explanations or quotes.")
    
    return question


def getOutput(question: str):
    try:
        # Use OpenAI to intelligently analyze context and generate appropriate data
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
                    "content": question
                }
            ],
            max_tokens=50,
            temperature=0.2,  # Lower for more consistent context analysis
            stop=["\n", ".", "\"", "'"]
        )
        
        # Process and validate response
        if response.choices and response.choices[0].message.content:
            result = response.choices[0].message.content.strip()
            # Clean up unwanted characters and artifacts
            result = result.replace('"', '').replace("'", '').strip()
            result = result.replace('Example:', '').replace('Sample:', '').strip()
            result = result.replace('Answer:', '').replace('Data:', '').strip()
            
            # If result seems generic or invalid, try simpler approach
            if (len(result) < 2 or 
                result.lower() in ['text', 'data', 'input', 'sample', 'field'] or
                any(word in result.lower() for word in ['generate', 'analyze', 'context'])):
                
                # Fallback with more direct prompt
                simple_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "user",
                            "content": f"What data would a user type here? {question[:150]}... Just the data:"
                        }
                    ],
                    max_tokens=20,
                    temperature=0.1
                )
                
                if simple_response.choices and simple_response.choices[0].message.content:
                    fallback_result = simple_response.choices[0].message.content.strip()
                    fallback_result = fallback_result.replace('"', '').replace("'", '').strip()
                    if len(fallback_result) > 1 and fallback_result.lower() not in ['text', 'data']:
                        return fallback_result
            
            return result if result else "sample_data"
        else:
            print("Empty response from OpenAI API")
            return "sample_data"
            
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "sample_data"


def show_hint_console_only(res: list, hint_text: str):
    """Enhanced version - shows sample data in console AND displays on emulator"""
    x1 = int(res[0])
    y1 = int(res[1])
    x2 = int(res[2])
    y2 = int(res[3])
    
    # Show clear console output with ASCII characters
    print("\n" + "=" * 60)
    print(">>> SAMPLE DATA SUGGESTION <<<")
    print(f"EditText Position: ({x1},{y1}) to ({x2},{y2})")
    print(f"Sample Input Data: '{hint_text}'")
    print(f"Field Dimensions: {x2-x1}px x {y2-y1}px")
    print("=" * 60)
    
    # Also try to show sample data on emulator screen
    try:
        # Connect to device
        d = u2.connect()
        
        # Calculate center of EditText
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        print("[EMULATOR] Displaying sample data on screen...")
        print(f"[EMULATOR] Clicking at position ({center_x}, {center_y})")
        
        # Click on the EditText to focus it
        d.click(center_x, center_y)
        time.sleep(0.5)
        
        # Simply clear and type new text in one operation using set_text
        try:
            # Get the focused EditText element and set the text directly
            # This method replaces ALL existing content
            edit_field = d(focused=True)
            if edit_field.exists():
                edit_field.set_text(hint_text)  # Replace everything with sample data
                print(f"[EMULATOR] Set text directly to: '{hint_text}'")
            else:
                # Fallback: use the specific resource ID if available
                # Note: component_id would need to be passed as parameter
                d.send_keys(hint_text)
                print(f"[EMULATOR] Sent keys: '{hint_text}'")
        except Exception as e:
            print(f"[DEBUG] Error setting text: {e}")
            # Last resort: just send the keys
            d.send_keys(hint_text)
        
        time.sleep(0.3)
        
        print(f"[EMULATOR] Displayed sample data '{hint_text}' successfully!")
        
    except Exception as e:
        print(f"[EMULATOR] Could not display on emulator: {e}")
        print("[EMULATOR] But sample data suggestion is available above")
    
    print("=" * 60 + "\n")
    return True


while True:
    print('Connect to device...')
    try:
        # First check if any devices are available
        import subprocess
        result = subprocess.run([
            r"C:\Users\islam.elafify\AppData\Local\Android\Sdk\platform-tools\adb.exe", 
            "devices"
        ], capture_output=True, text=True)
        
        devices_output = result.stdout.strip()
        print(f"ADB devices output:\n{devices_output}")
        
        if "device" not in devices_output or "List of devices attached" in devices_output and len(devices_output.split('\n')) <= 1:
            print("No Android devices/emulators detected!")
            print("Please make sure:")
            print("1. Android emulator is running")
            print("2. USB debugging is enabled (for physical devices)")
            print("3. ADB server is running")
            print("\nWaiting 10 seconds before retrying...")
            time.sleep(10)
            continue
        
        d = u2.connect()
        print('✅ Device connected successfully!')
        print(d.info)
        break  # Exit the retry loop once connected
        
    except Exception as e:
        print(f"Failed to connect to device: {e}")
        print("Retrying in 10 seconds...")
        time.sleep(10)
        continue

# Main processing loop - runs after successful connection
while True:
    page_source = d.dump_hierarchy(compressed=True, pretty=True)
    save_path = r"C:\Users\islam.elafify\OneDrive - Accenture\Desktop\uivision"
    xml_file = open(os.path.join(save_path, 'hierarchy.xml'), 'w', encoding='utf-8')
    xml_file.write(page_source)
    xml_file.close()

    xml_file = open(os.path.join(save_path, 'hierarchy.xml'), 'r', encoding='utf-8')
    print('Reading hierarchy tree...')
    data_dict = xmltodict.parse(xml_file.read())

    all_components = getAllComponents(data_dict)

    print('All components nums:' + str(len(all_components)))

    components_with_edit_text = find_EditText(data_dict)

    print('EditText components nums:' + str(len(components_with_edit_text)))

    no_hint_text = []

    for e in components_with_edit_text:
        if e['@content-desc'] == '':
            no_hint_text.append(e)

    print('EditText with no hint nums:' + str(len(no_hint_text)))

    f_path = ''

    if len(no_hint_text) != 0:
        msg = ("Found " + str(len(no_hint_text)) + " EditText components without hint text! "
               "Do you want to generate and display hint suggestions on the screen?")
        ret = win32api.MessageBox(0, msg, "Generate Hint Suggestions",
                                  win32con.MB_YESNO)
        if ret == 7:  # No was clicked
            print("User chose not to generate hints. Waiting...")
            time.sleep(3)
            continue
        
        print("Generating sample input data for EditText components...")
    else:
        print("No EditText components without hints found. Waiting for changes...")
        time.sleep(3)
        continue

    for e_component in no_hint_text:
        print('---------------')
        pprint.pprint(e_component)
        print('---------------')
        bounds = e_component['@bounds']
        dict_info = get_basic_info(e_component)

        (same_horizon_components, same_vertical_components) = chooseFromPos(all_components, bounds)
        dict_info['same-horizon'] = []
        dict_info['same-vertical'] = []
        for e_hor_component in same_horizon_components:
            dict_info['same-horizon'].append(get_basic_info(e_hor_component))
        for e_ver_component in same_vertical_components:
            dict_info['same-vertical'].append(get_basic_info(e_ver_component))
        dict_info['activity_name'] = ''
        pprint.pprint(dict_info)
        final_text = use_context_info_generate_prompt(dict_info)
        print(final_text)
        output = getOutput(final_text)
        print(f"API Response: {output}")
        
        # Use Gemini's output and clean it to ensure realistic sample data
        real_ans = output.strip() if output else "sample_text"
        
        # Parse and clean the Gemini response to get realistic sample data
        try:
            # Remove common unwanted prefixes/suffixes
            unwanted_phrases = [
                "Given the context:",
                "Based on the context:",
                "Answer:",
                "A:",
                "The hint text is",
                "Hint:",
                "You should use",
                "I suggest",
                "The appropriate hint would be"
            ]
            
            for phrase in unwanted_phrases:
                if real_ans.lower().startswith(phrase.lower()):
                    real_ans = real_ans[len(phrase):].strip()
                    break
            
            # Try to extract text between quotes if present
            if "'" in real_ans and real_ans.count("'") >= 2:
                quoted_text = real_ans.split("'")[1]
                if len(quoted_text.strip()) > 0:
                    real_ans = quoted_text.strip()
            elif '"' in real_ans and real_ans.count('"') >= 2:
                quoted_text = real_ans.split('"')[1]
                if len(quoted_text.strip()) > 0:
                    real_ans = quoted_text.strip()
            
            # Remove punctuation at the end
            real_ans = real_ans.rstrip('.,!?:')
            
            # If response is too generic, try asking Gemini again with more specific prompt
            generic_responses = ['email', 'enter email', 'your email',
                                'password', 'enter password', 'phone',
                                'enter phone', 'name', 'enter name',
                                'username', 'enter username', 'text',
                                'input', 'data', 'field']
            
            if (real_ans.lower() in generic_responses or
                    len(real_ans) < 3 or
                    any(word in real_ans.lower() for word in
                        ['context', 'question', 'android', 'edittext'])):
                
                print(f"[DEBUG] Got generic response: '{real_ans}', "
                      f"asking Gemini for specific example...")
                
                # Create a more specific prompt for Gemini
                component_id = dict_info.get('id', '').lower()
                component_hint = e_component.get('@hint', '').lower()
                
                specific_prompt = (f"Generate a realistic example for this field: "
                                 f"Field ID: '{component_id}', "
                                 f"Hint: '{component_hint}'. "
                                 f"Provide ONLY the example data that a real user "
                                 f"would type, nothing else. "
                                 f"Examples: john.doe@example.com, +1234567890, "
                                 f"John Smith, MySecure123")
                
                # Try asking Gemini again with more specific prompt
                try:
                    specific_output = getOutput(specific_prompt)
                    if specific_output and len(specific_output.strip()) > 2:
                        real_ans = specific_output.strip()
                        print(f"[DEBUG] Gemini's specific response: '{real_ans}'")
                    else:
                        real_ans = "sample_data"
                        print(f"[DEBUG] No specific response, using: {real_ans}")
                except Exception:
                    real_ans = "sample_data"
                    print(f"[DEBUG] Error getting specific response, "
                          f"using: {real_ans}")
            else:
                print(f"[DEBUG] Using Gemini's response: '{real_ans}'")
                    
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            real_ans = "sample_data"
            
        print('Sample input data suggested: (' + real_ans + ')')

        res = []
        bounds = e_component['@bounds']
        bounds = bounds.split(',')
        print(bounds)
        res.append(bounds[0].replace('[', ''))
        mid = bounds[1].split('][')
        res.append(mid[0])
        res.append(mid[1])
        res.append(bounds[2].replace(']', ''))
        print(res)
        
        # Show the sample data suggestion
        success = show_hint_console_only(res, real_ans)
        if success:
            print(f"Successfully processed EditText with sample data: '{real_ans}'")
        else:
            print(f" Could not display hint directly, but suggestion is: '{real_ans}'")
        
        # Optional: Add a small delay between processing each EditText
        time.sleep(2)  # Give user time to see the hint
    
    print("Finished processing all EditText components. Waiting before next scan...")
    time.sleep(5)  # Wait 5 seconds before scanning again
