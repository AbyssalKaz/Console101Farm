"""
Wizard101 Bot Suite UI
Dark Grey + Lavender Theme
With Auto-Updater Integration
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import time
from typing import Optional, Dict, Tuple
import os
import json

from .config import config, AppConfig
from .bot_engine import bot_engine, BotMode, BotState
from .controller_emulator import controller, XboxButton
from .input_handler import input_handler
from .mana_refill import mana_refill
from .mana_detection import mana_detector
from .updater import updater

# Custom colors - Dark Grey + Lavender
COLORS = {
    'bg_dark': '#1a1a2e',
    'bg_medium': '#252540',
    'bg_light': '#2d2d4a',
    'lavender': '#9d8cff',
    'lavender_dark': '#7b68ee',
    'lavender_light': '#b8a9ff',
    'text': '#e0e0e0',
    'text_dim': '#888899',
    'success': '#6bba75',
    'warning': '#e6a23c',
    'error': '#f56c6c',
}

ctk.set_appearance_mode("dark")


class ThemedFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('fg_color', COLORS['bg_medium'])
        kwargs.setdefault('corner_radius', 10)
        super().__init__(parent, **kwargs)


class ThemedScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('fg_color', COLORS['bg_dark'])
        kwargs.setdefault('corner_radius', 10)
        super().__init__(parent, **kwargs)


class ThemedButton(ctk.CTkButton):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('fg_color', COLORS['lavender'])
        kwargs.setdefault('hover_color', COLORS['lavender_dark'])
        kwargs.setdefault('text_color', '#ffffff')
        kwargs.setdefault('corner_radius', 8)
        super().__init__(parent, **kwargs)


class ThemedEntry(ctk.CTkEntry):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('fg_color', COLORS['bg_light'])
        kwargs.setdefault('border_color', COLORS['lavender'])
        kwargs.setdefault('text_color', COLORS['text'])
        super().__init__(parent, **kwargs)


class ThemedSwitch(ctk.CTkSwitch):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('progress_color', COLORS['lavender'])
        kwargs.setdefault('button_color', COLORS['lavender_light'])
        kwargs.setdefault('button_hover_color', COLORS['lavender'])
        kwargs.setdefault('text_color', COLORS['text'])
        super().__init__(parent, **kwargs)


class ThemedSlider(ctk.CTkSlider):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('progress_color', COLORS['lavender'])
        kwargs.setdefault('button_color', COLORS['lavender_light'])
        kwargs.setdefault('button_hover_color', COLORS['lavender'])
        super().__init__(parent, **kwargs)


class ThemedOptionMenu(ctk.CTkOptionMenu):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('fg_color', COLORS['lavender'])
        kwargs.setdefault('button_color', COLORS['lavender_dark'])
        kwargs.setdefault('button_hover_color', COLORS['lavender'])
        kwargs.setdefault('dropdown_fg_color', COLORS['bg_medium'])
        kwargs.setdefault('dropdown_hover_color', COLORS['lavender_dark'])
        super().__init__(parent, **kwargs)


class LogPanel(ThemedFrame):
    def __init__(self, parent):
        super().__init__(parent, height=150)
        
        self.log_text = ctk.CTkTextbox(
            self, height=120, font=("Consolas", 10),
            fg_color=COLORS['bg_light'], text_color=COLORS['text'],
            state="disabled"
        )
        self.log_text.pack(padx=5, pady=5, fill="both", expand=True)
        
        ThemedButton(self, text="Clear", command=self.clear, width=60, height=24).pack(pady=2)
    
    def log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def clear(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


class BotControlTab(ThemedScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        ctk.CTkLabel(self, text="Bot Control", font=("Segoe UI", 20, "bold"),
                    text_color=COLORS['lavender']).pack(pady=10)
        
        # Mode selection
        mode_frame = ThemedFrame(self)
        mode_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(mode_frame, text="Mode:", text_color=COLORS['text']).pack(side="left", padx=10)
        self.mode_var = ctk.StringVar(value="Simple")
        ThemedOptionMenu(mode_frame, values=["Simple", "Advanced (Enchant)"], 
                        variable=self.mode_var, width=180).pack(side="left", padx=10)
        
        # Bot keys config
        keys_frame = ThemedFrame(self)
        keys_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(keys_frame, text="Bot Action Keys", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        key_row = ThemedFrame(keys_frame, fg_color=COLORS['bg_light'])
        key_row.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(key_row, text="Select Card:", text_color=COLORS['text'], width=100).pack(side="left", padx=5)
        self.select_key_entry = ThemedEntry(key_row, width=80)
        self.select_key_entry.insert(0, config.bot_keys.select_card)
        self.select_key_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(key_row, text="Confirm:", text_color=COLORS['text'], width=70).pack(side="left", padx=5)
        self.confirm_key_entry = ThemedEntry(key_row, width=80)
        self.confirm_key_entry.insert(0, config.bot_keys.confirm_cast)
        self.confirm_key_entry.pack(side="left", padx=5)
        
        ThemedButton(key_row, text="Save", command=self.save_bot_keys, width=60).pack(side="right", padx=5)
        
        # Status
        status_frame = ThemedFrame(self)
        status_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(status_frame, text="Status:", text_color=COLORS['text']).pack(side="left", padx=10)
        self.status_label = ctk.CTkLabel(status_frame, text="STOPPED", text_color=COLORS['error'],
                                         font=("Segoe UI", 14, "bold"))
        self.status_label.pack(side="left", padx=10)
        
        # Buttons
        btn_frame = ThemedFrame(self)
        btn_frame.pack(pady=10, padx=20, fill="x")
        
        self.start_btn = ThemedButton(btn_frame, text="Start", command=self.start_bot,
                                      fg_color=COLORS['success'], hover_color='#5aa865', width=100)
        self.start_btn.pack(side="left", padx=5, expand=True)
        
        self.pause_btn = ThemedButton(btn_frame, text="Pause", command=self.toggle_pause,
                                      fg_color=COLORS['warning'], hover_color='#cf9235',
                                      width=100, state="disabled")
        self.pause_btn.pack(side="left", padx=5, expand=True)
        
        self.stop_btn = ThemedButton(btn_frame, text="Stop", command=self.stop_bot,
                                     fg_color=COLORS['error'], hover_color='#d45c5c',
                                     width=100, state="disabled")
        self.stop_btn.pack(side="left", padx=5, expand=True)
        
        # Toggles
        toggle_frame = ThemedFrame(self)
        toggle_frame.pack(pady=10, padx=20, fill="x")
        
        self.movement_var = ctk.BooleanVar(value=True)
        ThemedSwitch(toggle_frame, text="Movement Enabled", variable=self.movement_var,
                    command=lambda: setattr(bot_engine, 'movement_enabled', self.movement_var.get())
                    ).pack(pady=5, padx=10, anchor="w")
        
        self.mana_refill_var = ctk.BooleanVar(value=config.mana_refill.enabled)
        ThemedSwitch(toggle_frame, text="Mana Refill Enabled", variable=self.mana_refill_var,
                    command=lambda: setattr(config.mana_refill, 'enabled', self.mana_refill_var.get())
                    ).pack(pady=5, padx=10, anchor="w")
        
        self.debug_var = ctk.BooleanVar(value=True)
        ThemedSwitch(toggle_frame, text="Debug Logging", variable=self.debug_var,
                    command=lambda: setattr(bot_engine, 'debug_mode', self.debug_var.get())
                    ).pack(pady=5, padx=10, anchor="w")
        
        # Stats
        stats_frame = ThemedFrame(self)
        stats_frame.pack(pady=10, padx=20, fill="x")
        
        self.cycles_label = ctk.CTkLabel(stats_frame, text="Cycles: 0", text_color=COLORS['text'])
        self.cycles_label.pack(side="left", padx=20)
        
        self.casts_label = ctk.CTkLabel(stats_frame, text="Casts: 0", text_color=COLORS['text'])
        self.casts_label.pack(side="left", padx=20)
        
        self.idle_label = ctk.CTkLabel(stats_frame, text="Idle: 0s", text_color=COLORS['text'])
        self.idle_label.pack(side="left", padx=20)
    
    def save_bot_keys(self):
        config.bot_keys.select_card = self.select_key_entry.get()
        config.bot_keys.confirm_cast = self.confirm_key_entry.get()
        config.save()
        self.app.log("[+] Bot keys saved")
    
    def start_bot(self):
        mode = BotMode.SIMPLE if "Simple" in self.mode_var.get() else BotMode.ADVANCED
        bot_engine.start(mode)
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
    
    def stop_bot(self):
        bot_engine.stop()
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="Pause")
        self.stop_btn.configure(state="disabled")
    
    def toggle_pause(self):
        bot_engine.toggle_pause()
        self.pause_btn.configure(text="Resume" if bot_engine.state == BotState.PAUSED else "Pause")
    
    def update_status(self, state: BotState):
        colors = {BotState.RUNNING: COLORS['success'], BotState.PAUSED: COLORS['warning'], 
                  BotState.STOPPED: COLORS['error']}
        self.status_label.configure(text=state.name, text_color=colors.get(state, COLORS['text_dim']))
        
        if state == BotState.STOPPED:
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled", text="Pause")
            self.stop_btn.configure(state="disabled")
    
    def update_stats(self):
        self.cycles_label.configure(text=f"Cycles: {bot_engine.cycle_count}")
        self.casts_label.configure(text=f"Casts: {bot_engine.successful_casts}")
        self.idle_label.configure(text=f"Idle: {mana_refill.get_idle_time():.0f}s")


class ControllerTab(ThemedScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        ctk.CTkLabel(self, text="Controller Emulation", font=("Segoe UI", 20, "bold"),
                    text_color=COLORS['lavender']).pack(pady=10)
        
        # Status
        status_frame = ThemedFrame(self)
        status_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(status_frame, text="Status:", text_color=COLORS['text']).pack(side="left", padx=10)
        self.status_label = ctk.CTkLabel(status_frame, text="DISCONNECTED", 
                                         text_color=COLORS['error'], font=("Segoe UI", 12, "bold"))
        self.status_label.pack(side="left", padx=10)
        
        try:
            import vgamepad
            vg_status, vg_color = "Installed", COLORS['success']
        except ImportError:
            vg_status, vg_color = "Not Installed", COLORS['error']
        
        ctk.CTkLabel(status_frame, text=f"(vgamepad: {vg_status})", 
                    text_color=vg_color, font=("Segoe UI", 10)).pack(side="right", padx=10)
        
        # Buttons
        btn_frame = ThemedFrame(self)
        btn_frame.pack(pady=10, padx=20, fill="x")
        
        self.connect_btn = ThemedButton(btn_frame, text="Connect", command=self.connect,
                                        fg_color=COLORS['success'], hover_color='#5aa865', width=120)
        self.connect_btn.pack(side="left", padx=10, expand=True)
        
        self.disconnect_btn = ThemedButton(btn_frame, text="Disconnect", command=self.disconnect,
                                           fg_color=COLORS['error'], hover_color='#d45c5c',
                                           width=120, state="disabled")
        self.disconnect_btn.pack(side="left", padx=10, expand=True)
        
        # Polling toggle
        poll_frame = ThemedFrame(self)
        poll_frame.pack(pady=10, padx=20, fill="x")
        
        self.polling_var = ctk.BooleanVar(value=False)
        self.polling_switch = ThemedSwitch(poll_frame, text="Keyboard-to-Controller Translation",
                                           variable=self.polling_var, command=self.toggle_polling,
                                           state="disabled")
        self.polling_switch.pack(pady=5, padx=10, anchor="w")
        
        ctk.CTkLabel(poll_frame, text="Enable for smooth movement (rapid steps mode)",
                    font=("Segoe UI", 10), text_color=COLORS['text_dim']).pack(padx=10, anchor="w")
        
        # Movement settings
        move_frame = ThemedFrame(self)
        move_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(move_frame, text="Movement Settings", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        step_row = ThemedFrame(move_frame, fg_color=COLORS['bg_light'])
        step_row.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(step_row, text="Step Duration (s):", text_color=COLORS['text'], width=120).pack(side="left", padx=5)
        self.step_dur_entry = ThemedEntry(step_row, width=60)
        self.step_dur_entry.insert(0, str(controller.step_duration))
        self.step_dur_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(step_row, text="Gap (s):", text_color=COLORS['text'], width=60).pack(side="left", padx=5)
        self.step_gap_entry = ThemedEntry(step_row, width=60)
        self.step_gap_entry.insert(0, str(controller.step_gap))
        self.step_gap_entry.pack(side="left", padx=5)
        
        ThemedButton(step_row, text="Apply", command=self.apply_step_settings, width=60).pack(side="right", padx=5)
        
        # Live state display
        state_frame = ThemedFrame(self)
        state_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(state_frame, text="Controller State", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5)
        
        self.buttons_label = ctk.CTkLabel(state_frame, text="Buttons: None", 
                                          font=("Consolas", 10), text_color=COLORS['text'])
        self.buttons_label.pack(pady=2)
        
        self.sticks_label = ctk.CTkLabel(state_frame, text="L: (0,0) | R: (0,0)", 
                                         font=("Consolas", 10), text_color=COLORS['text'])
        self.sticks_label.pack(pady=2)
        
        self.triggers_label = ctk.CTkLabel(state_frame, text="LT: 0 | RT: 0", 
                                           font=("Consolas", 10), text_color=COLORS['text'])
        self.triggers_label.pack(pady=2)
        
        # Help
        help_frame = ThemedFrame(self)
        help_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(help_frame, text="Setup Requirements", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5)
        
        help_text = """1. Install ViGEmBus driver:
   https://github.com/ViGEm/ViGEmBus/releases

2. Install vgamepad: pip install vgamepad

3. Restart computer after installing ViGEmBus"""
        
        ctk.CTkLabel(help_frame, text=help_text, font=("Consolas", 10), 
                    justify="left", text_color=COLORS['text']).pack(padx=10, anchor="w")
    
    def connect(self):
        if controller.connect():
            self.status_label.configure(text="CONNECTED", text_color=COLORS['success'])
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.polling_switch.configure(state="normal")
            self.app.log("[+] Controller connected")
        else:
            self.app.log("[X] Failed to connect controller")
            messagebox.showerror("Error", "Failed to connect. Install ViGEmBus and vgamepad.")
    
    def disconnect(self):
        self.polling_var.set(False)
        controller.disconnect()
        self.status_label.configure(text="DISCONNECTED", text_color=COLORS['error'])
        self.connect_btn.configure(state="normal")
        self.disconnect_btn.configure(state="disabled")
        self.polling_switch.configure(state="disabled")
        self.app.log("[+] Controller disconnected")
    
    def toggle_polling(self):
        if self.polling_var.get():
            controller.start_polling(self.app.log)
            self.app.log("[+] Keyboard translation enabled (rapid steps)")
        else:
            controller.stop_polling()
            self.app.log("[+] Keyboard translation disabled")
    
    def apply_step_settings(self):
        try:
            controller.step_duration = float(self.step_dur_entry.get())
            controller.step_gap = float(self.step_gap_entry.get())
            self.app.log(f"[+] Step settings: duration={controller.step_duration}s, gap={controller.step_gap}s")
        except ValueError:
            messagebox.showerror("Error", "Invalid number format")
    
    def update_preview(self):
        if not controller.is_enabled:
            return
        
        state = controller.state
        
        btns = []
        btn_names = [
            (XboxButton.A, "A"), (XboxButton.B, "B"), (XboxButton.X, "X"), (XboxButton.Y, "Y"),
            (XboxButton.DPAD_UP, "Up"), (XboxButton.DPAD_DOWN, "Dn"),
            (XboxButton.DPAD_LEFT, "Lt"), (XboxButton.DPAD_RIGHT, "Rt"),
            (XboxButton.LEFT_SHOULDER, "LB"), (XboxButton.RIGHT_SHOULDER, "RB"),
        ]
        for btn, name in btn_names:
            if state.buttons & btn:
                btns.append(name)
        
        self.buttons_label.configure(text=f"Buttons: {', '.join(btns) if btns else 'None'}")
        self.sticks_label.configure(text=f"L: ({state.left_stick_x},{state.left_stick_y}) | R: ({state.right_stick_x},{state.right_stick_y})")
        self.triggers_label.configure(text=f"LT: {state.left_trigger} | RT: {state.right_trigger}")


class ControllerBindingsTab(ThemedScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._entries: Dict[str, ThemedEntry] = {}
        
        ctk.CTkLabel(self, text="Controller Bindings", font=("Segoe UI", 20, "bold"),
                    text_color=COLORS['lavender']).pack(pady=10)
        
        ctk.CTkLabel(self, text="Enter keyboard key names (e.g., 'space', 'lctrl', 'w', 'up')",
                    font=("Segoe UI", 10), text_color=COLORS['text_dim']).pack(pady=5)
        
        bindings = config.controller
        
        self._create_section("Face Buttons", [
            ("A Button:", "button_a", bindings.button_a),
            ("B Button:", "button_b", bindings.button_b),
            ("X Button:", "button_x", bindings.button_x),
            ("Y Button:", "button_y", bindings.button_y),
        ])
        
        self._create_section("Bumpers & Triggers", [
            ("Left Bumper:", "left_bumper", bindings.left_bumper),
            ("Right Bumper:", "right_bumper", bindings.right_bumper),
            ("Left Trigger:", "left_trigger", bindings.left_trigger),
            ("Right Trigger:", "right_trigger", bindings.right_trigger),
        ])
        
        self._create_section("D-Pad", [
            ("D-Pad Up:", "dpad_up", bindings.dpad_up),
            ("D-Pad Down:", "dpad_down", bindings.dpad_down),
            ("D-Pad Left:", "dpad_left", bindings.dpad_left),
            ("D-Pad Right:", "dpad_right", bindings.dpad_right),
        ])
        
        self._create_section("Left Stick", [
            ("Up (Forward):", "left_stick_up", bindings.left_stick_up),
            ("Down (Back):", "left_stick_down", bindings.left_stick_down),
            ("Left:", "left_stick_left", bindings.left_stick_left),
            ("Right:", "left_stick_right", bindings.left_stick_right),
            ("Click:", "left_stick_click", bindings.left_stick_click),
        ])
        
        self._create_section("Menu Buttons", [
            ("Start:", "start", bindings.start),
            ("Back:", "back", bindings.back),
            ("Guide:", "guide", bindings.guide),
        ])
        
        # Mouse options
        mouse_frame = ThemedFrame(self)
        mouse_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(mouse_frame, text="Mouse Bindings", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5)
        
        self.mouse_left_var = ctk.BooleanVar(value=bindings.mouse_left_trigger)
        ThemedSwitch(mouse_frame, text="Left Click -> Trigger", 
                    variable=self.mouse_left_var).pack(pady=2, padx=10, anchor="w")
        
        self.mouse_right_var = ctk.BooleanVar(value=bindings.mouse_right_trigger)
        ThemedSwitch(mouse_frame, text="Right Click -> Trigger", 
                    variable=self.mouse_right_var).pack(pady=2, padx=10, anchor="w")
        
        ThemedButton(self, text="Save Bindings", command=self.save_bindings,
                    fg_color=COLORS['success'], hover_color='#5aa865').pack(pady=20)
    
    def _create_section(self, title: str, items: list):
        frame = ThemedFrame(self)
        frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(frame, text=title, font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        for label, key, default in items:
            row = ThemedFrame(frame, fg_color=COLORS['bg_light'])
            row.pack(pady=2, padx=10, fill="x")
            
            ctk.CTkLabel(row, text=label, width=120, anchor="w", text_color=COLORS['text']).pack(side="left")
            entry = ThemedEntry(row, width=100)
            entry.insert(0, default)
            entry.pack(side="left", padx=5)
            self._entries[key] = entry
    
    def save_bindings(self):
        try:
            for key, entry in self._entries.items():
                setattr(config.controller, key, entry.get())
            
            config.controller.mouse_left_trigger = self.mouse_left_var.get()
            config.controller.mouse_right_trigger = self.mouse_right_var.get()
            
            config.save()
            self.app.log("[+] Bindings saved")
            messagebox.showinfo("Saved", "Controller bindings saved!")
        except Exception as e:
            messagebox.showerror("Error", str(e))


class ComboEditorTab(ThemedScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        ctk.CTkLabel(self, text="Combo Editor", font=("Segoe UI", 20, "bold"),
                    text_color=COLORS['lavender']).pack(pady=10)
        
        ctk.CTkLabel(self, text="Edit the mana refill combo sequence (JSON format)",
                    font=("Segoe UI", 10), text_color=COLORS['text_dim']).pack(pady=5)
        
        # Action reference
        ref_frame = ThemedFrame(self)
        ref_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(ref_frame, text="Available Actions", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        ref_text = """button        - Press a button (value: A, B, X, Y, DPAD_UP, etc.)
wait          - Wait for duration seconds
stick_forward - Hold stick forward for duration
stick_back    - Hold stick backward for duration
stick_left    - Hold stick left for duration
stick_right   - Hold stick right for duration
stick_hold    - Hold stick (value: up/down/left/right) until release
stick_release - Release stick
trigger_hold  - Hold trigger (value: left/right) until release
trigger_release - Release trigger (value: left/right)"""
        
        ctk.CTkLabel(ref_frame, text=ref_text, font=("Consolas", 9), justify="left",
                    text_color=COLORS['text']).pack(padx=10, anchor="w")
        
        # Editor
        editor_frame = ThemedFrame(self)
        editor_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(editor_frame, text="Combo Sequence (JSON)", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        self.combo_text = ctk.CTkTextbox(editor_frame, height=300, font=("Consolas", 10),
                                         fg_color=COLORS['bg_light'], text_color=COLORS['text'])
        self.combo_text.pack(padx=10, pady=10, fill="both", expand=True)
        
        self._load_combo()
        
        # Buttons
        btn_frame = ThemedFrame(self)
        btn_frame.pack(pady=10, padx=20, fill="x")
        
        ThemedButton(btn_frame, text="Save Combo", command=self.save_combo,
                    fg_color=COLORS['success'], hover_color='#5aa865', width=120).pack(side="left", padx=10)
        
        ThemedButton(btn_frame, text="Reset to Default", command=self.reset_combo,
                    fg_color=COLORS['warning'], hover_color='#cf9235', width=120).pack(side="left", padx=10)
        
        ThemedButton(btn_frame, text="Test Combo", command=self.test_combo,
                    fg_color=COLORS['lavender'], width=120).pack(side="left", padx=10)
    
    def _load_combo(self):
        self.combo_text.delete("1.0", "end")
        combo_json = json.dumps(config.mana_refill_combo, indent=2)
        self.combo_text.insert("1.0", combo_json)
    
    def save_combo(self):
        try:
            combo_json = self.combo_text.get("1.0", "end").strip()
            combo = json.loads(combo_json)
            
            if not isinstance(combo, list):
                raise ValueError("Combo must be a list of steps")
            
            for i, step in enumerate(combo):
                if 'action' not in step:
                    raise ValueError(f"Step {i+1} missing 'action' field")
            
            config.mana_refill_combo = combo
            config.save()
            self.app.log("[+] Combo saved successfully")
            messagebox.showinfo("Saved", "Combo sequence saved!")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Invalid JSON: {e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def reset_combo(self):
        if messagebox.askyesno("Reset", "Reset combo to default?"):
            config.mana_refill_combo = AppConfig().mana_refill_combo
            config.save()
            self._load_combo()
            self.app.log("[+] Combo reset to default")
    
    def test_combo(self):
        if not controller.is_enabled:
            messagebox.showwarning("Warning", "Connect controller first!")
            return
        
        if messagebox.askyesno("Test", "Run combo sequence now?"):
            self.save_combo()
            threading.Thread(target=mana_refill.execute, daemon=True).start()
            self.app.log("[*] Running test combo...")


class TimingSettingsTab(ThemedScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._entries: Dict[str, ThemedEntry] = {}
        
        ctk.CTkLabel(self, text="Timing Settings", font=("Segoe UI", 20, "bold"),
                    text_color=COLORS['lavender']).pack(pady=10)
        
        self._create_section("Key Press Timing", [
            ("Key Duration (s):", "key_dur", str(config.timing.key_press_duration)),
            ("Key Delay (s):", "key_delay", str(config.timing.key_press_delay)),
            ("Action Delay (s):", "action_delay", str(config.timing.action_delay)),
        ])
        
        self._create_section("Battle Timing", [
            ("Post-Cast Wait (s):", "cast_wait", str(config.timing.post_cast_wait)),
            ("Scan Interval (s):", "scan", str(config.timing.scan_interval)),
        ])
        
        self._create_section("Movement", [
            ("W/S Repeats:", "ws_repeats", str(config.movement.ws_repeats)),
            ("Hold Duration (s):", "hold_dur", str(config.movement.hold_duration)),
        ])
        
        # Confidence sliders
        img_frame = ThemedFrame(self)
        img_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(img_frame, text="Image Recognition", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        conf_row = ThemedFrame(img_frame, fg_color=COLORS['bg_light'])
        conf_row.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(conf_row, text="Match Confidence:", width=150, text_color=COLORS['text']).pack(side="left")
        self.conf_slider = ThemedSlider(conf_row, from_=0.5, to=1.0, number_of_steps=50)
        self.conf_slider.set(config.images.confidence)
        self.conf_slider.pack(side="left", padx=5, expand=True, fill="x")
        self.conf_label = ctk.CTkLabel(conf_row, text=f"{config.images.confidence:.2f}", 
                                       width=50, text_color=COLORS['text'])
        self.conf_label.pack(side="right")
        self.conf_slider.configure(command=lambda v: self.conf_label.configure(text=f"{v:.2f}"))
        
        ThemedButton(self, text="Save Settings", command=self.save_settings,
                    fg_color=COLORS['success'], hover_color='#5aa865').pack(pady=20)
    
    def _create_section(self, title: str, items: list):
        frame = ThemedFrame(self)
        frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(frame, text=title, font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        for label, key, default in items:
            row = ThemedFrame(frame, fg_color=COLORS['bg_light'])
            row.pack(pady=2, padx=10, fill="x")
            
            ctk.CTkLabel(row, text=label, width=180, anchor="w", text_color=COLORS['text']).pack(side="left")
            entry = ThemedEntry(row, width=80)
            entry.insert(0, default)
            entry.pack(side="left", padx=5)
            self._entries[key] = entry
    
    def save_settings(self):
        try:
            config.timing.key_press_duration = float(self._entries["key_dur"].get())
            config.timing.key_press_delay = float(self._entries["key_delay"].get())
            config.timing.action_delay = float(self._entries["action_delay"].get())
            config.timing.post_cast_wait = float(self._entries["cast_wait"].get())
            config.timing.scan_interval = float(self._entries["scan"].get())
            config.movement.ws_repeats = int(self._entries["ws_repeats"].get())
            config.movement.hold_duration = float(self._entries["hold_dur"].get())
            config.images.confidence = self.conf_slider.get()
            
            config.save()
            self.app.log("[+] Timing settings saved")
            messagebox.showinfo("Saved", "Settings saved!")
        except Exception as e:
            messagebox.showerror("Error", str(e))


class ImagesTab(ThemedScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        ctk.CTkLabel(self, text="Image Templates", font=("Segoe UI", 20, "bold"),
                    text_color=COLORS['lavender']).pack(pady=10)
        
        # Instructions
        info_frame = ThemedFrame(self)
        info_frame.pack(pady=10, padx=20, fill="x")
        
        info_text = """Required Images (place in 'images' folder):

CARDS:
  tempest.png      - Your spell card (Tempest)
  colossal.png     - Enchant card (Colossal)
  tempest_enchanted.png - Enchanted Tempest

TIPS:
  - Crop tightly around the card
  - Use PNG format
  - Lower confidence if not detecting"""
        
        ctk.CTkLabel(info_frame, text=info_text, font=("Consolas", 10), 
                    justify="left", text_color=COLORS['text']).pack(padx=10, pady=10, anchor="w")
        
        # Status
        status_frame = ThemedFrame(self)
        status_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(status_frame, text="Image Status", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        self.status_labels = {}
        images = [
            ("Tempest (Spell)", config.images.tempest_image),
            ("Colossal (Enchant)", config.images.colossal_image),
            ("Tempest Enchanted", config.images.tempest_enchanted_image),
            ("Mana Zero", config.images.mana_zero),
        ]
        
        for name, filename in images:
            row = ThemedFrame(status_frame, fg_color=COLORS['bg_light'])
            row.pack(pady=2, padx=10, fill="x")
            
            ctk.CTkLabel(row, text=f"{name}:", width=150, anchor="w", text_color=COLORS['text']).pack(side="left")
            
            exists = os.path.exists(os.path.join(config.images.folder, filename))
            status = "Found" if exists else "Missing"
            color = COLORS['success'] if exists else COLORS['error']
            
            label = ctk.CTkLabel(row, text=status, text_color=color)
            label.pack(side="left", padx=5)
            
            ctk.CTkLabel(row, text=f"({filename})", text_color=COLORS['text_dim'], 
                        font=("Consolas", 9)).pack(side="right", padx=5)
            
            self.status_labels[name] = (label, filename)
        
        # Buttons
        btn_frame = ThemedFrame(self)
        btn_frame.pack(pady=10, padx=20, fill="x")
        
        ThemedButton(btn_frame, text="Refresh", command=self.refresh, width=100).pack(side="left", padx=10)
        ThemedButton(btn_frame, text="Open Folder", command=self.open_folder, width=100).pack(side="left", padx=10)
        ThemedButton(btn_frame, text="Test Detection", command=self.test_detection, width=120).pack(side="left", padx=10)
    
    def refresh(self):
        for name, (label, filename) in self.status_labels.items():
            exists = os.path.exists(os.path.join(config.images.folder, filename))
            label.configure(text="Found" if exists else "Missing",
                          text_color=COLORS['success'] if exists else COLORS['error'])
        self.app.log("[*] Image status refreshed")
    
    def open_folder(self):
        import subprocess
        folder = config.images.folder
        if not os.path.exists(folder):
            os.makedirs(folder)
        subprocess.Popen(f'explorer "{os.path.abspath(folder)}"')
    
    def test_detection(self):
        """Test card detection on current screen"""
        from .image_recognition import image_recognition, CardType
        
        self.app.log("[*] Testing card detection...")
        
        # Load templates
        image_recognition.load_card_template("tempest", config.images.tempest_image, CardType.SPELL)
        image_recognition.load_card_template("colossal", config.images.colossal_image, CardType.ENCHANT)
        image_recognition.load_card_template("tempest_enchanted", config.images.tempest_enchanted_image, CardType.ENCHANTED_SPELL)
        
        # Find cards
        cards = image_recognition.find_cards(config.images.confidence)
        
        if cards:
            self.app.log(f"[+] Found {len(cards)} cards:")
            for card in cards:
                self.app.log(f"    - {card.name} ({card.card_type.name}) at ({card.x}, {card.y}) conf={card.confidence:.2f}")
        else:
            self.app.log("[!] No cards detected. Check your image templates.")
            self.app.log(f"    - Confidence threshold: {config.images.confidence}")
            self.app.log("    - Try lowering confidence in Timing settings")


class HotkeysTab(ThemedScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._entries: Dict[str, ThemedEntry] = {}
        
        ctk.CTkLabel(self, text="Hotkeys", font=("Segoe UI", 20, "bold"),
                    text_color=COLORS['lavender']).pack(pady=10)
        
        frame = ThemedFrame(self)
        frame.pack(pady=10, padx=20, fill="x")
        
        hotkeys = [
            ("Stop Bot:", "stop", config.hotkeys.stop),
            ("Pause/Resume:", "pause", config.hotkeys.pause),
            ("Toggle Movement:", "movement", config.hotkeys.toggle_movement),
            ("Toggle Controller:", "controller", config.hotkeys.toggle_controller),
        ]
        
        for label, key, default in hotkeys:
            row = ThemedFrame(frame, fg_color=COLORS['bg_light'])
            row.pack(pady=2, padx=10, fill="x")
            
            ctk.CTkLabel(row, text=label, width=150, anchor="w", text_color=COLORS['text']).pack(side="left")
            entry = ThemedEntry(row, width=100)
            entry.insert(0, default)
            entry.pack(side="left", padx=5)
            self._entries[key] = entry
        
        ThemedButton(self, text="Save Hotkeys", command=self.save_hotkeys,
                    fg_color=COLORS['success'], hover_color='#5aa865').pack(pady=20)
    
    def save_hotkeys(self):
        try:
            config.hotkeys.stop = self._entries["stop"].get()
            config.hotkeys.pause = self._entries["pause"].get()
            config.hotkeys.toggle_movement = self._entries["movement"].get()
            config.hotkeys.toggle_controller = self._entries["controller"].get()
            config.save()
            self.app.log("[+] Hotkeys saved")
            messagebox.showinfo("Saved", "Hotkeys saved!")
        except Exception as e:
            messagebox.showerror("Error", str(e))


class AboutTab(ThemedScrollableFrame):
    """About tab with version info and update button"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        ctk.CTkLabel(self, text="About", font=("Segoe UI", 20, "bold"),
                    text_color=COLORS['lavender']).pack(pady=10)
        
        # Version info
        version_frame = ThemedFrame(self)
        version_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(version_frame, text="Wizard101 Bot Suite", font=("Segoe UI", 16, "bold"),
                    text_color=COLORS['text']).pack(pady=10)
        
        self.version_label = ctk.CTkLabel(version_frame, text=f"Version: {updater.current_version}",
                                          font=("Segoe UI", 12), text_color=COLORS['text_dim'])
        self.version_label.pack(pady=5)
        
        # Update section
        update_frame = ThemedFrame(self)
        update_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(update_frame, text="Updates", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        self.update_status = ctk.CTkLabel(update_frame, text="Click 'Check for Updates' to check",
                                          font=("Segoe UI", 10), text_color=COLORS['text_dim'])
        self.update_status.pack(pady=5, padx=10, anchor="w")
        
        btn_row = ThemedFrame(update_frame, fg_color=COLORS['bg_medium'])
        btn_row.pack(pady=10, padx=10, fill="x")
        
        self.check_btn = ThemedButton(btn_row, text="Check for Updates", command=self.check_updates,
                                      width=150)
        self.check_btn.pack(side="left", padx=5)
        
        self.install_btn = ThemedButton(btn_row, text="Install Update", command=self.install_update,
                                        fg_color=COLORS['success'], hover_color='#5aa865',
                                        width=150, state="disabled")
        self.install_btn.pack(side="left", padx=5)
        
        # GitHub info
        github_frame = ThemedFrame(self)
        github_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(github_frame, text="GitHub Repository", font=("Segoe UI", 12, "bold"),
                    text_color=COLORS['lavender']).pack(pady=5, anchor="w", padx=10)
        
        repo_url = f"https://github.com/{updater.github_owner}/{updater.github_repo}"
        ctk.CTkLabel(github_frame, text=repo_url, font=("Consolas", 10),
                    text_color=COLORS['lavender_light']).pack(pady=5, padx=10, anchor="w")
    
    def check_updates(self):
        self.update_status.configure(text="Checking for updates...", text_color=COLORS['warning'])
        self.check_btn.configure(state="disabled")
        
        def do_check():
            available, version = updater.check_for_updates()
            
            def update_ui():
                self.check_btn.configure(state="normal")
                if available:
                    self.update_status.configure(
                        text=f"Update available: v{version}",
                        text_color=COLORS['success']
                    )
                    self.install_btn.configure(state="normal")
                    self.app.log(f"[+] Update available: v{updater.current_version} -> v{version}")
                elif version:
                    self.update_status.configure(
                        text=f"Up to date (v{version})",
                        text_color=COLORS['text']
                    )
                    self.app.log(f"[+] Already up to date: v{version}")
                else:
                    self.update_status.configure(
                        text="Could not check for updates",
                        text_color=COLORS['error']
                    )
                    self.app.log("[!] Could not check for updates")
            
            self.app.after(0, update_ui)
        
        threading.Thread(target=do_check, daemon=True).start()
    
    def install_update(self):
        if messagebox.askyesno("Install Update", "Download and install the latest update?"):
            self.update_status.configure(text="Downloading update...", text_color=COLORS['warning'])
            self.install_btn.configure(state="disabled")
            
            def do_install():
                success = updater.download_update()
                
                def update_ui():
                    if success:
                        self.update_status.configure(
                            text="Update installed! Please restart.",
                            text_color=COLORS['success']
                        )
                        self.app.log("[+] Update installed successfully!")
                        messagebox.showinfo("Success", "Update installed!\n\nPlease restart the application.")
                    else:
                        self.update_status.configure(
                            text="Update failed",
                            text_color=COLORS['error']
                        )
                        self.install_btn.configure(state="normal")
                        self.app.log("[X] Update failed")
                
                self.app.after(0, update_ui)
            
            threading.Thread(target=do_install, daemon=True).start()


class WizardBotApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Wizard101 Bot Suite")
        self.geometry(f"{config.window.width}x{config.window.height}")
        self.minsize(config.window.min_width, config.window.min_height)
        self.configure(fg_color=COLORS['bg_dark'])
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'])
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Tabview
        self.tabview = ctk.CTkTabview(main_frame, fg_color=COLORS['bg_medium'],
                                      segmented_button_fg_color=COLORS['bg_light'],
                                      segmented_button_selected_color=COLORS['lavender'],
                                      segmented_button_selected_hover_color=COLORS['lavender_dark'],
                                      segmented_button_unselected_color=COLORS['bg_light'],
                                      segmented_button_unselected_hover_color=COLORS['bg_medium'])
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create tabs
        tabs = ["Control", "Controller", "Bindings", "Combo", "Timing", "Images", "Hotkeys", "About"]
        for tab in tabs:
            self.tabview.add(tab)
            self.tabview.tab(tab).grid_columnconfigure(0, weight=1)
            self.tabview.tab(tab).grid_rowconfigure(0, weight=1)
        
        # Create panels
        self.control_panel = BotControlTab(self.tabview.tab("Control"), self)
        self.control_panel.grid(row=0, column=0, sticky="nsew")
        
        self.controller_panel = ControllerTab(self.tabview.tab("Controller"), self)
        self.controller_panel.grid(row=0, column=0, sticky="nsew")
        
        self.bindings_panel = ControllerBindingsTab(self.tabview.tab("Bindings"), self)
        self.bindings_panel.grid(row=0, column=0, sticky="nsew")
        
        self.combo_panel = ComboEditorTab(self.tabview.tab("Combo"), self)
        self.combo_panel.grid(row=0, column=0, sticky="nsew")
        
        self.timing_panel = TimingSettingsTab(self.tabview.tab("Timing"), self)
        self.timing_panel.grid(row=0, column=0, sticky="nsew")
        
        self.images_panel = ImagesTab(self.tabview.tab("Images"), self)
        self.images_panel.grid(row=0, column=0, sticky="nsew")
        
        self.hotkeys_panel = HotkeysTab(self.tabview.tab("Hotkeys"), self)
        self.hotkeys_panel.grid(row=0, column=0, sticky="nsew")
        
        self.about_panel = AboutTab(self.tabview.tab("About"), self)
        self.about_panel.grid(row=0, column=0, sticky="nsew")
        
        # Log panel
        self.log_panel = LogPanel(main_frame)
        self.log_panel.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Callbacks
        bot_engine.set_log_callback(self.log)
        bot_engine.set_state_callback(self.on_state_change)
        mana_refill.set_log_callback(self.log)
        updater.set_log_callback(self.log)
        
        # Hotkey thread
        self._hotkey_thread = threading.Thread(target=self._hotkey_loop, daemon=True)
        self._hotkey_thread.start()
        
        # Update loop
        self._update_loop()
        
        # Welcome message
        self.log(f"[*] Wizard101 Bot Suite v{updater.current_version}")
        self.log("[*] Theme: Dark Grey + Lavender")
        
        try:
            import vgamepad
            self.log("[+] vgamepad installed")
        except ImportError:
            self.log("[!] vgamepad not installed - pip install vgamepad")
        
        mana_detector.load_templates()
        
        # Check for updates on startup (background)
        self.after(2000, self._check_updates_startup)
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _check_updates_startup(self):
        """Check for updates in background on startup"""
        def do_check():
            available, version = updater.check_for_updates()
            if available:
                self.after(0, lambda: self._prompt_update(version))
        
        threading.Thread(target=do_check, daemon=True).start()
    
    def _prompt_update(self, version: str):
        """Prompt user about available update"""
        result = messagebox.askyesno(
            "Update Available",
            f"A new version is available!\n\n"
            f"Current: v{updater.current_version}\n"
            f"Latest: v{version}\n\n"
            f"Would you like to update now?"
        )
        
        if result:
            self.tabview.set("About")
            self.about_panel.install_update()
    
    def log(self, message: str):
        self.after(0, lambda: self.log_panel.log(message))
    
    def on_state_change(self, state: BotState):
        self.after(0, lambda: self.control_panel.update_status(state))
    
    def _hotkey_loop(self):
        key_states = {}
        
        while True:
            try:
                hotkeys = {
                    'stop': config.hotkeys.stop,
                    'pause': config.hotkeys.pause,
                    'movement': config.hotkeys.toggle_movement,
                    'controller': config.hotkeys.toggle_controller,
                }
                
                for name, key in hotkeys.items():
                    if not key:
                        continue
                    
                    pressed = input_handler.is_key_pressed(key)
                    was_pressed = key_states.get(name, False)
                    
                    if was_pressed and not pressed:
                        if name == 'stop' and bot_engine.state in [BotState.RUNNING, BotState.PAUSED]:
                            self.after(0, self.control_panel.stop_bot)
                        elif name == 'pause' and bot_engine.state in [BotState.RUNNING, BotState.PAUSED]:
                            self.after(0, self.control_panel.toggle_pause)
                        elif name == 'movement':
                            bot_engine.toggle_movement()
                            self.after(0, lambda: self.control_panel.movement_var.set(bot_engine.movement_enabled))
                        elif name == 'controller':
                            if controller.is_enabled:
                                self.after(0, self.controller_panel.disconnect)
                            else:
                                self.after(0, self.controller_panel.connect)
                    
                    key_states[name] = pressed
                
                time.sleep(0.05)
            except:
                pass
    
    def _update_loop(self):
        self.control_panel.update_stats()
        self.controller_panel.update_preview()
        self.after(100, self._update_loop)
    
    def on_close(self):
        config.window.width = self.winfo_width()
        config.window.height = self.winfo_height()
        config.save()
        bot_engine.stop()
        controller.disconnect()
        self.destroy()


def run_app():
    app = WizardBotApp()
    app.mainloop()