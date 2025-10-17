# app/modules/hd/router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from app.core.database import get_db
from app.core.models import User, AppSession
from app.routers.auth import get_current_user_from_token
from app.modules.hd.models import HDSession, HDChatMessage, HDSummary
from app.modules.hd import service, schemas
from app.config.ai_models import get_model_config
import time
import uuid

router = APIRouter(tags=["hd"])

# ---------- INIT ----------
@router.post("/init/progress")
def update_progress(progress: schemas.HDInitProgress):
    """Save Human Design initialization progress"""
    return {
        "status": "saved",
        "user_id": progress.user_id,
        "phase": progress.phase,
        "step": progress.step
    }

@router.get("/cities/autocomplete")
def autocomplete_cities(query: str = Query(..., min_length=2)):
    """Autocomplete cities with country suggestions"""
    try:
        from geopy.geocoders import Nominatim
        
        geolocator = Nominatim(
            user_agent="hd_backend",
            timeout=10  # Increase timeout to 10 seconds
        )
        
        # Search for places with the query
        results = geolocator.geocode(
            query, 
            exactly_one=False, 
            limit=10,
            language="pl",
            addressdetails=True,
            timeout=10  # Additional timeout parameter
        )
        
        if not results:
            return {"cities": []}
        
        cities = []
        for location in results:
            address = location.raw.get("display_name", "")
            parts = address.split(", ")
            
            # Extract city and country
            city = parts[0] if len(parts) > 0 else ""
            country = parts[-1] if len(parts) > 1 else ""
            
            # Create a clean display name
            if len(parts) >= 2:
                display_name = f"{city}, {country}"
            else:
                display_name = city
            
            cities.append({
                "display_name": display_name,
                "city": city,
                "country": country,
                "lat": location.latitude,
                "lng": location.longitude,
                "full_address": address
            })
        
        # If no Polish cities found, add fallback Polish cities
        polish_cities_found = any(city["country"] == "Polska" for city in cities)
        if not polish_cities_found and len(query) >= 2:
            fallback_cities = [
                {"display_name": "Warszawa, Polska", "city": "Warszawa", "country": "Polska", "lat": 52.2297, "lng": 21.0122, "full_address": "Warszawa, Polska"},
                {"display_name": "Kraków, Polska", "city": "Kraków", "country": "Polska", "lat": 50.0647, "lng": 19.9450, "full_address": "Kraków, Polska"},
                {"display_name": "Gdańsk, Polska", "city": "Gdańsk", "country": "Polska", "lat": 54.3520, "lng": 18.6466, "full_address": "Gdańsk, Polska"},
                {"display_name": "Gdynia, Polska", "city": "Gdynia", "country": "Polska", "lat": 54.5165, "lng": 18.5403, "full_address": "Gdynia, Polska"},
                {"display_name": "Wrocław, Polska", "city": "Wrocław", "country": "Polska", "lat": 51.1079, "lng": 17.0385, "full_address": "Wrocław, Polska"},
                {"display_name": "Poznań, Polska", "city": "Poznań", "country": "Polska", "lat": 52.4064, "lng": 16.9252, "full_address": "Poznań, Polska"}
            ]
            
            # Filter fallback cities based on query
            query_lower = query.lower()
            for city in fallback_cities:
                city_name_lower = city["city"].lower()
                city_name_normalized = city_name_lower.replace('ą', 'a').replace('ć', 'c').replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')
                query_normalized = query_lower.replace('ą', 'a').replace('ć', 'c').replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')
                
                if query_normalized in city_name_normalized or city_name_normalized.startswith(query_normalized):
                    cities.insert(0, city)  # Add at the beginning
        
        return {"cities": cities}
        
    except Exception as e:
        print(f"Error in autocomplete: {e}")
        # Return some fallback cities for Poland
        fallback_cities = [
            {"display_name": "Warszawa, Polska", "city": "Warszawa", "country": "Polska", "lat": 52.2297, "lng": 21.0122, "full_address": "Warszawa, Polska"},
            {"display_name": "Kraków, Polska", "city": "Kraków", "country": "Polska", "lat": 50.0647, "lng": 19.9450, "full_address": "Kraków, Polska"},
            {"display_name": "Gdańsk, Polska", "city": "Gdańsk", "country": "Polska", "lat": 54.3520, "lng": 18.6466, "full_address": "Gdańsk, Polska"},
            {"display_name": "Gdynia, Polska", "city": "Gdynia", "country": "Polska", "lat": 54.5165, "lng": 18.5403, "full_address": "Gdynia, Polska"},
            {"display_name": "Wrocław, Polska", "city": "Wrocław", "country": "Polska", "lat": 51.1079, "lng": 17.0385, "full_address": "Wrocław, Polska"},
            {"display_name": "Poznań, Polska", "city": "Poznań", "country": "Polska", "lat": 52.4064, "lng": 16.9252, "full_address": "Poznań, Polska"},
            {"display_name": "Łódź, Polska", "city": "Łódź", "country": "Polska", "lat": 51.7592, "lng": 19.4560, "full_address": "Łódź, Polska"},
            {"display_name": "Szczecin, Polska", "city": "Szczecin", "country": "Polska", "lat": 53.4285, "lng": 14.5528, "full_address": "Szczecin, Polska"}
        ]
        
        # Filter fallback cities based on query (case insensitive, partial match)
        query_lower = query.lower()
        filtered_cities = []
        
        for city in fallback_cities:
            city_name_lower = city["city"].lower()
            # Remove Polish diacritics for better matching
            city_name_normalized = city_name_lower.replace('ą', 'a').replace('ć', 'c').replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')
            query_normalized = query_lower.replace('ą', 'a').replace('ć', 'c').replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')
            
            if query_normalized in city_name_normalized or city_name_normalized.startswith(query_normalized):
                filtered_cities.append(city)
        
        return {"cities": filtered_cities if filtered_cities else fallback_cities[:3]}

@router.get("/init/progress/{user_id}")
def read_progress(user_id: str):
    """Get Human Design initialization progress"""
    return {
        "user_id": user_id,
        "phase": "init",
        "step": 1,
        "data": None
    }

# ---------- CHART CALCULATION ----------
@router.post("/calculate")
def calculate_hd_chart(request: schemas.HDChartRequest):
    """Calculate Human Design chart"""
    try:
        print(f"🔄 HD Calculation started for {request.name}")
        print(f"📅 Birth data: {request.birth_date} {request.birth_time}")
        print(f"📍 Location: {request.birth_place} ({request.birth_lat}, {request.birth_lng})")
        print(f"🔧 Settings: {request.zodiac_system}, {request.calculation_method}")
        
        calculator = service.HumanDesignCalculator()
        
        # Calculate chart data
        chart_data = calculator.calculate_chart(
            request.birth_date,
            request.birth_time,
            request.birth_lat,
            request.birth_lng,
            request.zodiac_system,
            request.calculation_method,
            request.birth_place
        )
        
        print(f"✅ HD Calculation completed successfully")
        
        # Determine Human Design components
        type = calculator.determine_type(chart_data)
        strategy = calculator.get_strategy(type)
        authority = calculator.get_authority(chart_data)
        profile = calculator.get_profile(chart_data)
        
        # Create session ID
        session_id = f"{request.user_id}-hd-{int(time.time())}"
        
        # Prepare session data
        session_data = {
            "session_id": session_id,
            "name": request.name,
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
            "birth_place": request.birth_place,
            "birth_lat": request.birth_lat,
            "birth_lng": request.birth_lng,
            "zodiac_system": request.zodiac_system,
            "calculation_method": request.calculation_method,
            "type": type,
            "strategy": strategy,
            "authority": authority,
            "profile": profile,
            "sun_gate": chart_data.get("sun", {}).get("gate", 1),
            "earth_gate": chart_data.get("earth", {}).get("gate", 2),
            "moon_gate": chart_data.get("moon", {}).get("gate", 3),
            "north_node_gate": chart_data.get("north_node", {}).get("gate", 4),
            "south_node_gate": chart_data.get("south_node", {}).get("gate", 5),
            "defined_centers": chart_data.get("centers", {}).get("defined", []),
            "undefined_centers": chart_data.get("centers", {}).get("undefined", []),
            "defined_channels": chart_data.get("channels", {}).get("defined", []),
            "active_gates": chart_data.get("active_gates", []),
            "activations": chart_data.get("activations", [])
        }
        
        # Save to database
        session = service.save_hd_session_to_db(request.user_id, session_data)
        
        return schemas.HDChartResponse(
            session_id=session.session_id,
            type=session.type,
            strategy=session.strategy,
            authority=session.authority,
            profile=session.profile,
            sun_gate=session.sun_gate,
            earth_gate=session.earth_gate,
            moon_gate=session.moon_gate,
            north_node_gate=session.north_node_gate,
            south_node_gate=session.south_node_gate,
            defined_centers=session.defined_centers or [],
            undefined_centers=session.undefined_centers or [],
            defined_channels=session.defined_channels or [],
            active_gates=session.active_gates or [],
            activations=session.activations or []
        )
        
    except Exception as e:
        print(f"❌ HD Calculation failed: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error calculating chart: {str(e)}")

@router.get("/chart/{session_id}")
def get_hd_chart(session_id: str):
    """Get Human Design chart by session ID"""
    session = service.get_hd_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Backfill planetary activations for older sessions (pre-activations column)
    if not session.activations or len(session.activations) == 0:
        try:
            calculator = service.HumanDesignCalculator()
            chart_data = calculator.calculate_chart(
                session.birth_date,
                session.birth_time,
                session.birth_lat,
                session.birth_lng,
                session.zodiac_system,
                session.calculation_method,
                session.birth_place
            )
            session.activations = chart_data.get("activations", [])
            # also backfill active_gates if missing
            if not session.active_gates:
                session.active_gates = chart_data.get("active_gates", [])
            db = next(get_db())
            try:
                session = db.merge(session)
                db.commit()
                db.refresh(session)
            finally:
                db.close()
        except Exception as e:
            print(f"WARN: could not backfill activations: {e}")
    
    return schemas.HDSessionData(
        session_id=session.session_id,
        user_id=session.user_id,
        name=session.name,
        birth_date=session.birth_date,
        birth_time=session.birth_time,
        birth_place=session.birth_place,
        birth_lat=session.birth_lat,
        birth_lng=session.birth_lng,
        zodiac_system=session.zodiac_system,
        calculation_method=session.calculation_method,
        type=session.type,
        strategy=session.strategy,
        authority=session.authority,
        profile=session.profile,
        sun_gate=session.sun_gate,
        earth_gate=session.earth_gate,
        moon_gate=session.moon_gate,
        north_node_gate=session.north_node_gate,
        south_node_gate=session.south_node_gate,
        defined_centers=session.defined_centers or [],
        undefined_centers=session.undefined_centers or [],
        defined_channels=session.defined_channels or [],
        active_gates=session.active_gates or [],
        activations=session.activations or [],
        status=session.status,
        started_at=session.started_at.isoformat(),
        ended_at=session.ended_at.isoformat() if session.ended_at else None
    )

@router.post("/chart/{session_id}/regenerate")
def regenerate_hd_chart(session_id: str, request: schemas.HDChartRequest):
    """Regenerate Human Design chart with new calculation system"""
    try:
        # Get existing session
        existing_session = service.get_hd_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if user owns this session
        if existing_session.user_id != request.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        calculator = service.HumanDesignCalculator()
        
        # Calculate chart data with new parameters
        chart_data = calculator.calculate_chart(
            request.birth_date,
            request.birth_time,
            request.birth_lat,
            request.birth_lng,
            request.zodiac_system,
            request.calculation_method,
            request.birth_place
        )
        
        # Determine Human Design components
        type = calculator.determine_type(chart_data)
        strategy = calculator.get_strategy(type)
        authority = calculator.get_authority(chart_data)
        profile = calculator.get_profile(chart_data)
        
        print(f"DEBUG: Regenerating with new data:")
        print(f"  Birth date: {request.birth_date}")
        print(f"  Birth time: {request.birth_time}")
        print(f"  Birth place: {request.birth_place}")
        print(f"  Zodiac system: {request.zodiac_system}")
        print(f"  Calculation method: {request.calculation_method}")
        print(f"  Chart data keys: {list(chart_data.keys())}")
        print(f"  Calculated type: {type}")
        print(f"  Calculated strategy: {strategy}")
        print(f"  Calculated authority: {authority}")
        print(f"  Calculated profile: {profile}")
        print(f"  OLD session type: {existing_session.type}")
        print(f"  OLD session strategy: {existing_session.strategy}")
        
        # Update existing session with new data
        existing_session.name = request.name
        existing_session.birth_date = request.birth_date
        existing_session.birth_time = request.birth_time
        existing_session.birth_place = request.birth_place
        existing_session.birth_lat = request.birth_lat
        existing_session.birth_lng = request.birth_lng
        existing_session.zodiac_system = request.zodiac_system
        existing_session.calculation_method = request.calculation_method
        existing_session.type = type
        existing_session.strategy = strategy
        existing_session.authority = authority
        existing_session.profile = profile
        existing_session.sun_gate = chart_data.get("sun", {}).get("gate", 1)
        existing_session.earth_gate = chart_data.get("earth", {}).get("gate", 2)
        existing_session.moon_gate = chart_data.get("moon", {}).get("gate", 3)
        existing_session.north_node_gate = chart_data.get("north_node", {}).get("gate", 4)
        existing_session.south_node_gate = chart_data.get("south_node", {}).get("gate", 5)
        existing_session.defined_centers = chart_data.get("centers", {}).get("defined", [])
        existing_session.undefined_centers = chart_data.get("centers", {}).get("undefined", [])
        existing_session.defined_channels = chart_data.get("channels", {}).get("defined", [])
        existing_session.active_gates = chart_data.get("active_gates", [])
        existing_session.activations = chart_data.get("activations", [])
        
        # Save updated session
        db = next(get_db())
        try:
            # Merge the session into the new db session
            existing_session = db.merge(existing_session)
            db.commit()
            db.refresh(existing_session)
            
            return schemas.HDChartResponse(
                session_id=existing_session.session_id,
                type=existing_session.type,
                strategy=existing_session.strategy,
                authority=existing_session.authority,
                profile=existing_session.profile,
                sun_gate=existing_session.sun_gate,
                earth_gate=existing_session.earth_gate,
                moon_gate=existing_session.moon_gate,
                north_node_gate=existing_session.north_node_gate,
                south_node_gate=existing_session.south_node_gate,
                defined_centers=existing_session.defined_centers,
                undefined_centers=existing_session.undefined_centers,
                defined_channels=existing_session.defined_channels,
                active_gates=existing_session.active_gates or [],
                activations=existing_session.activations or []
            )
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error regenerating chart: {e}")
        raise HTTPException(status_code=500, detail=f"Error regenerating chart: {str(e)}")

# ---------- CHAT ----------
@router.post("/chat")
def chat_with_hd_ai(request: schemas.HDChatMessage):
    """Chat with Human Design AI coach"""
    try:
        # Get session
        session = service.get_hd_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # For now, return a simple response
        # TODO: Implement AI chat logic similar to values
        response = f"Based on your Human Design as a {session.type}, your strategy is to {session.strategy.lower()}. How can I help you understand this better?"
        
        # Save message to database
        db = next(get_db())
        try:
            # Get next message order
            last_message = db.query(HDChatMessage).filter(
                HDChatMessage.session_id == request.session_id
            ).order_by(desc(HDChatMessage.message_order)).first()
            
            next_order = (last_message.message_order + 1) if last_message else 1
            
            # Save user message
            user_message = HDChatMessage(
                session_id=request.session_id,
                role="user",
                content=request.message,
                message_order=next_order
            )
            db.add(user_message)
            
            # Save AI response
            ai_message = HDChatMessage(
                session_id=request.session_id,
                role="assistant",
                content=response,
                message_order=next_order + 1
            )
            db.add(ai_message)
            
            db.commit()
            
            return schemas.HDChatResponse(
                response=response,
                message_id=str(ai_message.id),
                has_action_chips=False
            )
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@router.get("/chat/{session_id}")
def get_chat_history(session_id: str):
    """Get chat history for HD session"""
    db = next(get_db())
    try:
        messages = db.query(HDChatMessage).filter(
            HDChatMessage.session_id == session_id
        ).order_by(HDChatMessage.message_order).all()
        
        message_list = []
        for msg in messages:
            message_list.append({
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "message_order": msg.message_order
            })
        
        return schemas.HDChatHistory(
            session_id=session_id,
            messages=message_list,
            total_messages=len(message_list)
        )
    finally:
        db.close()

# ---------- SUMMARY ----------
@router.post("/summary")
def generate_summary(request: schemas.HDSummaryRequest):
    """Generate summary for HD session"""
    try:
        # Get session
        session = service.get_hd_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate summary (simplified for now)
        summary = f"""
        Your Human Design Analysis:
        
        Type: {session.type}
        Strategy: {session.strategy}
        Authority: {session.authority}
        Profile: {session.profile}
        
        This is a comprehensive analysis of your unique energetic blueprint. 
        Your type indicates how you're designed to interact with the world, 
        while your strategy shows the correct way for you to make decisions.
        """
        
        # Save summary to database
        db = next(get_db())
        try:
            # Check if summary already exists
            existing_summary = db.query(HDSummary).filter(
                HDSummary.session_id == request.session_id
            ).first()
            
            if existing_summary:
                existing_summary.summary_content = summary
            else:
                summary_obj = HDSummary(
                    session_id=request.session_id,
                    summary_content=summary
                )
                db.add(summary_obj)
            
            # Update session status
            session.status = "completed"
            session.ended_at = datetime.now()
            
            db.commit()
            
            return schemas.HDSummaryResponse(
                summary=summary,
                generated_at=datetime.now().isoformat()
            )
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

# ---------- USER DASHBOARD ----------
@router.get("/user/{user_id}/dashboard")
def get_user_hd_dashboard(user_id: str):
    """Get HD sessions for user dashboard"""
    db = next(get_db())
    try:
        sessions = db.query(HDSession).filter(
            HDSession.user_id == user_id
        ).order_by(desc(HDSession.started_at)).all()
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session.session_id,
                "name": session.name,
                "type": session.type,
                "profile": session.profile,
                "status": session.status,
                "started_at": session.started_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None
            })
        
        return {
            "user_id": user_id,
            "sessions": session_list,
            "total_sessions": len(session_list)
        }
    finally:
        db.close()
