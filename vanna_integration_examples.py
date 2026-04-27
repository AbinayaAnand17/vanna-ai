"""
vanna AI Integration Examples
This file contains examples of how to integrate different vanna AI providers
into the vanna_dashboard.py application.

Use these examples as reference to update the generate_sql_from_question() function
and integrate your preferred LLM provider.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# =============================================================================

# EXAMPLE 1: Google Gemini Integration
# =============================================================================

"""
Installation:
pip install google-generativeai

Environment Setup:
export GOOGLE_API_KEY="your-google-api-key"
"""

def setup_gemini_vanna():
    """Initialize vanna with Google Gemini"""
    import os
    from vanna.googlegeminicf import vannaGoogleGeminiCF
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    vanna = vannaGoogleGeminiCF(
        api_key=api_key,
        model_name="gemini-pro"  # or gemini-pro-vision for multi-modal
    )
    return vanna

def integrate_gemini_in_dashboard():
    """
    Integration code for vanna_dashboard.py
    
    Replace the generate_sql_from_question() function with this:
    """
    
    CODE = '''
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """
    Generate SQL query from natural language question using Google Gemini
    
    Args:
        question: Natural language question
        
    Returns:
        Tuple of (success: bool, sql_query: str)
    """
    try:
        import os
        from vanna.googlegeminicf import vannaGoogleGeminiCF
        
        # Initialize if not already done
        if "vanna_instance" not in st.session_state:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return False, "GOOGLE_API_KEY environment variable not set"
            
            st.session_state.vanna_instance = vannaGoogleGeminiCF(api_key=api_key)
            
            # Connect to database
            st.session_state.vanna_instance.connect_to_postgres(
                **st.session_state.db_config
            )
        
        # Generate SQL
        vanna = st.session_state.vanna_instance
        sql_query = vanna.generate_sql(question, use_context=True)
        
        return True, sql_query
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"
    '''
    
    return CODE


# =============================================================================
# EXAMPLE 2: OpenAI Integration
# =============================================================================

"""
Installation:
pip install openai

Environment Setup:
export OPENAI_API_KEY="your-openai-api-key"
"""

def setup_openai_vanna():
    """Initialize vanna with OpenAI"""
    import os
    from vanna.openai import OpenAI_ChatGPT
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    vanna = OpenAI_ChatGPT(
        api_key=api_key,
        model="gpt-4"  # or "gpt-3.5-turbo" for faster/cheaper option
    )
    return vanna

def integrate_openai_in_dashboard():
    """Integration code for OpenAI in vanna_dashboard.py"""
    
    CODE = '''
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """
    Generate SQL query from natural language question using OpenAI
    
    Args:
        question: Natural language question
        
    Returns:
        Tuple of (success: bool, sql_query: str)
    """
    try:
        import os
        from vanna.openai import OpenAI_ChatGPT
        
        # Initialize if not already done
        if "vanna_instance" not in st.session_state:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return False, "OPENAI_API_KEY environment variable not set"
            
            st.session_state.vanna_instance = OpenAI_ChatGPT(api_key=api_key)
            
            # Optional: Train with your schema
            # schema_info = get_database_schema()
            # st.session_state.vanna_instance.train(
            #     documentation=schema_info
            # )
        
        # Generate SQL
        vanna = st.session_state.vanna_instance
        sql_query = vanna.generate_sql(question)
        
        return True, sql_query
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"
    '''
    
    return CODE


# =============================================================================
# EXAMPLE 3: Ollama (Local Open Source Models)
# =============================================================================

"""
Installation:
1. Download Ollama from https://ollama.ai/
2. Pull a model: ollama pull neural-chat
3. Run: ollama serve

Required Python packages:
pip install requests
"""

def integrate_ollama_in_dashboard():
    """Integration code for Ollama in vanna_dashboard.py"""
    
    CODE = '''
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """
    Generate SQL query using local Ollama model
    
    Args:
        question: Natural language question
        
    Returns:
        Tuple of (success: bool, sql_query: str)
    """
    try:
        import requests
        
        # Get database schema information
        schema = get_database_schema()
        
        # Prepare prompt for Ollama
        prompt = f"""You are a SQL expert. Given the following database schema and a question, 
generate a valid PostgreSQL query. Only return the SQL query, nothing else.

DATABASE SCHEMA:
{schema}

QUESTION: {question}

SQL QUERY:"""
        
        # Call local Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "neural-chat",  # or your preferred model
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3
            },
            timeout=60
        )
        
        if response.status_code == 200:
            sql_query = response.json().get("response", "").strip()
            
            # Clean up response if needed
            if sql_query.startswith("```"):
                sql_query = sql_query.split("```")[1].replace("sql", "").strip()
            
            return True, sql_query
        else:
            return False, f"Ollama API error: {response.text}"
            
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Ollama. Make sure 'ollama serve' is running."
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"
    '''
    
    return CODE


# =============================================================================
# EXAMPLE 4: Llama2 via Replicate
# =============================================================================

"""
Installation:
pip install replicate

Environment Setup:
export REPLICATE_API_TOKEN="your-replicate-api-token"
"""

def integrate_replicate_in_dashboard():
    """Integration code for Replicate (Llama2) in vanna_dashboard.py"""
    
    CODE = '''
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """
    Generate SQL query using Llama2 via Replicate
    
    Args:
        question: Natural language question
        
    Returns:
        Tuple of (success: bool, sql_query: str)
    """
    try:
        import os
        import replicate
        
        # Set API token
        replicate.api.token = os.getenv("REPLICATE_API_TOKEN")
        
        if not replicate.api.token:
            return False, "REPLICATE_API_TOKEN environment variable not set"
        
        # Get database schema
        schema = get_database_schema()
        
        # Prepare prompt
        prompt = f"""Generate a PostgreSQL query for the following question.

Database schema:
{schema}

Question: {question}

Only return the SQL query:"""
        
        # Call Llama2 model
        output = replicate.run(
            "meta/llama-2-70b-chat:02e509c789964a4ad46387b92cc247292c53b08b1921666c4c53c36ade9ac683",
            input={
                "prompt": prompt,
                "max_new_tokens": 500,
                "temperature": 0.1,
                "top_p": 0.9
            }
        )
        
        sql_query = "".join(output).strip()
        return True, sql_query
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"
    '''
    
    return CODE


# =============================================================================
# EXAMPLE 5: HuggingFace Transformers (Local)
# =============================================================================

"""
Installation:
pip install transformers torch

This runs locally without any API keys.
"""

def integrate_huggingface_in_dashboard():
    """Integration code for HuggingFace models in vanna_dashboard.py"""
    
    CODE = '''
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """
    Generate SQL query using HuggingFace transformers
    
    Args:
        question: Natural language question
        
    Returns:
        Tuple of (success: bool, sql_query: str)
    """
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        
        # Initialize model if not already done
        if "hf_model" not in st.session_state:
            # Use a lightweight model suitable for local execution
            model_name = "bigcode/starcoder-1b"
            
            st.session_state.hf_tokenizer = AutoTokenizer.from_pretrained(model_name)
            st.session_state.hf_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16
            )
        
        # Get database schema
        schema = get_database_schema()
        
        # Prepare prompt
        prompt = f"""Generate PostgreSQL SQL code:
        
Schema:
{schema}

Question: {question}

SQL:"""
        
        # Generate SQL
        inputs = st.session_state.hf_tokenizer.encode(prompt, return_tensors="pt")
        outputs = st.session_state.hf_model.generate(
            inputs,
            max_length=200,
            temperature=0.2,
            top_p=0.9
        )
        
        sql_query = st.session_state.hf_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the SQL part
        if "SQL:" in sql_query:
            sql_query = sql_query.split("SQL:")[-1].strip()
        
        return True, sql_query
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"
    '''
    
    return CODE


# =============================================================================
# EXAMPLE 6: Azure OpenAI
# =============================================================================

"""
Installation:
pip install openai

Environment Setup:
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="your-deployment-name"
"""

def integrate_azure_openai_in_dashboard():
    """Integration code for Azure OpenAI in vanna_dashboard.py"""
    
    CODE = '''
def generate_sql_from_question(question: str) -> Tuple[bool, str]:
    """
    Generate SQL query using Azure OpenAI
    
    Args:
        question: Natural language question
        
    Returns:
        Tuple of (success: bool, sql_query: str)
    """
    try:
        import os
        from openai import AzureOpenAI
        
        # Initialize client if not already done
        if "azure_client" not in st.session_state:
            st.session_state.azure_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-02-15-preview",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        
        # Get database schema
        schema = get_database_schema()
        
        # Prepare messages
        messages = [
            {"role": "system", "content": "You are a PostgreSQL expert. Generate valid SQL queries based on natural language questions."},
            {"role": "user", "content": f"Database schema:\\n{schema}\\n\\nQuestion: {question}"}
        ]
        
        # Call Azure OpenAI API
        response = st.session_state.azure_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=messages,
            temperature=0.1,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up markdown formatting if present
        if sql_query.startswith("```"):
            sql_query = sql_query.split("```")[1].replace("sql", "").strip()
        
        return True, sql_query
        
    except Exception as e:
        return False, f"Error generating SQL: {str(e)}"
    '''
    
    return CODE


# =============================================================================
# vanna AI TRAINING GUIDE
# =============================================================================

def vanna_training_example():
    """Example of training vanna with your database schema"""
    
    CODE = '''
def train_vanna_model():
    """Train vanna AI model with your database schema and sample queries"""
    import os
    from vanna.googlegeminicf import vannaGoogleGeminiCF
    
    # Initialize vanna
    vanna = vannaGoogleGeminiCF(
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Connect to database
    vanna.connect_to_postgres(**st.session_state.db_config)
    
    # Training examples - add more for better results
    training_data = [
        {
            "question": "How many users are in the system?",
            "sql": "SELECT COUNT(*) as user_count FROM users;"
        },
        {
            "question": "Show me the top 10 customers by total orders",
            "sql": "SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id ORDER BY order_count DESC LIMIT 10;"
        },
        {
            "question": "What is the average order value?",
            "sql": "SELECT AVG(total_amount) as avg_order_value FROM orders;"
        },
        {
            "question": "List all active products",
            "sql": "SELECT * FROM products WHERE status = 'active';"
        }
    ]
    
    # Train the model with example queries
    for example in training_data:
        vanna.train(sql=example["sql"], question=example["question"])
    
    # Optional: Train with documentation
    documentation = get_database_schema()
    vanna.train(documentation=documentation)
    
    st.success("? Model trained successfully!")
    '''
    
    return CODE


# =============================================================================
# QUICK START SETUP SCRIPT
# =============================================================================

def generate_setup_script():
    """Generate a setup script for easy installation"""
    
    SCRIPT = '''#!/bin/bash
# vanna AI Dashboard Setup Script

echo "? Setting up vanna AI Dashboard..."

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements_dashboard.txt

# Choose your LLM provider
echo ""
echo "Choose your LLM provider:"
echo "1. Google Gemini"
echo "2. OpenAI"
echo "3. Local Ollama (requires Ollama installed)"
echo "4. HuggingFace (free, local)"
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        pip install google-generativeai
        echo "API Key setup: Set GOOGLE_API_KEY environment variable"
        ;;
    2)
        pip install openai
        echo "API Key setup: Set OPENAI_API_KEY environment variable"
        ;;
    3)
        echo "Ensure Ollama is running: ollama serve"
        echo "Pull a model: ollama pull neural-chat"
        ;;
    4)
        pip install transformers torch
        echo "Ready to use HuggingFace models"
        ;;
esac

echo ""
echo "? Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your database connection in the app"
echo "2. Set required environment variables"
echo "3. Run: streamlit run vanna_dashboard.py"
    '''
    
    return SCRIPT


# =============================================================================
# ENVIRONMENT CONFIGURATION TEMPLATE
# =============================================================================

def generate_env_template():
    """Generate .env template for configuration"""
    
    ENV_TEMPLATE = '''
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME=your_database_name

# LLM Provider Selection
# Uncomment the provider you want to use
LLM_PROVIDER=gemini  # Options: gemini, openai, ollama, huggingface, azure

# Google Gemini
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your_deployment_name

# Replicate (for Llama2)
REPLICATE_API_TOKEN=your_replicate_token

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=neural-chat  # or your preferred model

# Streamlit Configuration
STREAMLIT_THEME_BASE=light
STREAMLIT_THEME_PRIMARY_COLOR=#1f77e4

# Application Settings
LOG_LEVEL=INFO
DEBUG_MODE=False
QUERY_TIMEOUT=60  # seconds
    '''
    
    return ENV_TEMPLATE


if __name__ == "__main__":
    print("vanna AI Integration Examples")
    print("=" * 50)
    print("\nRefer to functions in this file for integration examples")
    print("\nAvailable integrations:")
    print("1. Google Gemini (setup_gemini_vanna)")
    print("2. OpenAI (setup_openai_vanna)")
    print("3. Ollama (integrate_ollama_in_dashboard)")
    print("4. Replicate/Llama2 (integrate_replicate_in_dashboard)")
    print("5. HuggingFace (integrate_huggingface_in_dashboard)")
    print("6. Azure OpenAI (integrate_azure_openai_in_dashboard)")
    print("\nSee README_DASHBOARD.md for detailed setup instructions")
