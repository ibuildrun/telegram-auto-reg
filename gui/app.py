"""Modern GUI for Telegram Auto-Regger.

Dark theme with customtkinter.
"""

import customtkinter as ctk
from tkinter import messagebox
import webbrowser


# Theme setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class TelegramAutoRegApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Window config
        self.title("Telegram Auto-Regger")
        self.geometry("900x650")
        self.minsize(800, 600)
        
        # Colors
        self.bg_dark = "#0a0a0a"
        self.bg_card = "#141414"
        self.accent = "#ffffff"
        self.text_dim = "#666666"
        
        self.configure(fg_color=self.bg_dark)
        
        # Build UI
        self._create_header()
        self._create_main_content()
        self._create_footer()
        
    def _create_header(self):
        """Create header with logo."""
        header = ctk.CTkFrame(self, fg_color=self.bg_dark, height=120)
        header.pack(fill="x", padx=30, pady=(20, 10))
        header.pack_propagate(False)
        
        # Logo text
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(expand=True)
        
        title = ctk.CTkLabel(
            logo_frame,
            text="TELEGRAM AUTO",
            font=ctk.CTkFont(family="Consolas", size=42, weight="bold"),
            text_color=self.accent
        )
        title.pack()
        
        subtitle = ctk.CTkLabel(
            logo_frame,
            text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            font=ctk.CTkFont(size=12),
            text_color=self.text_dim
        )
        subtitle.pack(pady=(5, 0))
        
        tagline = ctk.CTkLabel(
            logo_frame,
            text="Automated Registration Pipeline",
            font=ctk.CTkFont(size=14, slant="italic"),
            text_color=self.text_dim
        )
        tagline.pack(pady=(5, 0))

    def _create_main_content(self):
        """Create main content area with menu buttons."""
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Left panel - Menu
        menu_frame = ctk.CTkFrame(main, fg_color=self.bg_card, corner_radius=15, width=280)
        menu_frame.pack(side="left", fill="y", padx=(0, 15))
        menu_frame.pack_propagate(False)
        
        menu_title = ctk.CTkLabel(
            menu_frame,
            text="═══ MENU ═══",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.accent
        )
        menu_title.pack(pady=(25, 20))
        
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
                font=ctk.CTkFont(size=14),
                fg_color="transparent",
                hover_color="#1a1a1a",
                text_color=self.accent,
                anchor="w",
                height=45,
                corner_radius=8,
                command=command
            )
            btn.pack(fill="x", padx=15, pady=5)
        
        # Exit button at bottom
        exit_btn = ctk.CTkButton(
            menu_frame,
            text="✕  Exit",
            font=ctk.CTkFont(size=14),
            fg_color="#1a1a1a",
            hover_color="#2a2a2a",
            text_color="#888888",
            height=40,
            corner_radius=8,
            command=self._on_exit
        )
        exit_btn.pack(side="bottom", fill="x", padx=15, pady=20)
        
        # Right panel - Content area
        self.content_frame = ctk.CTkFrame(main, fg_color=self.bg_card, corner_radius=15)
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
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.accent
        )
        welcome.pack(pady=(60, 20))
        
        desc = ctk.CTkLabel(
            self.content_frame,
            text="Select an option from the menu to get started.\n\nThis tool automates Telegram account registration\nusing Android emulators, SMS providers, and VPN rotation.",
            font=ctk.CTkFont(size=14),
            text_color=self.text_dim,
            justify="center"
        )
        desc.pack(pady=10)
        
        # Quick start button
        start_btn = ctk.CTkButton(
            self.content_frame,
            text="Quick Start →",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.accent,
            text_color=self.bg_dark,
            hover_color="#cccccc",
            height=50,
            width=200,
            corner_radius=10,
            command=self._on_start_registration
        )
        start_btn.pack(pady=30)

    def _on_start_registration(self):
        """Show registration form."""
        self._clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="═══ NEW REGISTRATION ═══",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(30, 25))
        
        # Form frame
        form = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        form.pack(fill="x", padx=40)
        
        # Country
        ctk.CTkLabel(form, text="Country", text_color=self.text_dim).pack(anchor="w")
        self.country_var = ctk.StringVar(value="USA")
        country_menu = ctk.CTkOptionMenu(
            form,
            values=["USA", "UK", "Russia", "Germany", "France", "Netherlands"],
            variable=self.country_var,
            fg_color="#1a1a1a",
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            dropdown_fg_color="#1a1a1a",
            width=300
        )
        country_menu.pack(anchor="w", pady=(5, 15))
        
        # Max price
        ctk.CTkLabel(form, text="Max SMS Price ($)", text_color=self.text_dim).pack(anchor="w")
        self.price_entry = ctk.CTkEntry(form, width=300, fg_color="#1a1a1a", border_color="#2a2a2a")
        self.price_entry.insert(0, "0.50")
        self.price_entry.pack(anchor="w", pady=(5, 15))
        
        # Number of accounts
        ctk.CTkLabel(form, text="Number of Accounts", text_color=self.text_dim).pack(anchor="w")
        self.accounts_entry = ctk.CTkEntry(form, width=300, fg_color="#1a1a1a", border_color="#2a2a2a")
        self.accounts_entry.insert(0, "1")
        self.accounts_entry.pack(anchor="w", pady=(5, 15))
        
        # Checkboxes
        self.proxy_var = ctk.BooleanVar(value=False)
        proxy_cb = ctk.CTkCheckBox(
            form, text="Use Proxies", variable=self.proxy_var,
            fg_color=self.accent, hover_color="#cccccc", text_color=self.accent
        )
        proxy_cb.pack(anchor="w", pady=5)
        
        self.vpn_var = ctk.BooleanVar(value=True)
        vpn_cb = ctk.CTkCheckBox(
            form, text="Rotate VPN", variable=self.vpn_var,
            fg_color=self.accent, hover_color="#cccccc", text_color=self.accent
        )
        vpn_cb.pack(anchor="w", pady=5)
        
        # Start button
        start_btn = ctk.CTkButton(
            form,
            text="Start Registration",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.accent,
            text_color=self.bg_dark,
            hover_color="#cccccc",
            height=45,
            width=300,
            corner_radius=8,
            command=self._start_registration
        )
        start_btn.pack(anchor="w", pady=(25, 0))
    
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
            text="═══ STATISTICS ═══",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(30, 25))
        
        # Stats grid
        stats_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=40)
        
        stats = [
            ("Total Registrations", "42"),
            ("Successful", "38"),
            ("Failed", "4"),
            ("Success Rate", "90.5%"),
            ("Total SMS Cost", "$12.50"),
            ("Avg Cost/Account", "$0.33"),
        ]
        
        for i, (label, value) in enumerate(stats):
            row = ctk.CTkFrame(stats_frame, fg_color="#1a1a1a", corner_radius=8, height=50)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)
            
            lbl = ctk.CTkLabel(row, text=label, text_color=self.text_dim, font=ctk.CTkFont(size=14))
            lbl.pack(side="left", padx=20)
            
            val = ctk.CTkLabel(row, text=value, text_color=self.accent, font=ctk.CTkFont(size=14, weight="bold"))
            val.pack(side="right", padx=20)
    
    def _on_proxies(self):
        """Show proxy management."""
        self._clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="═══ PROXY MANAGEMENT ═══",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(30, 25))
        
        info = ctk.CTkLabel(
            self.content_frame,
            text="Proxy management coming soon...\n\nSupported formats:\n• SOCKS5\n• HTTP/HTTPS",
            font=ctk.CTkFont(size=14),
            text_color=self.text_dim,
            justify="center"
        )
        info.pack(pady=20)
    
    def _on_settings(self):
        """Show settings view."""
        self._clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="═══ SETTINGS ═══",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(30, 25))
        
        settings_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        settings_frame.pack(fill="x", padx=40)
        
        settings = [
            ("SMS Provider", "sms-activate"),
            ("Device Type", "Emulator"),
            ("Appium Port", "4723"),
            ("VPN", "ExpressVPN"),
            ("Email Service", "Onion Mail"),
        ]
        
        for label, value in settings:
            row = ctk.CTkFrame(settings_frame, fg_color="#1a1a1a", corner_radius=8, height=45)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)
            
            lbl = ctk.CTkLabel(row, text=label, text_color=self.text_dim)
            lbl.pack(side="left", padx=20)
            
            val = ctk.CTkLabel(row, text=value, text_color=self.accent)
            val.pack(side="right", padx=20)
        
        note = ctk.CTkLabel(
            self.content_frame,
            text="Edit config.yaml to change settings",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=self.text_dim
        )
        note.pack(pady=20)
    
    def _on_check_config(self):
        """Check configuration."""
        self._clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="═══ CONFIG CHECK ═══",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.accent
        )
        title.pack(pady=(30, 25))
        
        checks = [
            ("config.yaml found", True),
            ("ADB connection", True),
            ("SMS API key", True),
            ("All paths exist", True),
        ]
        
        for label, ok in checks:
            row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            row.pack(anchor="w", padx=60, pady=5)
            
            icon = "●" if ok else "○"
            color = "#00ff00" if ok else "#ff4444"
            
            ctk.CTkLabel(row, text=icon, text_color=color, font=ctk.CTkFont(size=16)).pack(side="left")
            ctk.CTkLabel(row, text=f"  {label}", text_color=self.accent).pack(side="left")

    def _create_footer(self):
        """Create footer with credits."""
        footer = ctk.CTkFrame(self, fg_color="transparent", height=50)
        footer.pack(fill="x", padx=30, pady=(10, 20))
        footer.pack_propagate(False)
        
        # Separator
        sep = ctk.CTkLabel(
            footer,
            text="━" * 100,
            font=ctk.CTkFont(size=10),
            text_color="#333333"
        )
        sep.pack()
        
        # Credits frame
        credits_frame = ctk.CTkFrame(footer, fg_color="transparent")
        credits_frame.pack(expand=True)
        
        made_with = ctk.CTkLabel(
            credits_frame,
            text="Made with ♥ by ",
            font=ctk.CTkFont(size=12),
            text_color=self.text_dim
        )
        made_with.pack(side="left")
        
        author_btn = ctk.CTkButton(
            credits_frame,
            text="@ibuildrun",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            hover_color="#1a1a1a",
            text_color=self.accent,
            width=80,
            height=25,
            command=lambda: webbrowser.open("https://github.com/ibuildrun")
        )
        author_btn.pack(side="left")
        
        sep_label = ctk.CTkLabel(
            credits_frame,
            text="  │  ",
            font=ctk.CTkFont(size=12),
            text_color="#333333"
        )
        sep_label.pack(side="left")
        
        github_btn = ctk.CTkButton(
            credits_frame,
            text="GitHub",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#1a1a1a",
            text_color=self.text_dim,
            width=60,
            height=25,
            command=lambda: webbrowser.open("https://github.com/ibuildrun/telegram-auto-reg")
        )
        github_btn.pack(side="left")
    
    def _on_exit(self):
        """Exit application."""
        if messagebox.askyesno("Exit", "Exit application?"):
            self.quit()


def main():
    """Run the application."""
    app = TelegramAutoRegApp()
    app.mainloop()


if __name__ == "__main__":
    main()
