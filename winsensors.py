import winrt
from winrt.windows.devices.sensors import Accelerometer, SensorAccessStatus, KnownSensor

def getSensorData():
    from winrt.windows.devices.sensors import Accelerometer, AccelerometerReadingChangedEventArgs

    # Create an Accelerometer object
    accelerometer = Accelerometer.get_default()

    # Set up a callback function to handle sensor readings
    def on_reading_changed(sender, args):
        reading = args.reading
        print(f'Accelerometer reading: x={reading.acceleration_x:.2f}, y={reading.acceleration_y:.2f}, z={reading.acceleration_z:.2f}')

    # Register the callback function to handle sensor readings
    accelerometer.reading_changed += on_reading_changed

    # Start receiving sensor readings
    accelerometer.report_interval = accelerometer.minimum_report_interval
    accelerometer.start()

    # Wait for user input to stop receiving sensor readings
    input('Press enter to stop receiving sensor readings...')

    # Stop receiving sensor readings
    accelerometer.stop()

def listSensors():
    # Get the list of available sensors
    sensors = [s.id for s in KnownSensor.get_sensor_for_type(Accelerometer.type_id)]

    # Print the list of available sensors
    print('Available sensors:')
    for sensor in sensors:
        print(sensor)