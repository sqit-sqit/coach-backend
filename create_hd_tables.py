#!/usr/bin/env python
"""Create Human Design tables in database"""

from app.core.database import engine, Base
from app.modules.hd.models import HDSession, HDChatMessage, HDSummary

print("Creating Human Design tables...")

# Create tables
HDSession.__table__.create(engine, checkfirst=True)
print("✓ Created hd_sessions table")

HDChatMessage.__table__.create(engine, checkfirst=True)
print("✓ Created hd_chat_messages table")

HDSummary.__table__.create(engine, checkfirst=True)
print("✓ Created hd_summaries table")

print("\n✅ All Human Design tables created successfully!")


