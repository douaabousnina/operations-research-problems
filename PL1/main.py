from gurobipy import Model, GRB

class NegativeValueError(Exception):    
    def __init__(self, value,type):
        self.value = value
        self.type = type
    def __str__(self):
        return f"Le nombre de {self.type} ne peut pas être négative."

class numericaltype(Exception):
    def __init__(self,type):
        self.type = type
    def __str__(self):
        return f"La valeur de {self.type} doit être un nombre entier."

class propertyvalue(Exception):
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
        raise numericaltype("ingrédients")
    
    if n < 0:
        raise NegativeValueError(n,"ingrédients")   
    
  
    try:    
        m = int(m)
    except ValueError:
        raise numericaltype("propriétés")  


    if m < 0:
        raise NegativeValueError(m,"propriétés")

    

    # Coûts des ingrédients

    for i in costs:
        try:
            i = float(i)
        except ValueError:
            raise numericaltype("coûts")
        if i < 0:
            raise NegativeValueError(i,"coûts")
    

    # Limites des disponibilités
    for i in availabilities:
        try:
            i = float(i)
        except ValueError:
            raise numericaltype("disponibilités")
        if i < 0:
            raise NegativeValueError(i,"disponibilités")


    # Matrice des contributions des ingrédients pour chaque propriété
    for j_index, j in enumerate(contributions):
        for i_index, i in enumerate(j):
            try:
                contributions[j_index][i_index] = float(i)  # Update the original list
            except ValueError:
                raise numericaltype("contributions")    
            if contributions[j_index][i_index] < 0 or contributions[j_index][i_index] > 1:
                raise propertyvalue("contributions")

    # Debugging: Check the types after the loop
    for i in contributions:
        for j in i:
            print(type(j))  # This should now print <class 'float'>

    # Limites minimales et maximales des propriétés
    # Limites minimales et maximales des propriétés
    for j_index, j in enumerate(property_min):
        try:
            if j == "":
                j = 0
            property_min[j_index] = float(j)  # Update the original list
        except ValueError:
            raise numericaltype("valeurs minimales des propriétés")
        if property_min[j_index] < 0 or property_min[j_index] > 1:
            raise propertyvalue("valeurs minimales des propriétés")
        
    for j_index, j in enumerate(property_max):
        try:
            if j == "":
                j = 1
            property_max[j_index] = float(j)  # Update the original list
        except ValueError:
            raise numericaltype("valeurs maximales des propriétés")
        if property_max[j_index] < 0 or property_max[j_index] > 1:
            raise propertyvalue("valeurs maximales des propriétés")


    # Quantité totale du mélange
    try:
        total_quantity = float(total_quantity)
    except ValueError:
        raise numericaltype("quantité totale")
    if total_quantity < 0:
        raise NegativeValueError(total_quantity,"quantité totale")

    print(n, m, costs, contributions, property_min, property_max, total_quantity)


    # **Variables de décision**
    x = model.addVars(n, lb=0, name="IngredientQuantity")

    # **Fonction objectif**
    model.setObjective(sum(costs[i] * x[i] for i in range(n)), GRB.MINIMIZE)

    # **Contraintes**
    # Quantité totale
    model.addConstr(sum(x[i] for i in range(n)) == total_quantity, "TotalQuantity")

    # Contraintes de propriétés (qualité)
    for i in contributions:
        for j in i:
            print(type(j))

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
if __name__ == '__main__':
    try:
        PL1()        
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")