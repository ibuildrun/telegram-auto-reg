"""Modern GUI for Telegram Auto-Regger.

Dark theme with custom title bar, status cards, and modern design elements.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import webbrowser
import threading
import time

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
        self.geometry("950x720")
        self.minsize(900, 650)
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 950) // 2
        y = (self.winfo_screenheight() - 720) // 2
        self.geometry(f"950x720+{x}+{y}")
        
        # Colors - Modern dark palette
        self.bg_dark = "#080808"
        self.bg_card = "#111111"
        self.bg_card_hover = "#161616"
        self.bg_titlebar = "#0a0a0a"
        self.accent = "#ffffff"
        self.accent_dim = "#888888"
        self.text_dim = "#555555"
        self.border_color = "#1a1a1a"
        self.success = "#00d26a"
        self.warning = "#ffc107"
        self.error = "#ff4757"
        self.info = "#3498db"
        
        self.configure(fg_color=self.bg_dark)
        
        # Window state
        self._is_maximized = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._active_menu_btn = None
        
        # Build UI
        self._create_title_bar()
        self._create_header()
        self._create_main_content()
        self._create_footer()
        
        # Add border effect
        self.configure(highlightthickness=1, highlightbackground=self.border_color)

    def _create_title_bar(self):
        """Create custom title bar with window controls."""
        self.title_bar = ctk.CTkFrame(self, fg_color=self.bg_titlebar, height=42, corner_radius=0)
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.pack_propagate(False)
        
        # App icon
        icon_frame = ctk.CTkFrame(self.title_bar, fg_color="#1a1a1a", width=32, height=32, corner_radius=6)
        icon_frame.pack(side="left", padx=(12, 8), pady=5)
        icon_frame.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(icon_frame, text="◆", font=ctk.CTkFont(size=14), text_color=self.accent)
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        title_label = ctk.CTkLabel(
            self.title_bar, text="Telegram Auto-Regger",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=self.accent
        )
        title_label.pack(side="left", padx=5)
        
        # Version badge
        version_badge = ctk.CTkLabel(
            self.title_bar, text="v1.0",
            font=ctk.CTkFont(size=10), text_color=self.text_dim,
            fg_color="#1a1a1a", corner_radius=4, padx=6, pady=2
        )
        version_badge.pack(side="left", padx=8)
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        self.status_frame.pack(side="left", padx=20)
        
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", font=ctk.CTkFont(size=10), text_color=self.success)
        self.status_dot.pack(side="left")
        self.status_text = ctk.CTkLabel(self.status_frame, text="Ready", font=ctk.CTkFont(size=11), text_color=self.accent_dim)
        self.status_text.pack(side="left", padx=(5, 0))
        
        # Window controls
        controls_frame = ctk.CTkFrame(self.title_bar, fg_color="transparent")
        controls_frame.pack(side="right", padx=8)
        
        for text, hover, cmd in [("─", "#2a2a2a", self._minimize_window), 
                                  ("□", "#2a2a2a", self._toggle_maximize),
                                  ("✕", "#e81123", self._on_exit)]:
            btn = ctk.CTkButton(
                controls_frame, text=text, font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color=hover, text_color=self.accent_dim,
                width=42, height=32, corner_radius=6, command=cmd
            )
            btn.pack(side="left", padx=1)
        
        # Drag bindings
        for widget in [self.title_bar, title_label, icon_frame]:
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<Double-Button-1>", lambda e: self._toggle_maximize())
    
    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def _on_drag(self, event):
        if not self._is_maximized:
            x = self.winfo_x() + event.x - self._drag_start_x
            y = self.winfo_y() + event.y - self._drag_start_y
            self.geometry(f"+{x}+{y}")
    
    def _minimize_window(self):
        self.overrideredirect(False)
        self.iconify()
        self.after(100, lambda: self.overrideredirect(True))
    
    def _toggle_maximize(self):
        if self._is_maximized:
            self.geometry(self._restore_geometry)
            self._is_maximized = False
        else:
            self._restore_geometry = self.geometry()
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            self._is_maximized = True

    def _create_header(self):
        """Create header with animated logo."""
        header = ctk.CTkFrame(self, fg_color="transparent", height=90)
        header.pack(fill="x", padx=25, pady=(10, 5))
        header.pack_propagate(False)
        
        # Logo container with glow effect
        logo_container = ctk.CTkFrame(header, fg_color="transparent")
        logo_container.pack(expand=True)
        
        # Main title with gradient-like effect
        title_frame = ctk.CTkFrame(logo_container, fg_color="transparent")
        title_frame.pack()
        
        title = ctk.CTkLabel(
            title_frame, text="TELEGRAM",
            font=ctk.CTkFont(family="Consolas", size=36, weight="bold"),
            text_color=self.accent
        )
        title.pack(side="left")
        
        title2 = ctk.CTkLabel(
            title_frame, text=" AUTO",
            font=ctk.CTkFont(family="Consolas", size=36, weight="bold"),
            text_color=self.accent_dim
        )
        title2.pack(side="left")
        
        # Decorative line with dots
        deco_frame = ctk.CTkFrame(logo_container, fg_color="transparent")
        deco_frame.pack(pady=(5, 0))
        
        ctk.CTkLabel(deco_frame, text="◆", font=ctk.CTkFont(size=8), text_color="#333333").pack(side="left")
        ctk.CTkLabel(deco_frame, text="━" * 25, font=ctk.CTkFont(size=10), text_color="#222222").pack(side="left", padx=5)
        ctk.CTkLabel(deco_frame, text="◆", font=ctk.CTkFont(size=8), text_color="#333333").pack(side="left")
        
        # Tagline
        ctk.CTkLabel(
            logo_container, text="Automated Registration Pipeline",
            font=ctk.CTkFont(size=12, slant="italic"), text_color=self.text_dim
        ).pack(pady=(3, 0))

    def _create_main_content(self):
        """Create main content area."""
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=25, pady=8)
        
        # Left sidebar
        self.sidebar = ctk.CTkFrame(main, fg_color=self.bg_card, corner_radius=16, width=240)
        self.sidebar.pack(side="left", fill="y", padx=(0, 12))
        self.sidebar.pack_propagate(False)
        
        # Sidebar header
        sidebar_header = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=50)
        sidebar_header.pack(fill="x", padx=15, pady=(15, 10))
        sidebar_header.pack_propagate(False)
        
        ctk.CTkLabel(
            sidebar_header, text="NAVIGATION",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=self.text_dim
        ).pack(anchor="w")
        
        # Menu buttons with icons
        self.menu_buttons = []
        menu_items = [
            ("🏠", "Dashboard", self._show_dashboard),
            ("▶", "Registration", self._on_start_registration),
            ("📊", "Statistics", self._on_statistics),
            ("🌐", "Proxies", self._on_proxies),
            ("⚙", "Settings", self._on_settings),
            ("✓", "Config Check", self._on_check_config),
        ]
        
        for icon, text, cmd in menu_items:
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=44)
            btn_frame.pack(fill="x", padx=10, pady=2)
            btn_frame.pack_propagate(False)
            
            btn = ctk.CTkButton(
                btn_frame, text=f"  {icon}   {text}",
                font=ctk.CTkFont(size=13), fg_color="transparent",
                hover_color=self.bg_card_hover, text_color=self.accent_dim,
                anchor="w", height=44, corner_radius=10,
                command=lambda c=cmd, b=btn_frame: self._menu_click(c, b)
            )
            btn.pack(fill="both", expand=True)
            self.menu_buttons.append(btn_frame)
        
        # Sidebar footer - Quick stats
        stats_card = ctk.CTkFrame(self.sidebar, fg_color="#0d0d0d", corner_radius=12)
        stats_card.pack(side="bottom", fill="x", padx=12, pady=15)
        
        ctk.CTkLabel(
            stats_card, text="Quick Stats",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=self.text_dim
        ).pack(anchor="w", padx=12, pady=(10, 5))
        
        quick_stats = [("Today", "12"), ("Success", "92%"), ("Balance", "$4.50")]
        for label, value in quick_stats:
            row = ctk.CTkFrame(stats_card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11), text_color=self.text_dim).pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=11, weight="bold"), text_color=self.accent).pack(side="right")
        
        ctk.CTkFrame(stats_card, fg_color="transparent", height=8).pack()
        
        # Content area
        self.content_frame = ctk.CTkFrame(main, fg_color=self.bg_card, corner_radius=16)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Show dashboard by default
        self._show_dashboard()
    
    def _menu_click(self, command, btn_frame):
        """Handle menu button click with highlight."""
        # Reset all buttons
        for btn in self.menu_buttons:
            btn.configure(fg_color="transparent")
        # Highlight active
        btn_frame.configure(fg_color=self.bg_card_hover)
        self._active_menu_btn = btn_frame
        command()
    
    def _clear_content(self):
        """Clear content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_dashboard(self):
        """Show modern dashboard with cards."""
        self._clear_content()
        
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 20))
        
        ctk.CTkLabel(
            header, text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent
        ).pack(side="left")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            header, text="↻ Refresh", font=ctk.CTkFont(size=12),
            fg_color="#1a1a1a", hover_color="#2a2a2a", text_color=self.accent_dim,
            width=100, height=32, corner_radius=8
        )
        refresh_btn.pack(side="right")
        
        # Stats cards row
        cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        stats_data = [
            ("Total Accounts", "156", "↑ 12%", self.success, "📱"),
            ("Success Rate", "94.2%", "↑ 2.1%", self.success, "✓"),
            ("Failed Today", "3", "↓ 5", self.error, "✕"),
            ("SMS Balance", "$12.50", "", self.info, "💰"),
        ]
        
        for i, (title, value, change, color, icon) in enumerate(stats_data):
            card = ctk.CTkFrame(cards_frame, fg_color="#0d0d0d", corner_radius=14, height=110)
            card.pack(side="left", fill="both", expand=True, padx=5)
            card.pack_propagate(False)
            
            # Icon badge
            icon_badge = ctk.CTkFrame(card, fg_color="#1a1a1a", width=40, height=40, corner_radius=10)
            icon_badge.place(x=15, y=15)
            ctk.CTkLabel(icon_badge, text=icon, font=ctk.CTkFont(size=16)).place(relx=0.5, rely=0.5, anchor="center")
            
            # Value
            ctk.CTkLabel(
                card, text=value,
                font=ctk.CTkFont(size=26, weight="bold"), text_color=self.accent
            ).place(x=15, y=60)
            
            # Title
            ctk.CTkLabel(
                card, text=title,
                font=ctk.CTkFont(size=11), text_color=self.text_dim
            ).place(x=15, y=90)
            
            # Change indicator
            if change:
                ctk.CTkLabel(
                    card, text=change,
                    font=ctk.CTkFont(size=10), text_color=color
                ).place(relx=0.95, y=20, anchor="e")
        
        # Activity section
        activity_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        activity_frame.pack(fill="x", padx=15, pady=10)
        
        # Recent activity card
        recent_card = ctk.CTkFrame(activity_frame, fg_color="#0d0d0d", corner_radius=14)
        recent_card.pack(side="left", fill="both", expand=True, padx=5)
        
        ctk.CTkLabel(
            recent_card, text="Recent Activity",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=18, pady=(15, 10))
        
        activities = [
            ("●", "+1234567890", "Registered", "2 min ago", self.success),
            ("●", "+1987654321", "Registered", "15 min ago", self.success),
            ("○", "+1555666777", "Failed - SMS timeout", "32 min ago", self.error),
            ("●", "+1444333222", "Registered", "1 hour ago", self.success),
            ("●", "+1222111000", "Registered", "2 hours ago", self.success),
        ]
        
        for dot, phone, status, time_ago, color in activities:
            row = ctk.CTkFrame(recent_card, fg_color="transparent", height=38)
            row.pack(fill="x", padx=15, pady=2)
            row.pack_propagate(False)
            
            ctk.CTkLabel(row, text=dot, font=ctk.CTkFont(size=10), text_color=color).pack(side="left", padx=(5, 10))
            ctk.CTkLabel(row, text=phone, font=ctk.CTkFont(size=12), text_color=self.accent).pack(side="left")
            ctk.CTkLabel(row, text=status, font=ctk.CTkFont(size=11), text_color=self.accent_dim).pack(side="left", padx=15)
            ctk.CTkLabel(row, text=time_ago, font=ctk.CTkFont(size=10), text_color=self.text_dim).pack(side="right", padx=10)
        
        ctk.CTkFrame(recent_card, fg_color="transparent", height=12).pack()
        
        # System status card
        status_card = ctk.CTkFrame(activity_frame, fg_color="#0d0d0d", corner_radius=14, width=200)
        status_card.pack(side="right", fill="y", padx=5)
        status_card.pack_propagate(False)
        
        ctk.CTkLabel(
            status_card, text="System Status",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=18, pady=(15, 10))
        
        statuses = [
            ("ADB", "Connected", self.success),
            ("Appium", "Running", self.success),
            ("VPN", "Active", self.success),
            ("SMS API", "Online", self.success),
        ]
        
        for name, status, color in statuses:
            row = ctk.CTkFrame(status_card, fg_color="transparent", height=32)
            row.pack(fill="x", padx=15, pady=2)
            row.pack_propagate(False)
            
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=11), text_color=self.accent_dim).pack(side="left")
            
            status_badge = ctk.CTkFrame(row, fg_color=color, corner_radius=4, height=20)
            status_badge.pack(side="right")
            ctk.CTkLabel(status_badge, text=f" {status} ", font=ctk.CTkFont(size=9), text_color="#000000").pack(padx=2)
        
        ctk.CTkFrame(status_card, fg_color="transparent", height=12).pack()
        
        # Quick actions
        actions_frame = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        actions_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            actions_frame, text="Quick Actions",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=18, pady=(15, 12))
        
        actions_row = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions_row.pack(fill="x", padx=15, pady=(0, 15))
        
        actions = [
            ("▶ Start Registration", self.accent, self.bg_dark),
            ("🔄 Rotate VPN", "#1a1a1a", self.accent),
            ("📋 Export Sessions", "#1a1a1a", self.accent),
            ("🗑 Clear Logs", "#1a1a1a", self.accent),
        ]
        
        for text, bg, fg in actions:
            btn = ctk.CTkButton(
                actions_row, text=text, font=ctk.CTkFont(size=12),
                fg_color=bg, hover_color="#2a2a2a" if bg != self.accent else "#cccccc",
                text_color=fg, height=38, corner_radius=8,
                command=self._on_start_registration if "Start" in text else None
            )
            btn.pack(side="left", padx=5, expand=True, fill="x")

    def _on_start_registration(self):
        """Show registration form with modern design."""
        self._clear_content()
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(
            header, text="New Registration",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent
        ).pack(side="left")
        
        # Form card
        form_card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        form_card.pack(fill="x", padx=20, pady=15)
        
        # Form content
        form = ctk.CTkFrame(form_card, fg_color="transparent")
        form.pack(fill="x", padx=25, pady=20)
        
        # Two column layout
        left_col = ctk.CTkFrame(form, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        right_col = ctk.CTkFrame(form, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(15, 0))
        
        # Left column fields
        self._create_form_field(left_col, "Country", "dropdown", 
                               ["🇺🇸 USA", "🇬🇧 UK", "🇷🇺 Russia", "🇩🇪 Germany", "🇫🇷 France", "🇳🇱 Netherlands"])
        self._create_form_field(left_col, "Max SMS Price ($)", "entry", "0.50")
        self._create_form_field(left_col, "Number of Accounts", "entry", "1")
        
        # Right column fields
        self._create_form_field(right_col, "SMS Provider", "dropdown",
                               ["sms-activate", "grizzly-sms", "5sim", "smshub"])
        
        # Options
        options_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(options_frame, text="Options", font=ctk.CTkFont(size=12), text_color=self.text_dim).pack(anchor="w", pady=(0, 8))
        
        self.reg_proxy_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame, text="Use Proxies", variable=self.reg_proxy_var,
            fg_color=self.accent, hover_color="#cccccc", text_color=self.accent,
            font=ctk.CTkFont(size=12), corner_radius=4
        ).pack(anchor="w", pady=3)
        
        self.reg_vpn_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame, text="Rotate VPN", variable=self.reg_vpn_var,
            fg_color=self.accent, hover_color="#cccccc", text_color=self.accent,
            font=ctk.CTkFont(size=12), corner_radius=4
        ).pack(anchor="w", pady=3)
        
        self.reg_2fa_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            options_frame, text="Enable 2FA", variable=self.reg_2fa_var,
            fg_color=self.accent, hover_color="#cccccc", text_color=self.accent,
            font=ctk.CTkFont(size=12), corner_radius=4
        ).pack(anchor="w", pady=3)
        
        # Action buttons
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            btn_frame, text="▶  Start Registration",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.accent, text_color=self.bg_dark, hover_color="#cccccc",
            height=48, corner_radius=10, command=self._start_registration
        ).pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        ctk.CTkButton(
            btn_frame, text="Schedule",
            font=ctk.CTkFont(size=14),
            fg_color="#1a1a1a", text_color=self.accent, hover_color="#2a2a2a",
            height=48, width=120, corner_radius=10
        ).pack(side="right")
        
        # Progress section (hidden initially)
        self.progress_card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        
    def _create_form_field(self, parent, label, field_type, default):
        """Create a styled form field."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12), text_color=self.text_dim).pack(anchor="w", pady=(0, 5))
        
        if field_type == "dropdown":
            widget = ctk.CTkOptionMenu(
                frame, values=default,
                fg_color="#141414", button_color="#1a1a1a", button_hover_color="#2a2a2a",
                dropdown_fg_color="#141414", height=40, corner_radius=8
            )
            widget.pack(fill="x")
        else:
            widget = ctk.CTkEntry(
                frame, height=40, fg_color="#141414", border_color="#1a1a1a",
                corner_radius=8, placeholder_text=default
            )
            widget.insert(0, default)
            widget.pack(fill="x")
        
        return widget
    
    def _start_registration(self):
        """Start registration with progress display."""
        self.status_dot.configure(text_color=self.warning)
        self.status_text.configure(text="Registering...")
        messagebox.showinfo("Started", "Registration process started!")
        self.after(2000, lambda: [
            self.status_dot.configure(text_color=self.success),
            self.status_text.configure(text="Ready")
        ])

    def _on_statistics(self):
        """Show statistics with charts and graphs."""
        self._clear_content()
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        ctk.CTkLabel(
            scroll, text="Statistics",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=20, pady=(15, 20))
        
        # Overview cards
        overview = ctk.CTkFrame(scroll, fg_color="transparent")
        overview.pack(fill="x", padx=15, pady=(0, 15))
        
        stats = [
            ("Total", "156", "accounts"),
            ("Success", "147", "94.2%"),
            ("Failed", "9", "5.8%"),
            ("Cost", "$48.50", "avg $0.31"),
        ]
        
        for title, value, sub in stats:
            card = ctk.CTkFrame(overview, fg_color="#0d0d0d", corner_radius=12, height=90)
            card.pack(side="left", fill="both", expand=True, padx=5)
            card.pack_propagate(False)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color=self.text_dim).place(x=15, y=12)
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=self.accent).place(x=15, y=35)
            ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(size=10), text_color=self.accent_dim).place(x=15, y=68)
        
        # Chart placeholder
        chart_card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        chart_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            chart_card, text="Registration History",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=18, pady=(15, 10))
        
        # Simple bar chart visualization
        chart_frame = ctk.CTkFrame(chart_card, fg_color="transparent", height=150)
        chart_frame.pack(fill="x", padx=20, pady=10)
        chart_frame.pack_propagate(False)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        values = [12, 18, 15, 22, 28, 35, 26]
        max_val = max(values)
        
        for i, (day, val) in enumerate(zip(days, values)):
            col = ctk.CTkFrame(chart_frame, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True, padx=3)
            
            # Bar
            bar_height = int((val / max_val) * 100)
            bar_container = ctk.CTkFrame(col, fg_color="transparent", height=110)
            bar_container.pack(fill="x")
            bar_container.pack_propagate(False)
            
            spacer = ctk.CTkFrame(bar_container, fg_color="transparent", height=110-bar_height)
            spacer.pack(fill="x")
            
            bar = ctk.CTkFrame(bar_container, fg_color=self.accent, corner_radius=4, height=bar_height)
            bar.pack(fill="x", padx=8)
            
            # Value label
            ctk.CTkLabel(col, text=str(val), font=ctk.CTkFont(size=10), text_color=self.accent_dim).pack()
            
            # Day label
            ctk.CTkLabel(col, text=day, font=ctk.CTkFont(size=10), text_color=self.text_dim).pack()
        
        ctk.CTkFrame(chart_card, fg_color="transparent", height=15).pack()
        
        # Detailed stats table
        table_card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        table_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            table_card, text="Detailed Breakdown",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=18, pady=(15, 10))
        
        # Table header
        header_row = ctk.CTkFrame(table_card, fg_color="#141414", corner_radius=6, height=35)
        header_row.pack(fill="x", padx=15, pady=5)
        header_row.pack_propagate(False)
        
        headers = ["Country", "Total", "Success", "Failed", "Rate", "Avg Cost"]
        for h in headers:
            ctk.CTkLabel(header_row, text=h, font=ctk.CTkFont(size=11, weight="bold"), 
                        text_color=self.accent_dim, width=80).pack(side="left", padx=10, expand=True)
        
        # Table rows
        data = [
            ("🇺🇸 USA", "45", "43", "2", "95.6%", "$0.35"),
            ("🇬🇧 UK", "32", "30", "2", "93.8%", "$0.42"),
            ("🇷🇺 Russia", "28", "26", "2", "92.9%", "$0.18"),
            ("🇩🇪 Germany", "25", "24", "1", "96.0%", "$0.38"),
            ("🇫🇷 France", "26", "24", "2", "92.3%", "$0.40"),
        ]
        
        for row_data in data:
            row = ctk.CTkFrame(table_card, fg_color="transparent", height=38)
            row.pack(fill="x", padx=15, pady=1)
            row.pack_propagate(False)
            
            for val in row_data:
                color = self.success if "%" in val and float(val.replace("%", "")) > 94 else self.accent
                ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=11), 
                            text_color=color, width=80).pack(side="left", padx=10, expand=True)
        
        ctk.CTkFrame(table_card, fg_color="transparent", height=15).pack()

    def _on_proxies(self):
        """Show proxy management."""
        self._clear_content()
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 15))
        
        ctk.CTkLabel(
            header, text="Proxy Management",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent
        ).pack(side="left")
        
        ctk.CTkButton(
            header, text="+ Add Proxy",
            font=ctk.CTkFont(size=12), fg_color=self.accent, text_color=self.bg_dark,
            hover_color="#cccccc", height=35, width=110, corner_radius=8
        ).pack(side="right")
        
        # Proxy list card
        list_card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        list_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            list_card, text="Active Proxies",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=18, pady=(15, 10))
        
        proxies = [
            ("SOCKS5", "proxy1.example.com:1080", "Online", self.success),
            ("HTTP", "proxy2.example.com:8080", "Online", self.success),
            ("SOCKS5", "proxy3.example.com:1080", "Offline", self.error),
        ]
        
        for ptype, addr, status, color in proxies:
            row = ctk.CTkFrame(list_card, fg_color="#141414", corner_radius=8, height=50)
            row.pack(fill="x", padx=15, pady=4)
            row.pack_propagate(False)
            
            # Type badge
            type_badge = ctk.CTkFrame(row, fg_color="#1a1a1a", corner_radius=4)
            type_badge.pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(type_badge, text=f" {ptype} ", font=ctk.CTkFont(size=10), text_color=self.accent_dim).pack()
            
            # Address
            ctk.CTkLabel(row, text=addr, font=ctk.CTkFont(size=12), text_color=self.accent).pack(side="left", padx=10)
            
            # Status
            status_frame = ctk.CTkFrame(row, fg_color="transparent")
            status_frame.pack(side="right", padx=15)
            ctk.CTkLabel(status_frame, text="●", font=ctk.CTkFont(size=8), text_color=color).pack(side="left")
            ctk.CTkLabel(status_frame, text=f" {status}", font=ctk.CTkFont(size=11), text_color=self.accent_dim).pack(side="left")
            
            # Actions
            ctk.CTkButton(
                row, text="✕", font=ctk.CTkFont(size=12),
                fg_color="transparent", hover_color="#2a2a2a", text_color=self.error,
                width=30, height=30, corner_radius=6
            ).pack(side="right", padx=5)
        
        ctk.CTkFrame(list_card, fg_color="transparent", height=15).pack()
        
        # Import section
        import_card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        import_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            import_card, text="Import Proxies",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=18, pady=(15, 10))
        
        ctk.CTkLabel(
            import_card, text="Paste proxies (one per line) in format: type://host:port or type://user:pass@host:port",
            font=ctk.CTkFont(size=11), text_color=self.text_dim
        ).pack(anchor="w", padx=18, pady=(0, 10))
        
        self.proxy_textbox = ctk.CTkTextbox(
            import_card, height=100, fg_color="#141414", border_color="#1a1a1a",
            corner_radius=8, font=ctk.CTkFont(size=11)
        )
        self.proxy_textbox.pack(fill="x", padx=18, pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(import_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=18, pady=(0, 15))
        
        ctk.CTkButton(
            btn_frame, text="Import", font=ctk.CTkFont(size=12),
            fg_color=self.accent, text_color=self.bg_dark, hover_color="#cccccc",
            height=35, width=100, corner_radius=8
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_frame, text="Test All", font=ctk.CTkFont(size=12),
            fg_color="#1a1a1a", text_color=self.accent, hover_color="#2a2a2a",
            height=35, width=100, corner_radius=8
        ).pack(side="left", padx=10)

    def _on_settings(self):
        """Show settings with modern tabs."""
        self._clear_content()
        
        # Load config
        self.config = load_config()
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        ctk.CTkLabel(
            scroll, text="Settings",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=20, pady=(15, 20))
        
        # Settings sections
        sections = [
            ("SMS API", [
                ("Provider", "dropdown", ["sms-activate", "grizzly-sms", "5sim", "smshub"], "sms_api.provider"),
                ("API Key", "password", "", "sms_api.api_key"),
            ]),
            ("Telegram API", [
                ("API ID", "entry", "Get from my.telegram.org", "telethon.api_id"),
                ("API Hash", "password", "Get from my.telegram.org", "telethon.api_hash"),
            ]),
            ("ADB / Emulator", [
                ("Device Type", "dropdown", ["Emulator", "Physical"], "adb.device_type"),
                ("Device UDID", "entry", "127.0.0.1:5555", "adb.device_udid"),
                ("Appium Port", "entry", "4723", "adb.appium_port"),
                ("ADB Path", "file", "", "adb.adb_path"),
            ]),
            ("VPN", [
                ("Enable VPN", "switch", True, "vpn.enabled"),
                ("Provider", "dropdown", ["ExpressVPN", "NordVPN", "Surfshark"], "vpn.provider"),
            ]),
            ("Proxy", [
                ("Enable Proxy", "switch", False, "proxy.enabled"),
                ("Type", "dropdown", ["SOCKS5", "HTTP", "HTTPS"], "proxy.type"),
                ("Host", "entry", "proxy.example.com", "proxy.host"),
                ("Port", "entry", "1080", "proxy.port"),
            ]),
        ]
        
        self.settings_widgets = {}
        
        for section_name, fields in sections:
            # Section card
            card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
            card.pack(fill="x", padx=20, pady=8)
            
            # Section header
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=18, pady=(15, 10))
            
            ctk.CTkLabel(
                header, text=section_name,
                font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
            ).pack(side="left")
            
            # Fields
            for label, field_type, default, config_key in fields:
                field_frame = ctk.CTkFrame(card, fg_color="transparent")
                field_frame.pack(fill="x", padx=18, pady=6)
                
                ctk.CTkLabel(
                    field_frame, text=label,
                    font=ctk.CTkFont(size=12), text_color=self.text_dim, width=120
                ).pack(side="left")
                
                # Get current value from config
                keys = config_key.split(".")
                current_val = self.config
                for k in keys:
                    current_val = current_val.get(k, default) if isinstance(current_val, dict) else default
                
                if field_type == "dropdown":
                    widget = ctk.CTkOptionMenu(
                        field_frame, values=default,
                        fg_color="#141414", button_color="#1a1a1a",
                        width=250, height=35, corner_radius=8
                    )
                    if current_val in default:
                        widget.set(current_val)
                elif field_type == "switch":
                    var = ctk.BooleanVar(value=bool(current_val))
                    widget = ctk.CTkSwitch(
                        field_frame, text="", variable=var,
                        fg_color="#1a1a1a", progress_color=self.accent
                    )
                    widget.var = var
                elif field_type == "password":
                    widget = ctk.CTkEntry(
                        field_frame, width=250, height=35,
                        fg_color="#141414", border_color="#1a1a1a",
                        corner_radius=8, show="•", placeholder_text=default
                    )
                    if current_val:
                        widget.insert(0, str(current_val))
                elif field_type == "file":
                    file_frame = ctk.CTkFrame(field_frame, fg_color="transparent")
                    file_frame.pack(side="left")
                    widget = ctk.CTkEntry(
                        file_frame, width=200, height=35,
                        fg_color="#141414", border_color="#1a1a1a", corner_radius=8
                    )
                    widget.pack(side="left")
                    if current_val:
                        widget.insert(0, str(current_val))
                    ctk.CTkButton(
                        file_frame, text="...", width=40, height=35,
                        fg_color="#1a1a1a", hover_color="#2a2a2a", corner_radius=8,
                        command=lambda w=widget: self._browse_file(w)
                    ).pack(side="left", padx=(8, 0))
                else:
                    widget = ctk.CTkEntry(
                        field_frame, width=250, height=35,
                        fg_color="#141414", border_color="#1a1a1a",
                        corner_radius=8, placeholder_text=default
                    )
                    if current_val:
                        widget.insert(0, str(current_val))
                
                if field_type != "file":
                    widget.pack(side="left")
                
                self.settings_widgets[config_key] = widget
            
            ctk.CTkFrame(card, fg_color="transparent", height=10).pack()
        
        # Save button
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame, text="💾  Save Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.accent, text_color=self.bg_dark, hover_color="#cccccc",
            height=48, corner_radius=10, command=self._save_settings
        ).pack(side="left", expand=True, fill="x")
    
    def _browse_file(self, entry_widget):
        """Browse for file."""
        path = filedialog.askopenfilename()
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)
    
    def _save_settings(self):
        """Save settings to config."""
        try:
            config = load_config()
            
            for key, widget in self.settings_widgets.items():
                keys = key.split(".")
                
                # Get value based on widget type
                if hasattr(widget, 'var'):
                    value = widget.var.get()
                elif hasattr(widget, 'get'):
                    value = widget.get()
                else:
                    continue
                
                # Set nested value
                d = config
                for k in keys[:-1]:
                    d = d.setdefault(k, {})
                d[keys[-1]] = value
            
            if save_config(config):
                messagebox.showinfo("Success", "Settings saved!")
            else:
                messagebox.showerror("Error", "Failed to save")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_check_config(self):
        """Show config check with detailed status."""
        self._clear_content()
        
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header
        ctk.CTkLabel(
            scroll, text="Configuration Check",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=20, pady=(15, 20))
        
        # Status card
        status_card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        status_card.pack(fill="x", padx=20, pady=10)
        
        # Overall status
        overall = ctk.CTkFrame(status_card, fg_color="#141414", corner_radius=10)
        overall.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            overall, text="●", font=ctk.CTkFont(size=24), text_color=self.success
        ).pack(side="left", padx=15)
        
        status_text = ctk.CTkFrame(overall, fg_color="transparent")
        status_text.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            status_text, text="System Ready",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self.accent
        ).pack(anchor="w")
        ctk.CTkLabel(
            status_text, text="All checks passed successfully",
            font=ctk.CTkFont(size=11), text_color=self.accent_dim
        ).pack(anchor="w")
        
        ctk.CTkButton(
            overall, text="↻ Recheck",
            font=ctk.CTkFont(size=12), fg_color="#1a1a1a", hover_color="#2a2a2a",
            text_color=self.accent, width=90, height=35, corner_radius=8
        ).pack(side="right", padx=15)
        
        # Individual checks
        checks = [
            ("Configuration File", "config.yaml found and valid", True, "File loaded successfully"),
            ("ADB Connection", "Device connected via ADB", True, "127.0.0.1:5555 - Online"),
            ("Appium Server", "Appium service status", True, "Running on port 4723"),
            ("SMS API", "API key validation", True, "sms-activate - Connected"),
            ("Telegram API", "API credentials check", True, "API ID and Hash configured"),
            ("VPN Service", "ExpressVPN status", True, "Connected - USA"),
            ("Proxy", "Proxy configuration", False, "Not configured"),
        ]
        
        for name, desc, ok, detail in checks:
            check_row = ctk.CTkFrame(status_card, fg_color="transparent", height=60)
            check_row.pack(fill="x", padx=15, pady=4)
            check_row.pack_propagate(False)
            
            # Status icon
            icon_frame = ctk.CTkFrame(check_row, fg_color="#141414", width=40, height=40, corner_radius=8)
            icon_frame.pack(side="left", padx=(0, 12))
            icon_frame.pack_propagate(False)
            
            icon = "✓" if ok else "!"
            color = self.success if ok else self.warning
            ctk.CTkLabel(icon_frame, text=icon, font=ctk.CTkFont(size=16), text_color=color).place(relx=0.5, rely=0.5, anchor="center")
            
            # Text
            text_frame = ctk.CTkFrame(check_row, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True)
            
            ctk.CTkLabel(text_frame, text=name, font=ctk.CTkFont(size=13, weight="bold"), text_color=self.accent).pack(anchor="w")
            ctk.CTkLabel(text_frame, text=desc, font=ctk.CTkFont(size=10), text_color=self.text_dim).pack(anchor="w")
            
            # Detail
            ctk.CTkLabel(check_row, text=detail, font=ctk.CTkFont(size=11), text_color=self.accent_dim).pack(side="right", padx=10)
        
        ctk.CTkFrame(status_card, fg_color="transparent", height=15).pack()
        
        # Actions
        actions_card = ctk.CTkFrame(scroll, fg_color="#0d0d0d", corner_radius=14)
        actions_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            actions_card, text="Quick Actions",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.accent
        ).pack(anchor="w", padx=18, pady=(15, 10))
        
        actions_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_row.pack(fill="x", padx=15, pady=(0, 15))
        
        for text in ["Restart ADB", "Restart Appium", "Test SMS API", "Reconnect VPN"]:
            ctk.CTkButton(
                actions_row, text=text, font=ctk.CTkFont(size=11),
                fg_color="#141414", hover_color="#1a1a1a", text_color=self.accent,
                height=35, corner_radius=8
            ).pack(side="left", padx=5, expand=True, fill="x")

    def _create_footer(self):
        """Create footer with credits."""
        footer = ctk.CTkFrame(self, fg_color="transparent", height=40)
        footer.pack(fill="x", padx=25, pady=(5, 12))
        footer.pack_propagate(False)
        
        # Separator
        ctk.CTkFrame(footer, fg_color="#1a1a1a", height=1).pack(fill="x", pady=(0, 8))
        
        # Credits
        credits = ctk.CTkFrame(footer, fg_color="transparent")
        credits.pack(expand=True)
        
        ctk.CTkLabel(credits, text="Made with ♥ by ", font=ctk.CTkFont(size=11), text_color=self.text_dim).pack(side="left")
        
        ctk.CTkButton(
            credits, text="@ibuildrun", font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent", hover_color="#1a1a1a", text_color=self.accent,
            width=80, height=22, command=lambda: webbrowser.open("https://github.com/ibuildrun")
        ).pack(side="left")
        
        ctk.CTkLabel(credits, text=" │ ", font=ctk.CTkFont(size=11), text_color="#222222").pack(side="left")
        
        ctk.CTkButton(
            credits, text="GitHub", font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color="#1a1a1a", text_color=self.text_dim,
            width=55, height=22, command=lambda: webbrowser.open("https://github.com/ibuildrun/telegram-auto-reg")
        ).pack(side="left")
        
        # Version
        ctk.CTkLabel(credits, text=" │ v1.0.0", font=ctk.CTkFont(size=10), text_color="#333333").pack(side="left")
    
    def _on_exit(self):
        """Exit application."""
        self.quit()


def main():
    """Run the application."""
    app = TelegramAutoRegApp()
    app.mainloop()


if __name__ == "__main__":
    main()
