"""
Status LED Component - Shows online/offline status
"""
import customtkinter as ctk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


class StatusLed(ctk.CTkLabel):
    def __init__(self, master, is_online=True):
        super().__init__(
            master,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=config.Colors.PRIMARY if is_online else "#EF4444"
        )
        self.is_online = is_online

    def set_online(self, online: bool):
        self.is_online = online
        self.configure(text_color=config.Colors.PRIMARY if online else "#EF4444")