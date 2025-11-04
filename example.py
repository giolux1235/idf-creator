"""Example usage of IDF Creator as a Python module."""
from main import IDFCreator


def example_basic():
    """Basic example: create IDF from address only."""
    print("Example 1: Basic IDF Creation")
    print("-" * 50)
    
    creator = IDFCreator()
    
    creator.create_idf(
        address="Empire State Building, New York, NY"
    )


def example_with_parameters():
    """Example with custom parameters."""
    print("\nExample 2: Custom Parameters")
    print("-" * 50)
    
    creator = IDFCreator()
    
    user_params = {
        'building_type': 'Retail',
        'stories': 2,
        'floor_area': 1200,
        'window_to_wall_ratio': 0.6
    }
    
    creator.create_idf(
        address="Times Square, New York, NY",
        user_params=user_params,
        output_path="output/times_square_retail.idf"
    )


def example_with_documents():
    """Example with document parsing."""
    print("\nExample 3: With Documents")
    print("-" * 50)
    
    creator = IDFCreator()
    
    # Note: Add your actual document paths here
    documents = [
        # "path/to/building_plans.pdf",
        # "path/to/floorplan.jpg"
    ]
    
    if documents:
        creator.create_idf(
            address="123 Main Street, San Francisco, CA",
            documents=documents
        )
    else:
        print("Add document paths to use this example")


if __name__ == "__main__":
    # Run examples
    example_basic()
    
    # Uncomment to run other examples:
    # example_with_parameters()
    # example_with_documents()

















