import sys
import os
import logging
import threading
from dotenv import load_dotenv

# Load environmental variables from .env file before anything else
load_dotenv()

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
# Quiet down Google Client Library verbose logging
logging.getLogger("googleapiclient").setLevel(logging.WARNING)

from core.orchestrator import JarvisCore
from core.security import security_manager
from audio.listener import Listener
from audio.speaker import Speaker
from modules.shell_module import SystemController
from modules.github_module import ProjectAutomator
from modules.google_module import GoogleIntegrator
from gui.hud import JarvisHUD

def main():
    print("=" * 60)
    print("       JARVIS: Modular, Secure Voice Assistant (Local-First)")
    print("=" * 60)
    
    # Initialize HUD Overlay Window on the Main Thread
    hud = JarvisHUD()
    
    # Initialize Core Components
    jarvis = JarvisCore()
    listener = Listener()
    speaker = Speaker()
    
    # Link Security manager confirmation to voice speaker/listener & HUD updates
    def voice_confirm_callback(action_description: str) -> bool:
        hud.update_orb_state("listening")
        hud.update_hud_status("title", "Awaiting Approval...")
        speaker.speak(
            f"Security confirmation required. Do you approve the execution of: {action_description}?"
        )
        return listener.listen_raw_confirm()
        
    security_manager.set_confirm_callback(voice_confirm_callback)

    # Register Capability Modules
    print("\n[System] Initializing and registering modules...")
    
    shell_module = SystemController()
    jarvis.register_module(shell_module)
    
    github_module = ProjectAutomator()
    jarvis.register_module(github_module)
    
    google_module = GoogleIntegrator()
    jarvis.register_module(google_module)

    # Check for Gemini Key
    from core.config import settings
    if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
        print("\n[WARNING] 'GEMINI_API_KEY' is missing in your .env file.")
        hud.update_hud_status("System", "System: Key Missing")
        
    # Background Thread Worker for Voice/Command loop processing
    def assistant_loop():
        # Select Mode: Default to Text if no mic, else Voice
        mode = "text"
        if listener.microphone is not None:
            mode = "voice"
            
        print(f"\n[System] Threaded assistant running in [{mode.upper()}] mode.")
        hud.update_hud_status("System", f"System: Active ({mode.upper()})")
        
        # Initial status setup
        hud.update_hud_status("Gmail", "Gmail: Ready")
        hud.update_hud_status("Calendar", "Calendar: Ready")
        hud.update_hud_status("GitHub", "GitHub: Ready")
        
        while True:
            try:
                # Update HUD to awaiting state
                hud.update_orb_state("idle")
                hud.update_hud_status("title", "Awaiting command...")
                
                if mode == "voice":
                    # Update status when listening
                    hud.update_orb_state("listening")
                    hud.update_hud_status("title", "Listening...")
                    user_query = listener.listen()
                else:
                    user_query = input("\nYou: ").strip()
                    
                if not user_query:
                    continue
                    
                if user_query.lower() in ["exit", "quit", "goodbye", "shutdown"]:
                    speaker.speak("Goodbye, shutting down HUD overlay.")
                    # Close the Tkinter window safely from background thread
                    hud.after(0, hud.destroy)
                    break
                
                # Update HUD to thinking state
                hud.update_orb_state("thinking")
                hud.update_hud_status("title", "Thinking...")
                
                # Update status panels on relevant prompts
                query_lower = user_query.lower()
                if "gmail" in query_lower or "email" in query_lower:
                    hud.update_hud_status("Gmail", "Gmail: Loading...")
                elif "calendar" in query_lower or "event" in query_lower:
                    hud.update_hud_status("Calendar", "Calendar: Checking...")
                elif "github" in query_lower or "project" in query_lower:
                    hud.update_hud_status("GitHub", "GitHub: Ingesting...")
                    
                # Process query
                response = jarvis.handle_query(user_query)
                
                # Update status panels post-execution
                if "gmail" in query_lower or "email" in query_lower:
                    hud.update_hud_status("Gmail", "Gmail: Updated")
                elif "calendar" in query_lower or "event" in query_lower:
                    hud.update_hud_status("Calendar", "Calendar: Updated")
                elif "github" in query_lower or "project" in query_lower:
                    hud.update_hud_status("GitHub", "GitHub: Synced")
                
                # Update HUD to speaking state
                hud.update_orb_state("speaking")
                hud.update_hud_status("title", "Speaking...")
                speaker.speak(response)
                
            except Exception as e:
                print(f"[Error] Exception in assistant thread: {e}")
                hud.update_hud_status("System", "System: Fail Alert")
                hud.update_orb_state("idle")
                hud.update_hud_status("title", "Awaiting command...")

    # Boot the background assistant thread (as daemon)
    assistant_thread = threading.Thread(target=assistant_loop, daemon=True)
    assistant_thread.start()

    # Launch HUD overlay GUI loop on the Main Thread
    print("\n[System] Starting HUD Overlay Graphic Loop...")
    hud.mainloop()

if __name__ == "__main__":
    main()

