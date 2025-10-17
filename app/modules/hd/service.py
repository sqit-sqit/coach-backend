# app/modules/hd/service.py
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from app.modules.hd.models import HDSession, HDChatMessage, HDSummary
from app.core.database import get_db
from sqlalchemy.orm import Session
from app.modules.hd.hd_calculator import compute_hd_chart

class HumanDesignCalculator:
    """Calculator for Human Design charts using Swiss Ephemeris"""
    
    def __init__(self):
        # Używamy prawdziwych obliczeń z Swiss Ephemeris
        pass
    
    def calculate_chart(self, birth_date: datetime, birth_time: str, birth_lat: float, birth_lng: float, 
                        zodiac_system: str = "tropical", calculation_method: str = "degrees",
                        birth_place: Optional[str] = None) -> Dict:
        """Calculate Human Design chart using Swiss Ephemeris"""
        try:
            # Konwersja daty na string
            date_str = birth_date.strftime("%Y-%m-%d")
            
            # Preferuj nazwę miejsca z żądania; w przeciwnym razie spróbuj geokodowania wstecznego
            place_name = birth_place or None
            if not place_name:
                try:
                    from geopy.geocoders import Nominatim
                    geolocator = Nominatim(user_agent="hd_backend")
                    location = geolocator.reverse(f"{birth_lat}, {birth_lng}", language="pl")
                    place_name = location.address if location else f"Lat: {birth_lat}, Lng: {birth_lng}"
                except:
                    place_name = f"Lat: {birth_lat}, Lng: {birth_lng}"
            
            print(f"🔍 DEBUG: Computing HD chart with:")
            print(f"   Date: {date_str}, Time: {birth_time}")
            print(f"   Place: {place_name}")
            print(f"   Zodiac: {zodiac_system}, Method: {calculation_method}")
            
            result = compute_hd_chart(
                name="User",  # Będzie zastąpione w routerze
                date_str=date_str,
                time_str=birth_time,
                place=place_name,
                zodiac_system=zodiac_system,
                calculation_method=calculation_method
            )
            
            print(f"✅ DEBUG: HD calculation result: {result.get('summary', {})}")
            
            # Konwersja na format oczekiwany przez resztę aplikacji
            chart_data = self._convert_to_legacy_format(result)
            # Zapisz chart_data dla używania w innych metodach
            self._last_chart_data = chart_data
            return chart_data
            
        except Exception as e:
            print(f"Error calculating chart: {e}")
            # Fallback do mock data w przypadku błędu
            return self._get_mock_chart_data(zodiac_system, calculation_method)
    
    def _convert_to_legacy_format(self, hd_result: Dict) -> Dict:
        """Konwersja wyniku z prawdziwych obliczeń na format legacy"""
        summary = hd_result.get("summary", {})
        positions = hd_result.get("positions", [])
        
        # Znajdź pozycje Słońca
        sun_pers = next((p for p in positions if p["planet"] == "Sun" and p["side"] == "Personality"), None)
        sun_des = next((p for p in positions if p["planet"] == "Sun" and p["side"] == "Design"), None)
        
        # Znajdź pozycje Ziemi
        earth_pers = next((p for p in positions if p["planet"] == "Earth" and p["side"] == "Personality"), None)
        earth_des = next((p for p in positions if p["planet"] == "Earth" and p["side"] == "Design"), None)
        
        # Znajdź pozycje Księżyca
        moon_pers = next((p for p in positions if p["planet"] == "Moon" and p["side"] == "Personality"), None)
        moon_des = next((p for p in positions if p["planet"] == "Moon" and p["side"] == "Design"), None)
        
        # Znajdź węzły księżycowe
        north_node = next((p for p in positions if p["planet"] == "North Node"), None)
        south_node = next((p for p in positions if p["planet"] == "South Node"), None)
        
        converted = {
            "sun": {"gate": sun_pers["gate"] if sun_pers else 1, "line": sun_pers["line"] if sun_pers else 1},
            "earth": {"gate": earth_pers["gate"] if earth_pers else 2, "line": earth_pers["line"] if earth_pers else 1},
            "moon": {"gate": moon_pers["gate"] if moon_pers else 3, "line": moon_pers["line"] if moon_pers else 1},
            "north_node": {"gate": north_node["gate"] if north_node else 4, "line": north_node["line"] if north_node else 1},
            "south_node": {"gate": south_node["gate"] if south_node else 5, "line": south_node["line"] if south_node else 1},
            "centers": {
                "defined": summary.get("defined_centers", []),
                "undefined": []  # Będzie obliczone w determine_type
            },
            "channels": {
                "defined": summary.get("channels", [])
            },
            "calculation_info": {
                "zodiac_system": hd_result.get("input", {}).get("zodiac_mode", "Tropical"),
                "calculation_method": hd_result.get("input", {}).get("design_mode", "-88° (łuk Słońca)"),
                "description": f"Calculated using {hd_result.get('input', {}).get('zodiac_mode', 'Tropical')} zodiac and {hd_result.get('input', {}).get('design_mode', '-88° (łuk Słońca)')}"
            },
            "hd_summary": summary,
            "active_gates": summary.get("active_gates", []),
            "activations": hd_result.get("positions", [])
        }
        return converted
    
    def _get_mock_chart_data(self, zodiac_system: str = "tropical", calculation_method: str = "degrees") -> Dict:
        """Mock chart data for testing with different calculation systems"""
        # Simulate different results based on calculation system
        base_gate = 1
        if zodiac_system == "tropical":
            base_gate = 2  # Different gate for tropical
        if calculation_method == "days":
            base_gate += 1  # Different gate for days calculation
            
        return {
            "sun": {"gate": base_gate, "line": 1},
            "earth": {"gate": base_gate + 1, "line": 1},
            "moon": {"gate": base_gate + 2, "line": 1},
            "north_node": {"gate": base_gate + 3, "line": 1},
            "south_node": {"gate": base_gate + 4, "line": 1},
            "centers": {
                "defined": ["Root", "Sacral", "Solar Plexus"],
                "undefined": ["Head", "Ajna", "Throat", "G", "Heart", "Spleen"]
            },
            "channels": {
                "defined": ["1-8", "2-14", "3-60"]
            },
            "calculation_info": {
                "zodiac_system": zodiac_system,
                "calculation_method": calculation_method,
                "description": f"Calculated using {zodiac_system} zodiac and {calculation_method} method"
            }
        }
    
    def determine_type(self, chart_data: Dict) -> str:
        """Determine Human Design type based on chart data"""
        print(f"DEBUG: determine_type called with chart_data keys: {list(chart_data.keys())}")
        print(f"DEBUG: chart_data has hd_summary: {'hd_summary' in chart_data}")
        
        # Użyj prawdziwych obliczeń jeśli dostępne
        if "hd_summary" in chart_data:
            hd_type = chart_data["hd_summary"].get("type", "Unknown")
            print(f"DEBUG: Using hd_summary type: {hd_type}")
            return hd_type
        
        # Fallback do starej logiki
        print(f"DEBUG: Using fallback logic")
        defined_centers = chart_data.get("centers", {}).get("defined", [])
        
        if "Sacral" in defined_centers:
            if "Throat" in defined_centers:
                return "Manifesting Generator"
            else:
                return "Generator"
        elif "Throat" in defined_centers:
            return "Manifestor"
        elif "G" in defined_centers:
            return "Projector"
        else:
            return "Reflector"
    
    def get_strategy(self, type: str) -> str:
        """Get strategy for Human Design type"""
        # Użyj prawdziwych obliczeń jeśli dostępne
        if hasattr(self, '_last_chart_data') and "hd_summary" in self._last_chart_data:
            return self._last_chart_data["hd_summary"].get("strategy", "Unknown")
        
        # Fallback do mapowania
        strategies = {
            "Generator": "To Respond",
            "Manifesting Generator": "To Respond", 
            "Manifestor": "To Inform",
            "Projector": "To Wait for Invitation",
            "Reflector": "To Wait a Lunar Cycle"
        }
        return strategies.get(type, "Unknown")
    
    def get_authority(self, chart_data: Dict) -> str:
        """Determine authority based on chart data"""
        # Użyj prawdziwych obliczeń jeśli dostępne
        if "hd_summary" in chart_data:
            return chart_data["hd_summary"].get("authority", "Unknown")
        
        # Fallback do starej logiki
        defined_centers = chart_data.get("centers", {}).get("defined", [])
        
        if "Sacral" in defined_centers:
            return "Sacral"
        elif "Solar Plexus" in defined_centers:
            return "Solar Plexus"
        elif "Spleen" in defined_centers:
            return "Spleen"
        elif "Heart" in defined_centers:
            return "Heart"
        else:
            return "Lunar"
    
    def get_profile(self, chart_data: Dict) -> str:
        """Calculate profile (personality and design lines)"""
        # Użyj prawdziwych obliczeń jeśli dostępne
        if "hd_summary" in chart_data:
            return chart_data["hd_summary"].get("profile", "—")
        
        # Fallback do starej logiki
        sun_gate = chart_data.get("sun", {}).get("gate", 1)
        earth_gate = chart_data.get("earth", {}).get("gate", 2)
        
        personality_line = (sun_gate % 6) + 1
        design_line = (earth_gate % 6) + 1
        
        return f"{personality_line}/{design_line}"

def save_hd_session_to_db(user_id: str, session_data: Dict) -> HDSession:
    """Save Human Design session to database"""
    db = next(get_db())
    try:
        session = HDSession(
            session_id=session_data["session_id"],
            user_id=user_id,
            name=session_data["name"],
            birth_date=session_data["birth_date"],
            birth_time=session_data["birth_time"],
            birth_place=session_data["birth_place"],
            birth_lat=session_data["birth_lat"],
            birth_lng=session_data["birth_lng"],
            zodiac_system=session_data.get("zodiac_system", "sidereal"),
            calculation_method=session_data.get("calculation_method", "degrees"),
            type=session_data["type"],
            strategy=session_data["strategy"],
            authority=session_data["authority"],
            profile=session_data["profile"],
            sun_gate=session_data["sun_gate"],
            earth_gate=session_data["earth_gate"],
            moon_gate=session_data["moon_gate"],
            north_node_gate=session_data["north_node_gate"],
            south_node_gate=session_data["south_node_gate"],
            defined_centers=session_data["defined_centers"],
            undefined_centers=session_data["undefined_centers"],
            defined_channels=session_data["defined_channels"],
            active_gates=session_data.get("active_gates", []),
            activations=session_data.get("activations", [])
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    finally:
        db.close()

def get_hd_session(session_id: str) -> Optional[HDSession]:
    """Get Human Design session by ID"""
    db = next(get_db())
    try:
        return db.query(HDSession).filter(HDSession.session_id == session_id).first()
    finally:
        db.close()
