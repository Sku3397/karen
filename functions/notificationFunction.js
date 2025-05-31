const {PubSub} = require('@google-cloud/pubsub');
exports.sendNotification = async (message, topicName) => {
  const pubSubClient = new PubSub();

  // Publishes the message as a string, e.g., 'Message {message}'
  const dataBuffer = Buffer.from(message);

  try {
    const messageId = await pubSubClient.topic(topicName).publish(dataBuffer);
    console.log(`Message ${messageId} published.`);
  } catch (error) {
    console.error(`Received error while publishing: ${error.message}`);
    process.exitCode = 1;
  }
};