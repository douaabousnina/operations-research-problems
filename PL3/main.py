import gurobipy as gp
from gurobipy import GRB
import numpy as np

def solve_multi_product_inventory(periods, products, demands, holding_costs, ordering_costs, 
                                setup_costs, capacities, shared_capacity=None):
    """
    Solve a multi-period, multi-product inventory optimization problem
    
    Parameters:
    periods (int): Number of time periods
    products (int): Number of products
    demands (dict): Dictionary with (product, period) tuples as keys and demand values
    holding_costs (dict): Holding cost for each product
    ordering_costs (dict): Ordering cost per unit for each product
    setup_costs (dict): Fixed setup cost for ordering each product
    capacities (dict): Maximum inventory capacity for each product
    shared_capacity (float): Optional shared warehouse capacity constraint
    
    Returns:
    tuple: (order quantities, inventory levels, total cost)
    """
    
    # Create a new model
    model = gp.Model("Multi_Product_Inventory_Optimization")
    
    # Decision Variables
    order = model.addVars(products, periods, lb=0, vtype=GRB.CONTINUOUS, name="order")
    inventory = model.addVars(products, periods, lb=0, name="inventory")
    y = model.addVars(products, periods, vtype=GRB.BINARY, name="setup")
    
    # Objective Function
    obj = (gp.quicksum(ordering_costs[p] * order[p,t] + setup_costs[p] * y[p,t] + 
           holding_costs[p] * inventory[p,t] 
           for p in range(products) for t in range(periods)))
    model.setObjective(obj, GRB.MINIMIZE)
    
    # Constraints
    # Initial inventory (assuming zero for all products)
    initial_inventory = {p: 0 for p in range(products)}
    
    # Inventory balance constraints for each product
    for p in range(products):
        # First period
        model.addConstr(inventory[p,0] == initial_inventory[p] + order[p,0] - demands[p,0])
        
        # Subsequent periods
        for t in range(1, periods):
            model.addConstr(inventory[p,t] == inventory[p,t-1] + order[p,t] - demands[p,t])
    
    # Individual capacity constraints for each product
    for p in range(products):
        for t in range(periods):
            model.addConstr(inventory[p,t] <= capacities[p])
    
    # Shared warehouse capacity constraint (if specified)
    if shared_capacity is not None:
        for t in range(periods):
            model.addConstr(gp.quicksum(inventory[p,t] for p in range(products)) <= shared_capacity)
    
    # Setup constraints for each product
    M = {p: sum(demands[p,t] for t in range(periods)) for p in range(products)}  # Big M values
    for p in range(products):
        for t in range(periods):
            model.addConstr(order[p,t] <= M[p] * y[p,t])
    
    # Optimize the model
    model.optimize()
    
    # Extract results
    order_quantities = {(p,t): order[p,t].X for p in range(products) for t in range(periods)}
    inventory_levels = {(p,t): inventory[p,t].X for p in range(products) for t in range(periods)}
    total_cost = model.ObjVal
    
    return order_quantities, inventory_levels, total_cost

def print_multi_product_solution(order_quantities, inventory_levels, total_cost, periods, products):
    """Print the solution in a formatted way"""
    print("\nOptimal Solution:")
    print("-" * 70)
    print("Product\tPeriod\tOrder Qty\tInventory Level")
    print("-" * 70)
    for p in range(products):
        for t in range(periods):
            print(f"{p+1}\t{t+1}\t{order_quantities[p,t]:.2f}\t\t{inventory_levels[p,t]:.2f}")
        print("-" * 70)
    print(f"Total Cost: ${total_cost:.2f}")

# Example usage
if __name__ == "__main__":
    # Example problem parameters
    periods = 4
    products = 3
    
    # Create sample data
    demands = {
        (0,t): [10, 20, 15, 7][t] for t in range(periods)  # Product 0
    }
    demands.update({
        (1,t): [30, 45, 20, 15][t] for t in range(periods)    # Product 1
    })
    demands.update({
        (2,t): [19, 14, 20, 8][t] for t in range(periods)  # Product 2
    })
    
    holding_costs = {0: 2, 1: 3, 2: 2.5}      # Cost per unit per period
    ordering_costs = {0: 3, 1: 4, 2: 3.5}     # Cost per unit ordered
    setup_costs = {0: 100, 1: 120, 2: 110}    # Fixed cost per order
    capacities = {0: 500, 1: 400, 2: 600}     # Individual product capacity limits
    shared_capacity = 1200                     # Total warehouse capacity
    
    # Solve the problem
    orders, inventory, cost = solve_multi_product_inventory(
        periods, products, demands, holding_costs, ordering_costs,
        setup_costs, capacities, shared_capacity
    )
    
    # Print results
    print_multi_product_solution(orders, inventory, cost, periods, products)