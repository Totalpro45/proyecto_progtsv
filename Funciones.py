import json
# Cargo el JSON con encoding utf-8 para evitar problemas con las tildes o algun que otro caracter
def cargar_datos_json(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)
    return datos
def leer_csv_tasas(ruta):
    tasas = {}
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            next(f)
            for linea in f:
                    datos = linea.strip().split(',')
                    tasas[datos[0]] = float(datos[1])
        return tasas
    except:
        return {}




 # Uso recursividad para bajar por todos los niveles del diccionario hasta
 # encontrar la key "Precios" que es el dato que me interesa, siendo este mi caso
 # base
def recorrer_json(data, walk, lista_final):
    for keys, values in data.items():
        if keys == "Precios" and isinstance(values, dict):
            prices_product = {}
            for money, prices in values.items():
                if isinstance(prices, (int, float)):
                    prices_product[money] = prices

                if prices_product:
                    rec = {
                        "Municipio": walk[1] if len(walk) > 1 else None,
                        "mipyme": walk[2] if len(walk) > 2 else None,
                        "categoria": walk[4] if len(walk) > 4 else None,
                        "producto": walk[5] if len(walk) > 5 else None,
                        "precio": prices_product
                    }
                    lista_final.append(rec)
        elif isinstance(values, dict):
            new_walk = walk.copy()
            new_walk.append(keys)
            recorrer_json(values, new_walk, lista_final)
# Guardo todo el camino para que me sea mas facil sacar los datos

def filtrar_moneda (lista_fina, moneda, tasas_cambio = None):
  Lista = []
  for walk in lista_fina:
     if "precio" not in walk:
         continue
     prices = walk["precio"]
     precio_final = 0

     if isinstance(prices, dict) and moneda in prices:
         precio_final = prices[moneda]
     elif tasas_cambio and moneda == "CUP":
         if "USD" in prices:
             precio_final = prices["USD"] * tasas_cambio.get("USD", 1)
         elif "MLC" in prices:
             precio_final = prices["MLC"] * tasas_cambio.get("MLC", 1)
         elif "EUR" in prices:
             precio_final = prices["EUR"] * tasas_cambio.get("EUR", 1)

     if precio_final > 0:
         new = {
             "Municipio": walk["Municipio"],
             "mipyme": walk["mipyme"],
             "categoria": walk["categoria"],
             "producto": walk["producto"],
             "precio": precio_final
         }
         Lista.append(new)
  return Lista
# Aseguro que el producto tenga precio en la moneda que elegira el usuario mas adelante
def group_by_products(lista_filtrada):
    products = {}
    for walk in lista_filtrada:
        Product = walk["producto"]
        price = walk["precio"]

        if Product not in products:
            products[Product] = []

        products[Product].append(price)
    return products
# Tuve que agrupar primero por producto para poder sacar el promedio general
# Diccionario: Clave = Nombre Producto -> Valor = Lista de todos sus precios
# encontrados

def remove_duplicates(list):
    seen = set()
    results = []
    for walk in list:
        k = (
            walk.get ("Municipio"),
            walk.get ("mipyme"),
            walk.get ("categoria"),
            walk.get ("producto"),
         )
        if k not in seen:
            seen.add(k)
            results.append(walk)
    return results
# Uso un set() xq asi limpio duplicados q me quedaban al recorrer el json, asi que al convertirlos en tuplas no me da error de unhashable type, ya q el set no acepta diccionarios
def calculate_average(Products):
    promedios = {}
    for product, list_prices in Products.items():
        if len(list_prices) == 0:
            continue
        promedio = round(sum(list_prices) / len(list_prices))
        promedios[product] = promedio
    return promedios

def deviations_average(filtered_data, average):
    result = []
    for walk in filtered_data:
        product = walk ["producto"]
        price = walk["precio"]
        municipio = walk["Municipio"]
        mipyme = walk["mipyme"]
        if product not in average:
            continue
        averages = average[product]
        if average == 0:
            continue
 # La fórmula de la variación porcentual es : (Valor Real - Promedio) / Promedio
        deviation = (price - averages) / averages * 100
 # Asigno puntos según qué tan desviado esté el precio y poder hacer un scatter diciendo cual es mas cara segun la cantidad de puntos que obtiene
        pts = points(deviation)
        rec = {
            "Municipio": municipio,
            "mipyme": walk ["mipyme"],
            "producto": product,
            "precio": price,
            "average": averages,
            "deviation_%": deviation,
            "puntos": pts,
        }
        result.append(rec)
    return result
# la logica de esta funcion es q si no se pasa de un 10% del promedio para la grafica del scatter, aun asi si esta por encima del 0 sume, o si esta por debajo, que reste
def points(deviation_pct):
    if 10 > deviation_pct > 0:
        return 1
    if -10 < deviation_pct < 0:
        return -1
    return int(deviation_pct / 10)

def sum_points(desviations):
    points_mipyme = {}

    for walk in desviations:
        mipyme = walk ["mipyme"]
        points = walk["puntos"]
        if mipyme not in points_mipyme:
            points_mipyme[mipyme] = 0
        points_mipyme[mipyme] += points
    return points_mipyme

def colors (points):
    if points > 40:
        return 'red'
    elif points > 10:
        return 'orange'
    elif points >= 0:
        return 'white'
    elif points >= -10:
        return 'skyblue'
    else:
        return 'green'

def products_area(list):
    cont = {}
    for walk in list:
        municipio = walk["Municipio"]
        if municipio not in cont:
            cont[municipio] = 0
        cont[municipio] += 1
    return cont

def products_peer_mipyme ( lista , nombre_mipyme):
    products = []
    for walk in lista:
        if walk["mipyme"] == nombre_mipyme:
            products.append({
                "producto": walk["producto"],
                "precio": walk["precio"],
            })
    return products

def calclulate_salary(productos, salario):
    results = []
    for walk in productos:
        percent = (walk["precio"] / salario) * 100
        results.append({
            "producto": walk["producto"],
            "porcentaje": percent,
        })
    return results

def prepare_lines (desviaciones):
    data = {}
    for walk in desviaciones:
        product = walk["producto"]
        municipio = walk["Municipio"]
        deviation = walk["deviation_%"]
        if product not in data:
            data[product] = {}
        if municipio not in data[product]:
            data[product][municipio] = []
        data[product][municipio].append(deviation)
    return data

def average_by_municipio(data):
    result = {}

    for producto, municipios in data.items():
        result[producto] = {}
        for municipio, values in municipios.items():
            result[producto][municipio] = sum(values) / len(values)

    return result

def count_by_category(lista_final):
    counts = {}

    for walk in lista_final:
        categoria = walk["categoria"]
        counts[categoria] = counts.get(categoria, 0) + 1

    return counts

def mipymes_aviable(lista):
    mipymes = set()
    for walk in lista:
        if walk["mipyme"] is not None:
            mipymes.add(walk["mipyme"])
    return sorted(mipymes)