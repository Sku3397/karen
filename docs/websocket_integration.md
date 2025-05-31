# WebSocket Integration

## Server Setup
The WebSocket server is implemented in Python using the `websockets` library. It listens on localhost port 6789. The server echoes back any messages it receives.

## Client Integration
The client-side integration is done through JavaScript. It establishes a connection to the server and sends a message, "Hello Server!", upon connection. It also handles incoming messages and errors.

## Running the Server
To run the WebSocket server, execute the Python script `src/websocket_server.py`.

## Connecting from the Client
Open the HTML file containing the JS script `src/websocket_client.js` in a browser to establish the connection and start sending/receiving messages.