"""
Database initialization script
"""

from backend.app import create_app
from backend.database import db
from backend.models.BlockedEdges import BlockedEdges
import os
import osmnx as ox
from datetime import datetime
from sqlalchemy import text

app = create_app()

def init_database():
    """Initialize the database with tables and sample data"""
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

# Initialize blocked edges table to begin
def initialize_blocked_edges(batch_size=500):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    GRAPH_PATH = os.path.join(BASE_DIR, 'data', 'nyc_graphml.graphml')
    nyc_graph = ox.load_graphml(GRAPH_PATH)

    with app.app_context():
        sql = text('''
            SELECT * FROM nyc_street_data
            WHERE "Status" <> :status
            AND "Latitude" IS NOT NULL
            AND "Latitude" <> ''
            AND "Longitude" IS NOT NULL
            AND "Longitude" <> ''
        ''')
        result = db.session.execute(sql, {'status': 'Closed'}).mappings()

        # Pre-fetch existing edges as a set for fast lookup
        existing_edges = {(e.u, e.v, e.k) for e in BlockedEdges.query.with_entities(BlockedEdges.u, BlockedEdges.v, BlockedEdges.k).all()}

        edges_to_add = []

        for i, row in enumerate(result, start=1):
            try:
                lat, lon = float(row['Latitude']), float(row['Longitude'])
                u, v, k = ox.distance.nearest_edges(nyc_graph, X=lon, Y=lat)

                # Skip if already exists
                if (u, v, k) in existing_edges:
                    continue

                # Parse Created Date
                created_date = row['Created Date']
                reported_at = datetime.strptime(created_date, "%m/%d/%Y %I:%M:%S %p")

                edges_to_add.append(BlockedEdges(u=u, v=v, k=k, reported_at=reported_at))
                existing_edges.add((u, v, k))  # avoid duplicates in same batch

                # Commit in batches for large datasets
                if len(edges_to_add) >= batch_size:
                    db.session.bulk_save_objects(edges_to_add)
                    db.session.commit()
                    print(f"Processed {i} rows, inserted {len(edges_to_add)} edges...")
                    edges_to_add.clear()
                print(f"Blocked Edge {i} created")

            except Exception as e:
                print(f"Skipping row {i} due to error: {e}")
                continue

        # Insert remaining edges
        if edges_to_add:
            db.session.bulk_save_objects(edges_to_add)
            db.session.commit()
            print(f"Inserted final {len(edges_to_add)} edges")

        print("Blocked edges initialization complete.")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        reset_database()
    else:
        init_database()
    # initialize_blocked_edges(50)