from flask import Flask, render_template, request, redirect, url_for
from peewee import Model, CharField, IntegerField, SqliteDatabase
import pandas as pd
import matplotlib.pyplot as plt
import csv
import os

# Inicializē Flask lietotni
app = Flask(__name__)

# Iestata SQLite datubāzi
db = SqliteDatabase('database.db')

# Definē Peewee modeli
class BaseModel(Model):
    class Meta:
        database = db

class Data(BaseModel):
    name = CharField()
    age = IntegerField()

# Savienojās ar datubāzi
db.connect()
db.create_tables([Data])

@app.route('/')
def home():
    records = Data.select()  # Iegūst visus ierakstus no datubāzes
    return render_template('index.html', records=records)

@app.route('/add', methods=['POST'])
def add_record():
    # Pievieno jaunu ierakstu datubāzei
    name = request.form.get('name')
    age = request.form.get('age')
    Data.create(name=name, age=int(age))  # Pievieno datubāzei
    return redirect(url_for('home'))  # Novirza atpakaļ uz sākumlapu

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_record(id):
    record = Data.get(Data.id == id)  # Iegūst ierakstu pēc ID
    if request.method == 'POST':
        record.name = request.form.get('name')  # Atjaunina vārdu
        record.age = int(request.form.get('age'))  # Atjaunina vecumu
        record.save()  # Saglabā izmaiņas datubāzē
        return redirect(url_for('home'))
    return render_template('update.html', record=record)

@app.route('/delete/<int:id>')
def delete_record(id):
    record = Data.get(Data.id == id)  # Iegūst ierakstu pēc ID
    record.delete_instance()  # Dzēš ierakstu
    return redirect(url_for('home'))  # Novirza atpakaļ uz sākumlapu

@app.route('/data-visualization')
def data_visualization():
    # Pārbauda, vai eksistē 'data.csv' fails
    file_path = 'data.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        
        # Pārliecinās, ka 'Revenue (Millions)' kolonna ir skaitliska
        df['Revenue (Millions)'] = pd.to_numeric(df['Revenue (Millions)'], errors='coerce')
        
        # Izmet rindas ar NaN vērtībām 'Revenue (Millions)' kolonnā
        df = df.dropna(subset=['Revenue (Millions)'])
        
        # Izveido histogrammu
        plt.figure(figsize=(10, 6))
        df['Revenue (Millions)'].plot(kind='hist', bins=10, color='skyblue', edgecolor='black')
        plt.title('Histogramma: Novērtējums vs ieņēmumi')
        plt.xlabel('Ieņēmumi (Miljoni)')
        plt.ylabel('Novērtējums')

        # Saglabā grafiku kā attēlu
        plt.savefig('static/age_histogram.png')
        return render_template('data-visualization.html')
    else:
        return f"Kļūda: fails '{file_path}' netika atrasts."
    
@app.route('/page1')
def genre_bar_chart():
    # Pārbauda, vai eksistē 'data.csv' fails
    file_path = 'data.csv'
    if os.path.exists(file_path):
        # Ielādē CSV failu
        df = pd.read_csv(file_path)

        # Saskaita žanra ierakstus
        genre_counts = df['Genre'].value_counts()

        # Izveido stabiņu diagrammu
        plt.figure(figsize=(10, 6))
        genre_counts.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.title('Stabiņu diagramma: Filmu žanrs vs skaits')
        plt.xlabel('Žanrs')
        plt.ylabel('Skaits')
        plt.xticks(rotation=45, ha='right')

        # Saglabā stabiņu diagrammu kā attēlu 'static' mapē
        chart_path = 'static/chart_path.png'
        plt.savefig(chart_path)
        plt.close()  # Aizver grafiku, lai atbrīvotu atmiņu

        # Attēlot HTML lapu
        return render_template('page1.html', chart_path=chart_path)
    else:
        return f"Kļūda: fails '{file_path}' netika atrasts."
    
@app.route('/page2')
def scatter_year_revenue():
    # Pārbauda, vai eksistē 'data.csv' fails
    file_path = 'data.csv'
    if os.path.exists(file_path):
        # Ielādē CSV failu
        df = pd.read_csv(file_path)

        # Pārliecinās, ka vajadzīgās kolonnas ir skaitliskas
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Revenue (Millions)'] = pd.to_numeric(df['Revenue (Millions)'], errors='coerce')

        # Izmet rindas ar NaN vērtībām vajadzīgajās kolonnās
        df = df.dropna(subset=['Year', 'Revenue (Millions)'])

        # Izveido izkliedes diagrammu
        plt.figure(figsize=(10, 6))
        plt.scatter(df['Year'], df['Revenue (Millions)'], color='orange', edgecolors='black')
        plt.title('Izkliedes diagramma: Gads vs Ieņēmumi')
        plt.xlabel('Gads')
        plt.ylabel('Ieņēmumi (Miljoni)')
        plt.grid(True)

        # Saglabā izkliedes diagrammu kā attēlu 'static' mapē
        scatter_path = 'static/scatter_year_revenue.png'
        plt.savefig(scatter_path)
        plt.close()  # Aizver grafiku, lai atbrīvotu atmiņu

        # Attēlo HTML lapu (izveido 'scatter-year-revenue.html', lai attēlotu grafiku)
        return render_template('page2.html', scatter_path=scatter_path)
    else:
        return f"Kļūda: fails '{file_path}' netika atrasts."

@app.route('/upload-csv', methods=['POST']) # Šeit var augšupielādēt CSV failus, lai automātiski importētu tajos esošos datus datubāzē.
def upload_csv():
    file = request.files['file']
    filename = 'uploaded_data.csv'
    file.save(filename)  # Saglabā augšupielādēto failu

    # Atver un apstrādā CSV failu
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            # Izveido jaunus ierakstus datubāzē
            Data.create(name=row[0], age=row[1])

    return 'CSV fails augšupielādēts un dati apstrādāti', 200

@app.route('/database')
def database_view():
    data_records = Data.select()
    data_list = [f"{record.name}, {record.age}" for record in data_records]
    return render_template('database.html', data_list=data_list)

if __name__ == '__main__':
    app.run(debug=True)
