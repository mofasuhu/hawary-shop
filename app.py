import os
from dotenv import load_dotenv

# Load environment variables from Local.env if it exists, otherwise from .env
if os.path.exists('Local.env'):
    load_dotenv('Local.env')
else:
    load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    default_host = '0.0.0.0'
    default_debug = False
    host = os.getenv('HOST', default_host)
    port = int(os.getenv('PORT', 5000))
    debug = bool(os.getenv('FLASK_DEBUG', default_debug))
    
    app.run(debug=debug, host=host, port=port)
