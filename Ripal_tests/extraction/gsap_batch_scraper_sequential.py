import asyncio
from crawl4ai import AsyncWebCrawler
import time
from datetime import datetime
import re
import os

# Create output directory if it doesn't exist
output_dir = "Gsap_Docs"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"📁 Created directory: {output_dir}")

# GSAP documentation URLs to scrape
urls = [
    "https://gsap.com/docs/v3/GSAP/",
    "https://gsap.com/docs/v3/GSAP/gsap.effects",
    "https://gsap.com/docs/v3/GSAP/gsap.globalTimeline",
    "https://gsap.com/docs/v3/GSAP/gsap.ticker",
    "https://gsap.com/docs/v3/GSAP/gsap.utils",
    "https://gsap.com/docs/v3/GSAP/gsap.version",
    "https://gsap.com/docs/v3/GSAP/gsap.config()",
    "https://gsap.com/docs/v3/GSAP/gsap.context()",
    "https://gsap.com/docs/v3/GSAP/gsap.defaults()",
    "https://gsap.com/docs/v3/GSAP/gsap.delayedCall()"
    
]

def extract_topic_name(url):
    """Extract topic name from GSAP documentation URL"""
    # Remove the base URL and get the last part
    path = url.replace("https://gsap.com/docs/v3/GSAP/", "")
    
    # Handle special cases
    if path == "" or path == "/":
        return "main"
    
    # Remove parentheses and clean up
    topic = path.replace("()", "").replace("/", "_")
    
    # Handle gsap.* naming
    if topic.startswith("gsap."):
        topic = topic.replace("gsap.", "gsap_")
    
    return topic

async def scrape_gsap_docs():
    """Scrape GSAP documentation from multiple URLs"""
    
    print("="*60)
    print("🚀 GSAP Documentation Batch Scraper")
    print("="*60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total URLs to scrape: {len(urls)}")
    print("="*60)
    
    results = {
        "successful": [],
        "failed": [],
        "empty": []
    }
    
    async with AsyncWebCrawler(
        # Disable session to avoid connection issues
        use_session=False,
        # Add custom headers
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        # Increased timeout settings
        request_timeout=60,
        # Browser settings
        browser_type="chromium",
        # Additional crawler configs
        verbose=True,
        # Disable some features that might cause issues
        screenshot=False,
        bypass_cache=True
    ) as crawler:
        
        for i, url in enumerate(urls, 1):
            topic_name = extract_topic_name(url)
            filename = os.path.join(output_dir, f"gsap_{topic_name}.txt")
            
            print(f"\n[{i}/{len(urls)}] 🔄 Processing: {topic_name}")
            print(f"📍 URL: {url}")
            print(f"💾 File: {filename}")
            
            try:
                # Start timer for this URL
                start_time = time.time()
                
                # Scrape the content with simplified approach
                result = await crawler.arun(
                    url=url,
                    # Simplified approach - remove complex selectors that might cause issues
                    excluded_tags=['nav', 'footer', 'header', 'aside'],
                    # No specific CSS selector - let it get everything
                    # css_selector="main, article, .content, .documentation, .docs-content",
                    # Remove wait_for to avoid timing issues
                    # wait_for="css:h1, css:.content, css:main",
                    # Keep it simple
                    only_text=False,
                    # Add some crawl4ai specific settings
                    remove_overlay_elements=True,
                )
                
                # Calculate processing time
                process_time = time.time() - start_time
                
                # Check if content was extracted successfully
                if not result.markdown or len(result.markdown.strip()) < 100:
                    print(f"⚠️  Warning: Content seems empty or too short")
                    results["empty"].append({"url": url, "topic": topic_name})
                    continue
                
                # Prepare content with metadata
                content = f"""# GSAP Documentation: {topic_name}
                
**URL:** {url}
**Scraped:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Content Length:** {len(result.markdown)} characters
**Processing Time:** {process_time:.2f} seconds

---

{result.markdown}
"""
                
                # Save to file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                
                print(f"✅ Success: {len(result.markdown)} chars in {process_time:.2f}s")
                results["successful"].append({
                    "url": url, 
                    "topic": topic_name, 
                    "filename": filename,
                    "size": len(result.markdown),
                    "time": process_time
                })
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                results["failed"].append({"url": url, "topic": topic_name, "error": str(e)})
            
            # Be respectful - add delay between requests
            if i < len(urls):
                print("⏳ Waiting 2 seconds before next request...")
                await asyncio.sleep(2)
    
    # Generate summary report
    await generate_summary_report(results)
    
    return results

async def generate_summary_report(results):
    """Generate a summary report of the scraping session"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = os.path.join(output_dir, f"gsap_scraping_report_{timestamp}.txt")
    
    report = f"""# GSAP Documentation Scraping Report
    
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total URLs:** {len(urls)}
**Successful:** {len(results['successful'])}
**Failed:** {len(results['failed'])}
**Empty/Warning:** {len(results['empty'])}

## ✅ Successfully Scraped ({len(results['successful'])})
"""
    
    for item in results["successful"]:
        report += f"- {item['topic']} ({item['size']} chars, {item['time']:.2f}s)\n"
    
    if results["failed"]:
        report += f"\n## ❌ Failed to Scrape ({len(results['failed'])})\n"
        for item in results["failed"]:
            report += f"- {item['topic']}: {item['error']}\n"
    
    if results["empty"]:
        report += f"\n## ⚠️ Empty or Suspicious Content ({len(results['empty'])})\n"
        for item in results["empty"]:
            report += f"- {item['topic']}\n"
    
    report += f"\n## 📁 Generated Files\n"
    for item in results["successful"]:
        report += f"- {item['filename']}\n"
    
    report += f"\n## 🔗 Original URLs\n"
    for i, url in enumerate(urls, 1):
        status = "✅" if any(item["url"] == url for item in results["successful"]) else "❌"
        report += f"{i}. {status} {url}\n"
    
    # Save report
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📋 Summary report saved: {report_filename}")
    print(f"📁 All files saved in: {output_dir}/")

def print_final_summary(results):
    """Print final summary to console"""
    print("\n" + "="*60)
    print("📊 SCRAPING COMPLETE - SUMMARY")
    print("="*60)
    print(f"✅ Successful: {len(results['successful'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⚠️  Empty/Warning: {len(results['empty'])}")
    print(f"📁 Files generated: {len(results['successful'])} + 1 report")
    print("="*60)
    
    if results["successful"]:
        total_size = sum(item['size'] for item in results['successful'])
        avg_time = sum(item['time'] for item in results['successful']) / len(results['successful'])
        print(f"📈 Total content: {total_size:,} characters")
        print(f"⏱️  Average time per URL: {avg_time:.2f} seconds")
    
    if results["failed"]:
        print(f"\n❌ Failed URLs:")
        for item in results["failed"]:
            print(f"   - {item['topic']}")

async def main():
    """Main function to run the scraper"""
    try:
        results = await scrape_gsap_docs()
        print_final_summary(results)
        
        print(f"\n🎉 All done! Check your files in the {output_dir}/ directory.")
        print(f"💡 Tip: Use these files with your LLM processing script for RAG!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
