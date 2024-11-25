from flask import *
from PL1.main import PL1
import traceback

app	= Flask(__name__)
app.secret_key = 'random string'

@app.route('/')
def home():
    return render_template('index.html') 

@app.route('/PL1', methods=['GET','POST'])
def PL_1():
    
    if request.method == 'POST':
        # Nombre d'ingrédients
        n = int(request.form['n'])
        # Nombre de propriétés
        m = int(request.form['m'])
        # Coûts des ingrédients
        costs = [(request.form[f"cost{i+1}"]) for i in range(n)]
        # Contributions des ingrédients aux propriétés
        contributions = [[(request.form[f"contrib{i+1}{j+1}"]) for i in range(n)] for j in range(m)]
        # Valeurs minimales des propriétés
        property_min = [(request.form[f"property_min{j+1}"]) for j in range(m)]
        # Valeurs maximales des propriétés
        property_max = [(request.form[f"property_max{j+1}"]) for j in range(m)]
        # Quantité totale du mélange
        total_quantity = (request.form['total_quantity'])

        availabilities = [(request.form[f"availability{i+1}"]) for i in range(n)]

        # Résoudre le problème
        try:
            result = PL1(n=n, m=m, costs=costs, contributions=contributions, property_min=property_min, property_max=property_max, total_quantity=total_quantity, availabilities=availabilities)
            return render_template('index.html', result=result)
        except Exception as e:
            error_details = traceback.format_exc()  # Get the full error traceback as a string
            return render_template('index.html', error=error_details)
    return render_template('PL1.html')

if __name__ == '__main__':
    app.run(debug=True)
    # PL1()