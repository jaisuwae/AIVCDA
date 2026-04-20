import customtkinter as ctk
import json
import subprocess
import os
import shared_state
from config import load_config, save_config
import version_info

COLOR_BG = "#1a1a1a"
COLOR_SIDEBAR = "#141414"
COLOR_ACCENT = "#2a2a2a"
COLOR_TEXT = "#d1d1d1"
COLOR_SUBTEXT = "#888888"
COLOR_HOVER = "#3a3a3a"

ctk.set_appearance_mode("Dark")

VOICE_OPTIONS = ["en-US-AvaNeural (Female)", "en-US-AndrewNeural (Male)", "en-US-EmmaNeural (Female)", "en-GB-SoniaNeural (Female)"]
AI_PROVIDERS = ["Gemini", "ChatGPT", "Llama"]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Project AVCDA | v{version_info.VERSION}")
        self.geometry("1050x850")
        self.configure(fg_color=COLOR_BG)
        self.config = load_config()
        self.assistant_process = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main_frame()
        self._build_footer()
        self.load_data_to_ui()
        self.refresh_history()
        self.monitor_process()

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLOR_SIDEBAR, border_width=1, border_color="#222222")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar_frame, text="AVCDA", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT).grid(row=0, column=0, padx=20, pady=(40, 5))
        ctk.CTkLabel(self.sidebar_frame, text="Neural Intelligence Engine", font=ctk.CTkFont(size=12), text_color=COLOR_SUBTEXT).grid(row=1, column=0, padx=20, pady=(0, 30))

        self.start_btn = ctk.CTkButton(self.sidebar_frame, text="START ENGINE", height=45, corner_radius=4, font=ctk.CTkFont(weight="bold"), fg_color=COLOR_TEXT, text_color=COLOR_BG, command=self.toggle_assistant)
        self.start_btn.grid(row=2, column=0, padx=20, pady=10)

        self.save_btn = ctk.CTkButton(self.sidebar_frame, text="COMMIT DATA", height=45, corner_radius=4, fg_color=COLOR_ACCENT, text_color=COLOR_TEXT, command=self.save_settings)
        self.save_btn.grid(row=3, column=0, padx=20, pady=10)

        self.wipe_btn = ctk.CTkButton(self.sidebar_frame, text="WIPE APP MEMORY", height=35, corner_radius=4, fg_color="#330000", text_color="#ff5555", command=self.wipe_memory)
        self.wipe_btn.grid(row=4, column=0, padx=20, pady=(10, 0))

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Status: IDLE", text_color=COLOR_SUBTEXT)
        self.status_label.grid(row=5, column=0, padx=20, pady=(180, 10))

    def _build_main_frame(self):
        self.tabview = ctk.CTkTabview(self, fg_color=COLOR_BG, segmented_button_selected_color=COLOR_ACCENT, text_color=COLOR_TEXT)
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)
        
        self.tab_persona = self.tabview.add("Identity")
        self.tab_neural = self.tabview.add("Neural Hub")
        self.tab_commands = self.tabview.add("Commands")
        self.tab_scripts = self.tabview.add("Scripts")
        self.tab_info = self.tabview.add("About")
        self.tab_settings = self.tabview.add("Settings")

        self._build_persona_tab()
        self._build_neural_hub_tab()
        self._build_commands_tab()
        self._build_scripts_tab()
        self._build_info_tab()
        self._build_settings_tab()

    def _build_persona_tab(self):
        self._add_hdr(self.tab_persona, "IDENTITY", 0)
        card = self._add_card(self.tab_persona, 1)
        self.entry_name = self._add_entry(card, "Assistant Name:", 0)
        self.entry_aliases = self._add_entry(card, "Aliases:", 2)
        self.entry_salutation = self._add_entry(card, "User Salutation (sir, chief):", 4)
        ctk.CTkLabel(card, text="Neural Voice:", text_color=COLOR_SUBTEXT).grid(row=6, column=0, sticky="w", padx=20, pady=(5, 0))
        self.voice_dropdown = ctk.CTkOptionMenu(card, values=VOICE_OPTIONS, fg_color=COLOR_BG, button_color=COLOR_ACCENT)
        self.voice_dropdown.grid(row=7, column=0, sticky="w", padx=20, pady=(0, 15))

    def _build_neural_hub_tab(self):
        self._add_hdr(self.tab_neural, "MULTI-AI CONFIGURATION", 0)
        card = self._add_card(self.tab_neural, 1)
        ctk.CTkLabel(card, text="Primary AI Brain:", text_color=COLOR_SUBTEXT).grid(row=0, column=0, sticky="w", padx=20, pady=(10, 0))
        self.ai_dropdown = ctk.CTkOptionMenu(card, values=AI_PROVIDERS, fg_color=COLOR_BG, button_color=COLOR_ACCENT)
        self.ai_dropdown.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))
        self.entry_gemini_key = self._add_entry(card, "Gemini API Key:", 2)
        self.entry_openai_key = self._add_entry(card, "OpenAI API Key:", 4)
        self.entry_llama_url = self._add_entry(card, "Llama Endpoint (Url):", 6)

    def _build_commands_tab(self):
        self._add_hdr(self.tab_commands, "QUICK COMMANDS", 0)
        card = self._add_card(self.tab_commands, 1)
        self.entry_q_speech = self._add_entry(card, "When I say:", 0)
        self.entry_q_action = self._add_entry(card, "Run commands (comma separated):", 2)
        ctk.CTkButton(card, text="+ ADD", width=100, fg_color=COLOR_TEXT, text_color=COLOR_BG, command=self.add_quick_command).grid(row=4, column=0, padx=20, pady=15)

        self._add_hdr(self.tab_commands, "COMMAND HISTORY", 2)
        self.history_frame = ctk.CTkScrollableFrame(self.tab_commands, height=250, fg_color=COLOR_ACCENT, corner_radius=8)
        self.history_frame.grid(row=3, column=0, sticky="ew", padx=2, pady=5)
        self.history_frame.grid_columnconfigure(0, weight=1)

    def _build_scripts_tab(self):
        self._add_hdr(self.tab_scripts, "MANUAL SCRIPT INJECTOR", 0)
        card = self._add_card(self.tab_scripts, 1)
        self.entry_script_trigger = self._add_entry(card, "Trigger Word:", 0)
        ctk.CTkLabel(card, text="Type:", text_color=COLOR_SUBTEXT).grid(row=2, column=0, sticky="w", padx=20)
        self.script_type = ctk.CTkOptionMenu(card, values=["Python", "Shell"], fg_color=COLOR_BG, button_color=COLOR_ACCENT)
        self.script_type.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 10))
        self.text_script = ctk.CTkTextbox(card, height=180, fg_color=COLOR_BG, border_width=1, border_color="#333333")
        self.text_script.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        ctk.CTkButton(card, text="INJECT", fg_color=COLOR_TEXT, text_color=COLOR_BG, command=self.add_script).grid(row=5, column=0, padx=20, pady=10)

    def _build_info_tab(self):
        self._add_hdr(self.tab_info, "LIBRARIES & RESOURCES", 0)
        lib_card = self._add_card(self.tab_info, 1)
        lib_text = ""
        for lib in version_info.LIBRARIES:
            lib_text += f"• {lib['name']}: {lib['desc']}\n"
        ctk.CTkLabel(lib_card, text=lib_text, text_color=COLOR_SUBTEXT, justify="left", wraplength=700).grid(row=0, column=0, padx=20, pady=15)

        self._add_hdr(self.tab_info, "CHANGELOG", 2)
        ch_card = self._add_card(self.tab_info, 3)
        ch_text = ""
        for item in version_info.CHANGELOG:
            ch_text += f"{item['v']} ({item['date']}): {item['note']}\n"
        ctk.CTkLabel(ch_card, text=ch_text, text_color=COLOR_SUBTEXT, justify="left", wraplength=700).grid(row=0, column=0, padx=20, pady=15)

    def _build_settings_tab(self):
        self._add_hdr(self.tab_settings, "CORE ENGINE", 0)
        card = self._add_card(self.tab_settings, 1)
        self.sw_vosk = self._add_sw(card, "Neural Guard (Local)", 0)
        self.sw_stt = self._add_sw(card, "Google STT", 1)
        self.sw_tts = self._add_sw(card, "Cloud TTS", 2)
        self.sw_offline = self._add_sw(card, "Force Offline Mode", 3)

    def _build_footer(self):
        footer_frame = ctk.CTkFrame(self, height=30, fg_color="transparent")
        footer_frame.grid(row=1, column=1, sticky="ew", padx=25, pady=(0, 10))
        info_text = f"Built By {version_info.AUTHOR}  |  License: {version_info.LICENSE}  |  GitHub: {version_info.GITHUB.replace('https://','')}"
        ctk.CTkLabel(footer_frame, text=info_text, font=ctk.CTkFont(size=10), text_color="#444444").pack(side="left")

    def _add_hdr(self, p, t, r): ctk.CTkLabel(p, text=t, font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_SUBTEXT).grid(row=r, column=0, sticky="w", pady=(20, 10))
    def _add_card(self, p, r): 
        f = ctk.CTkFrame(p, fg_color=COLOR_ACCENT, corner_radius=8)
        f.grid(row=r, column=0, sticky="ew", padx=2); f.grid_columnconfigure(0, weight=1); return f
    def _add_entry(self, p, l, r):
        ctk.CTkLabel(p, text=l, text_color=COLOR_SUBTEXT).grid(row=r, column=0, sticky="w", padx=20, pady=(10, 0))
        e = ctk.CTkEntry(p, fg_color=COLOR_BG, border_width=1, border_color="#333333"); e.grid(row=r+1, column=0, sticky="ew", padx=20, pady=(0, 10)); return e
    def _add_sw(self, p, t, r):
        s = ctk.CTkSwitch(p, text=t, progress_color=COLOR_TEXT, button_color=COLOR_TEXT)
        s.grid(row=r, column=0, sticky="w", padx=20, pady=8); return s

    def load_data_to_ui(self):
        self.entry_name.insert(0, self.config.get("ASSISTANT_NAME", "Silvia"))
        self.entry_aliases.insert(0, ", ".join(self.config.get("ASSISTANT_ALIASES", [])))
        self.entry_salutation.insert(0, self.config.get("USER_SALUTATION", "sir"))
        self.entry_gemini_key.insert(0, self.config.get("GEMINI_API_KEY", ""))
        self.entry_openai_key.insert(0, self.config.get("OPENAI_API_KEY", ""))
        self.entry_llama_url.insert(0, self.config.get("LLAMA_URL", ""))
        self.ai_dropdown.set(self.config.get("PRIMARY_AI", "Gemini"))
        for opt in VOICE_OPTIONS:
            if self.config.get("EDGE_VOICE", "en-US-AvaNeural") in opt: self.voice_dropdown.set(opt); break
        if self.config.get("USE_LOCAL_VOSK", True): self.sw_vosk.select()
        if self.config.get("USE_GOOGLE_STT", True): self.sw_stt.select()
        if self.config.get("USE_CLOUD_TTS", True): self.sw_tts.select()
        if self.config.get("FORCE_OFFLINE", False): self.sw_offline.select()

    def wipe_memory(self): self.config["APP_TYPE_MEMORY"] = {}; save_config(self.config); print("Memory Wiped.")

    def refresh_history(self):
        # Clear current history view
        for widget in self.history_frame.winfo_children(): widget.destroy()
        
        # Show Commands
        quick = self.config.get("CUSTOM_COMMANDS", {})
        scripts = self.config.get("ADVANCED_SCRIPTS", {})
        
        for i, (trigger, action) in enumerate(quick.items()):
            f = ctk.CTkFrame(self.history_frame, fg_color=COLOR_BG, height=35)
            f.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(f, text=f"💬 {trigger} ➜ {action[:30]}...", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT).pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=25, height=25, fg_color="#441111", hover_color="#881111", command=lambda t=trigger: self.delete_command(t, "quick")).pack(side="right", padx=5)

        for i, (trigger, data) in enumerate(scripts.items()):
            f = ctk.CTkFrame(self.history_frame, fg_color="#1e252b", height=35)
            f.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(f, text=f"⚙️ {trigger} [{data['type'].upper()}]", font=ctk.CTkFont(size=11, weight="bold"), text_color="#7fb5eb").pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=25, height=25, fg_color="#441111", hover_color="#881111", command=lambda t=trigger: self.delete_command(t, "script")).pack(side="right", padx=5)

    def delete_command(self, trigger, c_type):
        if c_type == "quick": self.config.get("CUSTOM_COMMANDS", {}).pop(trigger, None)
        else: self.config.get("ADVANCED_SCRIPTS", {}).pop(trigger, None)
        save_config(self.config)
        self.refresh_history()

    def add_quick_command(self):
        s, a = self.entry_q_speech.get().lower().strip(), self.entry_q_action.get().strip()
        if s and a: self.config.setdefault("CUSTOM_COMMANDS", {})[s] = a; save_config(self.config); self.entry_q_speech.delete(0, 'end'); self.entry_q_action.delete(0, 'end'); self.refresh_history()

    def add_script(self):
        t, ty, c = self.entry_script_trigger.get().lower().strip(), self.script_type.get().lower(), self.text_script.get("1.0", "end-1c").strip()
        if t and c: self.config.setdefault("ADVANCED_SCRIPTS", {})[t] = {"type": ty, "code": c}; save_config(self.config); self.entry_script_trigger.delete(0, 'end'); self.text_script.delete("1.0", "end"); self.refresh_history()

    def save_settings(self):
        self.config["ASSISTANT_NAME"] = self.entry_name.get().strip()
        self.config["ASSISTANT_ALIASES"] = [x.strip() for x in self.entry_aliases.get().split(",") if x.strip()]
        self.config["USER_SALUTATION"] = self.entry_salutation.get().strip()
        self.config["PRIMARY_AI"] = self.ai_dropdown.get()
        self.config["GEMINI_API_KEY"] = self.entry_gemini_key.get().strip()
        self.config["OPENAI_API_KEY"] = self.entry_openai_key.get().strip()
        self.config["LLAMA_URL"] = self.entry_llama_url.get().strip()
        self.config["EDGE_VOICE"] = self.voice_dropdown.get().split("(")[0].strip()
        self.config["USE_LOCAL_VOSK"] = bool(self.sw_vosk.get())
        self.config["USE_GOOGLE_STT"] = bool(self.sw_stt.get())
        self.config["USE_CLOUD_TTS"] = bool(self.sw_tts.get())
        self.config["FORCE_OFFLINE"] = bool(self.sw_offline.get())
        save_config(self.config)

    def monitor_process(self):
        if self.assistant_process and self.assistant_process.poll() is not None: self.assistant_process = None; self._update_ui_stopped()
        self.after(1000, self.monitor_process)

    def _update_ui_stopped(self): self.start_btn.configure(text="START ENGINE", fg_color=COLOR_TEXT, text_color=COLOR_BG); self.status_label.configure(text="Status: IDLE")
    def _update_ui_started(self): self.start_btn.configure(text="STOP ENGINE", fg_color="#331111", text_color="#ff5555"); self.status_label.configure(text="Status: ACTIVE", text_color="#ffffff")

    def toggle_assistant(self):
        if self.assistant_process is None: self.assistant_process = subprocess.Popen(["python", "main.py"], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name=='nt' else 0); self._update_ui_started()
        else: self.assistant_process.terminate(); self.assistant_process = None; self._update_ui_stopped()

if __name__ == "__main__": app = App(); app.mainloop()
