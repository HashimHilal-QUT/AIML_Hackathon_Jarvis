 
const config = require('./environment');

const pool = new Pool({
    connectionString: config.DB_CONNECTION,
    ssl: config.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

module.exports = {
    query: (text, params) => pool.query(text, params),
    pool
};
