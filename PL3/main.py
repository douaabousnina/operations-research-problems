import gurobipy as gp
from gurobipy import GRB
import numpy as np

def solve_inventory_problem(periods, demand, holding_cost, ordering_cost, setup_cost, capacity):
    """
    Solve a multi-period inventory optimization problem
    
    Parameters:
    periods (int): Number of time periods
    demand (list): Demand for each period
    holding_cost (float): Cost to hold one unit for one period
    ordering_cost (float): Cost per unit ordered
    setup_cost (float): Fixed cost for placing an order
    capacity (float): Maximum inventory capacity
    
    Returns:
    tuple: (order quantities, inventory levels, total cost)
    """
    
    # Create a new model
    model = gp.Model("Inventory_Optimization")
    
    # Decision Variables
    order = model.addVars(periods, lb=0, vtype=GRB.CONTINUOUS, name="order")
    inventory = model.addVars(periods, lb=0, ub=capacity, vtype=GRB.CONTINUOUS, name="inventory")
    y = model.addVars(periods, vtype=GRB.BINARY, name="setup")
    
    # Objective Function
    # Minimize total cost = ordering cost + setup cost + holding cost
    obj = (gp.quicksum(ordering_cost * order[t] + setup_cost * y[t] + 
           holding_cost * inventory[t] for t in range(periods)))
    model.setObjective(obj, GRB.MINIMIZE)
    
    # Constraints
    # Initial inventory (assuming zero)
    initial_inventory = 0
    
    # Inventory balance constraints
    model.addConstr(inventory[0] == initial_inventory + order[0] - demand[0])
    for t in range(1, periods):
        model.addConstr(inventory[t] == inventory[t-1] + order[t] - demand[t])
    
    # Order quantity must be zero if no setup, and less than M if setup occurs
    M = sum(demand)  # Big M value
    for t in range(periods):
        model.addConstr(order[t] <= M * y[t])
    
    # Optimize the model
    model.optimize()
    
    # Extract results
    order_quantities = [order[t].X for t in range(periods)]
    inventory_levels = [inventory[t].X for t in range(periods)]
    total_cost = model.ObjVal
    
    return order_quantities, inventory_levels, total_cost

def print_solution(order_quantities, inventory_levels, total_cost, periods):
    """Print the solution in a formatted way"""
    print("\nOptimal Solution:")
    print("-" * 50)
    print("Period\tOrder Qty\tInventory Level")
    print("-" * 50)
    for t in range(periods):
        print(f"{t+1}\t{order_quantities[t]:.2f}\t\t{inventory_levels[t]:.2f}")
    print("-" * 50)
    print(f"Total Cost: ${total_cost:.2f}")

# Example usage
if __name__ == "__main__":
    # Example problem parameters
    periods = 4
    demand = [100, 150, 200, 120]  # Demand for each period
    holding_cost = 2  # Cost per unit per period
    ordering_cost = 3  # Cost per unit ordered
    setup_cost = 100  # Fixed cost per order
    capacity = 500  # Maximum inventory capacity
    
    # Solve the problem
    orders, inventory, cost = solve_inventory_problem(
        periods, demand, holding_cost, ordering_cost, setup_cost, capacity
    )
    
    # Print results
    print_solution(orders, inventory, cost, periods)