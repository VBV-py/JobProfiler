"""
Central configuration for the Redrob Candidate Ranking System.

All scoring weights, skill lists, title maps, thresholds, and constants
are defined here. Tuning the ranker = editing this file.
"""


MUST_HAVE_SKILLS_EXACT = {
    # Embeddings & retrieval
    "sentence-transformers", "openai embeddings", "bge", "e5",
    "semantic search", "information retrieval",
    "text embeddings", "embeddings",
    # Vector DBs & hybrid search
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch",
    "elasticsearch", "faiss", "vector database", "hybrid search",

    "python",
    # Ranking & evaluation
    "ndcg", "mrr", "a/b testing", "ranking",
    "recommendation systems", "search ranking", "learning to rank",
}

MUST_HAVE_KEYWORDS = [
    "embedding", "retrieval", "vector", "search", "ranking",
    "recommendation", "nlp", "natural language", "information retrieval",
    "reranking", "re-ranking", "bm25", "tf-idf", "tfidf",
    "elasticsearch", "opensearch", "faiss", "pinecone", "weaviate",
    "qdrant", "milvus", "sentence-transformer", "bert", "sbert",
]

NICE_TO_HAVE_SKILLS_EXACT = {
    "lora", "qlora", "peft", "fine-tuning", "fine-tuning llms",
    "xgboost", "lightgbm", "catboost", "learning to rank",
    "distributed systems", "kubernetes", "docker",
    "mlops", "ml engineering", "kubeflow",
    "pytorch", "tensorflow", "hugging face", "transformers",
    "llm", "rag", "prompt engineering", "langchain",
    "airflow", "spark", "data engineering",
    "open source",
}

NICE_TO_HAVE_KEYWORDS = [
    "lora", "qlora", "peft", "fine-tun", "xgboost", "lightgbm",
    "distributed", "kubernetes", "docker", "mlops",
    "pytorch", "tensorflow", "hugging", "transformer",
    "llm", "rag", "prompt", "airflow", "spark",
    "deep learning", "neural network", "machine learning",
    "data pipeline", "feature engineering", "model serving",
    "inference", "deployment", "ci/cd",
]

# TITLE CLASSIFICATION

AI_ML_TITLES_KEYWORDS = [
    "ai engineer", "ml engineer", "machine learning engineer",
    "data scientist", "nlp engineer", "research engineer",
    "applied scientist", "search engineer", "ranking engineer",
    "recommendation engineer", "ml scientist",
    "deep learning engineer", "ai scientist",
    "senior ai engineer", "senior ml engineer",
    "senior machine learning engineer", "senior data scientist",
    "junior ml engineer", "junior ai engineer",
    "lead ai engineer", "lead ml engineer", "staff engineer",
    "principal engineer",
]

TECH_TITLES_KEYWORDS = [
    "software engineer", "backend engineer", "platform engineer",
    "data engineer", "full stack", "fullstack", "devops",
    "site reliability", "sre", "infrastructure engineer",
    "developer", "programmer", "architect",
    "analytics engineer", "senior software engineer",
]

NON_TECH_TITLES = [
    "marketing manager", "hr manager", "human resources",
    "sales executive", "sales manager", "sales representative",
    "accountant", "accounting", "finance manager",
    "content writer", "copywriter", "content manager",
    "graphic designer", "ui designer", "ux designer",
    "operations manager", "operations lead",
    "customer support", "customer service", "support engineer",
    "business analyst", "business development",
    "project manager", "program manager", "scrum master",
    "civil engineer", "mechanical engineer", "chemical engineer",
    "electrical engineer", "structural engineer",
    "teacher", "professor", "lecturer",
    "recruiter", "talent acquisition",
]


CONSULTING_FIRMS = [
    "tcs", "tata consultancy", "tata consultancy services",
    "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl", "hcl technologies",
    "tech mahindra", "mindtree", "l&t infotech", "ltimindtree",
    "mphasis", "hexaware", "persistent systems",
    "zensar", "cyient", "niit technologies",
    "virtusa", "birlasoft", "sonata software",
    "igate", "patni", "satyam",
    "deloitte", "kpmg", "ey", "ernst & young", "pwc",
    "mckinsey", "bcg", "bain",
]

PRODUCT_COMPANY_KEYWORDS = [
    "google", "meta", "facebook", "amazon", "microsoft", "apple",
    "netflix", "uber", "airbnb", "stripe", "shopify",
    "flipkart", "swiggy", "zomato", "razorpay", "cred",
    "meesho", "phonepe", "paytm", "ola", "myntra",
    "freshworks", "zoho", "postman", "browserstack",
    "atlassian", "salesforce", "adobe", "linkedin",
    "twitter", "snap", "spotify", "slack",
    "startup", "fintech", "saas",
]

PRODUCTION_ML_KEYWORDS = [
    "production", "deployed", "shipped", "launched", "built",
    "ranking system", "recommendation system", "recommendation engine",
    "retrieval system", "search system", "search engine",
    "embedding", "vector search", "vector database",
    "ml pipeline", "model serving", "model deployment",
    "a/b test", "ab test", "online experiment",
    "real users", "user-facing", "customer-facing",
    "scale", "scalable", "latency", "throughput",
    "etl pipeline", "data pipeline", "feature store",
    "monitoring", "alerting", "sla",
    "inference", "serving infrastructure",
    "reranking", "candidate generation",
    "collaborative filtering", "content-based filtering",
    "semantic search", "hybrid search",
    "ndcg", "mrr", "precision", "recall",
    "fine-tuned", "fine tuned", "finetuned",
]

RESEARCH_ONLY_KEYWORDS = [
    "published paper", "conference paper", "journal paper",
    "phd thesis", "dissertation", "academic",
    "proof of concept", "poc only", "prototype only",
    "kaggle competition", "hackathon project",
]

# LOCATION PREFERENCES — From JD

PREFERRED_LOCATIONS = [
    "pune", "noida", "delhi ncr", "delhi", "new delhi",
    "gurgaon", "gurugram", "ghaziabad", "faridabad",
    "greater noida",
]

GOOD_LOCATIONS = [
    "hyderabad", "mumbai", "bangalore", "bengaluru",
    "chennai", "kolkata",
]

# SCORING WEIGHTS — The composite formula

WEIGHTS = {
    "title_relevance":    0.25,  # Most decisive against keyword-stuffing traps
    "skill_match":        0.20,  # Must-have + nice-to-have skills
    "career_trajectory":  0.25,  # Product co, production ML, stability
    "experience_fit":     0.10,  # 5-9 year sweet spot
    "location_fit":       0.05,  # Pune/Noida preferred
    "education":          0.05,  # Tier + field relevance
    "behavioral":         0.10,  # Engagement, responsiveness, availability
}

# EXPERIENCE THRESHOLDS

IDEAL_EXP_MIN = 5.0    # JD says 5-9 years
IDEAL_EXP_MAX = 9.0
SOFT_EXP_MIN = 3.0     # "Some people hit senior judgment at 4 years"
SOFT_EXP_MAX = 12.0    # Still reasonable if other signals are strong
HARD_EXP_MIN = 1.5     # Below this, almost certainly too junior

# BEHAVIORAL SIGNAL THRESHOLDS

# Notice period: "We'd love sub-30-day notice. We can buy out up to 30 days."
NOTICE_IDEAL_MAX = 30
NOTICE_OKAY_MAX = 60
NOTICE_PENALTY_START = 90

# Response time
RESPONSE_TIME_FAST = 24    # hours
RESPONSE_TIME_OK = 48
RESPONSE_TIME_SLOW = 96
RESPONSE_TIME_VERY_SLOW = 168

# Inactivity thresholds (days since last active)
INACTIVE_RECENT = 30
INACTIVE_MODERATE = 90
INACTIVE_STALE = 180
INACTIVE_DEAD = 365

# COARSE FILTER — Quick-reject thresholds

# Minimum composite score to even consider ranking (filters out noise)
COARSE_TITLE_THRESHOLD = 0.05   # If title score is this low, skip detailed scoring
MIN_RELEVANT_SIGNALS = 1         # Need at least 1 positive signal to proceed
