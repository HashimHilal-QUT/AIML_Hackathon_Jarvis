import pytest
import asyncio
from datetime import datetime, timedelta
from nepse_autonomous_agent import NepseAutonomousAgent
from agent_prompts import get_agent_prompt

@pytest.fixture
async def agent():
    """Create a test instance of the autonomous agent"""
    agent = NepseAutonomousAgent()
    await agent.initialize()
    return agent

@pytest.mark.asyncio
async def test_agent_initialization(agent):
    """Test agent initialization and component setup"""
    assert agent.autonomous_agent is not None
    assert agent.trading_agent is not None
    assert agent.research_agent is not None
    assert agent.market_agent is not None
    assert agent.pg_conn is not None
    assert agent.redis_conn is not None

@pytest.mark.asyncio
async def test_market_timing(agent):
    """Test market timing calculations"""
    # Test market hours
    assert agent.market_hours["open"] == "11:00"
    assert agent.market_hours["close"] == "15:00"
    assert agent.market_hours["pre_open"] == "10:45"
    assert agent.market_hours["pre_close"] == "14:45"
    
    # Test trading days
    assert agent.market_days == [0, 1, 2, 3, 4]  # Monday to Friday
    
    # Test settlement days
    assert agent.settlement_days == 3

@pytest.mark.asyncio
async def test_analyze_all_stocks(agent):
    """Test bulk stock analysis"""
    analyses = await agent.analyze_all_stocks()
    assert isinstance(analyses, list)
    
    if analyses:  # If any stocks were analyzed
        analysis = analyses[0]
        assert "market_context" in analysis
        assert "settlement_info" in analysis
        assert "historical_context" in analysis
        assert "trading_signal" in analysis

@pytest.mark.asyncio
async def test_liquidity_check(agent):
    """Test liquidity assessment"""
    # Test with sample data
    sample_data = {
        "daily_data": [
            {"volume": 1000, "last_price": 100},
            {"volume": 2000, "last_price": 100},
            {"volume": 1500, "last_price": 100}
        ]
    }
    
    # Test liquidity check
    is_liquid = agent._check_liquidity(sample_data)
    assert isinstance(is_liquid, bool)

@pytest.mark.asyncio
async def test_settlement_date_calculation(agent):
    """Test settlement date calculation"""
    settlement_date = agent._calculate_settlement_date()
    assert isinstance(settlement_date, str)
    
    # Verify date format
    try:
        datetime.strptime(settlement_date, "%Y-%m-%d")
    except ValueError:
        pytest.fail("Invalid date format")

@pytest.mark.asyncio
async def test_market_analysis(agent):
    """Test market analysis components"""
    # Test market overview
    overview = await agent._get_market_overview()
    assert isinstance(overview, dict)
    assert "trend" in overview
    assert "sector_performance" in overview
    assert "volatility" in overview
    assert "sentiment" in overview

@pytest.mark.asyncio
async def test_trading_signal_generation(agent):
    """Test trading signal generation"""
    # Test with a sample stock
    signal = await agent._generate_trading_signal("NIC")
    assert isinstance(signal, dict)
    assert "entry_price" in signal
    assert "stop_loss" in signal
    assert "take_profit" in signal
    assert "confidence" in signal
    assert "reasoning" in signal

@pytest.mark.asyncio
async def test_historical_analysis(agent):
    """Test historical data analysis"""
    # Test price trend analysis
    sample_data = {
        "daily_data": [
            {"last_price": 100},
            {"last_price": 110},
            {"last_price": 105},
            {"last_price": 115}
        ]
    }
    
    trend = agent._analyze_price_trend(sample_data)
    assert isinstance(trend, dict)
    assert "trend" in trend
    assert "volatility" in trend
    assert "momentum" in trend

@pytest.mark.asyncio
async def test_risk_assessment(agent):
    """Test risk assessment functionality"""
    sample_data = {
        "daily_data": [
            {"volume": 1000, "last_price": 100},
            {"volume": 2000, "last_price": 100},
            {"volume": 1500, "last_price": 100}
        ]
    }
    
    risk = agent._assess_liquidity_risk(sample_data)
    assert isinstance(risk, dict)
    assert "risk_level" in risk
    assert "liquidity_score" in risk
    assert "volume_volatility" in risk

@pytest.mark.asyncio
async def test_market_timing_validation(agent):
    """Test market timing validation"""
    # Test market open check
    now = datetime.now()
    is_open = agent._is_market_open()
    assert isinstance(is_open, bool)
    
    # Test during market hours
    if now.weekday() in agent.market_days:
        if agent.market_hours["open"] <= now.strftime("%H:%M") <= agent.market_hours["close"]:
            assert is_open == True

@pytest.mark.asyncio
async def test_agent_prompts():
    """Test agent prompt loading"""
    # Test all prompt types
    prompt_types = ["autonomous", "trading", "research", "market"]
    for prompt_type in prompt_types:
        prompt = get_agent_prompt(prompt_type)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        
    # Test invalid prompt type
    with pytest.raises(ValueError):
        get_agent_prompt("invalid_type")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 