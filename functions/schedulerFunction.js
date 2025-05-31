const {CloudTasksClient} = require('@google-cloud/tasks');

exports.scheduleAppointment = async (req, res) => {
  // Parse request
  const {appointmentDetails} = req.body;

  // Create a client
  let client;
  if (process.env.CLOUD_TASKS_EMULATOR_HOST) {
    client = new CloudTasksClient({
      apiEndpoint: 'localhost:9500'
    });
  } else {
    client = new CloudTasksClient();
  }

  // Build the task request
  const task = {
    appEngineHttpRequest: {
      httpMethod: 'POST',
      relativeUri: '/tasks/appointments',
      body: Buffer.from(JSON.stringify(appointmentDetails)).toString('base64'),
      headers: {
        'Content-Type': 'application/json'
      }
    }
  };

  // Send create task request
  await client.createTask({parent: 'projects/my-project/locations/my-location/queues/my-queue', task});

  res.send({message: 'Appointment scheduled successfully'});
};