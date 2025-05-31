const fs = require('fs');
const { google } = require('googleapis');

const TOKEN_PATH = 'gmail_token.json';
const CREDENTIALS_PATH = 'credentials.json';

(async () => {
  try {
    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH));
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH));
    const { client_secret, client_id, redirect_uris } = credentials.installed;
    const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);
    oAuth2Client.setCredentials(token);

    const gmail = google.gmail({ version: 'v1', auth: oAuth2Client });
    const res = await gmail.users.labels.list({ userId: 'me' });
    const labels = res.data.labels;
    if (!labels || labels.length === 0) {
      console.error('FAIL: No labels found.');
      process.exit(1);
    } else {
      console.log('PASS: Gmail API labels:', labels.map(l => l.name).join(', '));
      process.exit(0);
    }
  } catch (e) {
    console.error('FAIL: Gmail API error:', e.message || e);
    process.exit(1);
  }
})(); 