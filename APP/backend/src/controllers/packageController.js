 
const { logAuditEvent } = require('../utils/auditLogger');

const createPackage = async (req, res) => {
    const client = await db.pool.connect();
    try {
        await client.query('BEGIN');

        const { package_name, location_sk, batch_sk, documents } = req.body;

        // Create package header
        const headerResult = await client.query(`
            INSERT INTO fact_package_header (
                package_id,
                package_name,
                launch_date_time_sk,
                launch_by_sk,
                location_sk,
                batch_sk,
                active_row
            ) VALUES ($1, $2, $3, $4, $5, $6, true)
            RETURNING package_sk
        `, [
            `PKG${Date.now()}`,
            package_name,
            req.body.launch_date_time_sk || null,
            req.user.user_sk,
            location_sk,
            batch_sk
        ]);

        const package_sk = headerResult.rows[0].package_sk;

        // Create package details for each document
        if (documents && documents.length > 0) {
            for (const doc of documents) {
                await client.query(`
                    INSERT INTO fact_package_detail (
                        package_sk,
                        document_sk,
                        blob_link,
                        active_row
                    ) VALUES ($1, $2, $3, true)
                `, [package_sk, doc.document_sk, doc.blob_link]);
            }
        }

        await logAuditEvent(client, {
            user_sk: req.user.user_sk,
            action: 'PACKAGE_CREATED',
            table_name: 'fact_package_header',
            record_id: package_sk,
            new_value: { package_name, location_sk, batch_sk }
        });

        await client.query('COMMIT');
        res.status(201).json({
            package_sk,
            message: 'Package created successfully'
        });
    } catch (error) {
        await client.query('ROLLBACK');
        console.error('Create package error:', error);
        res.status(500).json({ error: 'Failed to create package' });
    } finally {
        client.release();
    }
};

const getPackageDetails = async (req, res) => {
    try {
        const { package_sk } = req.params;

        const headerResult = await db.query(`
            SELECT h.*, 
                   l.location_name,
                   b.batch_name,
                   u.first_name || ' ' || u.last_name as launched_by
            FROM fact_package_header h
            LEFT JOIN dim_api_location l ON h.location_sk = l.location_sk
            LEFT JOIN dim_batch b ON h.batch_sk = b.batch_sk
            LEFT JOIN dim_user u ON h.launch_by_sk = u.user_sk
            WHERE h.package_sk = $1 AND h.active_row = true
        `, [package_sk]);

        if (headerResult.rows.length === 0) {
            return res.status(404).json({ error: 'Package not found' });
        }

        const detailsResult = await db.query(`
            SELECT d.*, doc.document_name
            FROM fact_package_detail d
            LEFT JOIN dim_document doc ON d.document_sk = doc.document_sk
            WHERE d.package_sk = $1 AND d.active_row = true
        `, [package_sk]);

        res.json({
            header: headerResult.rows[0],
            details: detailsResult.rows
        });
    } catch (error) {
        console.error('Get package details error:', error);
        res.status(500).json({ error: 'Failed to get package details' });
    }
};

module.exports = {
    createPackage,
    getPackageDetails
};