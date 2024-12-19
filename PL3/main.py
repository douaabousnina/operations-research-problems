import gurobipy as gp
from gurobipy import GRB

def solve_multi_product_inventory(periods, products, demands, holding_costs, ordering_costs, 
                                setup_costs, capacities, expiration_periods, shared_capacity=None, initial_inventory=None):
    """
    Solve a multi-period, multi-product inventory optimization problem with expiration dates,
    treating inventory levels as an input.

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
    initial_inventory (dict): Dictionary with (product, period) tuples as keys and initial inventory values
    """
    try:
        model = gp.Model("Multi_Product_Inventory_Optimization")
        
        # Decision Variables
        order = model.addVars(products, periods, lb=0, vtype=GRB.CONTINUOUS, name="order")
        y = model.addVars(products, periods, vtype=GRB.BINARY, name="setup")
        
        # Objective Function: Minimize total costs (ordering and setup)
        obj = (gp.quicksum(ordering_costs[p] * order[p,t] + 
                          setup_costs[p] * y[p,t] 
                          for p in range(products) 
                          for t in range(periods)))
        model.setObjective(obj, GRB.MINIMIZE)
        
        # Initial inventory constraints (provided as input)
        for p in range(products):
            for t in range(periods):
                if initial_inventory:
                    model.addConstr(order[p,t] + initial_inventory.get((p,t), 0) - demands.get((p,t), 0) >= 0)
        
        # Inventory balance constraints (based on initial inventory + order quantity - demand)
        for p in range(products):
            for t in range(1, periods):
                model.addConstr(order[p,t] + initial_inventory.get((p,t), 0) - demands.get((p,t), 0) >= 0)
        
        # Expiration constraints
        for p in range(products):
            for t in range(periods):
                if t >= expiration_periods[p]:
                    start_period = max(0, t - expiration_periods[p] + 1)
                    total_old_inventory = gp.quicksum(order[p,k] for k in range(start_period, t+1))
                    model.addConstr(order[p,t] <= total_old_inventory)
        
        # Individual capacity constraints
        for p in range(products):
            for t in range(periods):
                model.addConstr(order[p,t] <= capacities[p])
        
        # Shared warehouse capacity constraint
        if shared_capacity is not None:
            for t in range(periods):
                model.addConstr(gp.quicksum(order[p,t] for p in range(products)) <= shared_capacity)
        
        # Setup constraints (order only when y is 1)
        M = {p: sum(demands[p,t] for t in range(periods)) for p in range(products)}
        for p in range(products):
            for t in range(periods):
                model.addConstr(order[p,t] <= M[p] * y[p,t])
        
        # Optimize
        model.optimize()
        
        # Check solution status
        if model.Status == GRB.OPTIMAL:
            # Extract results
            order_quantities = {(p,t): order[p,t].X for p in range(products) for t in range(periods)}
            total_cost = model.ObjVal
            
            print(order_quantities, "\n", total_cost)
            return order_quantities, total_cost
        
        else:
            print(f"Optimization failed with status {model.Status}")
            return None, None
            
    except gp.GurobiError as e:
        print(f"Gurobi error: {e}")
        return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def print_solution(order_quantities, total_cost, periods, products):
    """Print the solution in a formatted way"""
    if order_quantities is None:
        print("No solution to display")
        return
        
    print("\nOptimal Solution:")
    print("-" * 70)
    print("Product | Period | Order Quantity")
    print("-" * 70)
    
    for p in range(products):
        for t in range(periods):
            print(f"{p+1:7d} | {t+1:6d} | {order_quantities[p,t]:13.2f}")
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
    
    # Initial Inventory: Provided as input (e.g., initial inventory levels for each product at each period)
    initial_inventory = {
        (0, 0): 5, (0, 1): 5, (0, 2): 5, (0, 3): 5,  # Initial inventory for product 0
        (1, 0): 10, (1, 1): 10, (1, 2): 10, (1, 3): 10,  # Initial inventory for product 1
        (2, 0): 20, (2, 1): 20, (2, 2): 20, (2, 3): 20   # Initial inventory for product 2
    }

    # Solve the problem
    orders, cost = solve_multi_product_inventory(
        periods=periods,
        products=products,
        demands=demands,
        holding_costs=holding_costs,
        ordering_costs=ordering_costs,
        setup_costs=setup_costs,
        capacities=capacities,
        expiration_periods=expiration_periods,
        shared_capacity=shared_capacity,
        initial_inventory=initial_inventory
    )
    
    # Display results
    print_solution(orders, cost, periods, products)
