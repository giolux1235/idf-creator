"""Main application for IDF Creator."""
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List
import yaml

from src.location_fetcher import LocationFetcher
from src.enhanced_location_fetcher import EnhancedLocationFetcher
from src.document_parser import DocumentParser
from src.building_estimator import BuildingEstimator
from src.idf_generator import IDFGenerator
from src.professional_idf_generator import ProfessionalIDFGenerator


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
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
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
            print("🏗️ Using PROFESSIONAL mode with advanced features!")
        else:
            self.idf_generator = IDFGenerator()
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
        defaults.update(doc_params)
        if user_params:
            defaults.update(user_params)
        
        print(f"✓ Building type: {defaults.get('building_type', 'Office')}")
        print(f"✓ Stories: {defaults.get('stories', 3)}")
        print(f"✓ Floor area: {defaults.get('floor_area', 1500)} m²")
        
        return {
            'location': location,
            'building_params': defaults
        }
    
    def estimate_missing_parameters(self, building_params: Dict) -> Dict:
        """
        Estimate any missing building parameters.
        
        Args:
            building_params: Partial building parameters
            
        Returns:
            Complete building parameters with estimates
        """
        # Get floor area
        floor_area = building_params.get('floor_area')
        stories = building_params.get('stories', 3)
        
        # If no floor area provided, estimate from stories
        if not floor_area:
            floor_area_per_story = building_params.get('floor_area_per_story_m2', 500)
            floor_area = floor_area_per_story * stories
        
        # Estimate building dimensions
        dimensions = self.building_estimator.estimate_building_dimensions(floor_area)
        
        # Get zone parameters based on building type
        building_type = building_params.get('building_type', 'Office')
        zone_params = self.building_estimator.calculate_zone_parameters(
            floor_area, building_type, stories
        )
        
        # Combine all parameters
        complete_params = {
            **building_params,
            **dimensions,
            'floor_area': floor_area
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
        params = self.estimate_missing_parameters(data['building_params'])
        print(f"✓ Building dimensions: {params['building']['length']:.1f}m × {params['building']['width']:.1f}m")
        
        # Generate IDF
        print("\n⚙️  Generating IDF file...")
        if self.professional:
            idf_content = self.idf_generator.generate_professional_idf(
                address,
                params['building'],
                data['location'],
                documents
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
        if output_dir:  # Only create directory if path has a directory component
            os.makedirs(output_dir, exist_ok=True)
        
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
    
    args = parser.parse_args()
    
    # Prepare user parameters
    user_params = {}
    if args.building_type:
        user_params['building_type'] = args.building_type
    if args.stories:
        user_params['stories'] = args.stories
    if args.floor_area:
        user_params['floor_area'] = args.floor_area
    if args.window_ratio:
        user_params['window_to_wall_ratio'] = args.window_ratio
    # New WWR overrides
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
    # Equipment params
    if args.equip_source:
        user_params['equip_source'] = args.equip_source
    if args.equip_type:
        user_params['equip_type'] = args.equip_type
    if args.equip_capacity:
        user_params['equip_capacity'] = args.equip_capacity
    if args.equip_id:
        user_params['equip_id'] = args.equip_id
    
    # Determine mode
    enhanced = args.enhanced and not args.basic
    professional = args.professional
    
    # Create IDF
    try:
        creator = IDFCreator(
            config_path=args.config,
            enhanced=enhanced,
            professional=professional
        )
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

