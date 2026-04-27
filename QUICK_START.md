# 🚀 Sonline AI Dashboard - Quick Start Guide

## 5-Minute Setup

### 1️⃣ **Install Python Dependencies**

```bash
# Navigate to the project directory
cd Sonline-main

# Install required packages
pip install -r requirements_dashboard.txt
```

### 2️⃣ **Start PostgreSQL Database**

#### Option A: Using Docker (Recommended)

```bash
# Start PostgreSQL container with sample data
docker-compose up -d

# Verify it's running
docker ps  # Should show Sonline-postgres and Sonline-pgadmin

# Access pgAdmin at http://localhost:5050
# Email: admin@example.com | Password: admin
```

#### Option B: Using Local PostgreSQL

```bash
# If PostgreSQL is installed locally
psql -U postgres -d postgres < init-db.sql

# Or on Windows
psql -U postgres -f init-db.sql
```

#### Option C: Using Existing Database

No setup needed - just use your connection details in the app.

### 3️⃣ **Configure Environment**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and fill in:
# - Database credentials
# - Your LLM API key (Gemini/OpenAI/etc.)
# - Any other configuration
```

### 4️⃣ **Run the Application**

```bash
# Start Streamlit app
streamlit run Sonline_dashboard.py
```

The app opens automatically at: **http://localhost:8501**

## ⚙️ Configuration Steps

### In the Application UI:

1. **Sidebar → Settings**
   - Click "Clear Chat" if needed

2. **Sidebar → Access Control**
   - Select your role (analyst/admin/viewer)
   - Enable/disable write queries
   - Add blocked tables/columns if needed

3. **Main Panel → Database Connection**
   - Enter your database details
   - Click "🔌 Connect"
   - See green "Connected" status

4. **Start Querying!**
   - Type a question: "How many users?" 
   - Click Execute
   - See SQL and results

## 🔌 Database Connection Examples

### Example 1: Local PostgreSQL (Docker)

```
Host: localhost
Port: 5432
User: postgres
Password: Sonline_demo_password
Database: Sonline_demo
```

### Example 2: Local PostgreSQL (Direct Install)

```
Host: localhost
Port: 5432
User: postgres
Password: [your_password]
Database: [your_db]
```

### Example 3: Remote PostgreSQL (AWS RDS)

```
Host: mydb.xxxxx.us-east-1.rds.amazonaws.com
Port: 5432
User: postgres
Password: [your_password]
Database: Sonline_demo
```

## 🤖 LLM Provider Setup

### **Option 1: Google Gemini (Free, Most Powerful)**

```bash
# 1. Get Free API Key
# Visit: https://makersuite.google.com/app/apikey
# Click "Create API Key"

# 2. Install package
pip install google-generativeai

# 3. Add to .env
GOOGLE_API_KEY=your_key_here
LLM_PROVIDER=gemini

# 4. Uncomment integration in Sonline_integration_examples.py
# See: integrate_gemini_in_dashboard()
```

### **Option 2: OpenAI (Most Reliable)**

```bash
# 1. Get API Key
# Visit: https://platform.openai.com/api-keys
# Create new secret key

# 2. Install package
pip install openai

# 3. Add to .env
OPENAI_API_KEY=sk-xxx...
LLM_PROVIDER=openai

# 4. Use integration from Sonline_integration_examples.py
```

### **Option 3: Local Ollama (Free, Private)**

```bash
# 1. Install Ollama
# Download from: https://ollama.ai/

# 2. Pull a model
ollama pull neural-chat

# 3. Start Ollama server
ollama serve

# 4. No API key needed!
# App connects to http://localhost:11434

# 5. Use integrate_ollama_in_dashboard() 
```

### **Option 4: HuggingFace (Free, Local)**

```bash
# 1. Install transformers
pip install transformers torch

# 2. No API key needed
# Models download automatically

# 3. Use integrate_huggingface_in_dashboard()
```

## 📊 Sample Queries

Once connected, try these questions:

### Users & Customers
- "How many users do we have?"
- "Show me users from USA"
- "List all customers and their order count"
- "Who is our top customer?"

### Orders
- "What is the total revenue?"
- "Show pending orders"
- "What's the average order value?"
- "How many orders in 2024?"

### Products
- "What products do we have?"
- "Show products in Electronics category"
- "Which product has the most stock?"
- "List all product categories"

### Analytics
- "Average spending per customer"
- "Total revenue by product category"
- "Orders by country"
- "Sales trend this month"

## 🔐 Security Best Practices

1. **Never commit .env file**
   ```bash
   # Already in .gitignore, but double-check
   cat .gitignore  # Should contain: .env
   ```

2. **Use strong passwords**
   - For PostgreSQL: minimum 12 characters
   - Use special characters

3. **Restrict database user permissions**
   ```sql
   -- Create restricted user
   CREATE USER Sonline_user WITH PASSWORD 'strong_password';
   GRANT CONNECT ON DATABASE Sonline_demo TO Sonline_user;
   GRANT USAGE ON SCHEMA public TO Sonline_user;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO Sonline_user;
   ```

4. **Enable write query restrictions**
   - In app, disable "Allow Write Queries" for analysts
   - Only admins can modify data

5. **Block sensitive tables**
   - Add credit card tables to "Blocked Tables"
   - Add password columns to "Blocked Columns"

## 🐛 Troubleshooting

### "Connection refused"
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Or for local PostgreSQL
sudo systemctl status postgresql

# macOS
pg_isready -h localhost
```

### "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install --upgrade -r requirements_dashboard.txt
```

### "GOOGLE_API_KEY not found"
```bash
# Check .env file exists
ls -la .env

# Verify key is set
echo $GOOGLE_API_KEY  # Should print your key

# On Windows PowerShell
$env:GOOGLE_API_KEY  # Should print your key
```

### "Port 8501 already in use"
```bash
# Run on different port
streamlit run Sonline_dashboard.py --server.port 8502
```

### Large result sets slow down
```bash
# Limit rows in app settings
# Or modify execute_query() to paginate results
```

## 📚 Next Steps

### 1. **Train Your Model** (Optional)
Explore `Sonline_integration_examples.py` for training examples.

### 2. **Customize Dashboard**
Edit `Sonline_dashboard.py` to add:
- Your company logo
- Custom color scheme
- Additional features

### 3. **Deploy to Production**
See [Streamlit Deployment Docs](https://docs.streamlit.io/deploy/streamlit-community-cloud)

### 4. **Enable Query Logging**
Track all queries for audit/compliance

### 5. **Set Up Alerts**
For important queries or data changes

## 📖 Documentation

- [Sonline AI Docs](https://docs.Sonline.ai/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Docker Docs](https://docs.docker.com/)

## 🆘 Getting Help

1. Check the troubleshooting section above
2. Review error messages carefully
3. Check logs in `.streamlit/` directory
4. Search GitHub issues
5. Post in Sonline AI discussions

## ✨ Features Checklist

- ✅ Natural language to SQL conversion
- ✅ Real-time database connection
- ✅ Role-based access control
- ✅ Query history tracking
- ✅ CSV result export
- ✅ Schema explorer
- ✅ Query editing
- ✅ Result statistics
- ✅ Error handling
- ✅ Clean, professional UI

## 🎯 Pro Tips

1. **Use pgAdmin** (port 5050) to:
   - Browse database structure
   - Test queries directly
   - Add sample data

2. **Check query history** to:
   - Review past questions
   - Reuse successful queries
   - Find patterns

3. **Export results** for:
   - Further analysis in Excel
   - Sharing with stakeholders
   - Archival

4. **Block sensitive data**:
   - Configure access control per role
   - Add tables/columns to blocklist
   - Enforce write query restrictions

## 📞 Support

Having issues? Try:

```bash
# Check app logs
streamlit logs

# Check database connection
python check_db_connection.py

# Verify environment variables
env | grep DB_
env | grep GOOGLE_API_KEY
```

---

**🎉 Congratulations! Your Sonline AI Dashboard is ready to use.**

Happy querying! 🚀

