"""
Vavuniya University AI Assistant - Streamlit App
Premium chat interface with RAG-powered responses
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import Config
from src.rag.generator import get_generator
from src.utils.logger import setup_logger

# Page configuration
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light mode theme
st.markdown("""
<script>
    // Force light mode
    window.parent.document.body.classList.remove('dark-mode');
</script>
""", unsafe_allow_html=True)

# Custom CSS for university branding
st.markdown("""
<style>
    /* University brand colors: 70% white, 30% #6a0047 (maroon) */
    
    /* Main container - clean white background */
    .main {
        background-color: #ffffff;
    }
    
    /* Headers with university maroon */
    h1, h2, h3 {
        color: #6a0047 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Chat messages - clean white cards */
    .stChatMessage {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* User message - light maroon accent */
    .stChatMessage[data-testid="user-message"] {
        background-color: #fef2f8 !important;
        border-left: 4px solid #6a0047;
    }
    
    /* Assistant message - white with subtle border */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #ffffff !important;
        border-left: 4px solid #d1d5db;
    }
    
    /* Input box - clean with maroon focus */
    .stChatInputContainer {
        background-color: #ffffff;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
    }
    
    .stChatInputContainer:focus-within {
        border-color: #6a0047;
    }
    
    /* Sidebar - light maroon background */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #6a0047 0%, #8b0059 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    /* Buttons - university maroon */
    .stButton > button {
        background-color: #6a0047;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.625rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #8b0059;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(106, 0, 71, 0.3);
    }
    
    /* Source cards - clean white */
    .source-card {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .source-title {
        color: #6a0047;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .source-meta {
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    /* Links - maroon color */
    a {
        color: #6a0047 !important;
        text-decoration: none;
    }
    
    a:hover {
        color: #8b0059 !important;
        text-decoration: underline;
    }
    
    /* Expander - clean styling */
    .streamlit-expanderHeader {
        background-color: #f9fafb;
        border-radius: 8px;
        color: #6a0047 !important;
    }
    
    /* Select boxes in sidebar */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.3);
    }
    
    /* Sliders in sidebar */
    [data-testid="stSidebar"] .stSlider > div > div > div {
        background-color: rgba(255, 255, 255, 0.3);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        border-bottom: 3px solid #6a0047;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: #6b7280;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize logger
logger = setup_logger("streamlit_app")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'generator' not in st.session_state:
    try:
        st.session_state.generator = get_generator()
        logger.info("Generator initialized")
    except Exception as e:
        st.error(f"❌ Failed to initialize AI system: {e}")
        logger.error(f"Initialization error: {e}")
        st.stop()


def display_source(source: dict, index: int):
    """Display a source card"""
    title = source.get('title', 'Untitled')
    url = source.get('url', '')
    faculty = source.get('faculty', '')
    source_type = source.get('source_type', '')
    relevance = source.get('relevance_score', 0)
    
    # Format source type
    type_label = {
        'web': '🌐 Website',
        'faculty_web': '🏛️ Faculty',
        'handbook_pdf': '📚 Handbook'
    }.get(source_type, '📄 Document')
    
    st.markdown(f"""
    <div class="source-card">
        <div class="source-title">{index}. {title}</div>
        <div class="source-meta">
            {type_label} {f'• {faculty}' if faculty else ''} • Relevance: {relevance:.0%}
        </div>
        {f'<div style="margin-top: 0.5rem;"><a href="{url}" target="_blank">🔗 View source</a></div>' if url else ''}
    </div>
    """, unsafe_allow_html=True)


# Main app
def main():
    # Header with university branding
    st.markdown(f"""
    <div class="main-header">
        <h1>🎓 {Config.APP_TITLE}</h1>
        <p>Your intelligent assistant for university information</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # Faculty filter
        faculty_filter = st.selectbox(
            "Filter by Faculty",
            options=["All", "FTS", "FAS", "FBS"],
            help="Filter responses to specific faculty"
        )
        
        faculty = None if faculty_filter == "All" else faculty_filter
        
        # Advanced settings
        with st.expander("🔧 Advanced"):
            temperature = st.slider(
                "Response Creativity",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher = more creative, Lower = more focused"
            )
            
            top_k = st.slider(
                "Number of Sources",
                min_value=1,
                max_value=10,
                value=5,
                help="Number of sources to retrieve"
            )
        
        st.markdown("---")
        
        # Info
        st.markdown("### ℹ️ About")
        st.markdown("""
        This AI assistant can help you with:
        - 📚 Program information
        - 🎓 Admission requirements
        - 📅 Events and news
        - 🏛️ Faculty details
        - 📖 Handbook content
        """)
        
        # Clear chat
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; font-size: 0.875rem;">
            Powered by Groq & ChromaDB<br>
            University of Vavuniya
        </div>
        """, unsafe_allow_html=True)
    
    # Chat interface
    st.markdown("### 💬 Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display sources if available
            if message["role"] == "assistant" and "sources" in message:
                with st.expander(f"📚 View {len(message['sources'])} sources"):
                    for i, source in enumerate(message['sources'], 1):
                        display_source(source, i)
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about the university..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate streaming response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            sources = []
            
            try:
                # Get response from generator
                response = st.session_state.generator.generate(
                    query=prompt,
                    faculty=faculty,
                    top_k=top_k,
                    temperature=temperature
                )
                
                answer = response['answer']
                sources = response['sources']
                
                # Simulate streaming effect
                import time
                words = answer.split()
                for i, word in enumerate(words):
                    full_response += word + " "
                    # Update every 3 words for smooth streaming
                    if i % 3 == 0 or i == len(words) - 1:
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.05)  # Small delay for streaming effect
                
                # Final response without cursor
                message_placeholder.markdown(full_response)
                
                # Display sources
                if sources:
                    with st.expander(f"📚 View {len(sources)} sources"):
                        for i, source in enumerate(sources, 1):
                            display_source(source, i)
                
                # Add to message history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response.strip(),
                    "sources": sources
                })
                
                logger.info(f"Query answered: '{prompt}'")
                
            except Exception as e:
                error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                message_placeholder.error(error_msg)
                logger.error(f"Error generating response: {e}")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
    
    # Suggested queries (if no messages)
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Try asking:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📚 What programs does FTS offer?", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "What programs does the Faculty of Technological Studies offer?"
                })
                st.rerun()
            
            if st.button("🎓 How do I apply to the university?", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "How do I apply to the University of Vavuniya?"
                })
                st.rerun()
        
        with col2:
            if st.button("📅 What events are happening?", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "What recent events happened at the university?"
                })
                st.rerun()
            
            if st.button("🏛️ Tell me about the faculties", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": "Tell me about the different faculties at VAU"
                })
                st.rerun()


if __name__ == "__main__":
    main()
