"""
Economic Analysis Module - Phase 1, Priority #3
Comprehensive economic analysis for energy efficiency projects.

Features:
- Lifecycle Cost Analysis (LCC)
- Return on Investment (ROI)
- Net Present Value (NPV)
- Payback Period
- Internal Rate of Return (IRR)
- Utility rate escalation modeling
- Professional report generation

Reference:
- NIST Building Life Cycle Costing
- ASHRAE Handbook - Economics
- FEMP LCC Guidelines
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class EconomicParameters:
    """Parameters for economic analysis"""
    discount_rate: float = 0.05  # Discount rate (5% default)
    inflation_rate: float = 0.02  # General inflation (2% default)
    utility_escalation_rate: float = 0.03  # Utility rate escalation (3% default)
    analysis_period_years: int = 20  # Analysis period (20 years default)
    tax_rate: float = 0.25  # Income tax rate (25% default)
    depreciation_years: Optional[int] = None  # Depreciation period


@dataclass
class ProjectCosts:
    """Project cost breakdown"""
    implementation_cost: float  # Initial investment
    annual_maintenance: float = 0.0  # Annual maintenance cost
    annual_operating: float = 0.0  # Annual operating cost
    replacement_cost: Optional[float] = None  # Replacement cost at end of lifetime
    replacement_year: Optional[int] = None  # Year of replacement


@dataclass
class ProjectSavings:
    """Energy cost savings"""
    annual_energy_savings_kwh: float
    annual_demand_savings_kw: Optional[float] = None
    annual_gas_savings_therms: Optional[float] = None
    electricity_rate_kwh: float = 0.12  # $/kWh default
    demand_rate_kw: float = 15.0  # $/kW-month default
    gas_rate_therm: float = 1.20  # $/therm default
    
    def calculate_annual_savings(self, escalation_rate: float = 0.03) -> Dict[int, float]:
        """
        Calculate annual savings over analysis period with escalation.
        
        Returns:
            Dict mapping year -> savings amount
        """
        base_electricity = self.annual_energy_savings_kwh * self.electricity_rate_kwh
        
        base_demand = 0.0
        if self.annual_demand_savings_kw:
            base_demand = self.annual_demand_savings_kw * self.demand_rate_kw * 12
        
        base_gas = 0.0
        if self.annual_gas_savings_therms:
            base_gas = self.annual_gas_savings_therms * self.gas_rate_therm
        
        base_total = base_electricity + base_demand + base_gas
        
        savings_by_year = {}
        for year in range(1, 21):  # 20-year analysis
            escalated = base_total * ((1 + escalation_rate) ** (year - 1))
            savings_by_year[year] = escalated
        
        return savings_by_year


@dataclass
class EconomicAnalysisResult:
    """Results of economic analysis"""
    npv: float  # Net Present Value
    roi: float  # Return on Investment (%)
    payback_years: float  # Simple payback period
    irr: Optional[float] = None  # Internal Rate of Return
    lcc: Optional[float] = None  # Lifecycle Cost
    annual_savings_year1: float = 0.0
    total_savings_20yr: float = 0.0
    savings_to_investment_ratio: Optional[float] = None
    
    def is_economically_viable(self) -> bool:
        """Check if project is economically viable"""
        return self.npv > 0 and self.payback_years < 10


class EconomicAnalyzer:
    """
    Perform comprehensive economic analysis for energy projects.
    """
    
    def __init__(self, params: Optional[EconomicParameters] = None):
        """Initialize with economic parameters"""
        self.params = params or EconomicParameters()
    
    def analyze_project(
        self,
        costs: ProjectCosts,
        savings: ProjectSavings
    ) -> EconomicAnalysisResult:
        """
        Perform full economic analysis.
        
        Args:
            costs: Project cost structure
            savings: Energy savings structure
        
        Returns:
            EconomicAnalysisResult with all metrics
        """
        # Calculate annual savings by year
        savings_by_year = savings.calculate_annual_savings(
            escalation_rate=self.params.utility_escalation_rate
        )
        
        # Calculate NPV
        npv = self._calculate_npv(costs, savings_by_year)
        
        # Calculate simple payback
        year1_savings = savings_by_year.get(1, 0.0)
        payback = costs.implementation_cost / year1_savings if year1_savings > 0 else float('inf')
        
        # Calculate ROI (simple, annual)
        roi = (year1_savings / costs.implementation_cost * 100.0) if costs.implementation_cost > 0 else 0.0
        
        # Calculate IRR
        irr = self._calculate_irr(costs, savings_by_year)
        
        # Calculate LCC (negative NPV from owner perspective)
        lcc = -npv
        
        # Total savings over analysis period
        total_savings = sum(savings_by_year.values())
        
        # Savings to Investment Ratio
        sir = total_savings / costs.implementation_cost if costs.implementation_cost > 0 else 0.0
        
        return EconomicAnalysisResult(
            npv=npv,
            roi=roi,
            payback_years=payback,
            irr=irr,
            lcc=lcc,
            annual_savings_year1=year1_savings,
            total_savings_20yr=total_savings,
            savings_to_investment_ratio=sir
        )
    
    def _calculate_npv(
        self,
        costs: ProjectCosts,
        savings_by_year: Dict[int, float]
    ) -> float:
        """
        Calculate Net Present Value.
        
        NPV = -Initial Cost + Σ(Savings_t / (1+r)^t) - Σ(Costs_t / (1+r)^t)
        """
        # Initial investment (negative cash flow)
        npv = -costs.implementation_cost
        
        # Discounted savings and costs over analysis period
        for year in range(1, self.params.analysis_period_years + 1):
            discount_factor = 1.0 / ((1 + self.params.discount_rate) ** year)
            
            # Savings (positive cash flow)
            savings = savings_by_year.get(year, 0.0)
            npv += savings * discount_factor
            
            # Annual maintenance/operating (negative cash flow)
            annual_costs = costs.annual_maintenance + costs.annual_operating
            npv -= annual_costs * discount_factor
            
            # Replacement cost (if applicable)
            if costs.replacement_year and year == costs.replacement_year:
                if costs.replacement_cost:
                    npv -= costs.replacement_cost * discount_factor
        
        return npv
    
    def _calculate_irr(
        self,
        costs: ProjectCosts,
        savings_by_year: Dict[int, float]
    ) -> Optional[float]:
        """
        Calculate Internal Rate of Return (IRR).
        
        IRR is the discount rate where NPV = 0.
        Uses iterative approximation.
        """
        # Try different discount rates
        for rate in [i / 100.0 for i in range(1, 101)]:  # 1% to 100%
            test_params = EconomicParameters(discount_rate=rate)
            test_analyzer = EconomicAnalyzer(params=test_params)
            npv = test_analyzer._calculate_npv(costs, savings_by_year)
            
            if abs(npv) < 100.0:  # Close enough to zero
                return rate
        
        return None
    
    def generate_report(
        self,
        result: EconomicAnalysisResult,
        project_name: str = "Energy Efficiency Project"
    ) -> str:
        """Generate professional economic analysis report"""
        report = f"""
================================================================================
ECONOMIC ANALYSIS REPORT
================================================================================

Project: {project_name}
Analysis Date: {datetime.now().strftime('%Y-%m-%d')}
Analysis Period: {self.params.analysis_period_years} years
Discount Rate: {self.params.discount_rate * 100:.1f}%
Utility Escalation Rate: {self.params.utility_escalation_rate * 100:.1f}%

================================================================================
FINANCIAL METRICS
================================================================================

Net Present Value (NPV):          ${result.npv:>12,.0f}
Return on Investment (ROI):       {result.roi:>11.1f}%
Payback Period:                   {result.payback_years:>11.1f} years
Internal Rate of Return (IRR):    {(f'{result.irr * 100:.1f}%') if result.irr else 'N/A':>11}
Lifecycle Cost (LCC):             {(f'${result.lcc:,.0f}') if result.lcc else 'N/A':>12}
Savings-to-Investment Ratio:      {result.savings_to_investment_ratio:>11.2f}

================================================================================
CASH FLOW SUMMARY
================================================================================

Year 1 Annual Savings:           ${result.annual_savings_year1:>12,.0f}
Total Savings (20-year):         ${result.total_savings_20yr:>12,.0f}

================================================================================
ECONOMIC VIABILITY ASSESSMENT
================================================================================

"""
        if result.is_economically_viable():
            report += "✓ PROJECT IS ECONOMICALLY VIABLE\n"
            report += f"  - NPV > 0: ${result.npv:,.0f}\n"
            report += f"  - Payback < 10 years: {result.payback_years:.1f} years\n"
        else:
            report += "✗ PROJECT MAY NOT BE ECONOMICALLY VIABLE\n"
            if result.npv <= 0:
                report += f"  - NPV ≤ 0: ${result.npv:,.0f}\n"
            if result.payback_years >= 10:
                report += f"  - Payback ≥ 10 years: {result.payback_years:.1f} years\n"
        
        report += "\n" + "=" * 80 + "\n"
        
        return report
    
    def compare_scenarios(
        self,
        scenarios: List[Dict],  # List of {name, costs, savings}
        rank_by: str = 'npv'
    ) -> List[Dict]:
        """
        Compare multiple project scenarios.
        
        Args:
            scenarios: List of scenario dicts with costs and savings
            rank_by: Metric to rank by ('npv', 'roi', 'payback')
        
        Returns:
            Ranked list of scenarios with analysis results
        """
        results = []
        
        for scenario in scenarios:
            analysis = self.analyze_project(
                costs=scenario['costs'],
                savings=scenario['savings']
            )
            
            results.append({
                'name': scenario['name'],
                'costs': scenario['costs'],
                'savings': scenario['savings'],
                'analysis': analysis,
                'rank_metric': getattr(analysis, rank_by) if hasattr(analysis, rank_by) else 0.0
            })
        
        # Sort by rank metric
        reverse = rank_by != 'payback'  # Lower payback is better
        results.sort(key=lambda x: x['rank_metric'], reverse=reverse)
        
        return results


def analyze_energy_project(
    implementation_cost: float,
    annual_energy_savings_kwh: float,
    electricity_rate: float = 0.12,
    discount_rate: float = 0.05,
    utility_escalation: float = 0.03
) -> EconomicAnalysisResult:
    """
    Convenience function for quick economic analysis.
    
    Args:
        implementation_cost: Initial investment ($)
        annual_energy_savings_kwh: Annual energy savings (kWh)
        electricity_rate: Rate ($/kWh)
        discount_rate: Discount rate
        utility_escalation: Utility rate escalation
    
    Returns:
        EconomicAnalysisResult
    """
    costs = ProjectCosts(implementation_cost=implementation_cost)
    savings = ProjectSavings(
        annual_energy_savings_kwh=annual_energy_savings_kwh,
        electricity_rate_kwh=electricity_rate
    )
    
    params = EconomicParameters(
        discount_rate=discount_rate,
        utility_escalation_rate=utility_escalation
    )
    
    analyzer = EconomicAnalyzer(params=params)
    return analyzer.analyze_project(costs, savings)

