const fs = require('fs').promises;
const path = require('path');
const process = require('process');
const {authenticate} = require('@google-cloud/local-auth');
const {google} = require('googleapis');
const http = require('http');
const url = require('url');

// If modifying these scopes, delete token.json.
const SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
];

const TOKEN_PATH = path.join(process.cwd(), 'gmail_token.json');
const CREDENTIALS_PATH = path.join(process.cwd(), 'credentials.json');

const LOCAL_SERVER_PORT = 8080;
const REDIRECT_URI = `http://localhost:${LOCAL_SERVER_PORT}/callback`;

/**
 * Reads previously authorized credentials from the save file.
 *
 * @return {Promise<OAuth2Client|null>}
 */
async function loadSavedCredentialsIfExist() {
    try {
        const content = await fs.readFile(TOKEN_PATH);
        const credentials = JSON.parse(content);
        return google.auth.fromJSON(credentials);
    } catch (err) {
        return null;
    }
}

/**
 * Serializes credentials to a file compatible with GoogleAUth.fromJSON.
 *
 * @param {OAuth2Client} client
 * @return {Promise<void>}
 */
async function saveCredentials(client) {
    const content = await fs.readFile(CREDENTIALS_PATH);
    const keys = JSON.parse(content);
    const key = keys.installed || keys.web;
    const payload = JSON.stringify({
        type: 'authorized_user',
        client_id: key.client_id,
        client_secret: key.client_secret,
        refresh_token: client.credentials.refresh_token,
        // Store expiry_date in milliseconds as Google API client libraries often expect/provide this
        expiry_date: client.credentials.expiry_date,
        access_token: client.credentials.access_token,
        scopes: client.credentials.scopes || SCOPES, // client.credentials.scopes might be a string
    });
    await fs.writeFile(TOKEN_PATH, payload);
    console.log('Token stored to', TOKEN_PATH);
}

/**
 * Load or request or authorization to call APIs.
 */
async function authorize() {
    let client = await loadSavedCredentialsIfExist();
    if (client) {
        // Check if the token is expired or about to expire (within 1 minute)
        // The google-auth-library handles refresh automatically if refresh_token is present
        // and token is expired when making an API call. Here we can pre-emptively log.
        if (client.credentials.expiry_date && client.credentials.expiry_date < (Date.now() + 60000)) {
            console.log('Existing token is expired or nearing expiry, will attempt refresh if needed or re-authorize.');
            // A refresh will be attempted automatically by the library if possible when an API call is made.
            // Or, we can force re-authorization if we suspect issues.
            // For this script, let's force re-authorization if it seems expired to ensure a fresh token.
            // client = null; // Uncomment to force re-authorization
        }
        if (client) return client; // Return if valid or refreshable
    }

    // If no valid client, start the OAuth flow
    console.log('No valid token found or forcing re-authorization. Starting OAuth flow...');
    
    const {client_secret, client_id } = (JSON.parse(await fs.readFile(CREDENTIALS_PATH))).installed;
    const oAuth2Client = new google.auth.OAuth2(
        client_id,
        client_secret,
        REDIRECT_URI // This must match one of the authorized redirect URIs in Google Cloud Console
    );

    // Generate the url that will be used for the consent dialog.
    const authorizeUrl = oAuth2Client.generateAuthUrl({
        access_type: 'offline', // 'offline' gets a refresh token
        scope: SCOPES.join(' ')
    });

    console.log('Authorize this app by visiting this url:', authorizeUrl);

    return new Promise((resolve, reject) => {
        const server = http.createServer(async (req, res) => {
            try {
                const query = url.parse(req.url, true).query;
                if (query.error) { // An error response e.g. error=access_denied
                    res.end('Authentication failed. Please check the console.');
                    server.close();
                    reject(new Error(`Authentication failed: ${query.error}`));
                    return;
                }
                if (query.code) {
                    res.end('Authentication successful! You can close this browser tab and return to the console.');
                    server.close();
                    console.log('Authorization code received.');
                    
                    try {
                        const {tokens} = await oAuth2Client.getToken(query.code);
                        oAuth2Client.setCredentials(tokens);
                        console.log('Tokens obtained successfully.');
                        await saveCredentials(oAuth2Client);
                        resolve(oAuth2Client);
                    } catch (e) {
                        console.error('Error while trying to retrieve access token', e);
                        reject(e);
                    }
                } else {
                    res.writeHead(200, {'Content-Type': 'text/html'});
                    res.end('Waiting for Google to redirect with authorization code...');
                }
            } catch (e) {
                res.writeHead(500);
                res.end('Server error');
                server.close();
                console.error('Local server error:', e);
                reject(e);
            }
        }).listen(LOCAL_SERVER_PORT, () => {
            console.log(`Local server listening on ${REDIRECT_URI}`);
            console.log('After authorizing in the browser, you will be redirected back here.');
        });

        server.on('error', (e) => {
            if (e.code === 'EADDRINUSE') {
                console.error(`Port ${LOCAL_SERVER_PORT} is already in use. Please close the other process or choose a different port.`);
            } else {
                console.error('Local server failed to start:', e);
            }
            reject(e);
        });
    });
}

authorize().then(client => {
    console.log('Gmail OAuth authorization successful. Client is ready.');
    // You can add a test API call here if needed, e.g., list labels
    // const gmail = google.gmail({version: 'v1', auth: client});
    // gmail.users.labels.list({ userId: 'me' }, (err, res) => {
    //   if (err) return console.log('The API returned an error: ' + err);
    //   console.log('Labels:', res.data.labels);
    // });
}).catch(e => {
    console.error('Authorization failed:', e.message || e);
    process.exitCode = 1;
}); 