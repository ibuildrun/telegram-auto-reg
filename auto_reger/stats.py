"""Statistics management for Telegram Auto-Regger.

Loads and aggregates registration statistics from session files and cech.json.
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
SESSIONS_DIR = PROJECT_ROOT / "sessions" / "converted"
CECH_PATH = PROJECT_ROOT / "cech.json"
ACTIVATIONS_PATH = PROJECT_ROOT / "activations.json"


def load_json_safe(path: Path) -> Dict[str, Any]:
    """Load JSON file safely, return empty dict on error."""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f) or {}
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def get_all_sessions() -> List[Dict[str, Any]]:
    """Load all session metadata from sessions/converted directory."""
    sessions = []
    
    if not SESSIONS_DIR.exists():
        return sessions
    
    # Iterate through date folders
    for date_folder in SESSIONS_DIR.iterdir():
        if date_folder.is_dir():
            for session_file in date_folder.glob("*.json"):
                data = load_json_safe(session_file)
                if data:
                    # Add date from folder name if not in data
                    if "date" not in data:
                        data["date"] = date_folder.name
                    sessions.append(data)
    
    return sessions


def get_stats_summary() -> Dict[str, Any]:
    """Get aggregated statistics summary."""
    sessions = get_all_sessions()
    cech = load_json_safe(CECH_PATH)
    
    total = len(sessions)
    
    # Count by status (assume all saved sessions are successful)
    success = total
    failed = 0
    
    # Calculate total cost
    total_cost = sum(
        float(s.get("number_price", 0) or 0) 
        for s in sessions
    )
    
    # Today's stats
    today = datetime.now().strftime("%Y-%m-%d")
    today_sessions = [s for s in sessions if s.get("date") == today]
    today_count = len(today_sessions)
    today_cost = sum(
        float(s.get("number_price", 0) or 0) 
        for s in today_sessions
    )
    
    # Success rate
    success_rate = (success / total * 100) if total > 0 else 0
    avg_cost = (total_cost / total) if total > 0 else 0
    
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": round(success_rate, 1),
        "total_cost": round(total_cost, 2),
        "avg_cost": round(avg_cost, 2),
        "today_count": today_count,
        "today_cost": round(today_cost, 2),
        "last_registration": cech.get("phone_number", "-"),
    }


def get_stats_by_country() -> List[Dict[str, Any]]:
    """Get statistics grouped by country."""
    sessions = get_all_sessions()
    
    # Group by country (extract from phone number prefix)
    country_stats = defaultdict(lambda: {"total": 0, "cost": 0.0})
    
    country_prefixes = {
        "+1": "USA",
        "+44": "UK", 
        "+7": "Russia",
        "+49": "Germany",
        "+33": "France",
        "+31": "Netherlands",
        "+48": "Poland",
        "+380": "Ukraine",
    }
    
    for session in sessions:
        phone = session.get("phone_number", "")
        cost = float(session.get("number_price", 0) or 0)
        
        country = "Other"
        for prefix, name in country_prefixes.items():
            if phone.startswith(prefix):
                country = name
                break
        
        country_stats[country]["total"] += 1
        country_stats[country]["cost"] += cost
    
    # Convert to list and calculate rates
    result = []
    for country, stats in sorted(country_stats.items(), key=lambda x: -x[1]["total"]):
        total = stats["total"]
        cost = stats["cost"]
        result.append({
            "country": country,
            "total": total,
            "success": total,  # All saved are successful
            "failed": 0,
            "rate": "100%",
            "avg_cost": f"${cost/total:.2f}" if total > 0 else "$0.00",
        })
    
    return result


def get_weekly_stats() -> List[Tuple[str, int]]:
    """Get registration counts for the last 7 days."""
    sessions = get_all_sessions()
    
    # Initialize last 7 days
    today = datetime.now()
    days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        days.append(day.strftime("%Y-%m-%d"))
    
    # Count sessions per day
    day_counts = defaultdict(int)
    for session in sessions:
        date = session.get("date", "")
        if date in days:
            day_counts[date] += 1
    
    # Format for display
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    result = []
    for date_str in days:
        day = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = day_names[day.weekday()]
        result.append((day_name, day_counts[date_str]))
    
    return result


def get_recent_activity(limit: int = 5) -> List[Dict[str, Any]]:
    """Get most recent registration activity."""
    sessions = get_all_sessions()
    
    # Sort by registration time
    sessions_with_time = []
    for s in sessions:
        reg_time = s.get("registration_time", "")
        if reg_time:
            try:
                dt = datetime.fromisoformat(reg_time)
                sessions_with_time.append((dt, s))
            except ValueError:
                pass
    
    sessions_with_time.sort(key=lambda x: x[0], reverse=True)
    
    result = []
    for dt, session in sessions_with_time[:limit]:
        # Calculate time ago
        delta = datetime.now() - dt
        if delta.days > 0:
            time_ago = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds >= 60:
            mins = delta.seconds // 60
            time_ago = f"{mins} min ago"
        else:
            time_ago = "just now"
        
        result.append({
            "phone": session.get("phone_number", "Unknown"),
            "status": "Registered",
            "time_ago": time_ago,
            "success": True,
        })
    
    return result


def get_sms_balance() -> Optional[float]:
    """Get SMS provider balance (placeholder - needs API integration)."""
    # TODO: Integrate with SMS API to get real balance
    return None
