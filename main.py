"""Main application for IDF Creator."""
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.location_fetcher import LocationFetcher, GeocodingError
from src.enhanced_location_fetcher import EnhancedLocationFetcher
from src.document_parser import DocumentParser
from src.building_estimator import BuildingEstimator
from src.idf_generator import IDFGenerator
from src.professional_idf_generator import ProfessionalIDFGenerator
from src.utils import ConfigManager, merge_params, ensure_directory


class IDFCreator:
    """Main class that orchestrates IDF file creation from minimal inputs."""
    
    def __init__(self, config_path: str = "config.yaml", enhanced: bool = True, professional: bool = False):
        """
        Initialize the IDF Creator with configuration.
        
        Args:
            config_path: Path to configuration file
            enhanced: Use enhanced location fetcher with multiple API sources
            professional: Use professional IDF generator with advanced features
        """
        self.config_manager = ConfigManager.get_instance(config_path)
        self.config = self.config_manager.config
        
        # Use enhanced fetcher if requested
        if enhanced:
            self.location_fetcher = EnhancedLocationFetcher()
            print("✨ Using ENHANCED mode with multiple free APIs!")
        else:
            self.location_fetcher = LocationFetcher()
            print("📝 Using BASIC mode")
        
        self.document_parser = DocumentParser()
        self.building_estimator = BuildingEstimator(config_path)
        
        # Use professional generator if requested
        if professional:
            self.idf_generator = ProfessionalIDFGenerator()
            self.standard_idf_generator = IDFGenerator()
            print("🏗️ Using PROFESSIONAL mode with advanced features!")
        else:
            self.idf_generator = IDFGenerator()
            self.standard_idf_generator = None
            print("📝 Using STANDARD mode")
        
        self.enhanced = enhanced
        self.professional = professional
    
    def process_inputs(self, address: str, documents: List[str] = None,
                      user_params: Dict = None) -> Dict:
        """
        Process all user inputs to gather building information.
        
        Args:
            address: Building address
            documents: List of document file paths
            user_params: Dictionary of user-provided parameters
            
        Returns:
            Dictionary with all building and location information
        """
        print("🔍 Fetching location data...")
        
        # Use enhanced method if available
        if hasattr(self.location_fetcher, 'fetch_comprehensive_location_data'):
            location = self.location_fetcher.fetch_comprehensive_location_data(address)
        else:
            location = self.location_fetcher.fetch_location_data(address)
        
        print(f"✓ Found location: {location['latitude']:.3f}, {location['longitude']:.3f}")
        print(f"✓ Climate zone: {location['climate_zone']}")
        
        # Parse documents if provided
        doc_params = {}
        if documents:
            print(f"📄 Parsing {len(documents)} document(s)...")
            for doc_path in documents:
                if os.path.exists(doc_path):
                    params = self.document_parser.parse_document(doc_path)
                    doc_params.update(params)
                    print(f"✓ Parsed {Path(doc_path).name}")
        
        # Merge all parameters (user params override doc params, which override defaults)
        defaults = self.building_estimator.get_defaults()
        merged_params = merge_params(defaults, doc_params, user_params)
        
        print(f"✓ Building type: {merged_params.get('building_type', 'Office')}")
        print(f"✓ Stories: {merged_params.get('stories', 3)}")
        print(f"✓ Floor area: {merged_params.get('floor_area', 1500)} m²")
        
        return {
            'location': location,
            'building_params': merged_params
        }
    
    def estimate_missing_parameters(self, building_params: Dict) -> Dict:
        """
        Estimate any missing building parameters.
        
        Args:
            building_params: Partial building parameters
            
        Returns:
            Complete building parameters with estimates
        """
        # Strict mode enforces real-world data from sources (no synthetic defaults)
        strict = bool(building_params.get('strict_real_data'))

        # Injected location-derived building info (from create_idf)
        loc_building = building_params.get('__location_building') or {}

        # Prefer real stories from OSM if available
        stories = building_params.get('stories')
        if stories is None:
            osm_levels = loc_building.get('osm_levels')
            try:
                if osm_levels is not None:
                    stories = int(float(osm_levels))
            except Exception:
                stories = None
        if stories is None:
            if strict:
                raise ValueError("strict_real_data is enabled: missing 'stories' and no OSM levels available")
            stories = 3

        # Get floor area - FIX: Check user-specified floor_area_per_story FIRST
        floor_area = building_params.get('floor_area')
        
        # Track whether user explicitly locked the floor area
        user_forced_area = bool(building_params.get('force_area'))

        # Detect explicit floor area source so we can preserve true user overrides
        floor_area_source = building_params.get('floor_area_source')

        # FIX: If user specified floor_area_per_story_m2, use that instead of OSM
        floor_area_per_story = building_params.get('floor_area_per_story_m2')
        if floor_area_per_story is not None and floor_area is None:
            # User explicitly specified floor area per story - use it
            if stories is None or stories <= 0:
                stories = 3
            floor_area = floor_area_per_story * max(1, int(stories))
            print(f"✓ Using user-specified floor area: {floor_area_per_story:.0f} m²/floor × {stories} floors = {floor_area:.0f} m²")
            floor_area_source = floor_area_source or 'user'
        
        # Determine effective stories for calculations (fallback to 1 if unknown)
        effective_stories = max(1, int(stories)) if stories and stories > 0 else 1

        # Collect location-derived footprint areas (per floor) from multiple sources
        location_footprint_area = None
        location_sources = ['microsoft_area_m2', 'primary_area_m2', 'google_area_m2', 'osm_area_m2']
        for key in location_sources:
            value = loc_building.get(key)
            try:
                if value and float(value) > 10:
                    location_footprint_area = float(value)
                    break
            except Exception:
                continue
        
        # Apply location footprint if available and user did not explicitly force an override
        if location_footprint_area is not None and not user_forced_area and floor_area_source != 'user':
            total_area_from_location = location_footprint_area * effective_stories
            # Only log when this overrides a previous default or fills a gap
            if floor_area is None or abs(total_area_from_location - (floor_area or 0)) > 0.1:
                print(f"✓ Using location footprint: {location_footprint_area:.1f} m²/floor × {effective_stories} floors = {total_area_from_location:.0f} m²")
            floor_area = total_area_from_location
            floor_area_source = 'location'
            if not stories:
                stories = effective_stories
        
        # If still no floor area, check city data explicitly (legacy fallback)
        if floor_area is None:
            city_area = loc_building.get('city_area_m2')
            try:
                if city_area and float(city_area) > 10:
                    floor_area = float(city_area) * effective_stories
                    floor_area_source = 'city'
                    if not stories:
                        stories = effective_stories
            except Exception:
                pass
        
        # Ensure stories is not None
        if not stories:
            stories = 3
        
        # If no floor area provided, use defaults
        if floor_area is None:
            if strict:
                raise ValueError("strict_real_data is enabled: missing 'floor_area' and no OSM/city/document area available")
            floor_area = building_params.get('floor_area_per_story_m2', 500) * stories
            floor_area_source = floor_area_source or 'default'
        
        # Estimate building dimensions
        dimensions = self.building_estimator.estimate_building_dimensions(floor_area)
        
        # Get zone parameters based on building type
        building_type = building_params.get('building_type', 'Office')
        zone_params = self.building_estimator.calculate_zone_parameters(
            floor_area, building_type, stories
        )
        
        # Combine all parameters
        # Note: floor_area here is TOTAL building area (all floors combined)
        # Professional IDF expects 'total_area' for the same concept
        complete_params = {
            **building_params,
            **dimensions,
            'floor_area': floor_area,
            'total_area': floor_area,  # Alias for professional IDF
            'floor_area_source': floor_area_source or building_params.get('floor_area_source')
        }
        
        return {
            'building': complete_params,
            'zone': zone_params
        }
    
    def create_idf(self, address: str, documents: List[str] = None,
                   user_params: Dict = None, output_path: str = None) -> str:
        """
        Main method to create an IDF file from inputs.
        
        Args:
            address: Building address
            documents: List of document paths
            user_params: User-provided parameters
            output_path: Path to save the IDF file
            
        Returns:
            Path to created IDF file
        """
        print("\n" + "="*60)
        print("🏗️  IDF Creator for EnergyPlus")
        print("="*60 + "\n")
        
        # Process inputs
        data = self.process_inputs(address, documents, user_params)
        
        # Estimate missing parameters
        print("\n📐 Estimating building parameters...")
        # Attach location-derived building info for estimation (OSM area/levels)
        bp = dict(data['building_params'])
        bp['__location_building'] = data.get('location', {}).get('building') or {}
        params = self.estimate_missing_parameters(bp)
        print(f"✓ Building dimensions: {params['building']['length']:.1f}m × {params['building']['width']:.1f}m")
        
        # Generate IDF
        print("\n⚙️  Generating IDF file...")
        if self.professional:
            try:
                idf_content = self.idf_generator.generate_professional_idf(
                    address,
                    params['building'],
                    data['location'],
                    documents
                )
            except Exception as professional_error:
                import traceback
                error_trace = traceback.format_exc()
                print("⚠️ Professional IDF generation failed, falling back to standard generator.")
                print(f"   Reason: {professional_error}")
                print(f"   Traceback:\n{error_trace}")
                if not self.standard_idf_generator:
                    self.standard_idf_generator = IDFGenerator()
                idf_content = self.standard_idf_generator.generate_complete_idf(
                    data['location'],
                    params['building'],
                    params['zone'],
                    self.config
                )
        else:
            idf_content = self.idf_generator.generate_complete_idf(
                data['location'],
                params['building'],
                params['zone'],
                self.config
            )
        
        # Determine output path (default to organized artifacts folder)
        if not output_path:
            building_name = params['building'].get('name', 'Building').replace(' ', '_')
            output_path = f"artifacts/desktop_files/idf/{building_name}.idf"
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir:
            ensure_directory(output_dir)
        
        # Write IDF file
        with open(output_path, 'w') as f:
            f.write(idf_content)
        
        print(f"\n✅ IDF file created: {output_path}")
        print(f"📊 Zone area: {params['zone']['zone_area']:.1f} m²")
        print(f"👥 People per zone: {params['zone']['number_of_people']}")
        print(f"💡 Lighting power: {params['zone']['lighting_power']:.1f} W")
        
        print("\n" + "="*60)
        print("✨ Ready to simulate in EnergyPlus!")
        print("="*60 + "\n")
        
        return output_path
    
    def create_and_calibrate_idf(
        self,
        address: str,
        utility_data: Any,  # UtilityData from model_calibration
        weather_file: str,
        documents: List[str] = None,
        user_params: Dict = None,
        output_path: str = None,
        tolerance: float = 0.10,
        max_iterations: int = 20
    ) -> Dict[str, Any]:
        """
        Generate IDF and calibrate it to utility bills.
        
        Args:
            address: Building address
            utility_data: UtilityData object with monthly kWh consumption
            weather_file: Path to weather file (.epw)
            documents: Optional document paths
            user_params: Optional user parameters
            output_path: Optional output path for IDF
            tolerance: Calibration tolerance (default 10%)
            max_iterations: Maximum calibration iterations
            
        Returns:
            Dictionary with 'idf_path' and 'calibration_result'
        """
        from src.model_calibration import ModelCalibrator
        
        # Generate baseline IDF
        print("\n" + "="*60)
        print("🏗️  IDF Creator - Generate & Calibrate")
        print("="*60 + "\n")
        
        baseline_idf = self.create_idf(address, documents, user_params, output_path)
        
        # Calibrate to utility bills
        print("\n" + "="*60)
        print("📊 Model Calibration")
        print("="*60 + "\n")
        
        calibrator = ModelCalibrator()
        calibration_result = calibrator.calibrate_to_utility_bills(
            idf_file=baseline_idf,
            utility_data=utility_data,
            weather_file=weather_file,
            tolerance=tolerance,
            max_iterations=max_iterations
        )
        
        print(f"\n✅ Calibration complete!")
        print(f"   Calibrated IDF: {calibration_result.calibrated_idf_path}")
        print(f"   Annual Error: {calibration_result.accuracy_annual:.1f}%")
        print(f"   CVRMSE: {calibration_result.accuracy_monthly_cvrmse:.1f}%")
        print(f"   ASHRAE 14 Compliant: {calibration_result.accuracy_monthly_cvrmse <= 15.0}")
        
        return {
            'baseline_idf_path': baseline_idf,
            'calibrated_idf_path': calibration_result.calibrated_idf_path,
            'calibration_result': calibration_result
        }
    
    def create_and_optimize_retrofits(
        self,
        address: str,
        utility_rates: Any,  # UtilityRates from retrofit_optimizer
        weather_file: str,
        documents: List[str] = None,
        user_params: Dict = None,
        output_path: str = None,
        budget: Optional[float] = None,
        max_payback: Optional[float] = None,
        max_measures_per_scenario: int = 5
    ) -> Dict[str, Any]:
        """
        Generate IDF and create optimized retrofit scenarios.
        
        Args:
            address: Building address
            utility_rates: UtilityRates object with electricity rates
            weather_file: Path to weather file (.epw)
            documents: Optional document paths
            user_params: Optional user parameters
            output_path: Optional output path for IDF
            budget: Optional budget constraint for optimization
            max_payback: Optional maximum payback period (years)
            max_measures_per_scenario: Maximum measures per scenario
            
        Returns:
            Dictionary with 'idf_path', 'scenarios', and 'optimized_scenarios'
        """
        from src.retrofit_optimizer import RetrofitOptimizer
        
        # Generate baseline IDF
        print("\n" + "="*60)
        print("🏗️  IDF Creator - Generate & Optimize Retrofits")
        print("="*60 + "\n")
        
        baseline_idf = self.create_idf(address, documents, user_params, output_path)
        
        # Get building parameters for retrofit analysis
        data = self.process_inputs(address, documents, user_params)
        params = self.estimate_missing_parameters(data['building_params'])
        
        # Estimate baseline energy (will be updated after simulation)
        floor_area_m2 = params['building'].get('floor_area', 1500)
        floor_area_sf = floor_area_m2 * 10.764  # Convert m² to ft²
        estimated_annual_kwh = floor_area_sf * 20  # Rough estimate: 20 kWh/ft²/year
        
        # Generate retrofit scenarios
        print("\n" + "="*60)
        print("🔄 Retrofit Optimization")
        print("="*60 + "\n")
        
        optimizer = RetrofitOptimizer()
        building_type = params['building'].get('building_type', 'office').lower()
        
        scenarios = optimizer.generate_scenarios(
            baseline_energy_kwh=estimated_annual_kwh,
            floor_area_sf=floor_area_sf,
            baseline_idf_path=baseline_idf,
            building_type=building_type,
            max_measures_per_scenario=max_measures_per_scenario
        )
        
        print(f"✅ Generated {len(scenarios)} retrofit scenarios")
        
        # Run simulations to get actual energy savings
        scenarios = optimizer.run_scenario_simulations(
            scenarios=scenarios,
            baseline_idf_path=baseline_idf,
            weather_file=weather_file,
            max_concurrent=4
        )
        
        # Optimize scenarios
        optimized = optimizer.optimize(
            scenarios=scenarios,
            utility_rates=utility_rates,
            budget=budget,
            max_payback=max_payback
        )
        
        print(f"\n✅ Optimization complete!")
        print(f"   Optimized scenarios: {len(optimized)}")
        if optimized:
            print(f"   Top scenario NPV: ${optimized[0].npv:,.0f}")
            print(f"   Top scenario ROI: {optimized[0].roi:.1f}%")
        
        return {
            'baseline_idf_path': baseline_idf,
            'scenarios': scenarios,
            'optimized_scenarios': optimized
        }


def _parse_user_params(args: argparse.Namespace) -> Dict[str, any]:
    """
    Parse command-line arguments into user parameters dictionary.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Dictionary of user-provided parameters
    """
    user_params = {}
    
    # Basic building parameters
    if args.building_type:
        user_params['building_type'] = args.building_type
    if args.stories:
        user_params['stories'] = args.stories
    if args.floor_area:
        user_params['floor_area'] = args.floor_area
    if args.window_ratio:
        user_params['window_to_wall_ratio'] = args.window_ratio
    
    # Window-to-wall ratio overrides
    if args.wwr is not None:
        user_params['wwr'] = args.wwr
    if args.wwr_n is not None:
        user_params['wwr_n'] = args.wwr_n
    if args.wwr_e is not None:
        user_params['wwr_e'] = args.wwr_e
    if args.wwr_s is not None:
        user_params['wwr_s'] = args.wwr_s
    if args.wwr_w is not None:
        user_params['wwr_w'] = args.wwr_w
    if args.force_area:
        user_params['force_area'] = True
    
    # Equipment parameters
    if args.equip_source:
        user_params['equip_source'] = args.equip_source
    if args.equip_type:
        user_params['equip_type'] = args.equip_type
    if args.equip_capacity:
        user_params['equip_capacity'] = args.equip_capacity
    if args.equip_id:
        user_params['equip_id'] = args.equip_id
    
    # Age and certification parameters
    if args.year_built:
        user_params['year_built'] = args.year_built
    if args.retrofit_year:
        user_params['retrofit_year'] = args.retrofit_year
    if args.leed_level:
        user_params['leed_level'] = args.leed_level
    if args.cogeneration_capacity_kw:
        user_params['cogeneration_capacity_kw'] = args.cogeneration_capacity_kw
    if args.chp_provides_percent:
        user_params['chp_provides_percent'] = args.chp_provides_percent
    
    return user_params


def main():
    """Command-line interface for IDF Creator."""
    parser = argparse.ArgumentParser(
        description='Create EnergyPlus IDF files from minimal inputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with address
  python main.py "123 Main St, San Francisco, CA"
  
  # With documents
  python main.py "456 Oak Ave, Boston, MA" --documents building_plans.pdf floorplan.jpg
  
  # With custom parameters
  python main.py "789 Pine Rd, Seattle, WA" --building-type "Retail" --stories 2 --floor-area 1000
  
  # Specify output file
  python main.py "321 Elm St, Chicago, IL" --output my_building.idf
        """
    )
    
    parser.add_argument('address', type=str, 
                       help='Building address (required)')
    parser.add_argument('-d', '--documents', nargs='+', 
                       help='Document files to parse (PDF, images, text)')
    parser.add_argument('-o', '--output', type=str,
                       help='Output IDF file path (default: output/Building.idf)')
    parser.add_argument('--building-type', type=str,
                       choices=['Office', 'Residential', 'Retail', 'Warehouse', 
                               'School', 'Hospital'],
                       help='Building type')
    parser.add_argument('--stories', type=int,
                       help='Number of stories')
    parser.add_argument('--floor-area', type=float,
                       help='Total floor area (m²)')
    parser.add_argument('--window-ratio', type=float,
                       help='Window to wall ratio (0-1)')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='Configuration file path')
    parser.add_argument('--enhanced', action='store_true', default=True,
                       help='Use enhanced mode with multiple APIs (default: True)')
    parser.add_argument('--basic', action='store_true',
                       help='Use basic mode (overrides --enhanced)')
    parser.add_argument('--professional', action='store_true',
                       help='Use professional mode with advanced features')
    # WWR overrides
    parser.add_argument('--wwr', type=float,
                       help='Global window-to-wall ratio (0-1) override')
    parser.add_argument('--wwr-n', type=float,
                       help='North facade window-to-wall ratio (0-1)')
    parser.add_argument('--wwr-e', type=float,
                       help='East facade window-to-wall ratio (0-1)')
    parser.add_argument('--wwr-s', type=float,
                       help='South facade window-to-wall ratio (0-1)')
    parser.add_argument('--wwr-w', type=float,
                       help='West facade window-to-wall ratio (0-1)')
    parser.add_argument('--force-area', action='store_true',
                       help='Force target floor area by scaling footprint per floor')
    # Equipment catalog options
    parser.add_argument('--equip-source', type=str, choices=['bcl','ahri','mock'],
                       help='Equipment source catalog (default: mock in professional mode)')
    parser.add_argument('--equip-type', type=str,
                       help='Equipment type, e.g., DX_COIL, RTU, PTAC, CHILLER_EIR')
    parser.add_argument('--equip-capacity', type=str,
                       help='Desired capacity (e.g., 3ton, 35000W) for catalog search')
    parser.add_argument('--equip-id', type=str,
                       help='Specific catalog equipment identifier')
    parser.add_argument('--year-built', type=int,
                          help='Year building was constructed (for age-based efficiency adjustments)')
    parser.add_argument('--retrofit-year', type=int,
                          help='Year of major retrofit (if applicable)')
    parser.add_argument('--leed-level', type=str, choices=['Certified', 'Silver', 'Gold', 'Platinum'],
                          help='LEED certification level (applies efficiency bonuses)')
    parser.add_argument('--cogeneration-capacity-kw', type=float,
                          help='Cogeneration/CHP system capacity in kW (reduces grid electricity)')
    parser.add_argument('--chp-provides-percent', type=float,
                          help='CHP provides this percent of electrical load (0-100). If not specified, calculated from capacity.')
    
    args = parser.parse_args()
    
    # Parse user parameters
    user_params = _parse_user_params(args)
    
    # Determine mode
    enhanced = args.enhanced and not args.basic
    professional = args.professional
    
    # Create IDF with optional calibration/retrofit
    try:
        creator = IDFCreator(
            config_path=args.config,
            enhanced=enhanced,
            professional=professional
        )
        
        # Check if calibration or retrofit is requested
        if args.calibrate:
            if not args.utility_data or not args.weather_file:
                print("❌ Error: --calibrate requires --utility-data and --weather-file", file=sys.stderr)
                sys.exit(1)
            
            from src.model_calibration import UtilityData
            import json
            
            # Load utility data
            with open(args.utility_data, 'r') as f:
                util_json = json.load(f)
            
            utility_data = UtilityData(
                monthly_kwh=util_json.get('monthly_kwh', []),
                peak_demand_kw=util_json.get('peak_demand_kw'),
                heating_fuel=util_json.get('heating_fuel', 'electric'),
                cooling_fuel=util_json.get('cooling_fuel', 'electric'),
                gas_therms=util_json.get('gas_therms'),
                electricity_rate_kwh=util_json.get('electricity_rate_kwh', 0.12),
                gas_rate_therm=util_json.get('gas_rate_therm', 1.20)
            )
            
            result = creator.create_and_calibrate_idf(
                address=args.address,
                utility_data=utility_data,
                weather_file=args.weather_file,
                documents=args.documents,
                user_params=user_params,
                output_path=args.output
            )
            print(f"\n✅ Complete! Calibrated IDF: {result['calibrated_idf_path']}")
            
        elif args.generate_retrofits:
            if not args.weather_file:
                print("❌ Error: --generate-retrofits requires --weather-file", file=sys.stderr)
                sys.exit(1)
            
            from src.retrofit_optimizer import UtilityRates
            import json
            
            # Load or create utility rates
            if args.utility_rates:
                with open(args.utility_rates, 'r') as f:
                    rates_json = json.load(f)
                utility_rates = UtilityRates(
                    electricity_rate_kwh=rates_json.get('electricity_rate_kwh', 0.12),
                    gas_rate_therm=rates_json.get('gas_rate_therm'),
                    demand_rate_kw=rates_json.get('demand_rate_kw'),
                    escalation_rate=rates_json.get('escalation_rate', 0.03)
                )
            else:
                # Use defaults
                utility_rates = UtilityRates(
                    electricity_rate_kwh=0.12,
                    escalation_rate=0.03
                )
            
            result = creator.create_and_optimize_retrofits(
                address=args.address,
                utility_rates=utility_rates,
                weather_file=args.weather_file,
                documents=args.documents,
                user_params=user_params,
                output_path=args.output,
                budget=args.retrofit_budget,
                max_payback=args.max_payback
            )
            print(f"\n✅ Complete! Baseline IDF: {result['baseline_idf_path']}")
            print(f"   Optimized scenarios: {len(result['optimized_scenarios'])}")
            
        else:
            # Standard IDF generation
            creator.create_idf(
                address=args.address,
                documents=args.documents,
                user_params=user_params,
                output_path=args.output
            )
    except Exception as e:
        import traceback
        print(f"\n❌ Error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
