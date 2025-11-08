"""
Database initialization script
"""

from app import create_app
from database import db
import os

def init_database():
    """Initialize the database with tables and sample data"""
    app = create_app('production')
    
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables
        db.create_all()
        
        print("Database tables created successfully!")
        
        # Create upload directory
        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            print(f"Created upload directory: {upload_dir}")
        
        # Create models directory for CV models
        models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            print(f"Created models directory: {models_dir}")
        
    
        print("\nDatabase initialization complete!")
        print("\nNext steps:")
        print("1. Update config.py with your database credentials")
        print("2. Copy .env.example to .env and configure")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Run the application: python app.py")

def reset_database():
    """Reset the database (drops all tables and recreates them)"""
    app = create_app('production')
    
    with app.app_context():
        print("WARNING: This will delete all data in the database!")
        confirm = input("Are you sure you want to reset the database? (yes/no): ").lower().strip()
        
        if confirm == 'yes':
            print("Dropping all tables...")
            db.drop_all()
            
            print("Recreating tables...")
            db.create_all()
            
            print("Database reset complete!")
        else:
            print("Database reset cancelled.")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_database()
    else:
        init_database()