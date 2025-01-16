from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Connect to local MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['github_events']  # Access the "github_events" database
collection = db['events']  # Access the "events" collection

# Serve plain text on the home route
@app.route('/')
def index():
    return '''
    <h1>Recent GitHub Events</h1>
    <ul id="events"></ul>

    <script>
        function fetchEvents() {
            fetch('/events')
                .then(response => response.json())
                .then(data => {
                    const eventsList = document.getElementById('events');
                    eventsList.innerHTML = '';  // Clear old data
                    data.forEach(event => {
                        const li = document.createElement('li');
                        li.textContent = `${event.author} ${event.action} to ${event.to_branch} on ${new Date(event.timestamp)}`;
                        eventsList.appendChild(li);
                    });
                });
        }

        // Poll the events every 15 seconds
        setInterval(fetchEvents, 15000);
        fetchEvents();  // Initial fetch on page load
    </script>
    '''

# Webhook endpoint to receive GitHub actions
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Store necessary data in MongoDB
    event_data = {
        "action": request.headers.get('X-GitHub-Event'),
        "author": data.get('sender', {}).get('login', 'Unknown'),
        "from_branch": data.get('pull_request', {}).get('head', {}).get('ref', 'Unknown'),
        "to_branch": data.get('ref', 'Unknown'),
        "timestamp": datetime.utcnow()  # Store the time the event was received
    }
    collection.insert_one(event_data)  # Save to MongoDB
    return jsonify({"status": "success"}), 200

# API endpoint to fetch events for the UI
@app.route('/events', methods=['GET'])
def get_events():
# Retrieve the last 10 events from MongoDB
    events = collection.find().sort("timestamp", -1).limit(10)
    event_list = []
    for event in events:
        event_list.append({
            "action": event.get("action"),
            "author": event.get("author"),
            "from_branch": event.get("from_branch"),
            "to_branch": event.get("to_branch"),
            "timestamp": event.get("timestamp")
        })
    return jsonify(event_list)

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
