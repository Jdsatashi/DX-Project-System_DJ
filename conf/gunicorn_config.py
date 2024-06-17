command = '/home/jdsatashi/dx-backend/venv/bin/gunicorn'
pythonpath = '/home/jdsatashi/dx-backend/src'
bind = '0.0.0.0:8000'
worker = 3
app = 'app.wsgi.application'
http_protocol = "h2"
