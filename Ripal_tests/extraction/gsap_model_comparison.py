import asyncio
from openai import OpenAI
import time
from datetime import datetime
import os

# Create output directory if it doesn't exist
output_dir = "Gsap_Docs_refined"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"📁 Created directory: {output_dir}")

# Available models for parallel processing
models = {
    "deepseek": ("deepseek/deepseek-chat-v3-0324:free", "deepseek"),
    "qwen3": ("qwen/qwen3-235b-a22b:free", "qwen3"),
    "llama": ("meta-llama/llama-3.1-405b-instruct:free", "llama"),
    "deepseek_r1_qwen3": ("deepseek/deepseek-r1-0528-qwen3-8b:free", "deepseek_r1_qwen3"),
    "deepseek_r1": ("deepseek/deepseek-r1-0528:free", "deepseek_r1"),
    "qwen_coder": ("qwen/qwen3-coder:free", "qwen_coder")
}

# Input file
input_file = "Gsap_Docs/gsap_main.txt"

def get_refined_prompt(gsap_content):
    """Generate the refined prompt for LLM processing"""
    return (
        "You are a technical documentation processor specialized in creating clean, structured documentation for RAG systems.\n\n"
        
        "TASK: Transform the raw GSAP documentation into a clean, well-structured format while preserving ALL technical content.\n\n"
        
        "CRITICAL PRESERVATION REQUIREMENTS:\n"
        "✅ PRESERVE ALL CODE EXAMPLES - Every single JavaScript code block must remain intact and functional\n"
        "✅ PRESERVE ALL API DOCUMENTATION - Method descriptions, parameter lists, return values\n"
        "✅ PRESERVE ALL CONFIGURATION OPTIONS - Property descriptions, usage examples, default values\n"
        "✅ PRESERVE ALL FEATURE DESCRIPTIONS - Functionality explanations, use cases, benefits\n"
        "✅ PRESERVE ALL TECHNICAL DETAILS - Performance notes, browser compatibility, limitations\n"
        "✅ PRESERVE ALL EXAMPLES - Simple, advanced, and standalone examples with full context\n\n"
        
        "WHAT TO REMOVE:\n"
        "❌ Navigation menus, breadcrumbs, and site headers/footers\n"
        "❌ Login/account UI elements and user interface controls\n"
        "❌ Social media links and external promotional content\n"
        "❌ Advertisement banners and marketing copy\n"
        "❌ Duplicate navigation elements and redundant menu items\n"
        "❌ Page metadata and tracking elements\n\n"
        
        "OUTPUT STRUCTURE EXAMPLE:\n"
        "```markdown\n"
        "# GSAP Core Documentation\n\n"
        
        "## Quick Start\n"
        "### Installation\n"
        "```javascript\n"
        "npm install gsap\n"
        "import { gsap } from 'gsap'\n"
        "```\n\n"
        
        "### Basic Usage\n"
        "```javascript\n"
        "gsap.to('.box', {\n"
        "  rotation: 27,\n"
        "  x: 100,\n"
        "  duration: 1\n"
        "});\n"
        "```\n\n"
        
        "## Core Concepts\n"
        "### What's a Tween?\n"
        "A Tween is what does all the animation work...\n\n"
        
        "### What's a Timeline?\n"
        "A Timeline is a container for Tweens...\n\n"
        
        "## Methods\n"
        "### gsap.to()\n"
        "Description and usage...\n\n"
        
        "**Parameters:**\n"
        "- targets: Elements to animate\n"
        "- vars: Animation properties\n\n"
        
        "**Example:**\n"
        "```javascript\n"
        "gsap.to('.element', { x: 100 });\n"
        "```\n"
        "```\n\n"
        
        "FORMATTING REQUIREMENTS:\n"
        "📝 Use clean markdown with proper heading hierarchy (# ## ### ####)\n"
        "📝 Format all code blocks with ```javascript syntax highlighting\n"
        "📝 Use tables for configuration options and parameters\n"
        "📝 Organize content logically: Quick Start → Core Concepts → Methods → Properties\n"
        "📝 Ensure all technical examples are complete and runnable\n"
        "📝 Use bullet points and numbered lists for clarity\n"
        "📝 Bold important terms and concepts\n\n"
        
        "QUALITY ASSURANCE:\n"
        "🔍 Every code example must be syntactically correct\n"
        "🔍 All method signatures must include parameter types and descriptions\n"
        "🔍 Configuration tables must be complete with all available options\n"
        "🔍 No technical information should be summarized or abbreviated\n"
        "🔍 Maintain original technical accuracy and completeness\n\n"
        
        "Remember: This documentation will be used in a RAG system where developers need complete, accurate information. Missing details could lead to implementation errors.\n\n"
        
        "DOCUMENT TO PROCESS:\n" + "="*50 + "\n" + gsap_content
    )

async def process_with_model(model_key, model_info, gsap_content, semaphore):
    """Process content with a specific model"""
    async with semaphore:  # Limit concurrent requests
        model_url, model_short_name = model_info
        
        print(f"🔄 Starting {model_key}: {model_url}")
        
        try:
            start_time = time.time()
            
            # Create OpenAI client
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key="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",
            )
            
            # Generate prompt
            prompt = get_refined_prompt(gsap_content)
            
            # Make API call
            completion = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "<YOUR_SITE_URL>",
                    "X-Title": "<YOUR_SITE_NAME>",
                },
                extra_body={},
                model=model_url,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            process_time = time.time() - start_time
            
            # Generate filename
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = os.path.join(output_dir, f"refined_{model_short_name}_{current_time}.txt")
            
            # Save output
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(completion.choices[0].message.content)
            
            response_length = len(completion.choices[0].message.content)
            word_count = len(completion.choices[0].message.content.split())
            
            print(f"✅ {model_key}: {response_length} chars, {word_count} words in {process_time:.2f}s")
            
            return {
                "status": "success",
                "model": model_key,
                "model_url": model_url,
                "filename": output_filename,
                "response_length": response_length,
                "word_count": word_count,
                "process_time": process_time,
                "content": completion.choices[0].message.content
            }
            
        except Exception as e:
            print(f"❌ {model_key}: {str(e)[:100]}...")
            return {
                "status": "failed",
                "model": model_key,
                "model_url": model_url,
                "error": str(e)
            }

async def parallel_model_comparison():
    """Process the same content with all models in parallel"""
    
    print("="*70)
    print("🚀 GSAP Multi-Model Parallel Comparison")
    print("="*70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total models: {len(models)}")
    print(f"📁 Input file: {input_file}")
    print(f"💾 Output directory: {output_dir}")
    print("="*70)
    
    # Read input file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            gsap_content = f.read()
        print(f"📖 Loaded content: {len(gsap_content)} characters")
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found!")
        return
    
    # Create semaphore to limit concurrent requests (be respectful to API)
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
    
    # Create tasks for all models
    tasks = [
        process_with_model(model_key, model_info, gsap_content, semaphore)
        for model_key, model_info in models.items()
    ]
    
    # Start timer
    total_start_time = time.time()
    
    print(f"\n🚀 Starting parallel processing with {len(models)} models...")
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - total_start_time
    
    # Process results
    successful_results = []
    failed_results = []
    
    for result in results:
        if isinstance(result, Exception):
            print(f"❌ Unexpected error: {result}")
            continue
            
        if result["status"] == "success":
            successful_results.append(result)
        elif result["status"] == "failed":
            failed_results.append(result)
    
    # Generate comparison report
    await generate_comparison_report(successful_results, failed_results, total_time)
    
    return successful_results, failed_results, total_time

async def generate_comparison_report(successful_results, failed_results, total_time):
    """Generate detailed comparison report"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = os.path.join(output_dir, f"model_comparison_report_{timestamp}.txt")
    
    successful_count = len(successful_results)
    failed_count = len(failed_results)
    
    # Sort by response length for comparison
    successful_results.sort(key=lambda x: x['response_length'], reverse=True)
    
    report = f"""# GSAP Multi-Model Comparison Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Input File:** {input_file}
**Total Models:** {len(models)}
**Successful:** {successful_count}
**Failed:** {failed_count}
**Total Processing Time:** {total_time:.2f} seconds

## 📊 Performance Summary

| Model | Status | Response Length | Word Count | Processing Time | Output File |
|-------|--------|----------------|------------|----------------|-------------|
"""
    
    # Add successful results to table
    for result in successful_results:
        report += f"| {result['model']} | ✅ Success | {result['response_length']:,} chars | {result['word_count']:,} words | {result['process_time']:.2f}s | {os.path.basename(result['filename'])} |\n"
    
    # Add failed results to table
    for result in failed_results:
        report += f"| {result['model']} | ❌ Failed | - | - | - | Error occurred |\n"
    
    if successful_results:
        report += f"\n## 🏆 Performance Rankings\n\n"
        report += f"### By Response Length (Most Comprehensive)\n"
        for i, result in enumerate(successful_results, 1):
            report += f"{i}. **{result['model']}**: {result['response_length']:,} characters\n"
        
        report += f"\n### By Processing Speed (Fastest)\n"
        speed_sorted = sorted(successful_results, key=lambda x: x['process_time'])
        for i, result in enumerate(speed_sorted, 1):
            report += f"{i}. **{result['model']}**: {result['process_time']:.2f} seconds\n"
        
        # Calculate averages
        avg_length = sum(r['response_length'] for r in successful_results) / successful_count
        avg_words = sum(r['word_count'] for r in successful_results) / successful_count
        avg_time = sum(r['process_time'] for r in successful_results) / successful_count
        
        report += f"\n## 📈 Averages\n"
        report += f"- **Average Response Length:** {avg_length:,.0f} characters\n"
        report += f"- **Average Word Count:** {avg_words:,.0f} words\n"
        report += f"- **Average Processing Time:** {avg_time:.2f} seconds\n"
        
        # Find best and worst
        best_comprehensive = successful_results[0]  # Already sorted by length
        fastest = min(successful_results, key=lambda x: x['process_time'])
        
        report += f"\n## 🎯 Recommendations\n"
        report += f"- **Most Comprehensive:** {best_comprehensive['model']} ({best_comprehensive['response_length']:,} chars)\n"
        report += f"- **Fastest Processing:** {fastest['model']} ({fastest['process_time']:.2f}s)\n"
    
    if failed_results:
        report += f"\n## ❌ Failed Models ({failed_count})\n"
        for result in failed_results:
            report += f"- **{result['model']}**: {result['error'][:100]}...\n"
    
    report += f"\n## 📁 Generated Files\n"
    for result in successful_results:
        report += f"- {result['filename']}\n"
    
    report += f"\n## 💡 Next Steps\n"
    report += f"1. Review each output file to compare quality\n"
    report += f"2. Check for technical accuracy and completeness\n"
    report += f"3. Evaluate markdown formatting and structure\n"
    report += f"4. Choose the best model for your RAG system\n"
    report += f"5. Consider using the most comprehensive result as your base\n"
    
    # Save report
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📋 Comparison report saved: {report_filename}")

def print_final_summary(successful_results, failed_results, total_time):
    """Print final summary to console"""
    
    print("\n" + "="*70)
    print("📊 MULTI-MODEL COMPARISON COMPLETE")
    print("="*70)
    print(f"✅ Successful models: {len(successful_results)}")
    print(f"❌ Failed models: {len(failed_results)}")
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"🚀 Speed improvement: ~{len(models) * 30 / total_time:.1f}x faster than sequential")
    print("="*70)
    
    if successful_results:
        print("\n🏆 TOP PERFORMERS:")
        
        # Sort by length for display
        by_length = sorted(successful_results, key=lambda x: x['response_length'], reverse=True)
        print(f"📄 Most Comprehensive: {by_length[0]['model']} ({by_length[0]['response_length']:,} chars)")
        
        # Sort by speed
        by_speed = sorted(successful_results, key=lambda x: x['process_time'])
        print(f"⚡ Fastest: {by_speed[0]['model']} ({by_speed[0]['process_time']:.2f}s)")
        
        print(f"\n📁 Check {output_dir}/ for all refined outputs")
        print(f"📋 Review the comparison report to choose the best model!")

async def main():
    """Main function"""
    try:
        print("🧪 GSAP Multi-Model Comparison Tool")
        print("This will process the same GSAP content with all available models")
        print("to help you compare their outputs and choose the best one for RAG.\n")
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"❌ Error: Input file '{input_file}' not found!")
            print(f"Please make sure you have run the GSAP scraper first.")
            return
        
        # Start processing
        successful_results, failed_results, total_time = await parallel_model_comparison()
        print_final_summary(successful_results, failed_results, total_time)
        
        print(f"\n🎉 Comparison complete!")
        print(f"💡 Review all outputs to determine which model works best for your RAG system")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
