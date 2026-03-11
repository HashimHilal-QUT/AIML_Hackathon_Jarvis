 
const config = require('../config/environment');
const db = require('../config/database');

const authenticateToken = async (req, res, next) => {
    try {
        const authHeader = req.headers['authorization'];
        const token = authHeader && authHeader.split(' ')[1];

        if (!token) {
            return res.status(401).json({ error: 'Access token required' });
        }

        const decoded = jwt.verify(token, config.JWT_SECRET);
        
        // Check if session is valid
        const session = await db.query(
            'SELECT * FROM user_sessions WHERE access_token = $1 AND is_active = true',
            [token]
        );

        if (session.rows.length === 0) {
            return res.status(401).json({ error: 'Invalid session' });
        }

        req.user = decoded;
        next();
    } catch (error) {
        return res.status(403).json({ error: 'Invalid token' });
    }
};

module.exports = { authenticateToken };