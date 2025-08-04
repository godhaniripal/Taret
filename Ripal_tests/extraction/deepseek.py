from openai import OpenAI
import time
from datetime import datetime

# Available models
models = {
    "1": ("deepseek/deepseek-chat-v3-0324:free", "deepseek"),
    "2": ("qwen/qwen3-235b-a22b:free", "qwen3"),
    "3": ("meta-llama/llama-3.1-405b-instruct:free", "llama"),
    "4": ("deepseek/deepseek-r1-0528-qwen3-8b:free", "deepseek_r1_qwen3"),
    "5": ("deepseek/deepseek-r1-0528:free", "deepseek_r1"),
    "6": ("qwen/qwen3-coder:free", "qwen_coder"),
    "7": ("qwen/qwen3-235b-a22b:free", "qwen3_235b")
}

# Display model options
print("Available models:")
for key, (model_name, short_name) in models.items():
    print(f"{key}: {model_name}")

# Get user choice
choice = input("\nSelect a model (1-6): ").strip()

if choice not in models:
    print("Invalid choice. Using default model.")
    choice = "1"

selected_model, model_short_name = models[choice]

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

print(f"\nSending request to {selected_model}...\n")

# Start the timer
start_time = time.time()

# Make the API call

# Read the GSAP extraction output
with open("gsap_main.txt", "r", encoding="utf-8") as f:
    gsap_content = f.read()

# Prompt to clean the document
prompt = (
    "You are a technical documentation processor specialized in creating clean, structured documentation for RAG systems.\n\n"
    
    "TASK: Transform the raw GSAP ScrollTrigger documentation into a clean, well-structured format while preserving ALL technical content.\n\n"
    
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
    "# GSAP ScrollTrigger Documentation\n\n"
    
    "## Quick Start\n"
    "### Installation\n"
    "```javascript\n"
    "gsap.registerPlugin(ScrollTrigger);\n"
    "```\n\n"
    
    "### Basic Usage\n"
    "```javascript\n"
    "gsap.to('.box', {\n"
    "  scrollTrigger: '.box',\n"
    "  x: 500\n"
    "});\n"
    "```\n\n"
    
    "## Configuration Options\n"
    "| Property | Type | Description | Example |\n"
    "|----------|------|-------------|----------|\n"
    "| trigger | String/Element | Element that triggers the animation | '.my-element' |\n\n"
    
    "## Methods\n"
    "### ScrollTrigger.create()\n"
    "Creates a new ScrollTrigger instance.\n\n"
    
    "**Parameters:**\n"
    "- config (Object): Configuration options\n\n"
    
    "**Example:**\n"
    "```javascript\n"
    "ScrollTrigger.create({\n"
    "  trigger: '.element',\n"
    "  start: 'top center'\n"
    "});\n"
    "```\n"
    "```\n\n"
    
    "FORMATTING REQUIREMENTS:\n"
    "📝 Use clean markdown with proper heading hierarchy (# ## ### ####)\n"
    "📝 Format all code blocks with ```javascript syntax highlighting\n"
    "📝 Use tables for configuration options and parameters\n"
    "📝 Organize content logically: Quick Start → Examples → Configuration → Methods → Properties\n"
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

completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "<YOUR_SITE_URL>",
        "X-Title": "<YOUR_SITE_NAME>",
    },
    extra_body={},
    model=selected_model,
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

# Calculate the elapsed time
end_time = time.time()
response_time = end_time - start_time

# Generate filename with current date and time
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"refined_{model_short_name}_{current_time}.txt"

# Save the refined output to a new file
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(completion.choices[0].message.content)

print(f"\n" + "-"*50 + f"\nREFINED OUTPUT SAVED TO {output_filename}\n" + "-"*50)

# Print timing information
print("\n" + "-"*50)
print(f"Model: {selected_model}")
print(f"Response time: {response_time:.2f} seconds ({response_time*1000:.0f} ms)")
print(f"Tokens in response: {len(completion.choices[0].message.content.split())} (approximate)")
print("-"*50)

# Available models for reference:
# deepseek/deepseek-chat-v3-0324:free
# qwen/qwen3-235b-a22b:free  
# meta-llama/llama-3.1-405b-instruct:free
# deepseek/deepseek-r1-0528-qwen3-8b:free
# deepseek/deepseek-r1-0528:free
# qwen/qwen3-coder:free
