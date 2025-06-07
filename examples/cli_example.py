"""
CLI Example - Universal Types System

This example demonstrates how to use ModuLink with Click for CLI applications
using the simplified universal types approach:
- CLI command integration
- File processing workflows
- Progress tracking
- Configuration management
- Error handling in CLI context
"""

import click
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from modulink import Ctx, compose, catch_errors, timing
from typing import List, Dict, Any

# File processing functions using universal types
async def validate_input_directory(ctx: Ctx) -> Ctx:
    """Validate that input directory exists and is readable"""
    print("🔍 Validating input directory...")
    
    input_dir = ctx.get('input_dir')
    errors = ctx.get('errors', [])
    
    if not input_dir:
        errors.append({'message': 'Input directory not specified', 'code': 'INPUT_ERROR'})
        return {**ctx, 'errors': errors}
    
    input_path = Path(input_dir)
    if not input_path.exists():
        errors.append({'message': f'Input directory does not exist: {input_dir}', 'code': 'INPUT_ERROR'})
    elif not input_path.is_dir():
        errors.append({'message': f'Input path is not a directory: {input_dir}', 'code': 'INPUT_ERROR'})
    elif not os.access(input_path, os.R_OK):
        errors.append({'message': f'Input directory is not readable: {input_dir}', 'code': 'INPUT_ERROR'})
    
    return {**ctx, 'errors': errors}

async def create_output_directory(ctx: Ctx) -> Ctx:
    """Create output directory if it doesn't exist"""
    if ctx.get('errors'):
        return ctx
    
    print("📁 Creating output directory...")
    
    output_dir = ctx.get('output_dir')
    if not output_dir:
        return {**ctx, 'errors': [{'message': 'Output directory not specified', 'code': 'OUTPUT_ERROR'}]}
    
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Output directory ready: {output_dir}")
        return {**ctx, 'output_path': str(output_path)}
    except Exception as e:
        return {**ctx, 'errors': [{'message': f'Failed to create output directory: {e}', 'code': 'OUTPUT_ERROR'}]}

async def scan_files(ctx: Ctx) -> Ctx:
    """Scan input directory for files to process"""
    if ctx.get('errors'):
        return ctx
    
    print("🔍 Scanning for files...")
    
    input_dir = Path(ctx.get('input_dir'))
    file_pattern = ctx.get('file_pattern', '*.txt')
    
    try:
        files = list(input_dir.glob(file_pattern))
        file_list = [str(f) for f in files]
        
        print(f"📄 Found {len(file_list)} files to process")
        
        return {
            **ctx,
            'files': file_list,
            'total_files': len(file_list),
            'processed_files': 0
        }
    except Exception as e:
        return {**ctx, 'errors': [{'message': f'Failed to scan files: {e}', 'code': 'SCAN_ERROR'}]}

async def process_files(ctx: Ctx) -> Ctx:
    """Process each file in the list"""
    if ctx.get('errors'):
        return ctx
    
    files = ctx.get('files', [])
    output_dir = Path(ctx.get('output_dir'))
    processed_files = []
    failed_files = []
    
    print(f"⚙️  Processing {len(files)} files...")
    
    for i, file_path in enumerate(files, 1):
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple processing: add timestamp and line count
            lines = content.split('\n')
            processed_content = {
                'original_file': file_path,
                'processed_at': datetime.utcnow().isoformat(),
                'line_count': len(lines),
                'word_count': len(content.split()),
                'character_count': len(content),
                'first_10_lines': lines[:10]
            }
            
            # Write processed file
            input_file = Path(file_path)
            output_file = output_dir / f"{input_file.stem}_processed.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_content, f, indent=2)
            
            processed_files.append({
                'input': file_path,
                'output': str(output_file),
                'stats': {
                    'lines': len(lines),
                    'words': len(content.split()),
                    'characters': len(content)
                }
            })
            
            # Progress indicator
            print(f"  ✅ [{i}/{len(files)}] Processed: {input_file.name}")
            
        except Exception as e:
            failed_files.append({
                'file': file_path,
                'error': str(e)
            })
            print(f"  ❌ [{i}/{len(files)}] Failed: {Path(file_path).name} - {e}")
    
    return {
        **ctx,
        'processed_files': processed_files,
        'failed_files': failed_files,
        'processing_complete': True
    }

async def generate_report(ctx: Ctx) -> Ctx:
    """Generate processing report"""
    if ctx.get('errors'):
        return ctx
    
    print("📊 Generating report...")
    
    processed_files = ctx.get('processed_files', [])
    failed_files = ctx.get('failed_files', [])
    output_dir = Path(ctx.get('output_dir'))
    
    # Create summary report
    report = {
        'processing_summary': {
            'start_time': ctx.get('start_time'),
            'end_time': datetime.utcnow().isoformat(),
            'total_files': len(processed_files) + len(failed_files),
            'successful': len(processed_files),
            'failed': len(failed_files),
            'success_rate': len(processed_files) / (len(processed_files) + len(failed_files)) * 100 if (processed_files or failed_files) else 0
        },
        'processed_files': processed_files,
        'failed_files': failed_files,
        'configuration': {
            'input_dir': ctx.get('input_dir'),
            'output_dir': ctx.get('output_dir'),
            'file_pattern': ctx.get('file_pattern', '*.txt')
        }
    }
    
    # Write report
    report_file = output_dir / 'processing_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Report saved: {report_file}")
    print(f"📈 Processing complete: {len(processed_files)} successful, {len(failed_files)} failed")
    
    return {**ctx, 'report': report, 'report_file': str(report_file)}

# Create processing pipeline
file_processing_pipeline = compose(
    validate_input_directory,
    create_output_directory,
    scan_files,
    process_files,
    generate_report
)

@click.group()
def cli():
    """ModuLink CLI Example - Universal Types System"""
    pass

@cli.command()
@click.option('--input-dir', '-i', required=True, type=click.Path(exists=True), 
              help='Input directory containing files to process')
@click.option('--output-dir', '-o', required=True, type=click.Path(), 
              help='Output directory for processed files')
@click.option('--pattern', '-p', default='*.txt', 
              help='File pattern to match (default: *.txt)')
@click.option('--verbose', '-v', is_flag=True, 
              help='Enable verbose output')
def process(input_dir: str, output_dir: str, pattern: str, verbose: bool):
    """Process files in a directory using ModuLink pipeline."""
    
    async def run_processing():
        # Create context for CLI processing
        ctx: Ctx = {
            'input_dir': input_dir,
            'output_dir': output_dir,
            'file_pattern': pattern,
            'verbose': verbose,
            'start_time': datetime.utcnow().isoformat(),
            'command': 'process'
        }
        
        print("🚀 Starting file processing...")
        print(f"📂 Input: {input_dir}")
        print(f"📁 Output: {output_dir}")
        print(f"🔍 Pattern: {pattern}")
        print("-" * 50)
        
        # Run the processing pipeline
        result = await file_processing_pipeline(ctx)
        
        # Handle errors
        if result.get('errors'):
            print("\n❌ Processing failed with errors:")
            for error in result['errors']:
                print(f"  - {error['message']} ({error['code']})")
            return 1
        
        # Success summary
        print("\n" + "=" * 50)
        print("✅ Processing completed successfully!")
        
        report = result.get('report', {})
        summary = report.get('processing_summary', {})
        
        print(f"📊 Files processed: {summary.get('successful', 0)}")
        print(f"❌ Files failed: {summary.get('failed', 0)}")
        print(f"📈 Success rate: {summary.get('success_rate', 0):.1f}%")
        print(f"📄 Report saved: {result.get('report_file')}")
        
        return 0
    
    # Run the async processing
    result = asyncio.run(run_processing())
    exit(result)

@cli.command()
@click.option('--config-file', '-c', type=click.Path(exists=True), 
              help='Configuration file (JSON)')
def batch(config_file: str):
    """Run batch processing from configuration file."""
    
    async def run_batch():
        try:
            # Load configuration
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"📋 Loaded configuration from: {config_file}")
            
            # Process each batch item
            for i, batch_item in enumerate(config.get('batches', []), 1):
                print(f"\n🔄 Processing batch {i}/{len(config['batches'])}")
                print(f"📂 Input: {batch_item['input_dir']}")
                print(f"📁 Output: {batch_item['output_dir']}")
                
                # Create context for this batch
                ctx: Ctx = {
                    **batch_item,
                    'start_time': datetime.utcnow().isoformat(),
                    'command': 'batch',
                    'batch_number': i
                }
                
                # Run pipeline for this batch
                result = await file_processing_pipeline(ctx)
                
                if result.get('errors'):
                    print(f"❌ Batch {i} failed:")
                    for error in result['errors']:
                        print(f"  - {error['message']}")
                else:
                    report = result.get('report', {})
                    summary = report.get('processing_summary', {})
                    print(f"✅ Batch {i} completed: {summary.get('successful', 0)} files processed")
            
            print(f"\n🎉 All {len(config['batches'])} batches completed!")
            return 0
            
        except Exception as e:
            print(f"❌ Batch processing failed: {e}")
            return 1
    
    result = asyncio.run(run_batch())
    exit(result)

@cli.command()
@click.option('--input-dir', '-i', required=True, type=click.Path(exists=True))
def analyze(input_dir: str):
    """Analyze directory structure and file statistics."""
    
    async def run_analysis():
        # Simple analysis function
        async def analyze_directory(ctx: Ctx) -> Ctx:
            input_path = Path(ctx.get('input_dir'))
            
            # Collect statistics
            stats = {
                'total_files': 0,
                'total_size': 0,
                'file_types': {},
                'largest_file': None,
                'smallest_file': None
            }
            
            for file_path in input_path.rglob('*'):
                if file_path.is_file():
                    stats['total_files'] += 1
                    size = file_path.stat().st_size
                    stats['total_size'] += size
                    
                    # Track file types
                    ext = file_path.suffix.lower() or 'no_extension'
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                    
                    # Track largest/smallest
                    if not stats['largest_file'] or size > stats['largest_file']['size']:
                        stats['largest_file'] = {'path': str(file_path), 'size': size}
                    
                    if not stats['smallest_file'] or size < stats['smallest_file']['size']:
                        stats['smallest_file'] = {'path': str(file_path), 'size': size}
            
            return {**ctx, 'analysis': stats}
        
        # Run analysis
        ctx: Ctx = {'input_dir': input_dir}
        result = await analyze_directory(ctx)
        
        # Display results
        analysis = result['analysis']
        print(f"📊 Directory Analysis: {input_dir}")
        print("-" * 50)
        print(f"📄 Total files: {analysis['total_files']}")
        print(f"💾 Total size: {analysis['total_size']:,} bytes")
        print(f"📁 File types:")
        
        for ext, count in sorted(analysis['file_types'].items()):
            print(f"  {ext}: {count} files")
        
        if analysis['largest_file']:
            print(f"📈 Largest file: {analysis['largest_file']['path']} ({analysis['largest_file']['size']:,} bytes)")
        
        if analysis['smallest_file']:
            print(f"📉 Smallest file: {analysis['smallest_file']['path']} ({analysis['smallest_file']['size']:,} bytes)")
    
    asyncio.run(run_analysis())

@cli.command()
def demo():
    """Run a demonstration with sample data."""
    
    async def run_demo():
        print("🎭 ModuLink CLI Demo")
        print("=" * 50)
        
        # Create temporary demo directory structure
        from tempfile import TemporaryDirectory
        
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            
            # Create demo input directory and files
            input_dir.mkdir()
            
            # Create sample files
            sample_files = [
                ("sample1.txt", "Hello ModuLink!\nThis is a sample file.\nLine 3\nLine 4"),
                ("sample2.txt", "Another sample file\nWith different content\nAnd more lines\nLine 4\nLine 5"),
                ("sample3.txt", "Short file"),
                ("readme.md", "# Demo\nThis is a markdown file\nNot processed by default pattern")
            ]
            
            for filename, content in sample_files:
                (input_dir / filename).write_text(content)
            
            print(f"📁 Created demo files in: {input_dir}")
            
            # Create context and run pipeline
            ctx: Ctx = {
                'input_dir': str(input_dir),
                'output_dir': str(output_dir),
                'file_pattern': '*.txt',
                'start_time': datetime.utcnow().isoformat(),
                'command': 'demo'
            }
            
            print("🚀 Running processing pipeline...")
            result = await file_processing_pipeline(ctx)
            
            if result.get('errors'):
                print("❌ Demo failed:")
                for error in result['errors']:
                    print(f"  - {error['message']}")
            else:
                print("✅ Demo completed successfully!")
                
                # Show results
                report = result.get('report', {})
                summary = report.get('processing_summary', {})
                
                print(f"\n📊 Demo Results:")
                print(f"  Files processed: {summary.get('successful', 0)}")
                print(f"  Files failed: {summary.get('failed', 0)}")
                print(f"  Output directory: {output_dir}")
                
                # List output files
                if output_dir.exists():
                    print(f"\n📄 Generated files:")
                    for output_file in output_dir.iterdir():
                        print(f"  - {output_file.name}")
    
    asyncio.run(run_demo())

if __name__ == '__main__':
    cli()
