"""Modern TUI interface for Telegram Auto-Regger.

Black & white minimalist design with rich library.
"""

import os
import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich import box


# Black & white theme
console = Console(color_system="standard")


# ═══════════════════════════════════════════════════════════════════════════════
# ASCII Art Logo
# ═══════════════════════════════════════════════════════════════════════════════

LOGO = """
████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗
╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
   ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║
   ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║
   ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║
   ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝
                     █████╗ ██╗   ██╗████████╗ ██████╗                
                    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗               
                    ███████║██║   ██║   ██║   ██║   ██║               
                    ██╔══██║██║   ██║   ██║   ██║   ██║               
                    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝               
                    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝                
"""

MINI_LOGO = """
╔╦╗┌─┐┬  ┌─┐┌─┐┬─┐┌─┐┌┬┐  ╔═╗┬ ┬┌┬┐┌─┐
 ║ ├┤ │  ├┤ │ ┬├┬┘├─┤│││  ╠═╣│ │ │ │ │
 ╩ └─┘┴─┘└─┘└─┘┴└─┴ ┴┴ ┴  ╩ ╩└─┘ ┴ └─┘
"""


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_header():
    """Display application header."""
    clear_screen()
    
    header = Text(LOGO, style="bold white")
    console.print(Align.center(header))
    
    # Subtitle
    subtitle = Text("━" * 60, style="dim white")
    console.print(Align.center(subtitle))
    
    tagline = Text("Automated Telegram Account Registration Pipeline", style="italic dim")
    console.print(Align.center(tagline))
    console.print()


def show_mini_header():
    """Display compact header."""
    header = Text(MINI_LOGO, style="bold white")
    console.print(Align.center(header))
    console.print()


def show_footer():
    """Display footer with credits."""
    console.print()
    console.print("━" * 70, style="dim white")
    
    footer_text = Text()
    footer_text.append("Made with ", style="dim")
    footer_text.append("♥", style="white")
    footer_text.append(" by ", style="dim")
    footer_text.append("@ibuildrun", style="bold white")
    footer_text.append(" │ ", style="dim")
    footer_text.append("github.com/ibuildrun/telegram-auto-reg", style="dim italic")
    
    console.print(Align.center(footer_text))
    console.print()


def show_main_menu() -> str:
    """Display main menu and get user choice."""
    show_header()
    
    menu_panel = Panel(
        Align.center(Text.from_markup("""
[bold white]┌─────────────────────────────────────┐[/]
[bold white]│[/]                                     [bold white]│[/]
[bold white]│[/]  [white][1][/] ► Start Registration           [bold white]│[/]
[bold white]│[/]  [white][2][/] ► View Statistics              [bold white]│[/]
[bold white]│[/]  [white][3][/] ► Manage Proxies               [bold white]│[/]
[bold white]│[/]  [white][4][/] ► Settings                     [bold white]│[/]
[bold white]│[/]  [white][5][/] ► Check Configuration          [bold white]│[/]
[bold white]│[/]                                     [bold white]│[/]
[bold white]│[/]  [dim][0][/] ► Exit                          [bold white]│[/]
[bold white]│[/]                                     [bold white]│[/]
[bold white]└─────────────────────────────────────┘[/]
""")),
        title="[bold white]═══ MAIN MENU ═══[/]",
        border_style="white",
        box=box.DOUBLE,
        padding=(1, 2),
    )
    
    console.print(menu_panel)
    show_footer()
    
    choice = Prompt.ask(
        "[bold white]Select option[/]",
        choices=["0", "1", "2", "3", "4", "5"],
        default="1"
    )
    
    return choice


def show_registration_form() -> dict:
    """Display registration form and collect parameters."""
    clear_screen()
    show_mini_header()
    
    form_panel = Panel(
        "[bold white]Configure registration parameters[/]",
        title="[bold white]═══ NEW REGISTRATION ═══[/]",
        border_style="white",
        box=box.DOUBLE,
    )
    console.print(form_panel)
    console.print()
    
    # Country selection
    countries_table = Table(
        show_header=False,
        box=box.SIMPLE,
        border_style="dim white",
        padding=(0, 2),
    )
    countries_table.add_column("Code", style="bold white", width=6)
    countries_table.add_column("Country", style="white")
    countries_table.add_row("USA", "United States")
    countries_table.add_row("UK", "United Kingdom")
    countries_table.add_row("RU", "Russia")
    countries_table.add_row("DE", "Germany")
    countries_table.add_row("FR", "France")
    
    console.print("[dim]Available countries:[/]")
    console.print(countries_table)
    console.print()
    
    country = Prompt.ask(
        "[bold white]► Country[/]",
        default="USA"
    )
    
    max_price = FloatPrompt.ask(
        "[bold white]► Max SMS price ($)[/]",
        default=0.50
    )
    
    num_accounts = IntPrompt.ask(
        "[bold white]► Number of accounts[/]",
        default=1
    )
    
    use_proxy = Confirm.ask(
        "[bold white]► Use proxies?[/]",
        default=False
    )
    
    use_vpn = Confirm.ask(
        "[bold white]► Rotate VPN?[/]",
        default=True
    )
    
    console.print()
    
    # Confirmation
    summary_table = Table(
        title="[bold white]Registration Summary[/]",
        box=box.ROUNDED,
        border_style="white",
        show_header=False,
    )
    summary_table.add_column("Parameter", style="dim")
    summary_table.add_column("Value", style="bold white")
    summary_table.add_row("Country", country)
    summary_table.add_row("Max Price", f"${max_price:.2f}")
    summary_table.add_row("Accounts", str(num_accounts))
    summary_table.add_row("Proxies", "Yes" if use_proxy else "No")
    summary_table.add_row("VPN Rotation", "Yes" if use_vpn else "No")
    
    console.print(summary_table)
    console.print()
    
    if not Confirm.ask("[bold white]Start registration?[/]", default=True):
        return None
    
    return {
        "country": country,
        "max_price": max_price,
        "num_accounts": num_accounts,
        "use_proxy": use_proxy,
        "use_vpn": use_vpn,
    }


def show_progress(total: int):
    """Create and return progress display for registration."""
    progress = Progress(
        SpinnerColumn(style="white"),
        TextColumn("[bold white]{task.description}[/]"),
        BarColumn(bar_width=40, style="white", complete_style="bold white"),
        TaskProgressColumn(),
        console=console,
    )
    return progress


def show_registration_status(
    account_num: int,
    total: int,
    phone: str,
    step: str,
    status: str = "in_progress"
):
    """Display current registration status."""
    status_icons = {
        "in_progress": "◐",
        "success": "●",
        "error": "○",
        "waiting": "◌",
    }
    
    icon = status_icons.get(status, "◐")
    
    status_panel = Panel(
        f"""
[bold white]Account {account_num}/{total}[/]

[white]Phone:[/] [bold]{phone or "Acquiring..."}[/]
[white]Step:[/]  {step}
[white]Status:[/] {icon} {status.upper()}
""",
        title=f"[bold white]═══ REGISTRATION IN PROGRESS ═══[/]",
        border_style="white",
        box=box.DOUBLE,
    )
    
    return status_panel


def show_statistics(stats: dict):
    """Display statistics dashboard."""
    clear_screen()
    show_mini_header()
    
    # Main stats
    stats_table = Table(
        title="[bold white]═══ REGISTRATION STATISTICS ═══[/]",
        box=box.DOUBLE,
        border_style="white",
    )
    stats_table.add_column("Metric", style="white")
    stats_table.add_column("Value", style="bold white", justify="right")
    
    stats_table.add_row("Total Registrations", str(stats.get("total", 0)))
    stats_table.add_row("Successful", str(stats.get("success", 0)))
    stats_table.add_row("Failed", str(stats.get("failed", 0)))
    stats_table.add_row("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
    stats_table.add_row("─" * 20, "─" * 10)
    stats_table.add_row("Total SMS Cost", f"${stats.get('total_cost', 0):.2f}")
    stats_table.add_row("Avg Cost/Account", f"${stats.get('avg_cost', 0):.2f}")
    
    console.print(stats_table)
    console.print()
    
    # Recent registrations
    if stats.get("recent"):
        recent_table = Table(
            title="[bold white]Recent Registrations[/]",
            box=box.ROUNDED,
            border_style="dim white",
        )
        recent_table.add_column("Phone", style="white")
        recent_table.add_column("Status", style="white")
        recent_table.add_column("Cost", style="white", justify="right")
        recent_table.add_column("Date", style="dim")
        
        for reg in stats.get("recent", [])[:10]:
            status_icon = "●" if reg.get("success") else "○"
            recent_table.add_row(
                reg.get("phone", "N/A"),
                f"{status_icon} {'OK' if reg.get('success') else 'FAIL'}",
                f"${reg.get('cost', 0):.2f}",
                reg.get("date", "N/A"),
            )
        
        console.print(recent_table)
    
    show_footer()
    Prompt.ask("[dim]Press Enter to continue[/]")


def show_settings():
    """Display settings menu."""
    clear_screen()
    show_mini_header()
    
    settings_panel = Panel(
        """
[bold white]Current Configuration[/]

[white]SMS Provider:[/]     sms-activate
[white]Device Type:[/]      Emulator
[white]Appium Port:[/]      4723
[white]VPN:[/]              ExpressVPN
[white]Email Service:[/]    Onion Mail

[dim]Edit config.yaml to change settings[/]
""",
        title="[bold white]═══ SETTINGS ═══[/]",
        border_style="white",
        box=box.DOUBLE,
    )
    
    console.print(settings_panel)
    show_footer()
    Prompt.ask("[dim]Press Enter to continue[/]")


def show_config_check(valid: bool, errors: list = None):
    """Display configuration check results."""
    clear_screen()
    show_mini_header()
    
    if valid:
        result = """
[bold white]● Configuration Valid[/]

[white]✓[/] config.yaml found
[white]✓[/] ADB connection OK
[white]✓[/] SMS API key valid
[white]✓[/] All paths exist
"""
    else:
        error_list = "\n".join(f"[white]○[/] {e}" for e in (errors or ["Unknown error"]))
        result = f"""
[bold white]○ Configuration Invalid[/]

{error_list}
"""
    
    check_panel = Panel(
        result,
        title="[bold white]═══ CONFIG CHECK ═══[/]",
        border_style="white",
        box=box.DOUBLE,
    )
    
    console.print(check_panel)
    show_footer()
    Prompt.ask("[dim]Press Enter to continue[/]")


def show_error(message: str):
    """Display error message."""
    error_panel = Panel(
        f"[white]{message}[/]",
        title="[bold white]═══ ERROR ═══[/]",
        border_style="white",
        box=box.HEAVY,
    )
    console.print(error_panel)


def show_success(message: str):
    """Display success message."""
    success_panel = Panel(
        f"[bold white]{message}[/]",
        title="[bold white]═══ SUCCESS ═══[/]",
        border_style="white",
        box=box.DOUBLE,
    )
    console.print(success_panel)


def confirm_exit() -> bool:
    """Confirm application exit."""
    return Confirm.ask("[bold white]Exit application?[/]", default=False)
