from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson import ObjectId
import datetime
import os
import socket
import time
import json
import redis

app = Flask(__name__)

# Get pod hostname
def get_pod_name():
    return os.environ.get('HOSTNAME', socket.gethostname())

# --- MongoDB connection ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongos.dev.svc.cluster.local:27017")
try:
    client = MongoClient(MONGO_URI)
    db = client["notes_app"]
    notes = db["Note"]
    app.logger.info(f"✅ Connected to MongoDB at {MONGO_URI}")
except Exception as e:
    client = None
    db = None
    notes = None
    app.logger.warning(f"⚠️ MongoDB unavailable: {e}")

# --- Redis connection ---
REDIS_HOST = os.getenv("REDIS_HOST", "redis-master.dev.svc.cluster.local")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
try:
    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    cache.ping()
    app.logger.info(f"✅ Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    cache = None
    app.logger.warning(f"⚠️ Redis unavailable: {e}")

# --- Helper for caching ---
def get_cached_or_db(key, db_func, ttl=300):
    """Try to get cached value from Redis, otherwise fetch from DB and cache it."""
    if not cache:
        return db_func()

    cached = cache.get(key)
    if cached:
        app.logger.info(f"🔁 Cache hit for {key}")
        return json.loads(cached)
    else:
        app.logger.info(f"🆕 Cache miss for {key}")
        data = db_func()
        cache.set(key, json.dumps(data, default=str), ex=ttl)
        return data

# --- Routes ---
@app.route('/')
def index():
    return render_template("index.html")


@app.route("/api/message", methods=["GET"])
def message():
    return jsonify({"message": "MongoDB cluster is live!"})

@app.route('/health')
def health_check():
    mongo_status = "connected" if client and db else "disconnected"
    redis_status = "connected" if cache else "disconnected"
    
    return jsonify({
        'status': 'healthy',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'pod': get_pod_name(),
        'services': {
            'mongodb': mongo_status,
            'redis': redis_status
        }
    })

@app.route('/api/notes', methods=['POST'])
def create_note():
    """Create a new note. Expects JSON: {"title": "...", "content": "..."}"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Store in database
        note_id = None
        if notes:
            result = notes.insert_one({
                "title": title,
                "content": content,
                "created_at": datetime.datetime.utcnow()
            })
            note_id = str(result.inserted_id)
            
            # Clear cache for all notes list
            if cache:
                cache.delete("all_notes")
        
        return jsonify({
            'note_id': note_id,
            'title': title,
            'content': content,
            'message': 'Note created successfully'
        }), 201
    
    except Exception as e:
        app.logger.error(f"Error creating note: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes', methods=['GET'])
def get_all_notes():
    """Get all notes."""
    try:
        def fetch_notes():
            if not notes:
                return []
            note_list = list(notes.find().sort("created_at", -1).limit(100))
            # Convert ObjectId to string for JSON serialization
            for note in note_list:
                note['_id'] = str(note['_id'])
                if 'created_at' in note:
                    note['created_at'] = note['created_at'].isoformat()
            return note_list
        
        notes_data = get_cached_or_db("all_notes", fetch_notes, ttl=60)
        return jsonify({
            'notes': notes_data,
            'count': len(notes_data)
        })
    
    except Exception as e:
        app.logger.error(f"Error fetching notes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID."""
    try:
        if not notes:
            return jsonify({'error': 'Database not available'}), 503
        
        # Try cache first
        cache_key = f"note:{note_id}"
        if cache:
            cached = cache.get(cache_key)
            if cached:
                return jsonify(json.loads(cached))
        
        # Fetch from database
        try:
            note_doc = notes.find_one({"_id": ObjectId(note_id)})
        except:
            return jsonify({'error': 'Invalid note ID'}), 400
        
        if not note_doc:
            return jsonify({'error': 'Note not found'}), 404
        
        # Format response
        note_data = {
            'note_id': str(note_doc['_id']),
            'title': note_doc.get('title'),
            'content': note_doc.get('content'),
            'created_at': note_doc.get('created_at').isoformat() if note_doc.get('created_at') else None
        }
        
        # Cache it
        if cache:
            cache.set(cache_key, json.dumps(note_data, default=str), ex=300)
        
        return jsonify(note_data)
    
    except Exception as e:
        app.logger.error(f"Error retrieving note: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/links')
def all_links():
    """Display all notes in a web page."""
    def fetch_notes():
        if not notes:
            return []
        note_list = list(notes.find().sort("created_at", -1).limit(100))
        # Convert ObjectId to string for template rendering
        for note in note_list:
            note['_id'] = str(note['_id'])
            if 'created_at' in note:
                note['created_at'] = note['created_at'].isoformat() if hasattr(note['created_at'], 'isoformat') else str(note['created_at'])
        return note_list
    
    notes_data = get_cached_or_db("all_notes", fetch_notes, ttl=60)
    return render_template("links.html", notes=notes_data)


@app.route("/stats/<note_id>")
def stats(note_id):
    """Display note details in a web page."""
    if not notes:
        return "Database not available", 503
    
    try:
        note_doc = notes.find_one({"_id": ObjectId(note_id)})
    except:
        return "Invalid note ID", 400
    
    if not note_doc:
        return "Note not found", 404
    
    # Format for template
    note_data = {
        '_id': str(note_doc['_id']),
        'title': note_doc.get('title'),
        'content': note_doc.get('content'),
        'created_at': note_doc.get('created_at').isoformat() if note_doc.get('created_at') and hasattr(note_doc.get('created_at'), 'isoformat') else str(note_doc.get('created_at', '')),
        'version': note_doc.get('version')
    }
    
    return render_template("stats.html", note=note_data)


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get statistics about notes (API endpoint)."""
    try:
        if not notes:
            return jsonify({
                'total_notes': 0,
                'database': 'disconnected'
            })
        
        total = notes.count_documents({})
        
        return jsonify({
            'total_notes': total,
            'database': 'connected',
            'cache': 'connected' if cache else 'disconnected',
            'pod': get_pod_name()
        })
    
    except Exception as e:
        app.logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/migration_status', methods=['GET'])
def migration_status():
    """Check migration status."""
    if not notes:
        return jsonify({'error': 'Database not available'}), 503
    
    total = notes.count_documents({})
    migrated = notes.count_documents({"version": {"$exists": True}})
    
    return jsonify({
        "total_notes": total,
        "migrated_notes": migrated,
        "pending": total - migrated
    })

@app.route('/run_migration', methods=['POST'])
def run_migration():
    """Add a 'version' field to all notes that don't have it."""
    if not notes:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        result = notes.update_many(
            {"version": {"$exists": False}},
            {"$set": {"version": "1.0"}}
        )
        
        # Clear cache
        if cache:
            cache.delete("all_notes")
        
        msg = f"✅ Migration applied: {result.modified_count} notes updated (added 'version')."
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
