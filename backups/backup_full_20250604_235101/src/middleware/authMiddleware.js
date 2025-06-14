const jwt = require('jsonwebtoken');
const { verify } = require('../auth/googleAuth');

async function authenticate(req, res, next) {
  try {
    const token = req.headers.authorization.split(' ')[1];
    const googleUser = await verify(token);
    const user = { userID: googleUser.sub, email: googleUser.email }; // Simplified for example
    const jwtToken = jwt.sign(user, process.env.JWT_SECRET, { expiresIn: '24h' });
    req.user = jwtToken;
    next();
  } catch (error) {
    res.status(401).send('Unauthorized');
  }
}

module.exports = { authenticate };