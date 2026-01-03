# Vavuniya University AI Assistant 🎓

An intelligent chatbot for the University of Vavuniya built with RAG (Retrieval Augmented Generation) architecture, powered by Groq and ChromaDB.

## Features ✨

- 🤖 **Intelligent Q&A**: Ask questions about university programs, admissions, events, and more
- 📚 **Multi-Source Knowledge**: Combines data from university website, faculty sites, and handbooks
- 🎯 **Faculty Filtering**: Filter responses by specific faculties (FTS, FAS, FBS)
- 📖 **Source Citations**: Every answer includes clickable source references
- ⚡ **Fast Responses**: Powered by Groq's ultra-fast LLM inference
- 💎 **Premium UI**: Beautiful dark-themed interface with glassmorphism effects
- 🔄 **Automatic Fallback**: Uses OpenAI as backup if Groq is unavailable

## Tech Stack 🛠️

- **LLM**: Groq (llama-3.1-70b) + OpenAI (gpt-4o-mini) fallback
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector DB**: ChromaDB
- **UI**: Streamlit
- **Data Sources**: Firecrawl, PyPDF2

## Quick Start 🚀

### 1. Prerequisites

- Python 3.8+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Firecrawl API key (for scraping)
- Optional: OpenAI API key (for fallback)

### 2. Installation

```bash
# Clone the repository
cd university-ai-assistant

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
FIRECRAWL_API_KEY=your_firecrawl_key_here
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional
```

### 4. Build Knowledge Base

Run these scripts in order:

```bash
# 1. Scrape FTS faculty website
python scripts/02_scrape_fts_website.py

# 2. Process PDF handbooks
python scripts/03_process_pdfs.py

# 3. Build vector database
python scripts/04_build_knowledge_base.py
```

### 5. Run the App

```bash
streamlit run app/streamlit_app.py
```

The app will open at `http://localhost:8501`

## Project Structure 📁

```
university-ai-assistant/
├── app/
│   └── streamlit_app.py          # Streamlit UI
├── src/
│   ├── config.py                 # Configuration
│   ├── llm/
│   │   ├── api_manager.py        # LLM API management
│   │   └── prompts.py            # Prompt templates
│   ├── rag/
│   │   ├── embeddings.py         # Embedding generation
│   │   ├── vector_store.py       # ChromaDB interface
│   │   ├── retriever.py          # Document retrieval
│   │   └── generator.py          # Response generation
│   └── utils/
│       └── logger.py             # Logging utility
├── scripts/
│   ├── 01_scrape_uov_web.py      # Main website scraper
│   ├── 02_scrape_fts_website.py  # Faculty website scraper
│   ├── 03_process_pdfs.py        # PDF handbook processor
│   └── 04_build_knowledge_base.py # Knowledge base builder
├── data/
│   ├── raw/                      # Raw scraped data
│   ├── processed/                # Processed data
│   └── chromadb/                 # Vector database
├── requirements.txt
├── .env.example
└── README.md
```

## Usage Examples 💡

### Basic Queries

```
"What programs does the Faculty of Technological Studies offer?"
"How do I apply to the university?"
"What recent events happened at VAU?"
"Tell me about the DICT program"
```

### Faculty-Specific Queries

Use the sidebar to filter by faculty:
- **FTS**: Faculty of Technological Studies
- **FAS**: Faculty of Applied Science
- **FBS**: Faculty of Business Studies

### Advanced Settings

- **Response Creativity**: Adjust temperature (0.0 = focused, 1.0 = creative)
- **Number of Sources**: Control how many sources to retrieve (1-10)

## Data Sources 📊

### Current Coverage (Phase 1)

- ✅ **Main Website**: 379 documents from vau.ac.lk (Nov 2025+)
- ✅ **FTS Website**: Faculty of Technological Studies pages
- ✅ **FTS Handbook**: DICT Handbook 2022

### Future Expansion (Phase 2)

- ⏳ Faculty of Applied Science website & handbooks
- ⏳ Faculty of Business Studies website & handbooks
- ⏳ Additional program handbooks

## How It Works 🔍

1. **User Query** → Streamlit UI
2. **Embedding** → Convert query to vector using sentence-transformers
3. **Retrieval** → Search ChromaDB for relevant documents
4. **Context** → Format top-k documents as context
5. **Generation** → Send to Groq LLM with context
6. **Response** → Display answer with source citations

## Development 🔧

### Adding New Data Sources

1. Scrape new data (web or PDF)
2. Process and format documents
3. Rebuild knowledge base:
   ```bash
   python scripts/04_build_knowledge_base.py
   ```

### Customizing Prompts

Edit `src/llm/prompts.py` to customize:
- System prompt (assistant behavior)
- Query prompt template
- Citation format

### Changing Models

Edit `.env`:
```
EMBEDDING_MODEL=all-MiniLM-L6-v2
GROQ_MODEL=llama-3.1-70b-versatile
OPENAI_MODEL=gpt-4o-mini
```

## Troubleshooting 🔧

### "No LLM API clients available"
- Check that `GROQ_API_KEY` is set in `.env`
- Verify API key is valid at console.groq.com

### "ChromaDB collection not found"
- Run `python scripts/04_build_knowledge_base.py` to build the database

### "No documents found"
- Ensure you've run the scraping scripts first
- Check that data files exist in `data/raw/`

### Slow responses
- Groq is usually very fast (<2s)
- If using OpenAI fallback, responses may take longer
- Check your internet connection

## API Costs 💰

- **Groq**: FREE tier (30 req/min) - primary provider
- **Sentence Transformers**: FREE (runs locally)
- **ChromaDB**: FREE (local storage)
- **OpenAI**: ~$0.15/1M tokens (fallback only)

**Estimated cost**: $0-5/month for typical usage (mostly free via Groq)

## Contributing 🤝

This is a university project. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License 📄

MIT License - see LICENSE file

## Support 💬

For issues or questions:
- Check the troubleshooting section
- Review the code documentation
- Contact the development team

---

**Built with ❤️ for the University of Vavuniya**

*Powered by Groq, ChromaDB, and Streamlit*