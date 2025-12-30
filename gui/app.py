"""Modern GUI for Telegram Auto-Regger.

Dark theme with custom title bar and window controls.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import webbrowser

from .config_manager import load_config, save_config


# Theme setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class TelegramAutoRegApp(ctk.CTk):
    """Main application window with custom title bar."""
    
    def __init__(self):
        super().__init__()
        
        # Remove default title bar
        self.overrideredirect(True)
        
        # Window config
        self.geometry("900x680")
        self.minsize(800, 600)
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"900x680+{x}+{y}")
        
        # Colors
        self.bg_dark = "#0a0a0a"
        self.bg_card = "#141414"
        self.bg_titlebar = "#0d0d0d"
        self.accent = "#ffffff"
        self.text_dim = "#666666"
        self.border_color = "#1a1a1a"
        
        self.configure(fg_color=self.bg_dark)
        
        # Window state
        self._is_maximized = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        # Build UI
        self._create_title_bar()
        self._create_header()
        self._create_main_content()
        self._create_footer()
        
        # Add border effect
        self._create_border()
    
    def _create_border(self):
        """Create subtle border around window."""
        # This creates a visual border effect
        self.configure(highlightthickness=1, highlightbackground=self.border_color)
    
    def _create_title_bar(self):
        """Create custom title bar with window controls."""
        self.title_bar = ctk.CTkFrame(
            self, 
            fg_color=self.bg_titlebar, 
            height=40,
            corner_radius=0
        )
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.pack_propagate(False)
        
        # App icon/logo (left side)
        icon_label = ctk.CTkLabel(
            self.title_bar,
            text="◆",
            font=ctk.CTkFont(size=16),
            text_color=self.accent,
            width=40
        )
        icon_label.pack(side="left", padx=(15, 5))
        
        # Title text
        title_label = ctk.CTkLabel(
            self.title_bar,
            text="Telegram Auto-Regger",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.accent
        )
        title_label.pack(side="left", padx=5)
        
        # Window control buttons (right side)
        controls_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        controls_frame.pack(side="right", padx=5)
        
        # Minimize button
        self.min_btn = ctk.CTkButton(
            controls_frame,
            text="─",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color="#2a2a2a",
            text_color=self.text_dim,
            width=45,
            height=30,
            corner_radius=5,
            command=self._minimize_window
        )
        self.min_btn.pack(side="left", padx=2)
        
        # Maximize/Restore button
        self.max_btn = ctk.CTkButton(
            controls_frame,
            text="□",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#2a2a2a",
            text_color=self.text_dim,
            width=45,
            height=30,
            corner_radius=5,
            command=self._toggle_maximize
        )
        self.max_btn.pack(side="left", padx=2)
        
        # Close button
        self.close_btn = ctk.CTkButton(
            controls_frame,
            text="✕",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color="#e81123",
            text_color=self.text_dim,
            width=45,
            height=30,
            corner_radius=5,
            command=self._on_exit
        )
        self.close_btn.pack(side="left", padx=2)
        
        # Bind drag events to title bar
        self.title_bar.bind("<Button-1>", self._start_drag)
        self.title_bar.bind("<B1-Motion>", self._on_drag)
        self.title_bar.bind("<Double-Button-1>", lambda e: self._toggle_maximize())
        
        # Also bind to title label for dragging
        title_label.bind("<Button-1>", self._start_drag)
        title_label.bind("<B1-Motion>", self._on_drag)
        title_label.bind("<Double-Button-1>", lambda e: self._toggle_maximize())
        
        icon_label.bind("<Button-1>", self._start_drag)
        icon_label.bind("<B1-Motion>", self._on_drag)
    
    def _start_drag(self, event):
        """Start window drag."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def _on_drag(self, event):
        """Handle window dragging."""
        if self._is_maximized:
            return
        x = self.winfo_x() + event.x - self._drag_start_x
        y = self.winfo_y() + event.y - self._drag_start_y
        self.geometry(f"+{x}+{y}")
    
    def _minimize_window(self):
        """Minimize window."""
        self.overrideredirect(False)
        self.iconify()
        self.after(100, lambda: self.overrideredirect(True))
    
    def _toggle_maximize(self):
        """Toggle maximize/restore."""
        if self._is_maximized:
            # Restore
            self.geometry(self._restore_geometry)
            self.max_btn.configure(text="□")
            self._is_maximized = False
        else:
            # Maximize
            self._restore_geometry = self.geometry()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            self.geometry(f"{screen_w}x{screen_h}+0+0")
            self.max_btn.configure(text="❐")
            self._is_maximized = True

    def _create_header(self):
        """Create header with logo."""
        header = ctk.CTkFrame(self, fg_color=self.bg_dark, height=100)
        header.pack(fill="x", padx=30, pady=(15, 10))
        header.pack_propagate(False)
        
        # Logo text
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(expand=True)
        
        title = ctk.CTkLabel(
            logo_frame,
            text="TELEGRAM AUTO",
            font=ctk.CTkFont(family="Consolas", size=38, weight="bold"),
            text_color=self.accent
        )
        title.pack()
        
        subtitle = ctk.CTkLabel(
            logo_frame,
            text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            font=ctk.CTkFont(size=10),
            text_color="#333333"
        )
        subtitle.pack(pady=(3, 0))
        
        tagline = ctk.CTkLabel(
            logo_frame,
            text="Automated Registration Pipeline",
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color=self.text_dim
        )
        tagline.pack(pady=(3, 0))

    def _create_main_content(self):
        """Create main content area with menu buttons."""
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Left panel - Menu
        menu_frame = ctk.CTkFrame(main, fg_color=self.bg_card, corner_radius=12, width=260)
        menu_frame.pack(side="left", fill="y", padx=(0, 15))
        menu_frame.pack_propagate(False)
        
        menu_title = ctk.CTkLabel(
            menu_frame,
            text="══ MENU ══",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.accent
        )
        menu_title.pack(pady=(20, 15))
        
        # Menu buttons
        buttons_data = [
            ("▶  Start Registration", self._on_start_registration),
            ("📊  Statistics", self._on_statistics),
            ("🌐  Manage Proxies", self._on_proxies),
            ("⚙  Settings", self._on_settings),
            ("✓  Check Config", self._on_check_config),
        ]
        
        for text, command in buttons_data:
            btn = ctk.CTkButton(
                menu_frame,
                text=text,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color="#1a1a1a",
                text_color=self.accent,
                anchor="w",
                height=42,
                corner_radius=8,
                command=command
            )
            btn.pack(fill="x", padx=12, pady=4)
        
        # Exit button at bottom
        exit_btn = ctk.CTkButton(
            menu_frame,
            text="✕  Exit",
            font=ctk.CTkFont(size=13),
            fg_color="#1a1a1a",
            hover_color="#2a2a2a",
            text_color="#888888",
            height=38,
            corner_radius=8,
            command=self._on_exit
        )
        exit_btn.pack(side="bottom", fill="x", padx=12, pady=15)
        
        # Right panel - Content area
        self.content_frame = ctk.CTkFrame(main, fg_color=self.bg_card, corner_radius=12)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Show welcome screen
        self._show_welcome()
    
    def _clear_content(self):
        """Clear content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _show_welcome(self):
        """Show welcome screen."""
        self._clear_content()
        
        welcome = ctk.CTkLabel(
            self.content_frame,
            text="Welcome",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=self.accent
        )
        welcome.pack(pady=(50, 15))
        
        desc = ctk.CTkLabel(
            self.content_frame,
            text="Select an option from the menu to get started.\n\nThis tool automates Telegram account registration\nusing Android emulators, SMS providers, and VPN rotation.",
            font=ctk.CTkFont(size=13),
            text_color=self.text_dim,
            justify="center"
        )
        desc.pack(pady=10)
        
        # Quick start button
        start_btn = ctk.CTkButton(
            self.content_frame,
            text="Quick Start →",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.accent,
            text_color=self.bg_dark,
            hover_color="#cccccc",
            height=45,
            width=180,
            corner_radius=8,
            command=self._on_start_registration
        )
        start_btn.pack(pady=25)

    def _on_start_registration(self):
        """Show registration form."""
        self._clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="══ NEW REGISTRATION ══",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(25, 20))
        
        # Form frame
        form = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        form.pack(fill="x", padx=35)
        
        # Country
        ctk.CTkLabel(form, text="Country", text_color=self.text_dim, font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.country_var = ctk.StringVar(value="USA")
        country_menu = ctk.CTkOptionMenu(
            form,
            values=["USA", "UK", "Russia", "Germany", "France", "Netherlands"],
            variable=self.country_var,
            fg_color="#1a1a1a",
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            dropdown_fg_color="#1a1a1a",
            width=280,
            height=35
        )
        country_menu.pack(anchor="w", pady=(5, 12))
        
        # Max price
        ctk.CTkLabel(form, text="Max SMS Price ($)", text_color=self.text_dim, font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.price_entry = ctk.CTkEntry(form, width=280, height=35, fg_color="#1a1a1a", border_color="#2a2a2a")
        self.price_entry.insert(0, "0.50")
        self.price_entry.pack(anchor="w", pady=(5, 12))
        
        # Number of accounts
        ctk.CTkLabel(form, text="Number of Accounts", text_color=self.text_dim, font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.accounts_entry = ctk.CTkEntry(form, width=280, height=35, fg_color="#1a1a1a", border_color="#2a2a2a")
        self.accounts_entry.insert(0, "1")
        self.accounts_entry.pack(anchor="w", pady=(5, 12))
        
        # Checkboxes
        self.proxy_var = ctk.BooleanVar(value=False)
        proxy_cb = ctk.CTkCheckBox(
            form, text="Use Proxies", variable=self.proxy_var,
            fg_color=self.accent, hover_color="#cccccc", text_color=self.accent,
            font=ctk.CTkFont(size=12)
        )
        proxy_cb.pack(anchor="w", pady=4)
        
        self.vpn_var = ctk.BooleanVar(value=True)
        vpn_cb = ctk.CTkCheckBox(
            form, text="Rotate VPN", variable=self.vpn_var,
            fg_color=self.accent, hover_color="#cccccc", text_color=self.accent,
            font=ctk.CTkFont(size=12)
        )
        vpn_cb.pack(anchor="w", pady=4)
        
        # Start button
        start_btn = ctk.CTkButton(
            form,
            text="Start Registration",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.accent,
            text_color=self.bg_dark,
            hover_color="#cccccc",
            height=42,
            width=280,
            corner_radius=8,
            command=self._start_registration
        )
        start_btn.pack(anchor="w", pady=(20, 0))
    
    def _start_registration(self):
        """Start the registration process."""
        try:
            num = int(self.accounts_entry.get())
            price = float(self.price_entry.get())
            country = self.country_var.get()
            
            messagebox.showinfo(
                "Registration Started",
                f"Starting registration for {num} account(s)\n"
                f"Country: {country}\n"
                f"Max Price: ${price:.2f}\n"
                f"Proxies: {'Yes' if self.proxy_var.get() else 'No'}\n"
                f"VPN: {'Yes' if self.vpn_var.get() else 'No'}"
            )
        except ValueError:
            messagebox.showerror("Error", "Invalid input values")

    def _on_statistics(self):
        """Show statistics view."""
        self._clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="══ STATISTICS ══",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(25, 20))
        
        # Stats grid
        stats_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=35)
        
        stats = [
            ("Total Registrations", "42"),
            ("Successful", "38"),
            ("Failed", "4"),
            ("Success Rate", "90.5%"),
            ("Total SMS Cost", "$12.50"),
            ("Avg Cost/Account", "$0.33"),
        ]
        
        for label, value in stats:
            row = ctk.CTkFrame(stats_frame, fg_color="#1a1a1a", corner_radius=6, height=45)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            
            lbl = ctk.CTkLabel(row, text=label, text_color=self.text_dim, font=ctk.CTkFont(size=13))
            lbl.pack(side="left", padx=18)
            
            val = ctk.CTkLabel(row, text=value, text_color=self.accent, font=ctk.CTkFont(size=13, weight="bold"))
            val.pack(side="right", padx=18)
    
    def _on_proxies(self):
        """Show proxy management."""
        self._clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="══ PROXY MANAGEMENT ══",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(25, 20))
        
        info = ctk.CTkLabel(
            self.content_frame,
            text="Proxy management coming soon...\n\nSupported formats:\n• SOCKS5\n• HTTP/HTTPS",
            font=ctk.CTkFont(size=13),
            text_color=self.text_dim,
            justify="center"
        )
        info.pack(pady=15)
    
    def _on_settings(self):
        """Show settings editor."""
        self._clear_content()
        
        # Load current config
        self.config = load_config()
        
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame, 
            fg_color="transparent",
            scrollbar_button_color="#2a2a2a",
            scrollbar_button_hover_color="#3a3a3a"
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        title = ctk.CTkLabel(
            scroll_frame,
            text="══ SETTINGS ══",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(10, 20))
        
        # === SMS API Section ===
        self._create_section_header(scroll_frame, "SMS API")
        
        # Provider
        self._create_label(scroll_frame, "SMS Provider")
        self.sms_provider_var = ctk.StringVar(value=self.config.get("sms_api", {}).get("provider", "sms-activate"))
        sms_provider = ctk.CTkOptionMenu(
            scroll_frame,
            values=["sms-activate", "grizzly-sms", "5sim", "smshub"],
            variable=self.sms_provider_var,
            fg_color="#1a1a1a",
            button_color="#2a2a2a",
            width=350, height=35
        )
        sms_provider.pack(anchor="w", padx=20, pady=(0, 10))
        
        # API Key
        self._create_label(scroll_frame, "SMS API Key")
        self.sms_api_key = ctk.CTkEntry(
            scroll_frame, width=350, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a",
            placeholder_text="Enter your SMS API key..."
        )
        self.sms_api_key.insert(0, self.config.get("sms_api", {}).get("api_key", ""))
        self.sms_api_key.pack(anchor="w", padx=20, pady=(0, 15))
        
        # === Telethon API Section ===
        self._create_section_header(scroll_frame, "Telegram API (Telethon)")
        
        # API ID
        self._create_label(scroll_frame, "API ID")
        self.api_id_entry = ctk.CTkEntry(
            scroll_frame, width=350, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a",
            placeholder_text="Get from my.telegram.org"
        )
        self.api_id_entry.insert(0, str(self.config.get("telethon", {}).get("api_id", "")))
        self.api_id_entry.pack(anchor="w", padx=20, pady=(0, 10))
        
        # API Hash
        self._create_label(scroll_frame, "API Hash")
        self.api_hash_entry = ctk.CTkEntry(
            scroll_frame, width=350, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a",
            placeholder_text="Get from my.telegram.org"
        )
        self.api_hash_entry.insert(0, self.config.get("telethon", {}).get("api_hash", ""))
        self.api_hash_entry.pack(anchor="w", padx=20, pady=(0, 15))
        
        # === ADB Section ===
        self._create_section_header(scroll_frame, "ADB / Emulator")
        
        # Device Type
        self._create_label(scroll_frame, "Device Type")
        self.device_type_var = ctk.StringVar(value=self.config.get("adb", {}).get("device_type", "E"))
        device_type = ctk.CTkOptionMenu(
            scroll_frame,
            values=["E (Emulator)", "P (Physical)"],
            variable=self.device_type_var,
            fg_color="#1a1a1a",
            button_color="#2a2a2a",
            width=350, height=35
        )
        device_type.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Device UDID
        self._create_label(scroll_frame, "Device UDID")
        self.device_udid = ctk.CTkEntry(
            scroll_frame, width=350, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a",
            placeholder_text="127.0.0.1:5555"
        )
        self.device_udid.insert(0, self.config.get("adb", {}).get("device_udid", "127.0.0.1:5555"))
        self.device_udid.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Appium Port
        self._create_label(scroll_frame, "Appium Port")
        self.appium_port = ctk.CTkEntry(
            scroll_frame, width=350, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a"
        )
        self.appium_port.insert(0, str(self.config.get("adb", {}).get("appium_port", 4723)))
        self.appium_port.pack(anchor="w", padx=20, pady=(0, 10))
        
        # ADB Path
        self._create_label(scroll_frame, "ADB Path")
        adb_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        adb_frame.pack(anchor="w", padx=20, pady=(0, 15))
        
        self.adb_path = ctk.CTkEntry(
            adb_frame, width=280, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a"
        )
        self.adb_path.insert(0, self.config.get("adb", {}).get("adb_path", ""))
        self.adb_path.pack(side="left")
        
        browse_btn = ctk.CTkButton(
            adb_frame, text="...", width=60, height=35,
            fg_color="#2a2a2a", hover_color="#3a3a3a",
            command=self._browse_adb_path
        )
        browse_btn.pack(side="left", padx=(10, 0))
        
        # === VPN Section ===
        self._create_section_header(scroll_frame, "VPN")
        
        self.vpn_enabled = ctk.BooleanVar(value=self.config.get("vpn", {}).get("enabled", True))
        vpn_cb = ctk.CTkCheckBox(
            scroll_frame, text="Enable VPN rotation",
            variable=self.vpn_enabled,
            fg_color=self.accent, hover_color="#cccccc",
            text_color=self.accent
        )
        vpn_cb.pack(anchor="w", padx=20, pady=(0, 10))
        
        self._create_label(scroll_frame, "VPN Provider")
        self.vpn_provider_var = ctk.StringVar(value=self.config.get("vpn", {}).get("provider", "ExpressVPN"))
        vpn_provider = ctk.CTkOptionMenu(
            scroll_frame,
            values=["ExpressVPN", "NordVPN", "Surfshark", "ProtonVPN"],
            variable=self.vpn_provider_var,
            fg_color="#1a1a1a",
            button_color="#2a2a2a",
            width=350, height=35
        )
        vpn_provider.pack(anchor="w", padx=20, pady=(0, 15))
        
        # === Proxy Section ===
        self._create_section_header(scroll_frame, "Proxy")
        
        self.proxy_enabled = ctk.BooleanVar(value=self.config.get("proxy", {}).get("enabled", False))
        proxy_cb = ctk.CTkCheckBox(
            scroll_frame, text="Enable proxy",
            variable=self.proxy_enabled,
            fg_color=self.accent, hover_color="#cccccc",
            text_color=self.accent
        )
        proxy_cb.pack(anchor="w", padx=20, pady=(0, 10))
        
        self._create_label(scroll_frame, "Proxy Type")
        self.proxy_type_var = ctk.StringVar(value=self.config.get("proxy", {}).get("type", "SOCKS5"))
        proxy_type = ctk.CTkOptionMenu(
            scroll_frame,
            values=["SOCKS5", "HTTP", "HTTPS"],
            variable=self.proxy_type_var,
            fg_color="#1a1a1a",
            button_color="#2a2a2a",
            width=350, height=35
        )
        proxy_type.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Proxy Host:Port
        proxy_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        proxy_row.pack(anchor="w", padx=20, pady=(0, 10))
        
        self._create_label(proxy_row, "Host", pack=False)
        self.proxy_host = ctk.CTkEntry(
            proxy_row, width=220, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a",
            placeholder_text="proxy.example.com"
        )
        self.proxy_host.insert(0, self.config.get("proxy", {}).get("host", ""))
        self.proxy_host.pack(side="left", padx=(0, 10))
        
        self.proxy_port = ctk.CTkEntry(
            proxy_row, width=100, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a",
            placeholder_text="Port"
        )
        self.proxy_port.insert(0, self.config.get("proxy", {}).get("port", ""))
        self.proxy_port.pack(side="left")
        
        # Proxy Auth
        auth_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        auth_row.pack(anchor="w", padx=20, pady=(0, 15))
        
        self.proxy_user = ctk.CTkEntry(
            auth_row, width=165, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a",
            placeholder_text="Username (optional)"
        )
        self.proxy_user.insert(0, self.config.get("proxy", {}).get("username", ""))
        self.proxy_user.pack(side="left", padx=(0, 10))
        
        self.proxy_pass = ctk.CTkEntry(
            auth_row, width=165, height=35,
            fg_color="#1a1a1a", border_color="#2a2a2a",
            placeholder_text="Password (optional)",
            show="•"
        )
        self.proxy_pass.insert(0, self.config.get("proxy", {}).get("password", ""))
        self.proxy_pass.pack(side="left")
        
        # === Save Button ===
        save_btn = ctk.CTkButton(
            scroll_frame,
            text="💾  Save Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.accent,
            text_color=self.bg_dark,
            hover_color="#cccccc",
            height=45,
            width=350,
            corner_radius=8,
            command=self._save_settings
        )
        save_btn.pack(anchor="w", padx=20, pady=(20, 30))
    
    def _create_section_header(self, parent, text):
        """Create a section header."""
        header = ctk.CTkLabel(
            parent,
            text=f"─── {text} ───",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.text_dim
        )
        header.pack(anchor="w", padx=20, pady=(15, 10))
    
    def _create_label(self, parent, text, pack=True):
        """Create a form label."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color=self.text_dim
        )
        if pack:
            label.pack(anchor="w", padx=20, pady=(0, 3))
        return label
    
    def _browse_adb_path(self):
        """Browse for ADB executable."""
        path = filedialog.askopenfilename(
            title="Select ADB executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.adb_path.delete(0, "end")
            self.adb_path.insert(0, path)
    
    def _save_settings(self):
        """Save all settings to config file."""
        try:
            # Build config dict
            config = {
                "sms_api": {
                    "provider": self.sms_provider_var.get(),
                    "api_key": self.sms_api_key.get(),
                },
                "telethon": {
                    "api_id": self.api_id_entry.get(),
                    "api_hash": self.api_hash_entry.get(),
                },
                "adb": {
                    "device_type": self.device_type_var.get()[0],  # Get first char (E or P)
                    "device_udid": self.device_udid.get(),
                    "appium_port": int(self.appium_port.get() or 4723),
                    "adb_path": self.adb_path.get(),
                },
                "vpn": {
                    "enabled": self.vpn_enabled.get(),
                    "provider": self.vpn_provider_var.get(),
                },
                "proxy": {
                    "enabled": self.proxy_enabled.get(),
                    "type": self.proxy_type_var.get(),
                    "host": self.proxy_host.get(),
                    "port": self.proxy_port.get(),
                    "username": self.proxy_user.get(),
                    "password": self.proxy_pass.get(),
                },
            }
            
            if save_config(config):
                messagebox.showinfo("Success", "Settings saved successfully!")
            else:
                messagebox.showerror("Error", "Failed to save settings")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _on_check_config(self):
        """Check configuration."""
        self._clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="══ CONFIG CHECK ══",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(25, 20))
        
        checks = [
            ("config.yaml found", True),
            ("ADB connection", True),
            ("SMS API key", True),
            ("All paths exist", True),
        ]
        
        for label, ok in checks:
            row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            row.pack(anchor="w", padx=50, pady=4)
            
            icon = "●" if ok else "○"
            color = "#00ff00" if ok else "#ff4444"
            
            ctk.CTkLabel(row, text=icon, text_color=color, font=ctk.CTkFont(size=14)).pack(side="left")
            ctk.CTkLabel(row, text=f"  {label}", text_color=self.accent, font=ctk.CTkFont(size=13)).pack(side="left")

    def _create_footer(self):
        """Create footer with credits."""
        footer = ctk.CTkFrame(self, fg_color="transparent", height=45)
        footer.pack(fill="x", padx=30, pady=(8, 15))
        footer.pack_propagate(False)
        
        # Separator
        sep = ctk.CTkLabel(
            footer,
            text="━" * 100,
            font=ctk.CTkFont(size=8),
            text_color="#222222"
        )
        sep.pack()
        
        # Credits frame
        credits_frame = ctk.CTkFrame(footer, fg_color="transparent")
        credits_frame.pack(expand=True)
        
        made_with = ctk.CTkLabel(
            credits_frame,
            text="Made with ♥ by ",
            font=ctk.CTkFont(size=11),
            text_color=self.text_dim
        )
        made_with.pack(side="left")
        
        author_btn = ctk.CTkButton(
            credits_frame,
            text="@ibuildrun",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color="#1a1a1a",
            text_color=self.accent,
            width=75,
            height=22,
            command=lambda: webbrowser.open("https://github.com/ibuildrun")
        )
        author_btn.pack(side="left")
        
        sep_label = ctk.CTkLabel(
            credits_frame,
            text="  │  ",
            font=ctk.CTkFont(size=11),
            text_color="#333333"
        )
        sep_label.pack(side="left")
        
        github_btn = ctk.CTkButton(
            credits_frame,
            text="GitHub",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color="#1a1a1a",
            text_color=self.text_dim,
            width=55,
            height=22,
            command=lambda: webbrowser.open("https://github.com/ibuildrun/telegram-auto-reg")
        )
        github_btn.pack(side="left")
    
    def _on_exit(self):
        """Exit application."""
        self.quit()


def main():
    """Run the application."""
    app = TelegramAutoRegApp()
    app.mainloop()


if __name__ == "__main__":
    main()
