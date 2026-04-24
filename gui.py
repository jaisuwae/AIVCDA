import customtkinter as ctk
import json
import subprocess
import os
import sys
import shared_state
from tkinter import filedialog, messagebox
from config import load_config, save_config, get_resource_path
import ai_assistant as ai
import version_info
import platform

COLOR_BG = "#1a1a1a"
COLOR_SIDEBAR = "#141414"
COLOR_ACCENT = "#2a2a2a"
COLOR_TEXT = "#d1d1d1"
COLOR_SUBTEXT = "#888888"
COLOR_HOVER = "#3a3a3a"

ctk.set_appearance_mode("Dark")

VOICE_OPTIONS = ["en-US-AvaNeural (Female)", "en-US-AndrewNeural (Male)", "en-US-EmmaNeural (Female)", "en-GB-SoniaNeural (Female)"]
AI_PROVIDERS = ["Llama (Local)"]
BRAIN_OPTIONS = ["Eco (qwen2.5:1.5b)", "Standard (llama3.2:3b)", "Phi 3.5", "Custom"]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Project AIVCDA | Sidewing | v{version_info.VERSION}")
        self.geometry("1200x900")
        self.configure(fg_color=COLOR_BG)
        self.config = load_config()

        # Set taskbar and window icon
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("jaisuwae.aivcda.sidewing.v3")
            except Exception:
                pass

        icon_path = get_resource_path("ico.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.assistant_process = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main_frame()
        self._build_footer()
        self.load_data_to_ui()
        self.check_ollama_startup()
        self.refresh_history()
        self.monitor_process()

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLOR_SIDEBAR, border_width=1, border_color="#222222")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar_frame, text="AIVCDA", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_TEXT).grid(row=0, column=0, padx=20, pady=(40, 5))
        ctk.CTkLabel(self.sidebar_frame, text="Sidewing Neural Intelligence", font=ctk.CTkFont(size=12), text_color=COLOR_SUBTEXT).grid(row=1, column=0, padx=20, pady=(0, 30))

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
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.tab_persona = self.tabview.add("👤 Persona")
        self.tab_neural = self.tabview.add("🧠 Neural")
        self.tab_commands = self.tabview.add("⚡ Commands")
        self.tab_scripts = self.tabview.add("⚙️ Scripts")
        self.tab_info = self.tabview.add("📖 Info")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        # Configure tab frames for proper scrolling and sizing
        for tab in [self.tab_persona, self.tab_neural, self.tab_commands, self.tab_scripts, self.tab_info, self.tab_settings]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=0)

        self._build_persona_tab()
        self._build_neural_hub_tab()
        self._build_commands_tab()
        self._build_scripts_tab()
        self._build_info_tab()
        self._build_settings_tab()

    def _build_persona_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.tab_persona, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)
        self.tab_persona.grid_rowconfigure(0, weight=1)
        
        self._add_hdr(scroll_frame, "ASSISTANT IDENTITY", 0)
        card = self._add_card(scroll_frame, 1)
        self.entry_name = self._add_entry(card, "Assistant Name:", 0)
        self.entry_aliases = self._add_entry(card, "Aliases:", 2)
        self.entry_salutation = self._add_entry(card, "User Salutation (sir, chief):", 4)
        self.entry_personality = self._add_entry(card, "Response Personality:", 6)
        ctk.CTkLabel(card, text="Neural Voice:", text_color=COLOR_SUBTEXT).grid(row=8, column=0, sticky="w", padx=20, pady=(5, 0))
        self.voice_dropdown = ctk.CTkOptionMenu(card, values=VOICE_OPTIONS, fg_color=COLOR_BG, button_color=COLOR_ACCENT)
        self.voice_dropdown.grid(row=9, column=0, sticky="w", padx=20, pady=(0, 15))
        card.grid_columnconfigure(0, weight=1)

    def _build_neural_hub_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.tab_neural, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)
        self.tab_neural.grid_rowconfigure(0, weight=1)
        
        self._add_hdr(scroll_frame, "LOCAL AI CONFIGURATION", 0)
        card = self._add_card(scroll_frame, 1)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text="Primary AI Brain:", text_color=COLOR_SUBTEXT).grid(row=0, column=0, sticky="w", padx=20, pady=(10, 0))
        self.ai_dropdown = ctk.CTkOptionMenu(card, values=AI_PROVIDERS, fg_color=COLOR_BG, button_color=COLOR_ACCENT)
        self.ai_dropdown.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))
        ctk.CTkLabel(card, text="Default Brain:", text_color=COLOR_SUBTEXT).grid(row=2, column=0, sticky="w", padx=20, pady=(10, 0))
        self.brain_dropdown = ctk.CTkOptionMenu(card, values=BRAIN_OPTIONS, fg_color=COLOR_BG, button_color=COLOR_ACCENT)
        self.brain_dropdown.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 15))
        self.entry_custom_model = self._add_entry(card, "Custom Model Name:", 4)
        self.entry_llama_url = self._add_entry(card, "Llama Endpoint (e.g. Ollama or LM Studio):", 6)
        self.entry_ollama_dir = self._add_entry(card, "Ollama Directory (optional):", 8)
        self.lbl_ollama_status = ctk.CTkLabel(card, text="Ollama Status: Unknown", text_color=COLOR_SUBTEXT, justify="left", wraplength=650)
        self.lbl_ollama_status.grid(row=10, column=0, sticky="w", padx=20, pady=(5, 10))
        ctk.CTkButton(card, text="Auto-Locate Ollama", width=180, fg_color=COLOR_TEXT, text_color=COLOR_BG, command=self.auto_locate_ollama).grid(row=11, column=0, padx=20, pady=(0, 5))
        ctk.CTkButton(card, text="Activate Ollama", width=180, fg_color=COLOR_ACCENT, text_color=COLOR_TEXT, command=self.activate_ollama).grid(row=12, column=0, padx=20, pady=(0, 5))
        ctk.CTkButton(card, text="Choose Ollama Directory", width=180, fg_color=COLOR_ACCENT, text_color=COLOR_TEXT, command=self.add_ollama_directory).grid(row=13, column=0, padx=20, pady=(0, 10))
        ctk.CTkLabel(card, text="Note: Gemini and OpenAI have been removed to prioritize local privacy and performance.", font=ctk.CTkFont(size=10, slant="italic"), text_color=COLOR_SUBTEXT, wraplength=650).grid(row=14, column=0, sticky="w", padx=20, pady=(5, 15))

    def _build_commands_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.tab_commands, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)
        self.tab_commands.grid_rowconfigure(0, weight=1)
        
        self._add_hdr(scroll_frame, "QUICK COMMANDS", 0)
        card = self._add_card(scroll_frame, 1)
        card.grid_columnconfigure(0, weight=1)
        self.entry_q_speech = self._add_entry(card, "When I say:", 0)
        self.entry_q_action = self._add_entry(card, "Run commands (comma separated):", 2)
        ctk.CTkButton(card, text="+ ADD", width=100, fg_color=COLOR_TEXT, text_color=COLOR_BG, command=self.add_quick_command).grid(row=4, column=0, padx=20, pady=15)

        self._add_hdr(scroll_frame, "APP REGISTRY", 5)
        app_card = self._add_card(scroll_frame, 6)
        app_card.grid_columnconfigure(0, weight=1)
        self.entry_app_name = self._add_entry(app_card, "Application Name:", 0)
        self.entry_app_path = self._add_entry(app_card, "Directory or URL:", 2)
        ctk.CTkButton(app_card, text="+ ADD APP", width=150, fg_color=COLOR_TEXT, text_color=COLOR_BG, command=self.add_custom_app).grid(row=4, column=0, padx=20, pady=10)

        self._add_hdr(scroll_frame, "COMMAND HISTORY", 8)
        self.history_frame = ctk.CTkScrollableFrame(scroll_frame, height=300, fg_color=COLOR_ACCENT, corner_radius=8)
        self.history_frame.grid(row=9, column=0, sticky="ew", padx=2, pady=5)
        self.history_frame.grid_columnconfigure(0, weight=1)

    def _build_scripts_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.tab_scripts, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)
        self.tab_scripts.grid_rowconfigure(0, weight=1)
        
        self._add_hdr(scroll_frame, "MANUAL SCRIPT INJECTOR", 0)
        card = self._add_card(scroll_frame, 1)
        card.grid_columnconfigure(0, weight=1)
        self.entry_script_trigger = self._add_entry(card, "Trigger Word:", 0)
        ctk.CTkLabel(card, text="Type:", text_color=COLOR_SUBTEXT).grid(row=2, column=0, sticky="w", padx=20)
        self.script_type = ctk.CTkOptionMenu(card, values=["Python", "Shell"], fg_color=COLOR_BG, button_color=COLOR_ACCENT)
        self.script_type.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 10))
        self.text_script = ctk.CTkTextbox(card, height=200, fg_color=COLOR_BG, border_width=1, border_color="#333333")
        self.text_script.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        ctk.CTkButton(card, text="INJECT", fg_color=COLOR_TEXT, text_color=COLOR_BG, command=self.add_script).grid(row=5, column=0, padx=20, pady=10)

    def _build_info_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.tab_info, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)
        self.tab_info.grid_rowconfigure(0, weight=1)
        
        self._add_hdr(scroll_frame, "LIBRARIES & RESOURCES", 0)
        lib_card = self._add_card(scroll_frame, 1)
        lib_card.grid_columnconfigure(0, weight=1)
        lib_text = ""
        for lib in version_info.LIBRARIES:
            lib_text += f"• {lib['name']}: {lib['desc']}\n"
        ctk.CTkLabel(lib_card, text=lib_text, text_color=COLOR_SUBTEXT, justify="left", wraplength=650).grid(row=0, column=0, padx=20, pady=15)

        self._add_hdr(scroll_frame, "CHANGELOG", 2)
        ch_card = self._add_card(scroll_frame, 3)
        ch_card.grid_columnconfigure(0, weight=1)
        ch_text = ""
        for item in version_info.CHANGELOG:
            ch_text += f"{item['v']} ({item['date']}): {item['note']}\n"
        ctk.CTkLabel(ch_card, text=ch_text, text_color=COLOR_SUBTEXT, justify="left", wraplength=650).grid(row=0, column=0, padx=20, pady=15)

    def _build_settings_tab(self):
        scroll_frame = ctk.CTkScrollableFrame(self.tab_settings, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)
        self.tab_settings.grid_rowconfigure(0, weight=1)
        
        self._add_hdr(scroll_frame, "CORE ENGINE", 0)
        card = self._add_card(scroll_frame, 1)
        card.grid_columnconfigure(0, weight=1)
        self.sw_vosk = self._add_sw(card, "Neural Guard (Local)", 0)
        self.sw_stt = self._add_sw(card, "Google STT (Cloud)", 1)
        self.sw_tts = self._add_sw(card, "High-Quality Edge TTS", 2)
        self.sw_offline = self._add_sw(card, "Force Offline Mode (AI)", 3)

        self._add_hdr(scroll_frame, "LOGGING", 5)
        log_card = self._add_card(scroll_frame, 6)
        log_card.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(log_card, text="View Log File", width=180, fg_color=COLOR_TEXT, text_color=COLOR_BG, command=self.edit_log).grid(row=0, column=0, padx=20, pady=(10, 5))
        ctk.CTkButton(log_card, text="Clear Log", width=180, fg_color="#441111", text_color="#ff5555", command=self.clear_log).grid(row=1, column=0, padx=20, pady=(0, 15))

    def _build_footer(self):
        footer_frame = ctk.CTkFrame(self, height=30, fg_color="transparent")
        footer_frame.grid(row=1, column=1, sticky="ew", padx=25, pady=(0, 10))
        info_text = f"Built By {version_info.AUTHOR}  |  License: {version_info.LICENSE}  |  GitHub: {version_info.GITHUB.replace('https://','')}"
        ctk.CTkLabel(footer_frame, text=info_text, font=ctk.CTkFont(size=10), text_color="#444444").pack(side="left")

    def _add_hdr(self, p, t, r): ctk.CTkLabel(p, text=t, font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_SUBTEXT).grid(row=r, column=0, sticky="w", pady=(20, 10), padx=5)
    def _add_card(self, p, r): 
        f = ctk.CTkFrame(p, fg_color=COLOR_ACCENT, corner_radius=8)
        f.grid(row=r, column=0, sticky="ew", padx=5, pady=5)
        f.grid_columnconfigure(0, weight=1)
        return f
    def _add_entry(self, p, l, r):
        ctk.CTkLabel(p, text=l, text_color=COLOR_SUBTEXT).grid(row=r, column=0, sticky="w", padx=20, pady=(10, 0))
        e = ctk.CTkEntry(p, fg_color=COLOR_BG, border_width=1, border_color="#333333")
        e.grid(row=r+1, column=0, sticky="ew", padx=20, pady=(0, 10))
        return e
    def _add_sw(self, p, t, r):
        s = ctk.CTkSwitch(p, text=t, progress_color=COLOR_TEXT, button_color=COLOR_TEXT)
        s.grid(row=r, column=0, sticky="w", padx=20, pady=8)
        return s

    def _refresh_ollama_status(self):
        url = self.config.get("LLAMA_URL", "http://localhost:11434/api/generate")
        path = self.config.get("LLAMA_PATH", "Not configured")
        connected = ai.is_ollama_running(url)
        text = f"Ollama URL: {url}\nStatus: {'Connected' if connected else 'Disconnected'}\nPath: {path or 'Unknown'}"
        self.lbl_ollama_status.configure(text=text)

    def check_ollama_startup(self):
        url = self.config.get("LLAMA_URL", "http://localhost:11434/api/generate").strip()
        if not url:
            return
        if not ai.is_ollama_running(url):
            start_it = messagebox.askyesno(
                "Ollama not reachable",
                "Ollama does not appear to be running. Would you like to try starting Ollama now?"
            )
            if start_it:
                self.activate_ollama()
            self._refresh_ollama_status()

    def shutdown_assistant_process(self):
        if not self.assistant_process:
            return
        try:
            self.assistant_process.terminate()
            self.assistant_process.wait(timeout=3)
        except Exception:
            try:
                self.assistant_process.kill()
            except Exception:
                pass
        self.assistant_process = None
        self._update_ui_stopped()

    def on_close(self):
        self.shutdown_assistant_process()
        self.destroy()

    def auto_locate_ollama(self):
        candidate = ai.find_ollama_executable()
        if candidate:
            self.config["LLAMA_PATH"] = candidate
            self.entry_ollama_dir.delete(0, 'end')
            self.entry_ollama_dir.insert(0, candidate)
            self.config["LLAMA_URL"] = self.entry_llama_url.get().strip() or "http://localhost:11434/api/generate"
            self.save_settings()
            messagebox.showinfo("Ollama Located", f"Found Ollama at: {candidate}")
        else:
            messagebox.showinfo("Auto Locate", "Ollama executable was not found. Please select the directory manually or install Ollama.")
        self._refresh_ollama_status()

    def add_ollama_directory(self):
        directory = filedialog.askdirectory(title="Select Ollama install folder")
        if not directory:
            return
        candidate = ai.find_ollama_executable(directory)
        if candidate:
            self.config["LLAMA_PATH"] = candidate
            self.entry_ollama_dir.delete(0, 'end')
            self.entry_ollama_dir.insert(0, candidate)
            self.save_settings()
            messagebox.showinfo("Ollama Directory", f"Found Ollama at: {candidate}")
        else:
            messagebox.showerror("Ollama Directory", "No Ollama executable was found in the selected folder.")
        self._refresh_ollama_status()

    def activate_ollama(self):
        path = self.config.get("LLAMA_PATH") or ai.find_ollama_executable()
        if not path:
            messagebox.showerror("Activate Ollama", "Ollama executable not configured. Please locate the directory first.")
            return
        try:
            subprocess.Popen(
                [path, "daemon"],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
                cwd=os.path.dirname(path)
            )
            messagebox.showinfo("Activate Ollama", "Attempting to start Ollama daemon.")
        except Exception as e:
            messagebox.showerror("Activate Ollama", f"Could not start Ollama: {e}")
        self._refresh_ollama_status()

    def load_data_to_ui(self):
        self.entry_name.insert(0, self.config.get("ASSISTANT_NAME", "Silvia"))
        self.entry_aliases.insert(0, ", ".join(self.config.get("ASSISTANT_ALIASES", [])))
        self.entry_salutation.insert(0, self.config.get("USER_SALUTATION", "sir"))
        self.entry_personality.insert(0, self.config.get("ASSISTANT_PERSONALITY", "Answer briefly, politely, and clearly."))
        self.entry_llama_url.insert(0, self.config.get("LLAMA_URL", "http://localhost:11434/api/generate"))
        self.entry_ollama_dir.insert(0, self.config.get("LLAMA_PATH", ""))
        self.ai_dropdown.set(self.config.get("PRIMARY_AI", "Llama (Local)"))
        self.brain_dropdown.set(self.config.get("LLAMA_DEFAULT_BRAIN", "Eco (qwen2.5:1.5b)"))
        self.entry_custom_model.insert(0, self.config.get("LLAMA_CUSTOM_MODEL", ""))
        self._refresh_ollama_status()
        for opt in VOICE_OPTIONS:
            if self.config.get("EDGE_VOICE", "en-US-AvaNeural") in opt: self.voice_dropdown.set(opt); break
        if self.config.get("USE_LOCAL_VOSK", True): self.sw_vosk.select()
        if self.config.get("USE_GOOGLE_STT", True): self.sw_stt.select()
        if self.config.get("USE_CLOUD_TTS", True): self.sw_tts.select()
        if self.config.get("FORCE_OFFLINE", False): self.sw_offline.select()

    def wipe_memory(self): self.config["APP_TYPE_MEMORY"] = {}; save_config(self.config); print("Memory Wiped.")

    def edit_log(self):
        log_path = self.config.get("LOG_FILE", "assistant.log")
        if not os.path.exists(log_path):
            messagebox.showwarning("Log File", f"Log file not found at: {log_path}")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(log_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", log_path])
            else:
                subprocess.Popen(["xdg-open", log_path])
        except Exception as e:
            messagebox.showerror("Edit Log", f"Could not open log file: {e}")

    def clear_log(self):
        log_path = self.config.get("LOG_FILE", "assistant.log")
        confirm = messagebox.askyesno("Clear Log", f"Are you sure you want to clear the log file?\n\n{log_path}")
        if confirm:
            try:
                if os.path.exists(log_path):
                    open(log_path, 'w').close()
                    messagebox.showinfo("Clear Log", "Log file has been cleared.")
                else:
                    messagebox.showinfo("Clear Log", "Log file does not exist.")
            except Exception as e:
                messagebox.showerror("Clear Log", f"Could not clear log file: {e}")

    def refresh_history(self):
        # Clear current history view
        for widget in self.history_frame.winfo_children(): widget.destroy()
        
        # Show Commands
        quick = self.config.get("CUSTOM_COMMANDS", {})
        scripts = self.config.get("ADVANCED_SCRIPTS", {})
        custom_apps = self.config.get("CUSTOM_APPS", {})
        
        for i, (trigger, action) in enumerate(quick.items()):
            f = ctk.CTkFrame(self.history_frame, fg_color=COLOR_BG, height=35)
            f.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(f, text=f"💬 {trigger} ➜ {action[:30]}...", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT).pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=25, height=25, fg_color="#441111", hover_color="#881111", command=lambda t=trigger: self.delete_command(t, "quick")).pack(side="right", padx=5)

        if custom_apps:
            f = ctk.CTkFrame(self.history_frame, fg_color="#222222", height=35)
            f.pack(fill="x", padx=5, pady=(10, 2))
            ctk.CTkLabel(f, text="📁 Registered Apps", font=ctk.CTkFont(size=11, weight="bold"), text_color="#7fb5eb").pack(side="left", padx=10)
            f = None
            for name, path in custom_apps.items():
                f = ctk.CTkFrame(self.history_frame, fg_color="#1e252b", height=35)
                f.pack(fill="x", padx=5, pady=2)
                ctk.CTkLabel(f, text=f"🔗 {name} ➜ {path}", font=ctk.CTkFont(size=11), text_color="#a8dba8", wraplength=700, justify="left").pack(side="left", padx=10)
                ctk.CTkButton(f, text="X", width=25, height=25, fg_color="#441111", hover_color="#881111", command=lambda t=name: self.delete_custom_app(t)).pack(side="right", padx=5)

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
        if s and a:
            self.config.setdefault("CUSTOM_COMMANDS", {})[s] = a
            save_config(self.config)
            self.entry_q_speech.delete(0, 'end')
            self.entry_q_action.delete(0, 'end')
            self.refresh_history()

    def add_custom_app(self):
        name = self.entry_app_name.get().lower().strip()
        path = self.entry_app_path.get().strip()
        if name and path:
            self.config.setdefault("CUSTOM_APPS", {})[name] = path
            save_config(self.config)
            self.entry_app_name.delete(0, 'end')
            self.entry_app_path.delete(0, 'end')
            self.refresh_history()

    def delete_custom_app(self, name):
        self.config.get("CUSTOM_APPS", {}).pop(name, None)
        save_config(self.config)
        self.refresh_history()

    def add_script(self):
        t, ty, c = self.entry_script_trigger.get().lower().strip(), self.script_type.get().lower(), self.text_script.get("1.0", "end-1c").strip()
        if t and c: self.config.setdefault("ADVANCED_SCRIPTS", {})[t] = {"type": ty, "code": c}; save_config(self.config); self.entry_script_trigger.delete(0, 'end'); self.text_script.delete("1.0", "end"); self.refresh_history()

    def save_settings(self):
        try:
            self.config["ASSISTANT_NAME"] = self.entry_name.get().strip()
            self.config["ASSISTANT_ALIASES"] = [x.strip() for x in self.entry_aliases.get().split(",") if x.strip()]
            self.config["USER_SALUTATION"] = self.entry_salutation.get().strip()
            self.config["ASSISTANT_PERSONALITY"] = self.entry_personality.get().strip()
            self.config["PRIMARY_AI"] = self.ai_dropdown.get()
            self.config["LLAMA_URL"] = self.entry_llama_url.get().strip()
            self.config["LLAMA_PATH"] = self.entry_ollama_dir.get().strip()
            self.config["LLAMA_DEFAULT_BRAIN"] = self.brain_dropdown.get()
            self.config["LLAMA_CUSTOM_MODEL"] = self.entry_custom_model.get().strip()
            self.config["EDGE_VOICE"] = self.voice_dropdown.get().split("(")[0].strip()
            self.config["USE_LOCAL_VOSK"] = bool(self.sw_vosk.get())
            self.config["USE_GOOGLE_STT"] = bool(self.sw_stt.get())
            self.config["USE_CLOUD_TTS"] = bool(self.sw_tts.get())
            self.config["FORCE_OFFLINE"] = bool(self.sw_offline.get())
            save_config(self.config)
        except Exception as e:
            messagebox.showerror("Save Settings", f"Error saving settings: {e}")

    def monitor_process(self):
        if self.assistant_process and self.assistant_process.poll() is not None: self.assistant_process = None; self._update_ui_stopped()
        self.after(1000, self.monitor_process)

    def _update_ui_stopped(self): self.start_btn.configure(text="START ENGINE", fg_color=COLOR_TEXT, text_color=COLOR_BG); self.status_label.configure(text="Status: IDLE")
    def _update_ui_started(self): self.start_btn.configure(text="STOP ENGINE", fg_color="#331111", text_color="#ff5555"); self.status_label.configure(text="Status: ACTIVE", text_color="#ffffff")

    def toggle_assistant(self):
        if self.assistant_process is None:
            url = self.config.get("LLAMA_URL", "").strip()
            if not url or not ai.is_ollama_running(url):
                proceed = messagebox.askyesno(
                    "Ollama not available",
                    "Ollama is not running or the AI brain model may not be added. Continue anyway?"
                )
                if not proceed:
                    return
            self.save_settings()
            # Use the same Python interpreter (venv-aware)
            venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "Scripts", "python.exe")
            python_exe = venv_python if os.path.exists(venv_python) else sys.executable
            self.assistant_process = subprocess.Popen(
                [python_exe, "main.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            self._update_ui_started()
        else:
            self.shutdown_assistant_process()

if __name__ == "__main__": app = App(); app.mainloop()
