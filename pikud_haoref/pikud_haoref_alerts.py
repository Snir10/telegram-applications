from datetime import datetime
import pikudhaoref
import time

client = pikudhaoref.SyncClient(update_interval=2)


# Define polling function
def poll():
    while True:
        try:
            # Fetch all alerts
            active_alerts = client.get_history()  # Check if this is the correct method
            # Get the current datetime in the desired format
            current_time = datetime.now().strftime("%d/%m/%y | %H:%M")

            if active_alerts:
                print(f"{current_time} || Currently active alerts:")
                for alert in active_alerts:
                    print(f"{current_time} || {alert}")
            else:
                print(f"{current_time} || No active alerts.")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(30)  # Wait for 5 seconds before polling again


# Start polling for active alerts
poll()
