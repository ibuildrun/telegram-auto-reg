"""Main entry point for Telegram Auto-Regger CLI.

Run with: python -m cli
"""

import sys
from . import __version__, __author__
from .ui import (
    console,
    show_main_menu,
    show_registration_form,
    show_statistics,
    show_settings,
    show_config_check,
    show_error,
    show_success,
    show_footer,
    confirm_exit,
    clear_screen,
)


def main():
    """Main application loop."""
    try:
        while True:
            choice = show_main_menu()
            
            if choice == "0":
                if confirm_exit():
                    clear_screen()
                    console.print()
                    console.print("[bold white]Thanks for using Telegram Auto-Regger![/]")
                    show_footer()
                    sys.exit(0)
                    
            elif choice == "1":
                # Start Registration
                params = show_registration_form()
                if params:
                    # TODO: Connect to actual registration logic
                    show_success(f"Registration started for {params['num_accounts']} accounts")
                    input("\nPress Enter to continue...")
                    
            elif choice == "2":
                # View Statistics
                # TODO: Load real stats from cech.json
                mock_stats = {
                    "total": 42,
                    "success": 38,
                    "failed": 4,
                    "success_rate": 90.5,
                    "total_cost": 12.50,
                    "avg_cost": 0.33,
                    "recent": [
                        {"phone": "+1234567890", "success": True, "cost": 0.30, "date": "2025-01-15"},
                        {"phone": "+1234567891", "success": True, "cost": 0.35, "date": "2025-01-15"},
                        {"phone": "+1234567892", "success": False, "cost": 0.25, "date": "2025-01-14"},
                    ]
                }
                show_statistics(mock_stats)
                
            elif choice == "3":
                # Manage Proxies
                show_error("Proxy management coming soon...")
                input("\nPress Enter to continue...")
                
            elif choice == "4":
                # Settings
                show_settings()
                
            elif choice == "5":
                # Check Configuration
                # TODO: Implement real config validation
                show_config_check(valid=True)
                
    except KeyboardInterrupt:
        clear_screen()
        console.print("\n[bold white]Interrupted by user[/]")
        show_footer()
        sys.exit(0)


if __name__ == "__main__":
    main()
