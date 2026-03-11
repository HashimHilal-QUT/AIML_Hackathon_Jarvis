const express = require('express');
const router = express.Router();
const { authenticateToken } = require('../middleware/auth');
const {
    createApi,
    getApiDetails,
    updateApi
} = require('../controllers/apiController');

router.post('/', authenticateToken, createApi);
router.get('/:api_sk', authenticateToken, getApiDetails);
router.put('/:api_sk', authenticateToken, updateApi);

module.exports = router;