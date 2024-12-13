from flask import *
from PL1.main import PL1
from PL2.main import solve_graph_coloring
from test import render_graph
import traceback
import numpy as np


app	= Flask(__name__)
app.secret_key = 'random string'

from flask import Flask, render_template, request, redirect, url_for, session
from gurobipy import Model, GRB
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Important for using session

class BlendingProblemSolver:
    @staticmethod
    def solve_blending_problem(ingredients, properties, property_bounds, total_quantity):
        try:
            # Create Gurobi model
            model = Model("Blending Problem")
            model.setParam('OutputFlag', 0)  # Suppress output

            # Number of ingredients
            n = len(ingredients)
            print(type(n),n)
            print(type(ingredients),ingredients)
            print(type(properties),properties)
            print(type(property_bounds),property_bounds)
            print(type(total_quantity),total_quantity)
            
            
            # Decision variables: quantity of each ingredient
            x = model.addVars(n, lb=0, name="ingredient_quantity")

            # Objective: Minimize total cost
            model.setObjective(
                sum(x[i] * ingredients[i]['cost_per_unit'] for i in range(n)), 
                GRB.MINIMIZE
            )

            # Constraint: Total quantity
            model.addConstr(sum(x[i] for i in range(n)) == total_quantity, "Total_Quantity")

            # Constraints: Availability of ingredients
            for i in range(n):
                model.addConstr(x[i] <= ingredients[i]['available_quantity'], f"Availability_{i}")

            # Constraints: Property bounds
            for prop_index, prop_name in enumerate(properties):
                prop_contribution = sum(
                    x[i] * ingredients[i]['properties'][prop_name] 
                    for i in range(n)
                )
                min_bound = property_bounds[prop_name]['min'] * total_quantity
                max_bound = property_bounds[prop_name]['max'] * total_quantity

                model.addConstr(prop_contribution >= min_bound, f"{prop_name}_Min")
                model.addConstr(prop_contribution <= max_bound, f"{prop_name}_Max")

            # Solve the model
            model.optimize()

            # Check solution status
            if model.status == GRB.OPTIMAL:
                results = {
                    'status': 'Optimal Solution Found',
                    'total_cost': model.objVal,
                    'ingredient_quantities': {},
                    'property_totals': {}
                }

                for i in range(n):
                    results['ingredient_quantities'][ingredients[i]['name']] = x[i].x

                for prop_name in properties:
                    prop_total = sum(
                        x[i].x * ingredients[i]['properties'][prop_name] 
                        for i in range(n)
                    )
                    results['property_totals'][prop_name] = prop_total

                return results
            else:
                return {'status': 'No optimal solution found'}
        except Exception as e:
            return {'status': f'Error: {str(e)}'}

# Flask Routes
@app.route('/PL1', methods=['GET', 'POST'])
def index():
    """Initial page to set up problem parameters"""
    if request.method == 'POST':
        # Store problem parameters in session
        session['num_ingredients'] = int(request.form['num_ingredients'])
        session['num_properties'] = int(request.form['num_properties'])
        session['total_quantity'] = float(request.form['total_quantity'])
        
        return redirect(url_for('input_ingredients'))
    
    return render_template('PL1.html')

@app.route('/input_ingredients', methods=['GET', 'POST'])
def input_ingredients():
    """Page to input ingredient details"""
    num_ingredients = session.get('num_ingredients', 0)
    
    if request.method == 'POST':
        # Collect ingredient data
        ingredients = []
        for i in range(num_ingredients):
            ingredient = {
                'name': request.form[f'ingredient_name_{i}'],
                'cost_per_unit': float(request.form[f'cost_per_unit_{i}']),
                'available_quantity': float(request.form[f'available_quantity_{i}'])
            }
            ingredients.append(ingredient)
        
        # Store ingredients in session
        session['ingredients'] = ingredients
        
        return redirect(url_for('input_properties'))
    
    return render_template('input_ingredients.html', num_ingredients=num_ingredients)

@app.route('/input_properties', methods=['GET', 'POST'])
def input_properties():
    """Page to input property details for ingredients"""
    num_ingredients = session.get('num_ingredients', 0)
    num_properties = session.get('num_properties', 0)
    ingredients = session.get('ingredients', [])
    
    if request.method == 'POST':
        # Collect property data for ingredients
        for i, ingredient in enumerate(ingredients):
            properties = {}
            for j in range(num_properties):
                prop_name = request.form[f'property_name_{j}']
                prop_value = float(request.form[f'ingredient_{i}_property_{j}'])
                properties[prop_name] = prop_value
            ingredients[i]['properties'] = properties
        
        # Store updated ingredients
        session['ingredients'] = ingredients
        
        return redirect(url_for('input_property_bounds'))
    
    # If this is the first time, create property names
    if request.method == 'GET':
        default_properties = [f'Property {i+1}' for i in range(num_properties)]
        return render_template(
            'input_properties.html', 
            num_ingredients=num_ingredients, 
            num_properties=num_properties,
            ingredients=ingredients,
            default_properties=default_properties
        )

@app.route('/input_property_bounds', methods=['GET', 'POST'])
def input_property_bounds():
    """Page to set property bounds for final product"""
    num_properties = session.get('num_properties', 0)
    ingredients = session.get('ingredients', [])
    total_quantity = session.get('total_quantity', 0)
    
    # Extract property names from first ingredient
    properties = list(ingredients[0]['properties'].keys())
    
    if request.method == 'POST':
        # Collect property bounds
        property_bounds = {}
        for prop in properties:
            property_bounds[prop] = {
                'min': float(request.form[f'{prop}_min']),
                'max': float(request.form[f'{prop}_max'])
            }
        
        # Solve the blending problem
        solver = BlendingProblemSolver()
        result = solver.solve_blending_problem(
            ingredients, 
            properties, 
            property_bounds, 
            total_quantity
        )
        print(result)
        # Store result in session for display
        session['result'] = result
        
        return redirect(url_for('solution'))
    
    return render_template(
        'input_property_bounds.html', 
        properties=properties,
        total_quantity=total_quantity
    )

@app.route('/solution')
def solution():
    """Display optimization results"""
    result = session.get('result', {})
    return render_template('solve.html', result=result)


@app.route('/')
def home():
    return render_template('index.html') 

# @app.route('/PL1', methods=['GET','POST'])
# def PL_1():
    
#     if request.method == 'POST':
#         # Nombre d'ingrédients
#         n = int(request.form['n'])
#         # Nombre de propriétés
#         m = int(request.form['m'])
#         # Coûts des ingrédients
#         costs = [(request.form[f"cost{i+1}"]) for i in range(n)]
#         # Contributions des ingrédients aux propriétés
#         contributions = [[(request.form[f"contrib{i+1}{j+1}"]) for i in range(n)] for j in range(m)]
#         # Valeurs minimales des propriétés
#         property_min = [(request.form[f"property_min{j+1}"]) for j in range(m)]
#         # Valeurs maximales des propriétés
#         property_max = [(request.form[f"property_max{j+1}"]) for j in range(m)]
#         # Quantité totale du mélange
#         total_quantity = (request.form['total_quantity'])

#         availabilities = [(request.form[f"availability{i+1}"]) for i in range(n)]

#         # Résoudre le problème
#         try:
#             result = PL1(n=n, m=m, costs=costs, contributions=contributions, property_min=property_min, property_max=property_max, total_quantity=total_quantity, availabilities=availabilities)
#             return render_template('index.html', result=result)
#         except Exception as e:
#             error_details = traceback.format_exc()  # Get the full error traceback as a string
#             return render_template('index.html', error=error_details)
#     return render_template('PL1.html')

@app.route("/PL2", methods=["GET", "POST"])
def index2():
    if request.method == "POST":
        # Get the number of vertices and edges
        try:
            num_vertices = int(request.form["num_vertices"])
            num_edges = int(request.form["num_edges"])
            if num_vertices < 0 or num_edges < 0:
                raise ValueError
        except ValueError:
            return render_template("index2.html", error="Please enter a valid number of vertices and edges.")
            
        # Parse edges
        try:
            edges = []
            for i in range(num_edges):
                edge = request.form[f"edge_{i}"].split()
                edges.append((int(edge[0]), int(edge[1])))
        except (IndexError, ValueError, KeyError):
            return render_template("index2.html", error="Please enter valid edges.")

        # Solve the graph coloring problem
        try: 
            solution, num_colors = solve_graph_coloring(num_vertices, edges)
            render_graph(edges, solution)
        except Exception as e:
            return render_template("index2.html", error="No solution. Please check your input.")
  
        print(solution, num_colors)
        return render_template("result.html",solution=solution, num_colors=num_colors)
    return render_template("index2.html")

if __name__ == '__main__':
    app.run(debug=True)
    # PL1()