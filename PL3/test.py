import gurobipy as gp
from gurobipy import GRB

def solve_multi_product_inventory(periods, products, demands, holding_costs, ordering_costs, 
                                setup_costs, capacities, expiration_periods, shared_capacity=None):
    """
    Solve a multi-period, multi-product inventory optimization problem with expiration dates
    
    Parameters:
    periods (int): Number of time periods
    products (int): Number of products
    demands (dict): Dictionary with (product, period) tuples as keys and demand values
    holding_costs (dict): Holding cost for each product
    ordering_costs (dict): Ordering cost per unit for each product
    setup_costs (dict): Fixed setup cost for ordering each product
    capacities (dict): Maximum inventory capacity for each product
    expiration_periods (dict): Number of periods each product can be stored before expiring
    shared_capacity (float): Optional shared warehouse capacity constraint
    """
    try:
        model = gp.Model("Multi_Product_Inventory_Optimization")
        
        # Decision Variables
        order = model.addVars(products, periods, lb=0, vtype=GRB.CONTINUOUS, name="order")
        inventory = model.addVars(products, periods, lb=0, vtype=GRB.CONTINUOUS, name="inventory")
        y = model.addVars(products, periods, vtype=GRB.BINARY, name="setup")
        
        # Objective Function: Minimize total costs (excluding inventory level)
        obj = (gp.quicksum(ordering_costs[p] * order[p,t] + 
                          setup_costs[p] * y[p,t] 
                          for p in range(products) 
                          for t in range(periods)))
        model.setObjective(obj, GRB.MINIMIZE)
        
        # Initial inventory constraints (start with zero)
        for p in range(products):
            model.addConstr(inventory[p,0] == order[p,0] - demands[p,0])
        
        # Inventory balance constraints
        for p in range(products):
            for t in range(1, periods):
                model.addConstr(inventory[p,t] == inventory[p,t-1] + order[p,t] - demands[p,t])
        
        # Expiration constraints
        for p in range(products):
            for t in range(periods):
                if t >= expiration_periods[p]:
                    start_period = max(0, t - expiration_periods[p] + 1)
                    total_old_inventory = gp.quicksum(order[p,k] for k in range(start_period, t+1))
                    model.addConstr(inventory[p,t] <= total_old_inventory)
        
        # Individual capacity constraints
        for p in range(products):
            for t in range(periods):
                model.addConstr(inventory[p,t] <= capacities[p])
        
        # Shared warehouse capacity constraint
        if shared_capacity is not None:
            for t in range(periods):
                model.addConstr(gp.quicksum(inventory[p,t] for p in range(products)) <= shared_capacity)
        
        # Setup constraints (order only when y is 1)
        M = {p: sum(demands[p,t] for t in range(periods)) for p in range(products)}
        for p in range(products):
            for t in range(periods):
                model.addConstr(order[p,t] <= M[p] * y[p,t])
        
        # Non-negative inventory
        for p in range(products):
            for t in range(periods):
                model.addConstr(inventory[p,t] >= 0)
        
        # Optimize
        model.optimize()
        
        # Check solution status
        if model.Status == GRB.OPTIMAL:
            # Extract results
            order_quantities = {(p,t): order[p,t].X for p in range(products) for t in range(periods)}
            inventory_levels = {(p,t): inventory[p,t].X for p in range(products) for t in range(periods)}
            total_cost = model.ObjVal
            
            print(order_quantities,"\n", inventory_levels,"\n", total_cost)
            return order_quantities, inventory_levels, total_cost
        
        else:
            print(f"Optimization failed with status {model.Status}")
            return None, None, None
            
    except gp.GurobiError as e:
        print(f"Gurobi error: {e}")
        return None, None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

def print_solution(order_quantities, inventory_levels, total_cost, periods, products):
    """Print the solution in a formatted way"""
    if order_quantities is None:
        print("No solution to display")
        return
        
    print("\nOptimal Solution:")
    print("-" * 70)
    print("Product | Period | Order Quantity | Inventory Level")
    print("-" * 70)
    
    for p in range(products):
        for t in range(periods):
            print(f"{p+1:7d} | {t+1:6d} | {order_quantities[p,t]:13.2f} | {inventory_levels[p,t]:14.2f}")
        print("-" * 70)
    print(f"\nTotal Cost: ${total_cost:,.2f}")

# Example usage
if __name__ == "__main__":
  
    periods = 4
    products = 3
    
    # Demand for each product in each period
    demands = {
        (0,t): [10, 20, 15, 7][t] for t in range(periods)    # Product 0
    }
    demands.update({
        (1,t): [30, 45, 20, 15][t] for t in range(periods)   # Product 1
    })
    demands.update({
        (2,t): [19, 14, 20, 8][t] for t in range(periods)    # Product 2
    })
    
    # Costs and constraints
    holding_costs = {0: 2, 1: 3, 2: 2}          # Holding cost per unit per period
    ordering_costs = {0: 3, 1: 4, 2: 3}         # Cost per unit ordered
    setup_costs = {0: 100, 1: 120, 2: 110}        # Fixed cost per order
    capacities = {0: 50, 1: 60, 2: 70}            # Individual capacity limits
    shared_capacity = 150                          # Total warehouse capacity
    expiration_periods = {0: 1, 1: 4, 2: 4}       # Shelf life in periods
    
    # Solve the problem
    orders, inventory, cost = solve_multi_product_inventory(
        periods=periods,
        products=products,
        demands=demands,
        holding_costs=holding_costs,
        ordering_costs=ordering_costs,
        setup_costs=setup_costs,
        capacities=capacities,
        expiration_periods=expiration_periods,
        shared_capacity=shared_capacity
    )
    
    # Display results
    print_solution(orders, inventory, cost, periods, products)
