#!/usr/bin/env python3
"""
Simple startup script for the Plotholes backend
"""

import os
import sys
from app import create_app, db
from services import *

def main():
    """Main startup function"""
    print("🚀 Starting Plotholes Backend...")
    print("=" * 50)
    
    # Check if database is configured
    if not os.path.exists('.env'):
        print("⚠️  No .env file found!")
        print("📋 Copy .env.example to .env and configure your database")
        print("💡 For quick start, you can use SQLite by setting:")
        print("   DEV_DATABASE_URL=sqlite:///plotholes.db")
        
        # Ask if user wants to continue with default SQLite
        choice = input("\n🔄 Continue with SQLite? (y/n): ").lower().strip()
        if choice != 'y':
            sys.exit(1)
        
        # Set SQLite as default
        os.environ['DEV_DATABASE_URL'] = 'sqlite:///plotholes.db'
        print("✅ Using SQLite database: plotholes.db")
    
    # Create Flask app
    print("creating app...")
    app = create_app()

    with app.app_context():
        db.create_all()
        print("Database tables created!")
    
    print("\n🏗️  Backend Features:")
    print("  📸 Mock photo upload with AI analysis")
    print("  🗺️  Geospatial processing and heat maps")
    print("  🎯 Risk assessment algorithms")
    print("  📊 Real-time analytics and reporting")
    print("  🛣️  Safe path planning")
    print("  🔮 Predictive maintenance alerts")
    
    print(f"\n🌐 API available at: http://localhost:5000")
    print(f"📋 Health check: http://localhost:5000/api/health")
    print(f"📊 Sample endpoints:")
    print(f"  • GET  /api/infrastructure/issues")
    print(f"  • POST /api/photos/upload")
    print(f"  • GET  /api/reporting/dashboard-stats")
    
    print("\n" + "=" * 50)
    print("🎮 Ready for demo! Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    # Run the app
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Plotholes Backend...")
        print("💫 Thanks for using our geospatial AI platform!")

if __name__ == '__main__':
    main()