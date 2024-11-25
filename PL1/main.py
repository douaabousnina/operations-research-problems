from gurobipy import Model, GRB

class NegativeValueError(Exception):    
    def __init__(self, value,type):
        self.value = value
        self.type = type
    def __str__(self):
        return f"Le nombre de {self.type} ne peut pas être négative."

class NumericalType(Exception):
    def __init__(self,type):
        self.type = type
    def __str__(self):
        return f"La valeur de {self.type} doit être un nombre entier."

class PropertyValue(Exception):
    def __init__(self,type):
        self.type = type
    def __str__(self):
        return f"La valeur de {self.type} doit être un nombre entre 0 et 1."


def PL1(n,m,costs,availabilities,contributions,property_min,property_max,total_quantity):

    # Créer le modèle
    model = Model("Problème de mélange")

    # **Entrées dynamiques**
    # Nombre d'ingrédients et propriétés
    try:
        n = int(n)
    except ValueError:
        raise NumericalType("ingrédients")
    
    if n < 0:
        raise NegativeValueError(n,"ingrédients")   
    
  
    try:    
        m = int(m)
    except ValueError:
        raise NumericalType("propriétés")  


    if m < 0:
        raise NegativeValueError(m,"propriétés")

    

    # Coûts des ingrédients
    for cost in costs:
        try:
            cost = float(cost)
        except ValueError:
            raise NumericalType("coûts")
        if cost < 0:
            raise NegativeValueError(cost,"coûts")
    

    # Limites des disponibilités
    for availability in availabilities:
        try:
            availability = float(availability)
        except ValueError:
            raise NumericalType("disponibilités")
        if availability < 0:
            raise NegativeValueError(availability,"disponibilités")


    # Matrice des contributions des ingrédients pour chaque propriété
    for j_index, row in enumerate(contributions):
        for i_index, contribution in enumerate(row):
            try:
                contributions[j_index][i_index] = float(contribution)  # Update the original list
            except ValueError:
                raise NumericalType("contributions")    
            if contributions[j_index][i_index] < 0 or contributions[j_index][i_index] > 1:
                raise PropertyValue("contributions")

    # Limites minimales et maximales des propriétés
    for j_index, property in enumerate(property_min):
        try:
            if property == "":
                property = 0
            property_min[j_index] = float(property)
        except ValueError:
            raise NumericalType("valeurs minimales des propriétés")
        if property_min[j_index] < 0 or property_min[j_index] > 1:
            raise PropertyValue("valeurs minimales des propriétés")
        
    for j_index, property in enumerate(property_max):
        try:
            if property == "":
                property = 1
            property_max[j_index] = float(property)
        except ValueError:
            raise NumericalType("valeurs maximales des propriétés")
        if property_max[j_index] < 0 or property_max[j_index] > 1:
            raise PropertyValue("valeurs maximales des propriétés")


    # Quantité totale du mélange
    try:
        total_quantity = float(total_quantity)
    except ValueError:
        raise NumericalType("quantité totale")
    if total_quantity < 0:
        raise NegativeValueError(total_quantity,"quantité totale")
    

    # **Variables de décision**
    x = model.addVars(n, lb=0, name="IngredientQuantity")

    # **Fonction objectif**
    model.setObjective(sum(costs[i] * x[i] for i in range(n)), GRB.MINIMIZE)

    # **Contraintes**
    # Quantité totale
    model.addConstr(sum(x[i] for i in range(n)) == total_quantity, "TotalQuantity")

    # Contraintes de propriétés (qualité)
    for j in range(m):
        model.addConstr(
            sum(contributions[j][i] * x[i] for i in range(n)) >= property_min[j] * total_quantity,
            f"Property{j+1}_Min"
        )
        model.addConstr(
            sum(contributions[j][i] * x[i] for i in range(n)) <= property_max[j] * total_quantity,
            f"Property{j+1}_Max"
        )

    # Résoudre le modèle
    model.optimize()

    # **Afficher les résultats**
    if model.status == GRB.OPTIMAL:
        print("\nSolution optimale trouvée :")
        results = {}
        for i in range(n):
            print(f"Ingrédient {i+1} : {x[i].x:.2f} kg")
            results[f"Ingredient {i+1}"] = x[i].x
        print(f"Coût total : {model.objVal:.2f} €")
        results["Total Cost"] = model.objVal
    else:
        print("Aucune solution optimale trouvée.")
        results = None
    return results
