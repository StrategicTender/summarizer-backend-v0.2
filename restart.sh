pkill -f "python3 app.py"; export OPENAI_API_KEY=$(security find-generic-password -s OPENAI_API_KEY -w) && python3 app.py
