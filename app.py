# app.py
from flask import Flask, request, jsonify, render_template_string
from src.parser import StatementParser
import os
import json

app = Flask(__name__)
UPLOAD_FOLDER = "/tmp"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Sure Financial - Credit Card Parser</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui; margin: 2rem; background: #f8f9fa; }
    .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 800px; margin: auto; }
    input, select, button { padding: 12px; margin: 8px 0; width: 100%; border: 1px solid #ddd; border-radius: 8px; }
    button { background: #007bff; color: white; font-weight: bold; cursor: pointer; }
    button:hover { background: #0056b3; }
    pre { background: #f1f3f5; padding: 1rem; border-radius: 8px; overflow: auto; }
    .logo { font-size: 1.5rem; font-weight: bold; color: #007bff; margin-bottom: 1rem; }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">Sure.Financial Parser</div>
    <h2>Upload Credit Card Statement</h2>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept=".pdf" required>
      <select name="issuer">
        <option value="auto">Auto Detect</option>
        <option value="hdfc">HDFC</option>
        <option value="icici">ICICI</option>
        <option value="sbi">SBI</option>
        <option value="axis">Axis</option>
        <option value="kotak">Kotak</option>
      </select>
      <button type="submit">Parse Statement</button>
    </form>
    {% if result %}
    <h3>Extracted Data:</h3>
    <pre>{{ result }}</pre>
    {% endif %}
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if not file or not file.filename.endswith(".pdf"):
            return "Invalid file", 400
        
        path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(path)
        
        try:
            parser = StatementParser(path)
            data = parser.parse()
            os.remove(path)
            return render_template_string(HTML, result=json.dumps(data, indent=2))
        except Exception as e:
            os.remove(path)
            return f"Error: {str(e)}", 500
    
    return render_template_string(HTML, result=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)