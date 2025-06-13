import os
import threading
import time
from flask import Flask, jsonify, request

# Initialize the Flask application
app = Flask(__name__)

PORT = int(os.getenv('PORT', 5000))

# Get the number of Fibonacci iterations from 'FIB_ITERATIONS', default to 500,000
# This value determines the intensity of the CPU load.
FIB_ITERATIONS = int(os.getenv('FIB_ITERATIONS', 500000))

# A global flag to control the CPU-intensive operation.
# Set to True when a CPU load is requested, False to stop.
cpu_load_active = False

# A global variable to hold the thread running the CPU-intensive task.
cpu_thread = None

# --- Helper Function for CPU-Intensive Work ---
def calculate_fibonacci(iterations):
    """
    Performs a CPU-intensive calculation: Fibonacci sequence up to 'iterations'.
    This function will occupy the CPU for a duration proportional to 'iterations'.
    """
    a, b = 0, 1
    # Loop 'iterations' times to simulate CPU work.
    for _ in range(iterations):
        if not cpu_load_active:
            # If the stop signal is received, break out of the loop early.
            print("CPU load stopped prematurely.")
            break
        a, b = b, a + b
    print(f"Finished {iterations} Fibonacci calculations.")
    return b

def start_cpu_load_thread(iterations):
    """
    Starts the CPU-intensive Fibonacci calculation in a separate thread.
    This prevents the Flask server from blocking while the calculation is running.
    """
    global cpu_load_active
    cpu_load_active = True
    print(f"Starting CPU load with {iterations} iterations...")
    calculate_fibonacci(iterations)
    cpu_load_active = False # Reset flag once calculation is done or stopped.
    print("CPU load thread completed.")


# --- Flask Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health Check Endpoint:
    Returns a simple 'OK' status. This is crucial for Kubernetes liveness and readiness probes.
    """
    print("Health check requested.")
    return jsonify({"status": "OK"}), 200

@app.route('/start_cpu_intensive', methods=['POST'])
def start_cpu_intensive():
    """
    Endpoint to start CPU-intensive operations.
    If a CPU load is already active, it will report that.
    Otherwise, it starts a new thread to perform the CPU work.
    """
    global cpu_load_active, cpu_thread

    if cpu_load_active:
        print("CPU load is already active.")
        return jsonify({"message": "CPU load already active."}), 409 # Conflict status code

    # Get optional 'iterations' from request JSON or use the environment variable default.
    data = request.get_json(silent=True)
    iterations = FIB_ITERATIONS
    if data and 'iterations' in data:
        try:
            iterations = int(data['iterations'])
            if iterations <= 0:
                return jsonify({"error": "Iterations must be a positive integer."}), 400
        except ValueError:
            return jsonify({"error": "Invalid 'iterations' value. Must be an integer."}), 400

    # Start the CPU-intensive task in a new daemon thread.
    # A daemon thread will exit automatically when the main program exits.
    cpu_thread = threading.Thread(target=start_cpu_load_thread, args=(iterations,), daemon=True)
    cpu_thread.start()
    print(f"Initiated CPU-intensive task with {iterations} iterations.")
    return jsonify({"message": f"CPU-intensive task started with {iterations} iterations."}), 202 # Accepted status code

@app.route('/stop_cpu_intensive', methods=['POST'])
def stop_cpu_intensive():
    """
    Endpoint to stop the ongoing CPU-intensive operation.
    Sets the global flag 'cpu_load_active' to False, which signals the
    CPU calculation thread to terminate early.
    """
    global cpu_load_active, cpu_thread
    if not cpu_load_active:
        print("No CPU load is currently active to stop.")
        return jsonify({"message": "No CPU load active."}), 200

    cpu_load_active = False
    # Optionally, you could try to join the thread here if you want to wait for it
    # to actually finish. For a quick response, just setting the flag is enough.
    # if cpu_thread and cpu_thread.is_alive():
    #     cpu_thread.join(timeout=5) # Wait up to 5 seconds for it to finish

    print("Signal sent to stop CPU-intensive task.")
    return jsonify({"message": "Signal sent to stop CPU-intensive task."}), 200

@app.route('/status_cpu_load', methods=['GET'])
def get_cpu_load_status():
    """
    Endpoint to check the current status of the CPU-intensive operation.
    """
    status = "active" if cpu_load_active else "inactive"
    message = "CPU load is currently active." if cpu_load_active else "No CPU load is currently active."
    print(f"CPU load status requested: {status}")
    return jsonify({
        "status": status,
        "message": message,
        "fib_iterations_configured": FIB_ITERATIONS,
        "current_thread_alive": cpu_thread is not None and cpu_thread.is_alive()
    }), 200


# --- Main execution block ---
if __name__ == '__main__':
    print(f"Starting Flask app on port {PORT}...")
    print(f"Default Fibonacci iterations per request: {FIB_ITERATIONS}")
    # Run the Flask app
    app.run(host='0.0.0.0', port=PORT)
