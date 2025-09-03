import subprocess
try:
    import pyautogui
except ImportError:
    print("Missing dependency 'pyautogui'. Install it into your environment with: python -m pip install pyautogui")
    raise
import re
import time
import uuid

# Configure pyautogui for better reliability
pyautogui.FAILSAFE = True  # Disable fail-safe to prevent corner interruption
pyautogui.PAUSE = 0.01  # Small pause between operations

# Keep track of processed messages
processed_messages = set()
session_id = str(uuid.uuid4())[:8]  # Unique session ID for this server run

def decode_text(encoded_text):
    """Decode the encoded text back to original format with proper spacing and newlines"""
    decoded = encoded_text
    
    # Decode in reverse order of encoding (most specific first)
    decoded = decoded.replace('|||INDENT4|||', '    ')    # 4-space indents
    decoded = decoded.replace('|||INDENT2|||', '  ')      # 2-space indents  
    decoded = decoded.replace('|||TAB|||', '\t')          # Tabs
    decoded = decoded.replace('|||SPACE|||', ' ')         # Single spaces
    decoded = decoded.replace('|||NEWLINE|||', '\n')      # Newlines
    
    return decoded

def safe_type_text(text):
    """Safely type text with error handling and special character support"""
    try:
        print(f"🚀 Starting to type {len(text)} characters...")
        print(f"📝 Text preview: {text[:100]}...")
        
        # Split text by lines to handle newlines properly
        lines = text.split('\n')
        total_lines = len(lines)
        
        print(f"📄 Processing {total_lines} lines...")
        
        for line_num, line in enumerate(lines, 1):
            if line.strip() or line == '':  # Process all lines including empty ones
                if line.strip():  # Only show preview for non-empty lines
                    print(f"📝 Line {line_num}/{total_lines}: {line[:50]}{'...' if len(line) > 50 else ''}")
                
                # Type the line content (including empty lines for proper spacing)
                if len(line) <= 80:
                    # Normal lines - type all at once
                    pyautogui.typewrite(line, interval=0.02)
                else:
                    # Very long lines - type in chunks
                    chunk_size = 80
                    for i in range(0, len(line), chunk_size):
                        chunk = line[i:i + chunk_size]
                        pyautogui.typewrite(chunk, interval=0.02)
                        time.sleep(0.03)
                
                time.sleep(0.05)  # Small pause after each line
            
            # Add newline after each line except the last one
            if line_num < total_lines:
                pyautogui.press('enter')
                time.sleep(0.05)
        
        print(f"✅ Successfully typed complete text ({len(text)} characters, {total_lines} lines)")
        
        # Clear logs after successful typing to prevent re-processing
        print("🧹 Clearing logs to prevent re-processing...")
        subprocess.run(["adb", "logcat", "-c"], capture_output=True)
        time.sleep(0.5)  # Give it a moment to clear
        
    except Exception as e:
        print(f"❌ Error typing text: {e}")
        print(f"📊 Was attempting to type: {text[:100]}...")

def main():
    global session_id
    print(f"🚀 AutoTyper Server Starting... (Session: {session_id})")
    
    # Clear log buffer initially
    print("🧹 Clearing initial log buffer...")
    subprocess.run(["adb", "logcat", "-c"], capture_output=True)
    time.sleep(1)  # Give it a moment to clear
    
    process = subprocess.Popen(
        ["adb", "logcat"], 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )

    print("📱 Listening for ENCODED text messages from phone...")
    print("💻 Position your cursor where you want the text to appear...")
    print("✨ Will decode spaces and newlines automatically")

    for line in process.stdout:
        # Handle encoded messages
        if "RNKeyboardApp_ENCODED:" in line:
            match = re.search(r"RNKeyboardApp_ENCODED:\s*([^|]+)\|([^|]+)\|(.*)$", line)
            if match:
                timestamp_str = match.group(1).strip()
                unique_id = match.group(2).strip()
                encoded_text = match.group(3).strip()
                
                print(f"📨 Received encoded message: ID={unique_id}")
                print(f"📏 Encoded length: {len(encoded_text)} characters")
                
                if encoded_text and len(encoded_text) > 0:
                    if unique_id not in processed_messages:
                        processed_messages.add(unique_id)
                        
                        # Decode the text
                        decoded_text = decode_text(encoded_text)
                        print(f"🔓 Decoded length: {len(decoded_text)} characters")
                        print(f"📄 Lines in decoded text: {len(decoded_text.split(chr(10)))}")
                        
                        safe_type_text(decoded_text)
                        processed_messages.clear()
                        print("🔄 Ready for next message...\n")
                    else:
                        print(f"⏭  Skipping duplicate ID: {unique_id}")
        
        # Keep old handlers for backward compatibility (but skip them)
        elif "RNKeyboardApp_NEW:" in line or "RNKeyboardApp_CHUNK:" in line:
            print("⏭  Skipping old format message (use encoded format)")

if __name__ == "__main__":
    main()