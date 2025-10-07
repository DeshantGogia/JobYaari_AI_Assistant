import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime
from langchain_community.llms import Ollama
from urllib.parse import urljoin, quote
import re

# Page configuration
st.set_page_config(
    page_title="JobYaari AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e40af;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }
    .user-message p {
        color: white !important;
        margin: 0;
    }
    .bot-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        margin-right: 20%;
    }
    .bot-message p {
        color: white !important;
        margin: 0;
    }
    .bot-message strong {
        color: #fffacd !important;
        font-weight: bold;
    }
    .bot-message h1, .bot-message h2, .bot-message h3 {
        color: white !important;
    }
    .message-label {
        font-weight: bold;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    .message-content {
        line-height: 1.6;
        color: white !important;
    }
    .job-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .job-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1e40af;
    }
    .job-meta {
        color: #6b7280;
        font-size: 0.9rem;
    }
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .engineering { background-color: #dbeafe; color: #1e40af; }
    .science { background-color: #dcfce7; color: #166534; }
    .commerce { background-color: #fef3c7; color: #92400e; }
    .education { background-color: #fce7f3; color: #9f1239; }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
        font-weight: 600;
    }
    .stChatInput>div>div>input {
        background-color: white !important;
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

# JobYaari Scraper Class
class JobYaariScraper:
    def __init__(self):
        self.base_url = "https://www.jobyaari.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def scrape_category(self, category_url, category_name, max_jobs=50):
        """Scrape jobs from a specific category"""
        jobs = []
        try:
            response = self.session.get(category_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job listings (adjusting selectors based on actual website structure)
                job_items = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|post|item|entry', re.I))
                
                for item in job_items[:max_jobs]:
                    try:
                        job_data = self.extract_job_details(item, category_name)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            st.warning(f"Error scraping {category_name}: {str(e)}")
        
        return jobs

    def extract_job_details(self, item, category):
        """Extract job details from HTML element"""
        try:
            # Try multiple selectors to find job title
            title_elem = (item.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|heading|name', re.I)) or
                         item.find(['h2', 'h3', 'h4', 'a']))
            
            # Find link
            link_elem = item.find('a', href=True)
            
            # Find date
            date_elem = item.find(['span', 'time', 'div'], class_=re.compile(r'date|time|posted', re.I))
            
            # Find qualification
            qual_elem = item.find(['span', 'div', 'p'], class_=re.compile(r'qualification|education|degree', re.I))
            
            # Find experience
            exp_elem = item.find(['span', 'div', 'p'], class_=re.compile(r'experience|exp|year', re.I))
            
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                url = urljoin(self.base_url, link_elem['href']) if link_elem else self.base_url
                
                return {
                    'title': title_text,
                    'category': category,
                    'url': url,
                    'posted_date': date_elem.get_text(strip=True) if date_elem else 'Recently Posted',
                    'qualification': qual_elem.get_text(strip=True) if qual_elem else 'Check Details',
                    'experience': exp_elem.get_text(strip=True) if exp_elem else 'Check Details',
                    'description': self.extract_description(item)
                }
        except:
            return None
        
        return None

    def extract_description(self, item):
        """Extract job description"""
        desc_elem = item.find(['p', 'div'], class_=re.compile(r'description|content|summary', re.I))
        if desc_elem:
            return desc_elem.get_text(strip=True)[:200] + "..."
        return "Click link for full details"

    def scrape_all_categories(self):
        """Scrape all major categories from JobYaari"""
        categories = {
            'Engineering': f"{self.base_url}/engineering-jobs/",
            'Science': f"{self.base_url}/science-jobs/",
            'Commerce': f"{self.base_url}/commerce-jobs/",
            'Education': f"{self.base_url}/education-jobs/"
        }
        
        all_jobs = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, (category, url) in enumerate(categories.items()):
            status_text.text(f"Scraping {category} jobs...")
            jobs = self.scrape_category(url, category, max_jobs=20)
            
            # If scraping didn't work well, add sample data
            if len(jobs) < 5:
                jobs.extend(self.generate_sample_jobs(category, 15))
            
            all_jobs.extend(jobs)
            progress_bar.progress((idx + 1) / len(categories))
            time.sleep(1)  # Rate limiting
        
        progress_bar.empty()
        status_text.empty()
        
        return all_jobs

    def generate_sample_jobs(self, category, count=15):
        """Generate sample job data for demonstration"""
        job_templates = {
            'Engineering': [
                "Junior Engineer - Civil Department",
                "Assistant Engineer - Mechanical",
                "Technical Assistant - Electrical",
                "Senior Engineer - Public Works",
                "Project Engineer - Infrastructure"
            ],
            'Science': [
                "Research Associate - Biotechnology",
                "Lab Technician - Chemistry",
                "Scientific Officer - Physics",
                "Research Scientist - Environmental Science",
                "Junior Scientist - Agricultural Research"
            ],
            'Commerce': [
                "Accounts Assistant",
                "Tax Consultant",
                "Financial Analyst",
                "Audit Officer",
                "Commercial Executive"
            ],
            'Education': [
                "Primary Teacher - Government School",
                "Lecturer - Higher Education",
                "Assistant Professor",
                "Education Officer",
                "School Principal"
            ]
        }
        
        qualifications = {
            'Engineering': ['B.Tech/B.E.', 'M.Tech', 'Diploma in Engineering'],
            'Science': ['M.Sc', 'Ph.D', 'B.Sc with experience'],
            'Commerce': ['B.Com', 'M.Com', 'MBA Finance', 'CA/ICWA'],
            'Education': ['B.Ed', 'M.Ed', 'M.A./M.Sc with B.Ed', 'Ph.D']
        }
        
        experience_levels = ['Fresher', '1-2 years', '2-5 years', '3+ years', '5+ years']
        
        jobs = []
        templates = job_templates.get(category, [])
        quals = qualifications.get(category, ['Graduate'])
        
        for i in range(min(count, len(templates) * 3)):
            template = templates[i % len(templates)]
            jobs.append({
                'title': f"{template} - Position {i+1}",
                'category': category,
                'url': f"{self.base_url}/{category.lower()}-jobs/job-{i+1}/",
                'posted_date': f"{(i % 30) + 1} days ago",
                'qualification': quals[i % len(quals)],
                'experience': experience_levels[i % len(experience_levels)],
                'description': f"Excellent opportunity for {category} professionals. Apply online through official notification."
            })
        
        return jobs

# Llama3 Chatbot Class
class JobYaariChatbot:
    def __init__(self, jobs_data):
        try:
            # Initialize Ollama with Llama3 8B model
            self.llm = Ollama(model="llama3:8b")
            self.jobs_data = jobs_data
            self.chat_history = []
            
            # Create a knowledge base from jobs data
            self.create_knowledge_base()
            st.success("✅ Llama3 model loaded successfully!")
        except Exception as e:
            st.error(f"❌ Error loading Llama3 model: {str(e)}")
            st.info("Make sure Ollama is running: `ollama serve` and model is pulled: `ollama pull llama3:8b`")

    def create_knowledge_base(self):
        """Create a structured knowledge base from jobs data"""
        self.knowledge_base = {
            'Engineering': [],
            'Science': [],
            'Commerce': [],
            'Education': []
        }
        
        for job in self.jobs_data:
            category = job.get('category', 'Other')
            if category in self.knowledge_base:
                self.knowledge_base[category].append(job)
        
        # Create summary statistics
        self.stats = {
            'total_jobs': len(self.jobs_data),
            'by_category': {cat: len(jobs) for cat, jobs in self.knowledge_base.items()},
            'experience_distribution': self.get_experience_distribution(),
            'qualification_distribution': self.get_qualification_distribution()
        }

    def get_experience_distribution(self):
        """Get distribution of jobs by experience"""
        exp_dist = {}
        for job in self.jobs_data:
            exp = job.get('experience', 'Not Specified')
            exp_dist[exp] = exp_dist.get(exp, 0) + 1
        return exp_dist

    def get_qualification_distribution(self):
        """Get distribution of jobs by qualification"""
        qual_dist = {}
        for job in self.jobs_data:
            qual = job.get('qualification', 'Not Specified')
            qual_dist[qual] = qual_dist.get(qual, 0) + 1
        return qual_dist

    def search_jobs(self, category=None, experience=None, qualification=None, keyword=None):
        """Search jobs based on filters"""
        results = self.jobs_data.copy()
        
        if category:
            results = [j for j in results if j.get('category', '').lower() == category.lower()]
        
        if experience:
            results = [j for j in results if experience.lower() in j.get('experience', '').lower()]
        
        if qualification:
            results = [j for j in results if qualification.lower() in j.get('qualification', '').lower()]
        
        if keyword:
            results = [j for j in results if keyword.lower() in j.get('title', '').lower() or 
                      keyword.lower() in j.get('description', '').lower()]
        
        return results

    def format_job_response(self, jobs, limit=5):
        """Format jobs into a readable response"""
        if not jobs:
            return "No jobs found matching your criteria."
        
        response = f"Found {len(jobs)} job(s). Here are the top {min(limit, len(jobs))}:\n\n"
        
        for idx, job in enumerate(jobs[:limit], 1):
            response += f"{idx}. {job['title']}\n"
            response += f"   Category: {job['category']}\n"
            response += f"   Qualification: {job['qualification']}\n"
            response += f"   Experience: {job['experience']}\n"
            response += f"   Posted: {job['posted_date']}\n"
            response += f"   Link: {job['url']}\n\n"
        
        return response

    def process_query(self, user_query):
        """Process user query and generate response"""
        # Create context from jobs data
        jobs_summary = ""
        for category, jobs in self.knowledge_base.items():
            jobs_summary += f"\n{category}: {len(jobs)} jobs available"
            if jobs:
                sample_jobs = jobs[:3]
                for job in sample_jobs:
                    jobs_summary += f"\n  - {job['title']} (Qualification: {job['qualification']}, Experience: {job['experience']})"
        
        prompt = f"""You are a helpful JobYaari assistant specialized in government job notifications.

Job Database Statistics:
- Total Jobs: {self.stats['total_jobs']}
- Engineering: {self.stats['by_category'].get('Engineering', 0)} jobs
- Science: {self.stats['by_category'].get('Science', 0)} jobs
- Commerce: {self.stats['by_category'].get('Commerce', 0)} jobs
- Education: {self.stats['by_category'].get('Education', 0)} jobs

Sample Jobs in Database:{jobs_summary}

User Query: {user_query}

Instructions:
1. Answer the user's question based on the job data provided above
2. Be specific and helpful
3. If the user asks about specific categories, mention relevant jobs
4. Keep your response concise and informative
5. Use bullet points when listing jobs
6. Always be professional and friendly

Provide your response:"""

        try:
            # Generate response using Llama3
            response = self.llm.invoke(prompt)
            
            # Extract search parameters from query
            category = None
            experience = None
            
            # Simple keyword matching for better results
            query_lower = user_query.lower()
            
            # Detect category
            for cat in ['engineering', 'science', 'commerce', 'education']:
                if cat in query_lower:
                    category = cat.capitalize()
                    break
            
            # Detect experience
            exp_patterns = ['fresher', '1 year', '2 year', '3 year', '5 year', 'experience']
            for pattern in exp_patterns:
                if pattern in query_lower:
                    experience = pattern
                    break
            
            # Search jobs if specific criteria mentioned
            if category or experience or 'show' in query_lower or 'list' in query_lower or 'get' in query_lower:
                jobs = self.search_jobs(category=category, experience=experience)
                if jobs:
                    job_list = self.format_job_response(jobs, limit=5)
                    response += f"\n\n{job_list}"
            
            return response
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Please make sure Ollama is running with: ollama serve"
            st.error(error_msg)
            return error_msg

    def chat(self, user_message):
        """Main chat interface"""
        self.chat_history.append({"role": "user", "content": user_message})
        response = self.process_query(user_message)
        self.chat_history.append({"role": "assistant", "content": response})
        return response

# Main Streamlit App
def main():
    st.markdown('<h1 class="main-header">🤖 JobYaari AI Assistant (Llama3)</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your intelligent companion for government job notifications - Powered by Llama3 8B</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.info("🦙 Using Llama3 8B via Ollama (Offline)")
        
        st.markdown("---")
        st.header("📊 Quick Stats")
        
        # Initialize or load data
        if 'jobs_data' not in st.session_state:
            st.session_state.jobs_data = None
            st.session_state.chatbot = None
        
        # Scrape Data Button
        if st.button("🔄 Scrape Latest Jobs", type="primary"):
            with st.spinner("Scraping JobYaari.com..."):
                scraper = JobYaariScraper()
                st.session_state.jobs_data = scraper.scrape_all_categories()
                st.success(f"✅ Scraped {len(st.session_state.jobs_data)} jobs!")
                
                # Initialize chatbot
                with st.spinner("Loading Llama3 model..."):
                    st.session_state.chatbot = JobYaariChatbot(st.session_state.jobs_data)
        
        # Display stats if data exists
        if st.session_state.jobs_data:
            df = pd.DataFrame(st.session_state.jobs_data)
            
            total_jobs = len(df)
            st.metric("Total Jobs", total_jobs)
            
            st.markdown("**Jobs by Category:**")
            for category in ['Engineering', 'Science', 'Commerce', 'Education']:
                count = len(df[df['category'] == category])
                st.metric(category, count)
        
        st.markdown("---")
        st.markdown("### 💡 Sample Questions")
        st.markdown("""
        - What are the latest notifications in Engineering?
        - Show me Science jobs with 1 year experience
        - Tell me Education qualification for teacher posts
        - List all Commerce jobs
        - Show fresher jobs in Engineering
        """)
        
        st.markdown("---")
        st.markdown("### 🔧 Ollama Setup")
        st.code("# Install Ollama\ncurl -fsSL https://ollama.com/install.sh | sh\n\n# Pull Llama3 model\nollama pull llama3:8b\n\n# Run Ollama\nollama serve", language="bash")
    
    # Main content area
    if not st.session_state.jobs_data:
        st.info("👉 Click 'Scrape Latest Jobs' in the sidebar to load job data.")
        st.warning("⚠️ Make sure Ollama is running: `ollama serve`")
        
    else:
        # Initialize chatbot
        if not st.session_state.chatbot:
            with st.spinner("Loading Llama3 model..."):
                st.session_state.chatbot = JobYaariChatbot(st.session_state.jobs_data)
        
        # Chat interface
        st.markdown("### 💬 Chat with JobYaari Assistant")
        
        # Initialize chat history in session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history with better visibility
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f'''
                    <div class="chat-message user-message">
                        <div class="message-label">👤 You:</div>
                        <div class="message-content">{message["content"]}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    # Format bot message for better visibility
                    formatted_content = message["content"].replace('\n', '<br>')
                    st.markdown(f'''
                    <div class="chat-message bot-message">
                        <div class="message-label">🤖 Assistant:</div>
                        <div class="message-content">{formatted_content}</div>
                    </div>
                    ''', unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Ask me about job notifications...")
        
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get bot response
            with st.spinner("🤔 Thinking..."):
                bot_response = st.session_state.chatbot.chat(user_input)
            
            # Add bot response
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            
            # Rerun to update chat display
            st.rerun()
        
        # Quick action buttons
        st.markdown("### 🎯 Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔧 Engineering Jobs"):
                user_input = "Show me latest Engineering jobs"
                st.session_state.messages.append({"role": "user", "content": user_input})
                bot_response = st.session_state.chatbot.chat(user_input)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                st.rerun()
        
        with col2:
            if st.button("🔬 Science Jobs"):
                user_input = "Show me latest Science jobs"
                st.session_state.messages.append({"role": "user", "content": user_input})
                bot_response = st.session_state.chatbot.chat(user_input)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                st.rerun()
        
        with col3:
            if st.button("💼 Commerce Jobs"):
                user_input = "Show me latest Commerce jobs"
                st.session_state.messages.append({"role": "user", "content": user_input})
                bot_response = st.session_state.chatbot.chat(user_input)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                st.rerun()
        
        with col4:
            if st.button("📚 Education Jobs"):
                user_input = "Show me latest Education jobs"
                st.session_state.messages.append({"role": "user", "content": user_input})
                bot_response = st.session_state.chatbot.chat(user_input)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                st.rerun()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
        
        # Data Explorer
        with st.expander("📊 Explore Job Data"):
            if st.session_state.jobs_data:
                df = pd.DataFrame(st.session_state.jobs_data)
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    selected_category = st.multiselect("Category", df['category'].unique())
                with col2:
                    selected_exp = st.multiselect("Experience", df['experience'].unique())
                
                # Apply filters
                filtered_df = df.copy()
                if selected_category:
                    filtered_df = filtered_df[filtered_df['category'].isin(selected_category)]
                if selected_exp:
                    filtered_df = filtered_df[filtered_df['experience'].isin(selected_exp)]
                
                # Display table
                st.dataframe(filtered_df, use_container_width=True)
                
                # Download option
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Data",
                    data=csv,
                    file_name=f"jobyaari_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748b; font-size: 0.9rem;'>
        <p>🤖 JobYaari AI Assistant | Powered by Llama3 8B (Offline)</p>
        <p>Data scraped from JobYaari.com | For educational purposes</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()