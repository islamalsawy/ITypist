import os
import json
import xmltodict
import time
import win32api
import win32con
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# ===============================
#  ADB PATH SETUP
# ===============================
android_sdk_path = r"C:\Users\islam.elafify\AppData\Local\Android\Sdk\platform-tools"
current_path = os.environ.get('PATH', '')
if android_sdk_path not in current_path:
    os.environ['PATH'] = android_sdk_path + os.pathsep + current_path

os.environ['ANDROID_HOME'] = r"C:\Users\islam.elafify\AppData\Local\Android\Sdk"
os.environ['ANDROID_SDK_ROOT'] = r"C:\Users\islam.elafify\AppData\Local\Android\Sdk"

# Import uiautomator2 AFTER adb path is set
import uiautomator2 as u2
import pprint

# ===============================
#  MODEL + LORA LOADING
# ===============================
# Paths

MODEL_PATH = r"C:\Users\islam.elafify\Downloads\QTypist-main\source code\qwen2.5b_rico_lora_opt\models--Qwen--Qwen2.5-7B-Instruct\snapshots\a09a35458c702b33eeacc393d103063234e8bc28"
ADAPTER_PATH = MODEL_PATH  # since adapter + tokenizer + model are in same folder
OFFLOAD_DIR = r"C:\Users\islam.elafify\Downloads\QTypist-main\offload"
os.makedirs(OFFLOAD_DIR, exist_ok=True)
print("🔄 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

print("🔄 Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    torch_dtype="auto",
    low_cpu_mem_usage=True,
    ignore_mismatched_sizes=True,
    offload_folder=OFFLOAD_DIR
    )

print("🔄 Attaching LoRA adapter...")
lora_model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)

print("🔄 Merging LoRA weights into base model...")
merged_model = lora_model.merge_and_unload()

print("✅ Model + LoRA merged successfully!")

# Use merged_model everywhere instead of "model"
model = merged_model


# =====================================================
# Helper functions for UI analysis
# =====================================================

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
    if prop is None:
        return ''
    else:
        return prop


def component_basic_info(jsondata: dict):
    text_id = "The purpose of this component may be '<EditText id>'. "
    text_label = "The label of this component is '<label>'. "
    text_text = "The text on this component is '<text>'. "
    text_hint = "The hint text of this component is '<hint>'. "

    if jsondata['id'] == "" or jsondata['id'] is None:
        text_id = ""
    else:
        EditText_id = jsondata['id'].split('/')[-1]
        EditText_id = EditText_id.replace('_', ' ')
        text_id = text_id.replace('<EditText id>', EditText_id)

    if jsondata['label'] == "" or jsondata['label'] is None:
        text_label = ""
    else:
        label = jsondata['label']
        text_label = text_label.replace('<label>', label)

    if jsondata['text'] == "" or jsondata['text'] is None:
        text_text = ""
    else:
        text = jsondata['text']
        text_text = text_text.replace('<text>', text)

    if jsondata['text-hint'] == "" or jsondata['text-hint'] is None:
        text_hint = ""
    else:
        hint = jsondata['text-hint']
        text_hint = text_hint.replace('<hint>', hint)

    return text_id + text_label + text_text + text_hint + '\n'


def isEnglish(s: str):
    s = s.replace('\u2026', '')
    return s.isascii()


def use_context_info_generate_prompt(jsondata: dict):
    # Original structure but with better field type detection
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

    if jsondata['label'] == "" or jsondata['label'] is None:
        text_label = ""
    else:
        label = jsondata['label']
        text_label = text_label.replace('<label>', label)

    if jsondata['text'] == "" or jsondata['text'] is None:
        text_text = ""
    else:
        text = jsondata['text']
        text_text = text_text.replace('<text>', text)

    # Filter context to only include relevant information
    context_info = ""
    if len(jsondata['same-horizon']) > 0:
        for e in jsondata['same-horizon']:
            # Skip empty or irrelevant components
            text_content = turn_null_to_str(e['label']) + turn_null_to_str(e['text']) + turn_null_to_str(e['text-hint'])
            if not isEnglish(text_content) or len(text_content.strip()) == 0:
                continue
            # Skip keyboard and UI noise
            if (e['app_name'] and 'honeyboard' in e['app_name']) or len(e['text']) <= 1:
                continue
            # Only include meaningful context
            if any(keyword in text_content.lower() for keyword in ['email', 'password', 'phone', 'name', 'sign', 'login', 'register']):
                context_info += "There is a component on the same horizontal line as this input component. "
                context_info += component_basic_info(e)

    if len(jsondata['same-vertical']) > 0:
        for e in jsondata['same-vertical']:
            # Skip empty or irrelevant components  
            text_content = turn_null_to_str(e['label']) + turn_null_to_str(e['text']) + turn_null_to_str(e['text-hint'])
            if not isEnglish(text_content) or len(text_content.strip()) == 0:
                continue
            # Skip keyboard and UI noise
            if (e['app_name'] and 'honeyboard' in e['app_name']) or len(e['text']) <= 1:
                continue
            # Only include meaningful context
            if any(keyword in text_content.lower() for keyword in ['email', 'password', 'phone', 'name', 'sign', 'login', 'register']):
                context_info += "There is a component on the same vertical line as this input component. "
                context_info += component_basic_info(e)

    if context_info:
        text_context_info = text_context_info.replace('<context information>', context_info)
    else:
        text_context_info = ""

    if jsondata['id'] == "" or jsondata['id'] is None:
        text_id = ""
    else:
        EditText_id = jsondata['id'].split('/')[-1]
        EditText_id = EditText_id.replace('_', ' ')
        text_id = text_id.replace('<EditText id>', EditText_id)

    question = text_header + text_app_name + text_activity_name + text_label + text_text + text_context_info + text_id + text_ask
    final_text = question

    return final_text


# =====================================================
# LoRA Model functions
# =====================================================

def getOutput(question: str):
    """PURE LoRA model generation - direct model output only"""
    try:
        print("🚀 Pure LoRA generation...")
        
        # Create context-specific prompts that guide the model better
        if "Enter email" in question or "email" in question.lower():
            simple_prompt = "user@example"  # This will encourage email completion
        elif "password" in question.lower() or "Password" in question:
            simple_prompt = "secure password:"
        elif "phone" in question.lower() or "mobile" in question.lower():
            simple_prompt = "phone number:"
        elif "name" in question.lower():
            simple_prompt = "full name:"
        else:
            simple_prompt = "sample text:"
        
        # Use shorter input for faster generation
        inputs = tokenizer(simple_prompt, return_tensors="pt", max_length=32, truncation=True)
        
        # Move to device
        if hasattr(model, 'device'):
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        # Generate with parameters optimized for completion
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=6,        # Shorter for focused output
                do_sample=True,          
                temperature=0.7,         # Balanced creativity
                top_p=0.9,               
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.2,  
                num_beams=1
            )
        
        # Decode only the new generated tokens
        generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        
        # Combine prompt + generated completion
        full_result = simple_prompt + generated_text.strip()
        
        # Clean the result - remove quotes and take first meaningful part
        result = full_result.replace('"', '').replace("'", '').replace('`', '')
        
        # Take first line if multiple lines
        if '\n' in result:
            result = result.split('\n')[0].strip()
        
        # Take first word/token for cleaner output
        if ' ' in result:
            result = result.split()[0]
        
        # Remove any trailing punctuation
        result = result.strip('.,!?;:')
        
        # Final validation - ensure we have meaningful data
        if (result and len(result) >= 5 and any(c.isalnum() for c in result)):
            print(f"✅ Model generated: '{result}'")
            return result
        
        print("❌ Model failed to generate meaningful data")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def show_hint_console_only(res: list, hint_text: str, device_conn):
    """Enhanced version - shows sample data in console AND displays on phone"""
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
    
    # Also try to show sample data on phone screen
    try:
        # Use the passed device connection
        print("[PHONE] Connecting to device...")
        d = device_conn
        
        # Calculate center of EditText
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        print(f"[PHONE] Clicking at position ({center_x}, {center_y})")
        
        # Multiple attempts for Samsung phones
        for attempt in range(3):
            try:
                # Click on the EditText to focus it
                d.click(center_x, center_y)
                time.sleep(0.8)  # Longer wait for Samsung UI
                
                print(f"[PHONE] Attempt {attempt + 1}: Entering text '{hint_text}'")
                
                # Method 1: Try direct text input using shell
                try:
                    d.shell(f'input text "{hint_text}"')
                    print(f"[PHONE] ✅ Method 1 success: shell input")
                    break
                except:
                    pass
                
                # Method 2: Try using set_text on focused element
                try:
                    edit_field = d(focused=True)
                    if edit_field.exists():
                        edit_field.clear_text()  # Clear first
                        time.sleep(0.3)
                        edit_field.set_text(hint_text)
                        print(f"[PHONE] ✅ Method 2 success: set_text")
                        break
                    else:
                        print(f"[PHONE] No focused element found")
                except Exception as e:
                    print(f"[PHONE] Method 2 failed: {e}")
                
                # Method 3: Try send_keys
                try:
                    # Clear field first with Ctrl+A and delete
                    d.send_keys("ctrl+a")
                    time.sleep(0.2)
                    d.send_keys("delete")
                    time.sleep(0.2)
                    d.send_keys(hint_text)
                    print(f"[PHONE] ✅ Method 3 success: send_keys")
                    break
                except Exception as e:
                    print(f"[PHONE] Method 3 failed: {e}")
                
                # Method 4: Character-by-character input for complex fields
                if attempt == 2:  # Last attempt
                    try:
                        d.click(center_x, center_y)
                        time.sleep(0.5)
                        # Clear field
                        for _ in range(50):  # Clear any existing text
                            d.send_keys("backspace")
                        time.sleep(0.3)
                        # Type character by character
                        for char in hint_text:
                            d.send_keys(char)
                            time.sleep(0.1)
                        print(f"[PHONE] ✅ Method 4 success: char-by-char")
                        break
                    except Exception as e:
                        print(f"[PHONE] Method 4 failed: {e}")
                
            except Exception as e:
                print(f"[PHONE] Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(1)
                    continue
        
        time.sleep(0.5)
        print(f"[PHONE] ✅ Finished entering: '{hint_text}'")
        
    except Exception as e:
        print(f"[PHONE] ❌ Could not display on phone: {e}")
        print("[PHONE] But sample data suggestion is available above")
    
    print("=" * 60 + "\n")
    return True


# Add torch import at the top (needed for inference)
import torch

while True:
    print('Connect to device...')
    try:
        # First check if any devices are available
        import subprocess
        result = subprocess.run([
            r"C:\Users\islam.elafify\AppData\Local\Android\Sdk\platform-tools\adb.exe", 
            "devices", "-l"
        ], capture_output=True, text=True)
        
        devices_output = result.stdout.strip()
        print(f"ADB devices output:\n{devices_output}")
        
        if "device" not in devices_output or "List of devices attached" in devices_output and len(devices_output.split('\n')) <= 1:
            print("No Android devices/emulators detected!")
            print("Please make sure:")
            print("1. USB debugging is enabled on your phone")
            print("2. Phone is connected via USB cable")
            print("3. You've authorized USB debugging on the phone")
            print("4. Or Android emulator is running")
            print("5. ADB server is running")
            print("\nWaiting 10 seconds before retrying...")
            time.sleep(10)
            continue
        
        # Parse devices and prefer USB devices over emulators
        lines = devices_output.split('\n')[1:]  # Skip header
        usb_devices = []
        emulator_devices = []
        
        for line in lines:
            if line.strip() and 'device' in line:
                device_id = line.split()[0]
                if device_id.startswith('emulator-'):
                    emulator_devices.append(device_id)
                else:
                    usb_devices.append(device_id)
        
        # Prefer USB device over emulator
        target_device = None
        if usb_devices:
            target_device = usb_devices[0]
            print(f"📱 Found USB device: {target_device}")
        elif emulator_devices:
            target_device = emulator_devices[0]
            print(f"🔧 Using emulator: {target_device}")
        
        if target_device:
            d = u2.connect(target_device)
            print(f'✅ Connected to device: {target_device}')
            print(d.info)
            break  # Exit the retry loop once connected
        else:
            print("No suitable device found!")
            time.sleep(10)
            continue
        
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
        print(f"LoRA Model Response: {output}")
        
        # ONLY use LoRA model output - skip if model failed
        if output and output.strip():
            real_ans = output.strip()
            print(f'✅ Using LoRA-generated data: ({real_ans})')
        else:
            print("❌ LoRA model failed to generate data - skipping this field")
            continue  # Skip this EditText and move to next one

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
        success = show_hint_console_only(res, real_ans, d)
        if success:
            print(f"Successfully processed EditText with sample data: '{real_ans}'")
        else:
            print(f" Could not display hint directly, but suggestion is: '{real_ans}'")
        
        # Optional: Add a small delay between processing each EditText
        time.sleep(2)  # Give user time to see the hint
    
    print("Finished processing all EditText components. Waiting before next scan...")
    time.sleep(5)  # Wait 5 seconds before scanning again