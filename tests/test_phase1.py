"""
Unit tests for Phase 1 modules
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from src.model_calibration import UtilityData, ModelCalibrator
from src.retrofit_optimizer import RetrofitOptimizer, UtilityRates
from src.economic_analyzer import EconomicAnalyzer, ProjectCosts, ProjectSavings
from src.uncertainty_analysis import UncertaintyAnalyzer


def test_utility_data_structure():
    """Test UtilityData structure"""
    data = UtilityData(
        monthly_kwh=[1000, 1200, 1100] * 4,  # 12 months
        peak_demand_kw=100
    )
    assert len(data.monthly_kwh) == 12
    assert data.peak_demand_kw == 100


def test_utility_data_validation():
    """Test UtilityData validation"""
    with pytest.raises(ValueError):
        UtilityData(monthly_kwh=[100, 200])  # Not 12 months


def test_retrofit_optimizer_generation():
    """Test retrofit scenario generation"""
    optimizer = RetrofitOptimizer()
    scenarios = optimizer.generate_scenarios(
        baseline_energy_kwh=100000,
        floor_area_sf=10000,
        max_measures_per_scenario=2  # Limit for testing
    )
    
    assert len(scenarios) > 0
    assert all(s.baseline_energy_kwh == 100000 for s in scenarios)
    assert all(s.energy_savings_percent > 0 for s in scenarios)


def test_retrofit_scenario_economics():
    """Test retrofit scenario economics calculation"""
    optimizer = RetrofitOptimizer()
    scenarios = optimizer.generate_scenarios(
        baseline_energy_kwh=500000,
        floor_area_sf=50000,
        max_measures_per_scenario=1
    )
    
    utility_rates = UtilityRates(electricity_rate_kwh=0.12)
    
    # Calculate economics for first scenario
    scenario = scenarios[0]
    scenario.calculate_economics(utility_rates)
    
    assert scenario.annual_savings is not None
    assert scenario.roi is not None
    assert scenario.payback_years is not None
    assert scenario.npv is not None


def test_economic_analyzer():
    """Test economic analysis"""
    analyzer = EconomicAnalyzer()
    
    costs = ProjectCosts(implementation_cost=100000)
    savings = ProjectSavings(
        annual_energy_savings_kwh=50000,
        electricity_rate_kwh=0.12
    )
    
    result = analyzer.analyze_project(costs, savings)
    
    assert result.npv is not None
    assert result.roi is not None
    assert result.payback_years is not None
    assert result.annual_savings_year1 > 0


def test_economic_viability():
    """Test economic viability assessment"""
    analyzer = EconomicAnalyzer()
    
    # Good project
    costs = ProjectCosts(implementation_cost=100000)
    savings = ProjectSavings(
        annual_energy_savings_kwh=200000,  # High savings
        electricity_rate_kwh=0.12
    )
    
    result = analyzer.analyze_project(costs, savings)
    assert result.npv > 0
    assert result.payback_years < 10
    assert result.is_economically_viable()
    
    # Bad project
    costs_bad = ProjectCosts(implementation_cost=1000000)
    savings_bad = ProjectSavings(
        annual_energy_savings_kwh=10000,  # Low savings
        electricity_rate_kwh=0.12
    )
    
    result_bad = analyzer.analyze_project(costs_bad, savings_bad)
    assert result_bad.npv < 0 or result_bad.payback_years >= 10


def test_uncertainty_analyzer():
    """Test uncertainty analysis framework"""
    analyzer = UncertaintyAnalyzer()
    
    # Test default distributions
    assert len(analyzer.default_distributions) > 0
    assert 'infiltration_rate' in analyzer.default_distributions
    
    # Test parameter sampling
    dist = analyzer.default_distributions['infiltration_rate']
    sample = dist.sample()
    assert sample > 0


def test_retrofit_optimization():
    """Test optimization filtering"""
    optimizer = RetrofitOptimizer()
    scenarios = optimizer.generate_scenarios(
        baseline_energy_kwh=500000,
        floor_area_sf=50000,
        max_measures_per_scenario=2
    )
    
    utility_rates = UtilityRates(electricity_rate_kwh=0.12)
    
    # Test budget filtering
    optimized = optimizer.optimize(
        scenarios=scenarios,
        utility_rates=utility_rates,
        budget=500000
    )
    
    assert all(s.implementation_cost <= 500000 for s in optimized)
    
    # Test payback filtering
    optimized_payback = optimizer.optimize(
        scenarios=scenarios,
        utility_rates=utility_rates,
        max_payback=10.0
    )
    
    assert all(s.payback_years is None or s.payback_years <= 10.0 for s in optimized_payback)


def test_combined_savings_calculation():
    """Test combined savings calculation"""
    optimizer = RetrofitOptimizer()
    measures = optimizer.measures_db[:2]  # Get first 2 measures
    
    # Test single measure
    single_savings = optimizer._calculate_combined_savings([measures[0]])
    assert single_savings == measures[0].energy_savings_percent
    
    # Test combined measures (should be less than sum due to compounding)
    combined_savings = optimizer._calculate_combined_savings(measures)
    assert combined_savings < sum(m.energy_savings_percent for m in measures)
    assert combined_savings > max(m.energy_savings_percent for m in measures)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])






