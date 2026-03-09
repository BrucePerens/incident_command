import os
import csv
from flask import Flask, jsonify, request, render_template_string, Response

app = Flask(__name__)
DATA_DIR = 'data'
INDEX_FILE = os.path.join(DATA_DIR, 'Index.csv')

# ==========================================
# APIs
# ==========================================

@app.route('/api/forms', methods=['GET'])
def list_forms():
    """API to list the forms via the data in Index.csv"""
    forms = []
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    form_id = row[0].strip()
                    desc = row[1].strip()
                    forms.append({
                        "id": form_id, 
                        "description": desc, 
                        "display": f"{form_id} - {desc}"
                    })
    return jsonify(forms)

@app.route('/api/forms/<path:form_id>', methods=['GET'])
def get_form_html(form_id):
    """API to provide the form HTML to another module or the native interface"""
    html_file = os.path.join(DATA_DIR, f"{form_id}.html")
    if os.path.exists(html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='text/html')
    return jsonify({"error": "Form HTML not found"}), 404

@app.route('/api/email', methods=['POST'])
def email_form():
    """API to email the CSV and PDF data."""
    data = request.json
    form_id = data.get('form_id')
    email_addr = data.get('email')
    csv_content = data.get('csv_content')
    filename = data.get('filename', f"{form_id}_data")
    
    # Simulating email logic
    print(f"Simulating email to {email_addr} for Form {form_id}")
    print(f"Attachments would be named: {filename}.pdf and {filename}.csv")
    return jsonify({"status": "success", "message": f"Email queued for {email_addr} with attachment base name: {filename}"})

# ==========================================
# Native Interface
# ==========================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ICS Forms Module</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #fff;
        }
        .toolbar { 
            margin-bottom: 20px; 
            padding: 15px; 
            background: #f4f4f4; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
        }
        .toolbar select, .toolbar button, .toolbar input { 
            margin-right: 10px; 
            padding: 5px; 
        }
        
        #form-container { 
            border: 1px solid #ccc; 
            padding: 0 0 20px 0; 
            min-height: 500px; 
            width: 100%; 
            box-sizing: border-box;
            overflow-x: hidden;
            container-type: inline-size; 
        }
        
        #form-container form {
            width: 100% !important;
            margin: 0 !important;
        }

        #form-container h2 {
            color: #333 !important;
            padding: 20px;
            margin: 0;
            background: #eee;
        }
        
        #form-container .page-svg {
            width: 100% !important;
            height: 100% !important;
        }

        #form-container .form-field {
            font-size: 2.12cqi !important;
            /* Ensure padding doesn't block scroll calculations */
            box-sizing: border-box; 
        }

        #form-container input[type="submit"], 
        #form-container button[type="submit"] { 
            display: none !important; 
        }

        /* --- PRINT STYLES --- */
        @media print {
            .toolbar { 
                display: none !important; 
            }
            body { 
                margin: 0 !important; 
                padding: 0 !important; 
            }
            #form-container { 
                border: none !important; 
                padding: 0 !important; 
                margin: 0 !important;
            }
            #form-container h2 {
                display: none !important;
            }
        }
    </style>
</head>
<body>

    <div class="toolbar">
        <label for="form-select"><strong>Select Form:</strong></label>
        <select id="form-select" onchange="handleSelectChange(event)">
            <option value="">-- Loading Forms... --</option>
        </select>
        
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <button onclick="printPDF()">Print as PDF</button>
        <button onclick="downloadPDF()">Download as PDF</button>
        <button onclick="downloadCSV()">Download as CSV</button>
        <button onclick="downloadJSON()">Download JSON</button>
        <button onclick="triggerLoadJSON()">Load JSON</button>
        <input type="file" id="json-file-input" accept=".json" style="display: none;" onchange="handleLoadJSON(event)">
        
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <input type="email" id="email-input" placeholder="Enter email address">
        <button onclick="emailForm()">Email Completed Form</button>
    </div>

    <div id="form-container">
        <p style="padding: 20px;">Select a form from the dropdown to begin.</p>
    </div>

    <script>
        let currentFormId = "";
        let isDirty = false;

        window.onload = function() {
            fetch('/api/forms')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('form-select');
                    select.innerHTML = '<option value="">-- Select a Form --</option>';
                    data.forEach(form => {
                        let opt = document.createElement('option');
                        opt.value = form.id;
                        opt.textContent = form.display;
                        select.appendChild(opt);
                    });
                });
        };

        function handleSelectChange(event) {
            const select = event.target;
            const targetFormId = select.value;

            if (isDirty) {
                const abandon = confirm("Abandon your work on this form?");
                if (!abandon) {
                    select.value = currentFormId;
                    return;
                }
            }

            loadForm(targetFormId);
        }

        // --- TEXT SCALING HELPER ---
        
        function autoScaleText(element) {
            element.style.removeProperty('font-size');
            
            const computedStyle = window.getComputedStyle(element);
            let currentSize = parseFloat(computedStyle.fontSize);
            const minSize = 6; 
            
            if (element.tagName.toLowerCase() === 'input') {
                while (element.scrollWidth > element.clientWidth && currentSize > minSize) {
                    currentSize -= 0.5;
                    element.style.setProperty('font-size', currentSize + 'px', 'important');
                }
            } else if (element.tagName.toLowerCase() === 'textarea') {
                while (element.scrollHeight > element.clientHeight && currentSize > minSize) {
                    currentSize -= 0.5;
                    element.style.setProperty('font-size', currentSize + 'px', 'important');
                }
            }
        }

        function loadForm(formId) {
            const container = document.getElementById('form-container');

            if (!formId) {
                container.innerHTML = '<p style="padding: 20px;">Select a form from the dropdown to begin.</p>';
                currentFormId = "";
                isDirty = false;
                return Promise.resolve();
            }

            return fetch('/api/forms/' + formId)
                .then(response => {
                    if (!response.ok) throw new Error("Form HTML not found.");
                    return response.text();
                })
                .then(html => {
                    container.innerHTML = html;
                    currentFormId = formId;
                    isDirty = false;
                    
                    const pages = container.querySelectorAll('.page-container');
                    pages.forEach(page => {
                        const w = parseFloat(page.style.width) || 612;
                        const h = parseFloat(page.style.height) || 792;
                        
                        page.style.width = '100%';
                        page.style.height = 'auto';
                        page.style.aspectRatio = `${w} / ${h}`;
                    });
                    
                    const inputs = container.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => {
                        input.addEventListener('input', function() { 
                            isDirty = true; 
                            autoScaleText(this);
                        });
                        input.addEventListener('change', () => { isDirty = true; });
                        
                        if(input.value) {
                            autoScaleText(input);
                        }
                    });
                })
                .catch(err => {
                    container.innerHTML = `<p style="color:red; padding: 20px;">Error: ${err.message}</p>`;
                    document.getElementById('form-select').value = currentFormId;
                });
        }

        // --- FILENAME GENERATION HELPERS ---

        function getIncidentName() {
            const container = document.getElementById('form-container');
            const inputs = Array.from(container.querySelectorAll('input[type="text"], textarea'));
            
            let targetInput = inputs.find(i => {
                let n = (i.name || '').toLowerCase();
                let id = (i.id || '').toLowerCase();
                return (n.includes('incident') && n.includes('name')) || 
                       (id.includes('incident') && id.includes('name'));
            });

            if (!targetInput) {
                targetInput = inputs.find(i => {
                    let n = (i.name || '').toLowerCase();
                    let id = (i.id || '').toLowerCase();
                    return n.includes('incident') || id.includes('incident');
                });
            }

            if (!targetInput) {
                targetInput = inputs.find(i => i.name === 'field_1' || i.id === 'field_1');
            }

            if (targetInput && targetInput.value.trim() !== '') {
                return targetInput.value.trim().replace(/[^a-zA-Z0-9_-]/g, '_');
            }

            return 'None';
        }

        function generateExportFilename() {
            const formName = currentFormId || "Unknown_Form";
            const incidentName = getIncidentName();
            const isoDate = new Date().toISOString().replace(/[:\\.]/g, '-'); 
            
            return `${formName}_${incidentName}_${isoDate}`;
        }

        // --- EXPORT & IMPORT FUNCTIONS ---

        function getCSVData() {
            const container = document.getElementById('form-container');
            const inputs = container.querySelectorAll('input, select, textarea');
            
            let csv = currentFormId + "\\n";
            csv += "Field Name,Value\\n";
            
            inputs.forEach(input => {
                let name = input.name || input.id || 'Unnamed_Field';
                let value = input.value || '';
                value = value.replace(/"/g, '""');
                if (value.indexOf(',') > -1 || value.indexOf('\\n') > -1) {
                    value = `"${value}"`;
                }
                csv += `${name},${value}\\n`;
            });
            return csv;
        }

        function downloadCSV() {
            if (!currentFormId) return alert("Select a form first.");
            const filename = generateExportFilename() + '.csv';
            const csv = getCSVData();
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.setAttribute('hidden', '');
            a.setAttribute('href', url);
            a.setAttribute('download', filename);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            isDirty = false;
        }

        function downloadJSON() {
            if (!currentFormId) return alert("Select a form first.");
            
            const container = document.getElementById('form-container');
            const inputs = container.querySelectorAll('input, select, textarea');
            
            let formData = {};
            inputs.forEach(input => {
                let name = input.name || input.id;
                if (name) {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        formData[name] = input.checked;
                    } else {
                        formData[name] = input.value;
                    }
                }
            });

            const jsonObj = {
                form_id: currentFormId,
                data: formData
            };

            const jsonString = JSON.stringify(jsonObj, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.setAttribute('hidden', '');
            a.setAttribute('href', url);
            a.setAttribute('download', generateExportFilename() + '.json');
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            isDirty = false;
        }

        function triggerLoadJSON() {
            if (isDirty) {
                const abandon = confirm("Abandon your work on this form?");
                if (!abandon) return;
            }
            document.getElementById('json-file-input').click();
        }

        function handleLoadJSON(event) {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = async function(e) {
                try {
                    const jsonObj = JSON.parse(e.target.result);
                    const targetFormId = jsonObj.form_id;
                    const formData = jsonObj.data;

                    if (!targetFormId) {
                        alert("Invalid JSON format: Missing 'form_id'.");
                        return;
                    }

                    // Update UI dropdown
                    const select = document.getElementById('form-select');
                    select.value = targetFormId;

                    // Switch form if needed, wait for it to render
                    if (currentFormId !== targetFormId) {
                        await loadForm(targetFormId);
                    }

                    // Populate data
                    const container = document.getElementById('form-container');
                    for (const key in formData) {
                        const input = container.querySelector(`[name="${key}"], [id="${key}"]`);
                        if (input) {
                            if (input.type === 'checkbox' || input.type === 'radio') {
                                input.checked = formData[key];
                            } else {
                                input.value = formData[key];
                            }
                            autoScaleText(input);
                        }
                    }
                    
                    isDirty = false;
                } catch (err) {
                    alert("Error reading JSON file: " + err.message);
                } finally {
                    // Clear the file input so the same file can be re-loaded if necessary
                    event.target.value = "";
                }
            };
            reader.readAsText(file);
        }

        function printPDF() {
            if (!currentFormId) return alert("Select a form first.");
            
            const originalTitle = document.title;
            document.title = generateExportFilename();
            window.print();
            document.title = originalTitle;
            
            isDirty = false;
        }

        function downloadPDF() {
            if (!currentFormId) return alert("Select a form first.");
            
            const targetElement = document.querySelector('#form-container form') || document.getElementById('form-container');
            const heading = targetElement.querySelector('h2');
            if (heading) heading.style.display = 'none';

            const filename = generateExportFilename() + '.pdf';

            const opt = {
                margin:       0,
                filename:     filename,
                image:        { type: 'jpeg', quality: 1.0 },
                html2canvas:  { scale: 2, useCORS: true },
                jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
            };
            
            html2pdf().set(opt).from(targetElement).save().then(() => {
                if (heading) heading.style.display = '';
            });
            
            isDirty = false;
        }

        function emailForm() {
            if (!currentFormId) return alert("Select a form first.");
            const email = document.getElementById('email-input').value;
            if (!email) return alert("Please enter an email address.");

            const csvData = getCSVData();
            const filename = generateExportFilename();

            fetch('/api/email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    form_id: currentFormId,
                    email: email,
                    csv_content: csvData,
                    filename: filename
                })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                isDirty = false;
            })
            .catch(err => {
                alert("Error sending email.");
            });
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    """Native interface serving the HTML application."""
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    print("ICS Forms Module Starting...")
    print("Running on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
