import os

import dotenv

dotenv.load_dotenv()

APP_SERVER = os.environ.get('APP_SERVER')
