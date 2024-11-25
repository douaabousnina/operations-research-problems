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

def PL1(*args, **kwargs):
    # Créer le modèle
    model = Model("Problème de mélange")

    # **Entrées dynamiques**
    # Nombre d'ingrédients et propriétés
    try:
        n = int(input("Nombre d'ingrédients : "))
    except ValueError:
        raise numericaltype("ingrédients")
    
    if n < 0:
        raise NegativeValueError(n,"ingrédients")   
    
  
    try:    
        m = int(input("Nombre de propriétés : "))
    except ValueError:
        raise numericaltype("propriétés")  


    if m < 0:
        raise NegativeValueError(m,"propriétés")

    

    # Coûts des ingrédients
    costs = []
    for i in range(n):
        try:
            costs.append(float(input(f"Coût de l'ingrédient {i+1} (€) : ")))
        except ValueError:
            raise numericaltype("coûts")
        if costs[i] < 0:
            raise NegativeValueError(costs[i],"coûts")
    

    # Limites des disponibilités
    availabilities = []
    for i in range(n):
        try:
            availabilities.append(float(input(f"Quantité disponible de l'ingrédient {i+1} (kg) : ")))
        except ValueError:
            raise numericaltype("disponibilités")
        if availabilities[i] < 0:
            raise NegativeValueError(availabilities[i],"disponibilités")


    # Matrice des contributions des ingrédients pour chaque propriété
    contributions = []
    for j in range(m):
        row = []
        for i in range(n):
            try:
                value = float(input(f"Contribution de l'ingrédient {i+1} à la propriété {j+1} : "))
                row.append(value)
            except ValueError:
                raise numericaltype("contributions")    
            if value < 0 or value > 1:
                raise propertyvalue("contributions")
        contributions.append(row)


    # Limites minimales et maximales des propriétés
    # Limites minimales et maximales des propriétés
    property_min = []
    for j in range(m):
        try:
            value = (input(f"Valeur minimale de la propriété {j+1} : "))
            if value ==  "":
                value = 0
            value = float(value)    
            property_min.append(value)
        except ValueError:
            raise numericaltype("valeurs minimales des propriétés")
        if value < 0 or value > 1:
            raise propertyvalue("valeurs minimales des propriétés")

    property_max = []
    for j in range(m):
        try:
            value = (input(f"Valeur maximale de la propriété {j+1} : "))
            if value ==  "":
                value = 1
            property_max.append(float(value))
        except ValueError:
            raise numericaltype("valeurs maximales des propriétés")
        if value < 0 or value > 1:
            raise propertyvalue("valeurs maximales des propriétés")

    # Quantité totale du mélange
    try:
        total_quantity = float(input("Quantité totale du mélange (kg) : "))
    except ValueError:
        raise numericaltype("quantité totale")
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
        for i in range(n):
            print(f"Ingrédient {i+1} : {x[i].x:.2f} kg")
        print(f"Coût total : {model.objVal:.2f} €")
    else:
        print("Aucune solution optimale trouvée.")
if __name__ == '__main__':
    try:
        PL1()        
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")