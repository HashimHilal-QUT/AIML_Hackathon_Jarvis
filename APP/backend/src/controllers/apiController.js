 
const { logAuditEvent } = require('../utils/auditLogger');

const createApi = async (req, res) => {
    const client = await db.pool.connect();
    try {
        await client.query('BEGIN');

        const { api_name, location_sk, batch_sk, documents } = req.body;

        // Create API header
        const headerResult = await client.query(`
            INSERT INTO fact_api_header (
                api_id,
                api_name,
                launch_date_fk,
                launch_by_fk,
                location_fk,
                batch_sk,
                active_row
            ) VALUES ($1, $2, $3, $4, $5, $6, true)
            RETURNING api_sk
        `, [
            `API${Date.now()}`,
            api_name,
            req.body.launch_date_fk || null,
            req.user.user_sk,
            location_sk,
            batch_sk
        ]);

        const api_sk = headerResult.rows[0].api_sk;

        // Create API details for each document
        if (documents && documents.length > 0) {
            for (const doc of documents) {
                await client.query(`
                    INSERT INTO fact_api_detail (
                        api_sk,
                        document_sk,
                        blob_link,
                        active_row
                    ) VALUES ($1, $2, $3, true)
                `, [api_sk, doc.document_sk, doc.blob_link]);
            }
        }

        await logAuditEvent(client, {
            user_sk: req.user.user_sk,
            action: 'API_CREATED',
            table_name: 'fact_api_header',
            record_id: api_sk,
            new_value: { api_name, location_sk, batch_sk }
        });

        await client.query('COMMIT');
        res.status(201).json({ 
            api_sk,
            message: 'API created successfully' 
        });
    } catch (error) {
        await client.query('ROLLBACK');
        console.error('Create API error:', error);
        res.status(500).json({ error: 'Failed to create API' });
    } finally {
        client.release();
    }
};

const getApiDetails = async (req, res) => {
    try {
        const { api_sk } = req.params;

        const headerResult = await db.query(`
            SELECT h.*, 
                   l.location_name,
                   b.batch_name,
                   u.first_name || ' ' || u.last_name as launched_by
            FROM fact_api_header h
            LEFT JOIN dim_api_location l ON h.location_fk = l.location_sk
            LEFT JOIN dim_batch b ON h.batch_sk = b.batch_sk
            LEFT JOIN dim_user u ON h.launch_by_fk = u.user_sk
            WHERE h.api_sk = $1 AND h.active_row = true
        `, [api_sk]);

        if (headerResult.rows.length === 0) {
            return res.status(404).json({ error: 'API not found' });
        }

        const detailsResult = await db.query(`
            SELECT d.*, doc.document_name
            FROM fact_api_detail d
            LEFT JOIN dim_document doc ON d.document_sk = doc.document_sk
            WHERE d.api_sk = $1 AND d.active_row = true
        `, [api_sk]);

        res.json({
            header: headerResult.rows[0],
            details: detailsResult.rows
        });
    } catch (error) {
        console.error('Get API details error:', error);
        res.status(500).json({ error: 'Failed to get API details' });
    }
};

const updateApi = async (req, res) => {
    const client = await db.pool.connect();
    try {
        await client.query('BEGIN');

        const { api_sk } = req.params;
        const { api_name, location_sk, batch_sk, documents } = req.body;

        // Update API header
        await client.query(`
            UPDATE fact_api_header
            SET active_row = false
            WHERE api_sk = $1
        `, [api_sk]);

        const headerResult = await client.query(`
            INSERT INTO fact_api_header (
                api_id,
                api_name,
                launch_date_fk,
                launch_by_fk,
                location_fk,
                batch_sk,
                active_row
            )
            SELECT 
                api_id,
                $2,
                $3,
                $4,
                $5,
                $6,
                true
            FROM fact_api_header
            WHERE api_sk = $1
            RETURNING api_sk
        `, [
            api_sk,
            api_name,
            req.body.launch_date_fk || null,
            req.user.user_sk,
            location_sk,
            batch_sk
        ]);

        // Update API details
        await client.query(`
            UPDATE fact_api_detail
            SET active_row = false
            WHERE api_sk = $1
        `, [api_sk]);

        if (documents && documents.length > 0) {
            for (const doc of documents) {
                await client.query(`
                    INSERT INTO fact_api_detail (
                        api_sk,
                        document_sk,
                        blob_link,
                        active_row
                    ) VALUES ($1, $2, $3, true)
                `, [headerResult.rows[0].api_sk, doc.document_sk, doc.blob_link]);
            }
        }

        await logAuditEvent(client, {
            user_sk: req.user.user_sk,
            action: 'API_UPDATED',
            table_name: 'fact_api_header',
            record_id: api_sk,
            new_value: { api_name, location_sk, batch_sk }
        });

        await client.query('COMMIT');
        res.json({ message: 'API updated successfully' });
    } catch (error) {
        await client.query('ROLLBACK');
        console.error('Update API error:', error);
        res.status(500).json({ error: 'Failed to update API' });
    } finally {
        client.release();
    }
};

module.exports = {
    createApi,
    getApiDetails,
    updateApi
};