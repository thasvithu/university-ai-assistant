"""
Quick Setup and Test Script
Verifies installation and runs basic tests
"""

import sys
from pathlib import Path

print("="*60)
print("🎓 University AI Assistant - Setup Verification")
print("="*60)

# Check Python version
print(f"\n✓ Python version: {sys.version}")

# Check required packages
print("\n📦 Checking dependencies...")

required_packages = [
    'groq',
    'openai',
    'sentence_transformers',
    'chromadb',
    'streamlit',
    'PyPDF2',
    'firecrawl',
    'dotenv'
]

missing = []
for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        print(f"  ✓ {package}")
    except ImportError:
        print(f"  ✗ {package} - MISSING")
        missing.append(package)

if missing:
    print(f"\n❌ Missing packages: {', '.join(missing)}")
    print("\nInstall with:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

# Check environment
print("\n🔑 Checking environment variables...")

from dotenv import load_dotenv
import os

load_dotenv()

env_vars = {
    'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
    'FIRECRAWL_API_KEY': os.getenv('FIRECRAWL_API_KEY'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
}

for key, value in env_vars.items():
    if value:
        print(f"  ✓ {key} is set")
    else:
        status = "⚠️" if key == "OPENAI_API_KEY" else "✗"
        print(f"  {status} {key} - NOT SET")

if not env_vars['GROQ_API_KEY']:
    print("\n❌ GROQ_API_KEY is required!")
    print("Add it to your .env file")
    sys.exit(1)

# Check data files
print("\n📁 Checking data files...")

data_files = {
    'Main website data': Path('data/raw/vau_scraped_latest.json'),
    'FTS website data': Path('data/raw/fts_scraped_latest.json'),
    'FTS handbook PDF': Path('data/raw/pdfs/FTS-DICT-HB-2022.pdf'),
    'Processed handbooks': Path('data/processed/handbooks_processed_latest.json')
}

for name, path in data_files.items():
    if path.exists():
        size = path.stat().st_size / 1024  # KB
        print(f"  ✓ {name} ({size:.1f} KB)")
    else:
        print(f"  ✗ {name} - NOT FOUND")

# Check ChromaDB
print("\n💾 Checking ChromaDB...")

chromadb_path = Path('data/chromadb')
if chromadb_path.exists():
    print(f"  ✓ ChromaDB directory exists")
    
    # Try to connect
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(chromadb_path))
        collections = client.list_collections()
        
        if collections:
            for coll in collections:
                count = coll.count()
                print(f"  ✓ Collection '{coll.name}': {count} documents")
        else:
            print(f"  ⚠️ No collections found - run build_knowledge_base.py")
    except Exception as e:
        print(f"  ⚠️ Could not connect to ChromaDB: {e}")
else:
    print(f"  ✗ ChromaDB not initialized")

# Summary
print("\n" + "="*60)
print("📊 SETUP STATUS")
print("="*60)

print("\n✅ Ready to run:")
print("  - streamlit run app/streamlit_app.py")

print("\n⏳ Need to run:")
if not data_files['FTS website data'].exists():
    print("  - python scripts/02_scrape_fts_website.py")
if not data_files['Processed handbooks'].exists():
    print("  - python scripts/03_process_pdfs.py")
if not chromadb_path.exists() or not collections:
    print("  - python scripts/04_build_knowledge_base.py")

print("\n" + "="*60)
print("✨ Setup verification complete!")
print("="*60)
