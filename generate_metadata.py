import os
import json
import pandas as pd

# Path to dataset examples
dataset_dir = os.path.expanduser("~/Documents/SEEKER/dataset_examples")

# Get all CSV files
csv_files = [f for f in os.listdir(dataset_dir) if f.endswith('.csv')]

# Create basic metadata for each CSV
for csv_file in csv_files:
    base_name = os.path.splitext(csv_file)[0]
    metadata_file = f"{base_name}_metadata.json"
    metadata_path = os.path.join(dataset_dir, metadata_file)
    
    # Skip if metadata already exists
    if os.path.exists(metadata_path):
        print(f"Metadata already exists for {csv_file}")
        continue
    
    try:
        # Read a few rows to get column names
        df = pd.read_csv(os.path.join(dataset_dir, csv_file), nrows=5)
        columns = df.columns.tolist()
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        columns = []
    
    # Create basic metadata structure
    metadata = {
        "dataset_name": base_name,
        "description": f"Dataset containing information from {csv_file}",
        "columns": columns,
        "source": "NYC Open Data",
        "date_created": "2025-03-11",
        "tags": ["nyc", "data"]
    }
    
    # Save metadata to file
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Created metadata for {csv_file}")

print("Metadata generation complete!")
