#!/usr/bin/env python3
"""
Natural Language IDF Creator CLI
Accepts building descriptions and documents to generate IDF files
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.nlp_building_parser import BuildingDescriptionParser
from src.document_parser import DocumentParser
from main import IDFCreator


def main():
    parser = argparse.ArgumentParser(
        description='IDF Creator with Natural Language and Document Input',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Text description only
  python nlp_cli.py "5-story office building in downtown with 50,000 sq ft and VAV system"
  
  # With address
  python nlp_cli.py "Modern office tower, 30 stories, 500,000 sq ft" --address "123 Main St, San Francisco, CA"
  
  # With documents
  python nlp_cli.py "Office building with conference rooms" --address "Chicago, IL" --documents plan.pdf floorplan.jpg
  
  # From file
  python nlp_cli.py --input building_description.txt --address "New York, NY" --professional
  
  # Upload multiple documents
  python nlp_cli.py "Retail store" --documents site_plan.pdf mechanical_drawing.pdf specifications.docx
        """
    )
    
    # Input methods (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('description', nargs='?', type=str,
                            help='Natural language building description')
    input_group.add_argument('--input', '-i', type=str,
                            help='Input file with building description')
    
    # Required arguments
    parser.add_argument('--address', '-a', type=str, required=True,
                       help='Building address (required)')
    
    # Optional arguments
    parser.add_argument('--documents', '-d', nargs='+',
                       help='Document files (PDF, images, Word docs)')
    parser.add_argument('--output', '-o', type=str,
                       help='Output IDF file path')
    parser.add_argument('--professional', action='store_true',
                       help='Use professional mode with advanced features')
    parser.add_argument('--enhanced', action='store_true', default=True,
                       help='Use enhanced mode (default: True)')
    parser.add_argument('--debug', action='store_true',
                       help='Show parsed parameters')
    
    args = parser.parse_args()
    
    # Get description
    if args.description:
        description = args.description
    elif args.input:
        with open(args.input, 'r') as f:
            description = f.read()
    
    print("="*60)
    print("🏗️  Natural Language IDF Creator")
    print("="*60)
    print()
    print(f"📝 Building Description:")
    print(f"   {description[:200]}{'...' if len(description) > 200 else ''}")
    print()
    print(f"📍 Address: {args.address}")
    print()
    
    # Parse description
    print("🔍 Parsing description...")
    nlp_parser = BuildingDescriptionParser()
    result = nlp_parser.process_and_generate_idf(description, args.address)
    
    if args.debug:
        print("\n📋 Parsed Parameters:")
        print(f"   Building Type: {result['parsed_description']['building_type']}")
        print(f"   Stories: {result['parsed_description']['stories']}")
        print(f"   Area: {result['parsed_description']['area']}")
        print(f"   HVAC: {result['parsed_description']['hvac_system']}")
        print()
    
    # Parse documents if provided
    idf_params = result['idf_parameters'].copy()
    
    if args.documents:
        print(f"📄 Parsing {len(args.documents)} document(s)...")
        doc_parser = DocumentParser()
        
        for doc_path in args.documents:
            if Path(doc_path).exists():
                doc_params = doc_parser.parse_document(doc_path)
                idf_params.update(doc_params)
                print(f"   ✓ Extracted data from {Path(doc_path).name}")
            else:
                print(f"   ⚠️  File not found: {doc_path}")
    
    # Override with parsed values
    if idf_params.get('building_type'):
        building_type = idf_params['building_type']
    else:
        building_type = 'Office'
    
    # Create IDF
    print("\n⚙️  Generating IDF file...")
    try:
        creator = IDFCreator(
            enhanced=args.enhanced,
            professional=args.professional
        )
        
        # Prepare user params
        user_params = {}
        if idf_params.get('stories'):
            user_params['stories'] = idf_params['stories']
        if idf_params.get('floor_area'):
            user_params['floor_area'] = idf_params['floor_area']
        if idf_params.get('building_type'):
            user_params['building_type'] = idf_params['building_type']
        
        # Generate IDF
        output_path = creator.create_idf(
            address=args.address,
            documents=args.documents,
            user_params=user_params,
            output_path=args.output
        )
        
        print(f"\n✅ IDF file created: {output_path}")
        print("\n✨ Ready to simulate in EnergyPlus!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

