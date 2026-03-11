 
const db = require('../config/database');
const { logAuditEvent } = require('../utils/auditLogger');

const generateApiKey = async (req, res) => {
    const client = await db.pool.connect();

    try {
        await client.query('BEGIN');

        // Generate a secure random API key
        const apiKey = crypto.randomBytes(32).toString('hex');
        
        // Store the API key
        const result = await client.query(`
            INSERT INTO api_keys (
                user_sk,
                api_key,
                description,
                expires_at
            ) VALUES ($1, $2, $3, $4)
            RETURNING key_id
        `, [
            req.user.user_sk,
            apiKey,
            req.body.description || 'Generated via dashboard',
            req.body.expires_at || null
        ]);

        await logAuditEvent(client, {
            user_sk: req.user.user_sk,
            action: 'API_KEY_GENERATED',
            table_name: 'api_keys',
            record_id: result.rows[0].key_id
        });

        await client.query('COMMIT');

        res.json({
            key_id: result.rows[0].key_id,
            api_key: apiKey,
            message: 'API key generated successfully'
        });
    } catch (error) {
        await client.query('ROLLBACK');
        console.error('Generate API key error:', error);
        res.status(500).json({ error: 'Failed to generate API key' });
    } finally {
        client.release();
    }
};

const listApiKeys = async (req, res) => {
    try {
        const result = await db.query(`
            SELECT 
                key_id,
                api_key,
                description,
                created_at,
                expires_at,
                is_active
            FROM api_keys
            WHERE user_sk = $1
            ORDER BY created_at DESC
        `, [req.user.user_sk]);

        res.json(result.rows);
    } catch (error) {
        console.error('List API keys error:', error);
        res.status(500).json({ error: 'Failed to list API keys' });
    }
};

const revokeApiKey = async (req, res) => {
    const client = await db.pool.connect();

    try {
        await client.query('BEGIN');

        // Verify key belongs to user
        const keyResult = await client.query(`
            SELECT key_id
            FROM api_keys
            WHERE key_id = $1 AND user_sk = $2 AND is_active = true
        `, [req.params.keyId, req.user.user_sk]);

        if (keyResult.rows.length === 0) {
            return res.status(404).json({ error: 'API key not found' });
        }

        // Revoke the key
        await client.query(`
            UPDATE api_keys
            SET is_active = false
            WHERE key_id = $1
        `, [req.params.keyId]);

        await logAuditEvent(client, {
            user_sk: req.user.user_sk,
            action: 'API_KEY_REVOKED',
            table_name: 'api_keys',
            record_id: req.params.keyId
        });

        await client.query('COMMIT');
        res.json({ message: 'API key revoked successfully' });
    } catch (error) {
        await client.query('ROLLBACK');
        console.error('Revoke API key error:', error);
        res.status(500).json({ error: 'Failed to revoke API key' });
    } finally {
        client.release();
    }
};

module.exports = {
    generateApiKey,
    listApiKeys,
    revokeApiKey
};