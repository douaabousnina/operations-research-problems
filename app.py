from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from gurobipy import Model, GRB
import traceback
from PL2.main import solve_graph_coloring
from test import render_graph
from PL1.main import solve_blending_problem
from PL3.main import solve_multi_product_inventory

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for using session data


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
            try:
                ingredient = {
                    'name': request.form[f'ingredient_name_{i}'],
                    'cost_per_unit': float(request.form[f'cost_per_unit_{i}']),
                    'available_quantity': float(request.form[f'available_quantity_{i}']),
                    'properties': {}  # Placeholder for properties
                }
                ingredients.append(ingredient)
            except ValueError as e:
                return render_template('input_ingredients.html', 
                                       num_ingredients=num_ingredients, 
                                       error=f"Invalid input for ingredient {i}: {str(e)}")
        
        session['ingredients'] = ingredients
        return redirect(url_for('property_naming'))
    
    return render_template('input_ingredients.html', num_ingredients=num_ingredients)

@app.route('/property_naming', methods=['GET', 'POST'])
def property_naming():
    """Page to name the properties before inputting their percentages"""
    num_properties = session.get('num_properties', 0)

    if request.method == 'POST':
        # Collect property names
        property_names = [request.form[f'property_name_{i}'] for i in range(num_properties)]
        session['property_names'] = property_names
        return redirect(url_for('input_properties'))
    
    return render_template('property_naming.html', num_properties=num_properties)

@app.route('/input_properties', methods=['GET', 'POST'])
def input_properties():
    num_properties = session.get('num_properties', 0)
    """Page to input property details for ingredients"""
    num_ingredients = session.get('num_ingredients', 0)
    ingredients = session.get('ingredients', [])
    property_names = session.get('property_names', [])

    if request.method == 'POST':
        # Collect property data for ingredients
        for i, ingredient in enumerate(ingredients):
            for j, prop_name in enumerate(property_names):
                prop_value = float(request.form[f'ingredient_{i}_property_{j}'])
                ingredient['properties'][prop_name] = prop_value
        session['ingredients'] = ingredients
        return redirect(url_for('input_property_bounds'))
    
    return render_template(
        'input_properties.html', 
        num_ingredients=num_ingredients, 
        num_properties=num_properties,
        ingredients=ingredients,
        property_names=property_names,
        enumerate=enumerate  # Pass enumerate to the template
    )

@app.route('/input_property_bounds', methods=['GET', 'POST'])
def input_property_bounds():
    """Page to set property bounds for final product"""
    property_names = session.get('property_names', [])
    total_quantity = session.get('total_quantity', 0)

    if request.method == 'POST':
        # Collect property bounds
        property_bounds = {
            prop: {
                'min': float(request.form[f'{prop}_min']),
                'max': float(request.form[f'{prop}_max'])
            }
            for prop in property_names
        }
        session['property_bounds'] = property_bounds

        # Solve the blending problem
        
        result = solve_blending_problem(
            session.get('ingredients', []),
            property_names,
            property_bounds,
            total_quantity
        )
        session['result'] = result
        return redirect(url_for('solution'))

    return render_template('input_property_bounds.html', property_names=property_names, total_quantity=total_quantity)

@app.route('/solution')
def solution():
    """Display optimization results"""
    result = session.get('result', {})
    return render_template('solve.html', result=result)



@app.route('/')
def home():
    return render_template('index.html')



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




@app.route('/PL3', methods=['GET', 'POST'])
def PL3():
    if request.method == 'POST':
        # Retrieve number of periods and products
        periods = int(request.form['periods'])
        products = int(request.form['products'])

        # Redirect to the product names page
        return redirect(url_for('PL3_names', periods=periods, products=products))

    return render_template('PL3.html')


@app.route('/PL3/names', methods=['GET', 'POST'])
def PL3_names():
    periods = int(request.args.get('periods'))
    products = int(request.args.get('products'))

    if request.method == 'POST':
        # Retrieve product names and pass them to the details form
        product_names = [request.form[f'product_name_{i}'] for i in range(1, products + 1)]
        return redirect(url_for('PL3_details', periods=periods, products=products, product_names=','.join(product_names)))

    return render_template('PL3_names.html', periods=periods, products=products)


@app.route('/PL3/details', methods=['GET', 'POST'])
def PL3_details():
    periods = int(request.args.get('periods'))
    products = int(request.args.get('products'))
    product_names = request.args.get('product_names').split(',')

    if request.method == 'POST':
        demands = {(p, t): float(request.form[f'demand_{p}_{t}']) 
                   for p in range(products) for t in range(periods)}
        holding_costs = {p: float(request.form[f'holding_cost_{p}']) for p in range(products)}
        ordering_costs = {p: float(request.form[f'ordering_cost_{p}']) for p in range(products)}
        setup_costs = {p: float(request.form[f'setup_cost_{p}']) for p in range(products)}
        capacities = {p: float(request.form[f'capacity_{p}']) for p in range(products)}
        expiration_periods = {p: int(request.form[f'expiration_{p}']) for p in range(products)}
        shared_capacity = float(request.form['shared_capacity']) if 'shared_capacity' in request.form else None

        order_quantities, inventory_levels, total_cost = solve_multi_product_inventory(
            periods, products, demands, holding_costs, ordering_costs,
            setup_costs, capacities, expiration_periods, shared_capacity
        )

        if order_quantities is None:
            return render_template('PL3_details.html', error="Optimization failed.", periods=periods, products=products, product_names=product_names)

        return render_template('PL3_results.html', 
                               order_quantities=order_quantities, 
                               inventory_levels=inventory_levels, 
                               total_cost=total_cost,
                               product_names=product_names)

    return render_template('PL3_details.html', periods=periods, products=products, product_names=product_names)





if __name__ == '__main__':
    app.run(debug=True)
