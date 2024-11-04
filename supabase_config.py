import os
from supabase import create_client, Client
from dotenv import load_dotenv
from postgrest import APIError

load_dotenv()

SUPABASE_URL = "https://mradubnvwmxovyjbuknk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1yYWR1Ym52d214b3Z5amJ1a25rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzAyMTgyMjksImV4cCI6MjA0NTc5NDIyOX0.0JjrDEMH6hXbDiRcnev2DzdOSwrkdsnjZU2yBV5eyaE"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar definidos no arquivo .env")

# Configuração correta do cliente Supabase
options = {
    'schema': 'public',
    'headers': {
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'apikey': SUPABASE_KEY
    },
    'autoRefreshToken': True,
    'persistSession': True,
    'detectSessionInUrl': True
}

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Erro ao criar cliente Supabase: {str(e)}")
    raise

# Função auxiliar para lidar com erros do Supabase
def handle_supabase_error(error):
    if isinstance(error, APIError):
        return f"Erro da API Supabase: {error.message}"
    return f"Erro inesperado: {str(error)}"
