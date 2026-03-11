const db = require('../config/database');
const { logAuditEvent } = require('../utils/auditLogger');

const getSubscriptionTiers = async (req, res) => {
    try {
        const result = await db.query(`
            SELECT 
                tier_id,
                tier_name,
                request_limit,
                pricing,
                description
            FROM dim_subscription_tier
            WHERE is_active = true
            ORDER BY pricing ASC
        `);

        res.json(result.rows);
    } catch (error) {
        console.error('Get subscription tiers error:', error);
        res.status(500).json({ error: 'Failed to get subscription tiers' });
    }
};

const getCurrentUsage = async (req, res) => {
    try {
        const { user_sk } = req.user;
        const currentDate = new Date();
        const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);

        const result = await db.query(`
            SELECT COUNT(*) as request_count
            FROM api_usage_log
            WHERE user_sk = $1
            AND logged_at >= $2
        `, [user_sk, firstDayOfMonth]);

        res.json({
            current_usage: parseInt(result.rows[0].request_count),
            period_start: firstDayOfMonth
        });
    } catch (error) {
        console.error('Get current usage error:', error);
        res.status(500).json({ error: 'Failed to get current usage' });
    }
};

const upgradeSubscription = async (req, res) => {
    const client = await db.pool.connect();
    try {
        await client.query('BEGIN');
        const { tier_id } = req.body;
        const { user_sk } = req.user;

        // Update user's subscription tier
        await client.query(`
            UPDATE dim_user
            SET subscription_tier_id = $1,
                record_end_date = CURRENT_TIMESTAMP
            WHERE user_sk = $2 AND is_current = true
        `, [tier_id, user_sk]);

        // Insert new user record with updated subscription
        await client.query(`
            INSERT INTO dim_user (
                user_id,
                user_login_id,
                subscription_tier_id,
                record_start_date,
                is_current
            )
            SELECT 
                user_id,
                user_login_id,
                $1,
                CURRENT_TIMESTAMP,
                true
            FROM dim_user
            WHERE user_sk = $2
        `, [tier_id, user_sk]);

        await logAuditEvent(client, {
            user_sk,
            action: 'SUBSCRIPTION_UPGRADED',
            table_name: 'dim_user',
            record_id: user_sk,
            new_value: { subscription_tier_id: tier_id }
        });

        await client.query('COMMIT');
        res.json({ message: 'Subscription upgraded successfully' });
    } catch (error) {
        await client.query('ROLLBACK');
        console.error('Upgrade subscription error:', error);
        res.status(500).json({ error: 'Failed to upgrade subscription' });
    } finally {
        client.release();
    }
};

module.exports = {
    getSubscriptionTiers,
    getCurrentUsage,
    upgradeSubscription
};