from flask import *
from PL1.main import PL1
app	= Flask(__name__)
app.secret_key = 'random string'

@app.route('/')
def home():
    return render_template('index.html') 

@app.route('/PL1', methods=['GET','POST'])
def PL1():
    
    if request.method == 'POST':
        # Nombre d'ingrédients
        n = int(request.form['n'])
        # Nombre de propriétés
        m = int(request.form['m'])
        # Coûts des ingrédients
        costs = [float(request.form[f"cost{i+1}"]) for i in range(n)]
        # Contributions des ingrédients aux propriétés
        contributions = [[float(request.form[f"contrib{i+1}{j+1}"]) for i in range(n)] for j in range(m)]
        # Valeurs minimales des propriétés
        property_min = [float(request.form[f"property_min{j+1}"]) for j in range(m)]
        # Valeurs maximales des propriétés
        property_max = [float(request.form[f"property_max{j+1}"]) for j in range(m)]
        # Quantité totale du mélange
        total_quantity = float(request.form['total_quantity'])

        # Résoudre le problème
        try:
            result = PL1(n=n, m=m, costs=costs, contributions=contributions, property_min=property_min, property_max=property_max, total_quantity=total_quantity)
            return render_template('result.html', result=result)
        except Exception as e:
            return render_template('error.html', error=e)
    return render_template('PL1.html')

if __name__ == '__main__':
    app.run(debug=True)
    # PL1()