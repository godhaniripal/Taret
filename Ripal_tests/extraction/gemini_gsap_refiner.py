import asyncio
import google.generativeai as genai
import time
from datetime import datetime
import os

# Create output directory if it doesn't exist
output_dir = "Gsap_Docs_refined"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"📁 Created directory: {output_dir}")

# Input file
input_file = "gsap_main.txt"

# Available Gemini models
gemini_models = {
    "1": ("gemini-1.5-flash", "gemini_flash"),
    "2": ("gemini-1.5-pro", "gemini_pro"),
    "3": ("gemini-1.5-flash-latest", "gemini_flash_latest"),
    "4": ("gemini-pro-vision", "gemini_pro_vision"),
    "5": ("gemini-1.0-pro", "gemini_1_pro"),
    "6": ("gemini-2.5-pro", "gemini_2_pro"),
    "7": ("gemini-2.0-flash", "gemini_2_flash")
}

def get_refined_prompt(gsap_content):
    """Generate the refined prompt for Gemini processing"""
    return f"""You are a technical documentation processor specialized in creating clean, structured documentation for RAG systems.

TASK: Transform the raw GSAP documentation into a clean, well-structured format while preserving ALL technical content.

CRITICAL PRESERVATION REQUIREMENTS:
✅ PRESERVE ALL CODE EXAMPLES - Every single JavaScript code block must remain intact and functional
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

OUTPUT STRUCTURE EXAMPLE:
```markdown
# GSAP Core Documentation

## Quick Start
### Installation
```javascript
npm install gsap
import {{ gsap }} from 'gsap'
```

### Basic Usage
```javascript
gsap.to('.box', {{
  rotation: 27,
  x: 100,
  duration: 1
}});
```

## Core Concepts
### What's a Tween?
A Tween is what does all the animation work...

### What's a Timeline?
A Timeline is a container for Tweens...

## Methods
### gsap.to()
Description and usage...

**Parameters:**
- targets: Elements to animate
- vars: Animation properties

**Example:**
```javascript
gsap.to('.element', {{ x: 100 }});
```
```

FORMATTING REQUIREMENTS:
📝 Use clean markdown with proper heading hierarchy (# ## ### ####)
📝 Format all code blocks with ```javascript syntax highlighting
📝 Use tables for configuration options and parameters
📝 Organize content logically: Quick Start → Core Concepts → Methods → Properties
📝 Ensure all technical examples are complete and runnable
📝 Use bullet points and numbered lists for clarity
📝 Bold important terms and concepts

QUALITY ASSURANCE:
🔍 Every code example must be syntactically correct
🔍 All method signatures must include parameter types and descriptions
🔍 Configuration tables must be complete with all available options
🔍 No technical information should be summarized or abbreviated
🔍 Maintain original technical accuracy and completeness

Remember: This documentation will be used in a RAG system where developers need complete, accurate information. Missing details could lead to implementation errors.

DOCUMENT TO PROCESS:
{"="*50}
{gsap_content}"""

async def process_with_gemini_model(model_name, model_short_name, gsap_content, api_key):
    """Process content with a specific Gemini model"""
    
    print(f"🔄 Starting {model_name}")
    
    try:
        start_time = time.time()
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Create model instance
        model = genai.GenerativeModel(model_name)
        
        # Generate prompt
        prompt = get_refined_prompt(gsap_content)
        
        # Generate content
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent technical documentation
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,  # Increase for comprehensive output
            }
        )
        
        process_time = time.time() - start_time
        
        # Get response text
        response_text = response.text
        
        # Generate filename
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(output_dir, f"refined_{model_short_name}_{current_time}.txt")
        
        # Add metadata header
        content_with_metadata = f"""# GSAP Documentation - Refined by {model_name}

**Model:** {model_name}
**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Processing Time:** {process_time:.2f} seconds
**Content Length:** {len(response_text)} characters

---

{response_text}
"""
        
        # Save output
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(content_with_metadata)
        
        response_length = len(response_text)
        word_count = len(response_text.split())
        
        print(f"✅ {model_name}: {response_length} chars, {word_count} words in {process_time:.2f}s")
        
        return {
            "status": "success",
            "model": model_name,
            "model_short_name": model_short_name,
            "filename": output_filename,
            "response_length": response_length,
            "word_count": word_count,
            "process_time": process_time,
            "content": response_text
        }
        
    except Exception as e:
        print(f"❌ {model_name}: {str(e)[:100]}...")
        return {
            "status": "failed",
            "model": model_name,
            "model_short_name": model_short_name,
            "error": str(e)
        }

async def main():
    """Main function"""
    try:
        print("🤖 GSAP Gemini Refiner Tool")
        print("This will refine GSAP documentation using Google Gemini models.\n")
        
        # Get Gemini API key
        api_key = input("🔑 Enter your Gemini API key: ").strip()
        if not api_key:
            print("❌ Error: Gemini API key is required!")
            return
        
        # Display available models
        print("\nAvailable Gemini models:")
        for key, (model_name, short_name) in gemini_models.items():
            print(f"{key}: {model_name}")
        
        model_choice = input("\nSelect a model (1-5): ").strip()
        if model_choice not in gemini_models:
            print("❌ Invalid model selection!")
            return
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"❌ Error: Input file '{input_file}' not found!")
            print(f"Please make sure you have run the GSAP scraper first.")
            return
        
        # Read content
        with open(input_file, "r", encoding="utf-8") as f:
            gsap_content = f.read()
        
        print(f"📖 Loaded content: {len(gsap_content)} characters")
        
        # Process with selected model
        model_name, model_short_name = gemini_models[model_choice]
        print(f"\n🚀 Processing with {model_name}...")
        
        result = await process_with_gemini_model(model_name, model_short_name, gsap_content, api_key)
        
        if result["status"] == "success":
            print(f"\n✅ Processing complete!")
            print(f"📁 Output: {result['filename']}")
            print(f"📊 Stats: {result['response_length']:,} chars, {result['word_count']:,} words")
            print(f"⏱️  Time: {result['process_time']:.2f} seconds")
        else:
            print(f"\n❌ Processing failed: {result['error']}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
