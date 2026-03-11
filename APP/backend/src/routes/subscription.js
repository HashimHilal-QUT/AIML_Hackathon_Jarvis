 
const router = express.Router();
const { authenticateToken } = require('../middleware/auth');
const { 
    getSubscriptionInfo, 
    upgradeSubscription 
} = require('../controllers/subscriptionController');

router.get('/info', authenticateToken, getSubscriptionInfo);
router.post('/upgrade', authenticateToken, upgradeSubscription);

module.exports = router;