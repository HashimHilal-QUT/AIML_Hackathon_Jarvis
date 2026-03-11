const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const db = require('../config/database');
const config = require('../config/environment');

const register = async (req, res) => {
    try {
        const { email, password, firstName, lastName, userTypeId } = req.body;

        // Check if user exists
        const userExists = await db.query(
            'SELECT * FROM dim_user WHERE email = $1 AND is_current = true',
            [email]
        );

        if (userExists.rows.length > 0) {
            return res.status(400).json({ error: 'User already exists' });
        }

        // Hash password
        const salt = await bcrypt.genSalt(10);
        const passwordHash = await bcrypt.hash(password, salt);

        // Create user
        const result = await db.query(
            `INSERT INTO dim_user (
                user_id,
                user_login_id,
                email,
                password_hash,
                first_name,
                last_name,
                user_type_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING user_sk`,
            [
                `USER${Date.now()}`,
                email,
                email,
                passwordHash,
                firstName,
                lastName,
                userTypeId
            ]
        );

        res.status(201).json({ message: 'User created successfully' });
    } catch (error) {
        console.error('Register error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
};

const login = async (req, res) => {
    try {
        const { email, password } = req.body;

        // Get user
        const result = await db.query(
            'SELECT * FROM dim_user WHERE email = $1 AND is_current = true',
            [email]
        );

        if (result.rows.length === 0) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        const user = result.rows[0];

        // Check password
        const validPassword = await bcrypt.compare(password, user.password_hash);
        if (!validPassword) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        // Generate tokens
        const accessToken = jwt.sign(
            { user_sk: user.user_sk },
            config.JWT_SECRET,
            { expiresIn: config.JWT_EXPIRE }
        );

        const refreshToken = jwt.sign(
            { user_sk: user.user_sk },
            config.JWT_SECRET,
            { expiresIn: config.REFRESH_TOKEN_EXPIRE }
        );

        // Create session
        await db.query(
            `INSERT INTO user_sessions (
                user_sk,
                access_token,
                refresh_token,
                expires_at,
                ip_address,
                user_agent
            ) VALUES ($1, $2, $3, $4, $5, $6)`,
            [
                user.user_sk,
                accessToken,
                refreshToken,
                new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
                req.ip,
                req.headers['user-agent']
            ]
        );

        res.json({
            accessToken,
            refreshToken,
            user: {
                email: user.email,
                firstName: user.first_name,
                lastName: user.last_name
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
};

module.exports = {
    register,
    login
};