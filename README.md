# Plist Comparison Tool

A powerful Python-based tool for comparing and analyzing differences between two plist files, specifically designed for complex data structures like those used in content management systems.

## Overview

This tool provides a comprehensive comparison of two plist files, highlighting created, destroyed, and modified entities. It's particularly useful for tracking changes in content management systems, app configurations, or any system using plist files for data storage.

## Features

- **Detailed Comparison**: Analyzes differences between two plist files at a granular level
- **Entity Tracking**: Identifies created, destroyed, and modified entities
- **Attribute Analysis**: Detects changes in individual attributes of entities
- **Human-Readable Output**: Generates easy-to-understand reports of the differences
- **Flexible Reporting**: Offers both detailed developer reports and concise consumer-facing summaries
- **Content Filter Handling**: Special handling for content filters and regional availability data

## Things I learned

1. **Data Structures**:
   - Dictionaries for efficient data lookup and storage
   - Lists for ordered data management
   - Custom object representations (e.g., entities, attributes)

2. **Algorithms**:
   - Diffing algorithms to compare complex nested structures
   - Set operations for efficient comparison of collections

3. **File I/O**: 
   - Reading and parsing plist files

4. **Object-Oriented Programming**:
   - Encapsulation of data and behaviors in classes and functions

5. **Functional Programming**:
   - Use of map, filter, and other higher-order functions

6. **Error Handling**: 
   - Robust error checking and exception handling

7. **Command-Line Interface**: 
   - Argument parsing for user input

8. **Data Serialization**: 
   - Working with plist format, a form of data serialization

9. **Text Processing**: 
   - Generating formatted text output for reports

10. **Version Control**: 
    - Tracking changes between different versions of data

11. **Data Analysis**: 
    - Extracting meaningful insights from raw data differences

## Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/TahirAlauddin/plist-comparison-tool.git
   ```
2. Navigate to the tool directory:
   ```
   cd plist-comparison-tool
   ```
3. Run the tool:
   ```
   python compare_plist.py -a path/to/file_a.plist -b path/to/file_b.plist
   ```

## Usage

The tool accepts two command-line arguments:
- `-a`: Path to the first plist file
- `-b`: Path to the second plist file

After running, you'll be prompted to choose between a full developer report or a consumer-facing summary.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
