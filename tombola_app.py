
from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'supersecretkey'
FILENAME = 'tombola_entries.csv'

# --- Helper functions ---
def write_to_csv(entry):
    file_exists = os.path.isfile(FILENAME)
    with open(FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "DateOfBirth", "Length", "Weight", "Gender"])
        writer.writerow(entry)

def read_entries():
    if not os.path.isfile(FILENAME):
        return []
    with open(FILENAME, mode='r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def clear_entries():
    if os.path.isfile(FILENAME):
        os.remove(FILENAME)

def calculate_winner(actual):
    entries = read_entries()
    if not entries:
        return None, []

    def distance(entry):
        try:
            length_diff = abs(float(entry["Length"]) - actual["Length"]) / 1.0
            weight_diff = abs(float(entry["Weight"]) - actual["Weight"]) / 50.0
            date_diff = abs((datetime.strptime(entry["DateOfBirth"], "%Y-%m-%d") - actual["DateOfBirth"]).days) / 1.0
            gender_penalty = 0 if entry["Gender"] == actual["Gender"] else 10
            return length_diff + weight_diff + date_diff + gender_penalty
        except:
            return float('inf')

    winner = min(entries, key=distance)
    return winner, entries

def plot_graphs(actual, winner_name):
    entries = read_entries()
    if not entries:
        return []

    names = [e["Name"] for e in entries]
    lengths = [float(e["Length"]) for e in entries]
    weights = [float(e["Weight"]) for e in entries]
    dates = [datetime.strptime(e["DateOfBirth"], "%Y-%m-%d") for e in entries]

    graphs = []

    def create_plot(title, y_data, actual_value, ylabel, diff=False):
        fig, ax = plt.subplots()
        ax.bar(names, y_data, color=['red' if n == winner_name else 'blue' for n in names])
        if diff:
            ax.axhline(0, color='green', linestyle='--', label="Actual")
        else:
            ax.axhline(actual_value, color='green', linestyle='--', label="Actual")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticklabels(names, rotation=45)
        ax.legend()
        fig.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return image

    graphs.append(create_plot("Length (cm)", lengths, actual["Length"], "Length (cm)"))
    graphs.append(create_plot("Weight (g)", weights, actual["Weight"], "Weight (g)"))
    date_diffs = [(d - actual["DateOfBirth"]).days for d in dates]
    graphs.append(create_plot("Date Difference (days)", date_diffs, 0, "Days from actual", diff=True))

    return graphs

# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/new', methods=['GET', 'POST'])
def new_entry():
    if request.method == 'POST':
        try:
            name = request.form['name']
            dob = request.form['dob']
            length = float(request.form['length'])
            weight = float(request.form['weight'])
            gender = request.form['gender']
            write_to_csv([name, dob, length, weight, gender])
            flash("Entry submitted successfully!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template('new_entry.html')

@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        try:
            actual = {
                "DateOfBirth": datetime.strptime(request.form['dob'], "%Y-%m-%d"),
                "Length": float(request.form['length']),
                "Weight": float(request.form['weight']),
                "Gender": request.form['gender']
            }
            winner, entries = calculate_winner(actual)
            graphs = plot_graphs(actual, winner['Name']) if winner else []
            return render_template('result.html', winner=winner, graphs=graphs)
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template('result_form.html')

@app.route('/entries')
def entries():
    data = read_entries()
    return render_template('entries.html', entries=data)

@app.route('/delete')
def delete():
    clear_entries()
    flash("All entries deleted.", "warning")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
