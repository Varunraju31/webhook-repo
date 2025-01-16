from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Set up MongoDB connection
client = MongoClient('mongodb+srv://gritikverma331:OyufWd2vgwOJUBVA@cluster0.uws1t.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['github_events']  # Create a database called "github_events"
collection = db['events']  # Collection to store GitHub events

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
        "author": data.get('sender', {}).get('login'),
        "from_branch": data.get('pull_request', {}).get('head', {}).get('ref', ''),
        "to_branch": data.get('ref'),
        "timestamp": datetime.utcnow()  # Store the time the event was received
    }
    collection.insert_one(event_data)  # Save to MongoDB
    return jsonify({"status": "success"}), 200

# API endpoint to fetch events for the UI
@app.route('/events', methods=['GET'])
def get_events():
    # Fetch latest events (within the last 15 seconds) from MongoDB
    events = list(collection.find().sort("timestamp", -1).limit(10))
    return jsonify(events), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
