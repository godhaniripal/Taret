import asyncio
import os
import time
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

# Handle optional imports
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    print("⚠️  aiofiles not installed - using synchronous file operations")

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️  google-generativeai not installed - Gemini models disabled")

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️  openai not installed - OpenRouter models disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_refining.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    filename: str
    model_used: str
    success: bool
    output_file: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    content_length: int = 0

@dataclass
class ModelConfig:
    name: str
    short_name: str
    provider: str  # 'openrouter' or 'gemini'
    rate_limit_delay: float = 10.0

class AdvancedDocumentRefiner:
    def __init__(self, mode: str = "all"):
        """
        Initialize the document refiner
        Args:
            mode: "all" for all models, "gemini" for Gemini only, "openrouter" for OpenRouter only
        """
        self.mode = mode
        
        # Model configurations
        all_models = [
            ModelConfig("gemini-2.5-pro", "gemini_25_pro", "gemini", 8.0),  # Reduced delay
            ModelConfig("deepseek/deepseek-r1-0528-qwen3-8b:free", "deepseek_qwen3_8b", "openrouter", 8.0),
            ModelConfig("deepseek/deepseek-r1-0528:free", "deepseek_r1", "openrouter", 8.0),
            ModelConfig("meta-llama/llama-3.1-405b-instruct:free", "llama_405b", "openrouter", 8.0),
            ModelConfig("mistralai/mistral-small-3.1-24b-instruct:free", "mistral_small", "openrouter", 8.0),
        ]
        
        # Filter models based on mode
        if mode == "gemini":
            self.models = [m for m in all_models if m.provider == "gemini"]
        elif mode == "openrouter":
            self.models = [m for m in all_models if m.provider == "openrouter"]
        else:  # mode == "all"
            self.models = all_models
        
        # Configuration
        self.input_dir = "Barba_Docs"
        self.output_dir = "Barba_Docs_Refined"
        self.max_parallel = 5  # Increased for better throughput with 300 files
        self.openrouter_api_key = "add_your_openrouter_api_key_here"  # Set your OpenRouter API key
        
        # Initialize clients
        self.setup_clients()
        
        # Processing state
        self.results: List[ProcessingResult] = []
        self.current_model_index = 0
        self.semaphore = asyncio.Semaphore(self.max_parallel)
        
    def setup_clients(self):
        """Initialize AI clients"""
        if HAS_GEMINI:
            # Setup Gemini
            api_key = os.getenv('GEMINI_API_KEY', 'add_your_gemini_api_key_here') #dont add down add here only brooww
            if api_key != 'YOUR_GEMINI_API_KEY_HERE':
                genai.configure(api_key=api_key)
                logger.info("Gemini client configured")
            else:
                logger.warning("Gemini API key not set")
        
        if HAS_OPENAI:
            # Setup OpenRouter
            self.openrouter_client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.openrouter_api_key,
            )
            logger.info("OpenRouter client configured")
        
        # Filter models based on available clients
        available_models = []
        for model in self.models:
            if model.provider == "gemini" and HAS_GEMINI:
                available_models.append(model)
            elif model.provider == "openrouter" and HAS_OPENAI:
                available_models.append(model)
        
        self.models = available_models
        if not self.models:
            raise RuntimeError("No AI models available - install required dependencies")
        
    async def read_file_async(self, file_path: str) -> str:
        """Read file content asynchronously or synchronously"""
        if HAS_AIOFILES:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        else:
            # Fallback to synchronous reading
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    async def write_file_async(self, file_path: str, content: str):
        """Write file content asynchronously or synchronously"""
        if HAS_AIOFILES:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
        else:
            # Fallback to synchronous writing
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
    def get_next_model(self) -> ModelConfig:
        """Get next model in rotation"""
        model = self.models[self.current_model_index]
        self.current_model_index = (self.current_model_index + 1) % len(self.models)
        return model
        
    async def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Output directory ready: {self.output_dir}")
        
    def get_files_to_process(self) -> List[str]:
        """Get list of files to process"""
        if not os.path.exists(self.input_dir):
            logger.error(f"❌ Input directory not found: {self.input_dir}")
            return []
            
        all_files = [f for f in os.listdir(self.input_dir) 
                    if f.endswith('.txt') and not f.startswith('refined_')]
        
        # Filter out already processed files
        processed_files = set()
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f.startswith('refined_'):
                    # Extract original filename from refined filename
                    parts = f.split('_')
                    if len(parts) >= 3:
                        original = '_'.join(parts[2:]).replace('.txt', '')
                        original = original.rsplit('_', 1)[0] + '.txt'  # Remove timestamp
                        processed_files.add(original)
        
        remaining_files = [f for f in all_files if f not in processed_files]
        logger.info(f"Found {len(all_files)} total files, {len(remaining_files)} remaining to process")
        
        return remaining_files
        
    def get_refining_prompt(self) -> str:
        """Get the universal refining prompt"""
        return """You are a technical documentation processor specialized in creating clean, structured documentation for RAG systems.

IMPORTANT: Provide ONLY the refined documentation output. Do NOT include any thinking process, reasoning steps, analysis, or meta-commentary. Start directly with the refined content.

TASK: Transform the raw technical documentation into a clean, well-structured format while preserving ALL technical content.

CRITICAL PRESERVATION REQUIREMENTS:
✅ PRESERVE ALL CODE EXAMPLES - Every single code block must remain intact and functional
✅ PRESERVE ALL API DOCUMENTATION - Method descriptions, parameter lists, return values
✅ PRESERVE ALL CONFIGURATION OPTIONS - Property descriptions, usage examples, default values
✅ PRESERVE ALL FEATURE DESCRIPTIONS - Functionality explanations, use cases, benefits
✅ PRESERVE ALL TECHNICAL DETAILS - Performance notes, browser compatibility, limitations
✅ PRESERVE ALL EXAMPLES - Simple, advanced, and standalone examples with full context

WHAT TO REMOVE:
❌ Navigation menus, breadcrumbs, and site headers/footers
❌ Login/account UI elements and user interface controls
❌ Social media links and external promotional content
❌ Advertisement banners and marketing copy
❌ Duplicate navigation elements and redundant menu items
❌ Page metadata and tracking elements
❌ ALL MARKDOWN LINKS - Convert [link text](url) to just 'link text'
❌ Cross-references to other pages or external documentation
❌ 'See more' or 'Read further' type references
❌ Navigation hints like 'Next:', 'Previous:', 'Back to:'

FORMATTING REQUIREMENTS:
📝 Use clean markdown with proper heading hierarchy (# ## ### ####)
📝 Format code blocks with appropriate syntax highlighting
📝 Use tables for configuration options and parameters
📝 Organize content logically: Quick Start → Examples → Configuration → Methods → Properties
📝 Ensure all technical examples are complete and runnable
📝 Use bullet points and numbered lists for clarity
📝 Bold important terms and concepts
📝 REMOVE ALL LINKS: Convert [text](url) to just 'text' - no URLs should remain
📝 Replace cross-references with simple text mentions

QUALITY ASSURANCE:
🔍 Every code example must be syntactically correct
🔍 All method signatures must include parameter types and descriptions
🔍 Configuration tables must be complete with all available options
🔍 No technical information should be summarized or abbreviated
🔍 Maintain original technical accuracy and completeness
🔍 NO LINKS ALLOWED: All [text](url) must become plain 'text'
🔍 Remove any 'see more', 'read here', or reference phrases

Remember: This documentation will be used in a RAG system where developers need complete, accurate information. Missing details could lead to implementation errors.

DOCUMENT TO PROCESS:
""" + "="*50 + "\n"

    async def process_with_gemini(self, content: str, model_config: ModelConfig) -> str:
        """Process content with Gemini"""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            prompt = self.get_refining_prompt() + content
            
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                )
            )
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Gemini processing error: {str(e)}")
            
    async def process_with_openrouter(self, content: str, model_config: ModelConfig) -> str:
        """Process content with OpenRouter model"""
        try:
            prompt = self.get_refining_prompt() + content
            
            response = await self.openrouter_client.chat.completions.create(
                model=model_config.name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                extra_headers={
                    "HTTP-Referer": "https://localhost:3000",
                    "X-Title": "Advanced Document Refiner",
                },
                timeout=120.0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenRouter processing error: {str(e)}")
            
    async def process_single_file(self, filename: str) -> ProcessingResult:
        """Process a single file with error handling and retries"""
        async with self.semaphore:
            start_time = time.time()
            model_config = self.get_next_model()
            
            logger.info(f"Processing {filename} with {model_config.short_name}")
            
            try:
                # Read input file
                input_path = os.path.join(self.input_dir, filename)
                content = await self.read_file_async(input_path)
                    
                # Process with selected model
                if model_config.provider == "gemini":
                    refined_content = await self.process_with_gemini(content, model_config)
                else:
                    refined_content = await self.process_with_openrouter(content, model_config)
                
                # Generate output filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_name = os.path.splitext(filename)[0]
                output_filename = f"refined_{model_config.short_name}_{base_name}_{timestamp}.txt"
                output_path = os.path.join(self.output_dir, output_filename)
                
                # Save refined content
                await self.write_file_async(output_path, refined_content)
                
                processing_time = time.time() - start_time
                
                logger.info(f"SUCCESS: {filename} -> {output_filename} ({processing_time:.1f}s)")
                
                # Rate limiting delay
                await asyncio.sleep(model_config.rate_limit_delay)
                
                return ProcessingResult(
                    filename=filename,
                    model_used=model_config.short_name,
                    success=True,
                    output_file=output_filename,
                    processing_time=processing_time,
                    content_length=len(refined_content)
                )
                
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"FAILED processing {filename}: {str(e)}")
                
                return ProcessingResult(
                    filename=filename,
                    model_used=model_config.short_name,
                    success=False,
                    error=str(e),
                    processing_time=processing_time
                )
                
    async def generate_report(self):
        """Generate comprehensive processing report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(self.output_dir, f"batch_refining_report_{timestamp}.txt")
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        total_time = sum(r.processing_time for r in self.results)
        avg_time = total_time / len(self.results) if self.results else 0
        total_content = sum(r.content_length for r in successful)
        
        # Model usage statistics
        model_stats = {}
        for result in self.results:
            model = result.model_used
            if model not in model_stats:
                model_stats[model] = {'total': 0, 'successful': 0, 'failed': 0}
            model_stats[model]['total'] += 1
            if result.success:
                model_stats[model]['successful'] += 1
            else:
                model_stats[model]['failed'] += 1
        
        report = f"""# Advanced Batch Document Refining Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Files:** {len(self.results)}
**Successful:** {len(successful)}
**Failed:** {len(failed)}
**Success Rate:** {len(successful)/len(self.results)*100:.1f}%

## ⏱️ Performance Metrics
- **Total Processing Time:** {total_time:.1f} seconds ({total_time/60:.1f} minutes)
- **Average Time per File:** {avg_time:.1f} seconds
- **Total Content Generated:** {total_content:,} characters
- **Parallel Processing:** Up to {self.max_parallel} files simultaneously

## 📊 Model Performance
"""
        
        for model, stats in model_stats.items():
            success_rate = stats['successful'] / stats['total'] * 100 if stats['total'] > 0 else 0
            report += f"- **{model}:** {stats['successful']}/{stats['total']} ({success_rate:.1f}% success)\n"
        
        if successful:
            report += f"\n## ✅ Successfully Processed ({len(successful)})\n"
            for result in successful:
                report += f"- `{result.filename}` → `{result.output_file}` ({result.model_used}, {result.processing_time:.1f}s)\n"
        
        if failed:
            report += f"\n## ❌ Failed Processing ({len(failed)})\n"
            for result in failed:
                report += f"- `{result.filename}` ({result.model_used}): {result.error}\n"
        
        report += f"\n## 📁 Output Directory\n`{self.output_dir}/`\n"
        report += f"\n## 🚀 Next Steps\n"
        report += f"- All refined files are ready for RAG ingestion\n"
        report += f"- Consider running quality checks on failed files\n"
        report += f"- Files can be reprocessed individually if needed\n"
        
        await self.write_file_async(report_path, report)
            
        logger.info(f"Report saved: {report_path}")
        
    def print_progress_summary(self):
        """Print real-time progress summary"""
        successful = len([r for r in self.results if r.success])
        failed = len([r for r in self.results if not r.success])
        total = len(self.results)
        
        print("\n" + "="*60)
        print("📊 BATCH REFINING PROGRESS SUMMARY")
        print("="*60)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Total Processed: {total}")
        if total > 0:
            print(f"🎯 Success Rate: {successful/total*100:.1f}%")
        print("="*60)
        
    async def run_batch_processing(self):
        """Main batch processing function"""
        print("\n" + "="*70)
        print("🚀 ADVANCED BATCH DOCUMENT REFINER")
        print("="*70)
        print(f"📁 Input: {self.input_dir}/")
        print(f"📁 Output: {self.output_dir}/")
        print(f"🎯 Mode: {self.mode.upper()}")
        print(f"🤖 Models: {len(self.models)} ({'Gemini only' if self.mode == 'gemini' else 'OpenRouter only' if self.mode == 'openrouter' else 'mixed Gemini + OpenRouter'})")
        print(f"⚡ Parallel: {self.max_parallel} files simultaneously")
        print(f"⏱️  Rate Limit: 8 seconds between requests")
        print("="*70)
        
        # Setup
        await self.setup_directories()
        files_to_process = self.get_files_to_process()
        
        if not files_to_process:
            logger.info("No files to process - all done!")
            return
            
        total_files = len(files_to_process)
        estimated_time = (total_files * 12) / self.max_parallel  # More accurate estimate for large batches
        
        print(f"\n📊 Processing {total_files} files")
        print(f"⏱️  Estimated time: {estimated_time/60:.1f} minutes")
        if total_files > 100:
            print(f"🔥 Large batch detected! Optimized for {total_files} files")
        print(f"🎯 Starting parallel processing...\n")
        
        # Process files in batches
        tasks = []
        for filename in files_to_process:
            task = self.process_single_file(filename)
            tasks.append(task)
            
        # Execute with progress tracking
        start_time = time.time()
        
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            result = await task
            self.results.append(result)
            
            # Print progress
            elapsed = time.time() - start_time
            remaining = (total_files - i) * (elapsed / i) if i > 0 else 0
            
            status = "✅" if result.success else "❌"
            print(f"[{i:2d}/{total_files}] {status} {result.filename} "
                  f"({result.model_used}) - ETA: {remaining/60:.1f}m")
            
        # Final summary
        total_time = time.time() - start_time
        await self.generate_report()
        self.print_progress_summary()
        
        print(f"\n🎉 Batch processing complete!")
        print(f"⏱️  Total time: {total_time/60:.1f} minutes")
        print(f"📁 Check {self.output_dir}/ for refined files")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Advanced Batch Document Refiner for RAG Systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_refiner.py                    # Process with all models (default)
  python batch_refiner.py --geminionly       # Process with Gemini models only
  python batch_refiner.py --openrouteronly   # Process with OpenRouter models only

Note: Make sure to set your API keys in the code or environment variables.
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--geminionly', 
        action='store_true',
        help='Use only Gemini models for processing'
    )
    group.add_argument(
        '--openrouteronly', 
        action='store_true',
        help='Use only OpenRouter models for processing'
    )
    
    return parser.parse_args()

async def main():
    """Main function with argument parsing"""
    try:
        args = parse_arguments()
        
        # Determine processing mode
        if args.geminionly:
            mode = "gemini"
            print("🎯 Running in GEMINI ONLY mode")
        elif args.openrouteronly:
            mode = "openrouter"
            print("🎯 Running in OPENROUTER ONLY mode")
        else:
            mode = "all"
            print("🎯 Running in ALL MODELS mode")
        
        refiner = AdvancedDocumentRefiner(mode=mode)
        await refiner.run_batch_processing()
        
    except KeyboardInterrupt:
        logger.info("Batch processing interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
