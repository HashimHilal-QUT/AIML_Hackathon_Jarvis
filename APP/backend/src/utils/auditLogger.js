 
    user_sk,
    action,
    table_name,
    record_id,
    old_value = null,
    new_value = null,
    ip_address = null
}) => {
    await client.query(`
        INSERT INTO audit_log (
            user_sk,
            action,
            table_name,
            record_id,
            old_value,
            new_value,
            ip_address
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
    `, [
        user_sk,
        action,
        table_name,
        record_id,
        old_value ? JSON.stringify(old_value) : null,
        new_value ? JSON.stringify(new_value) : null,
        ip_address
    ]);
};

module.exports = {
    logAuditEvent
};