command = '/home/jdsatashi/dev/dx-backend/venv/bin/gunicorn'
pythonpath = '/home/jdsatashi/dev/dx-backend/src'
bind = '0.0.0.0:8000'
worker = 3
app = 'app.wsgi.application'
http_protocol = "h2"
