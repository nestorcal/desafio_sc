# Desafio

## Justificacion

Este programa usa patron estrategia/clases, se compara con Funciones Puras y con Eval() en la siguiente tabla, mostrando ventajas y desventajas

| Enfoque          | Ventajas | Desventajes |
|------------------|----------|-------------|
| **Patrón Estrategia**<br>(Clases) | 🔹 Tipado fuerte<br>🔹 Extensible (herencia)<br>🔹 Encapsulamiento claro<br>🔹 Operaciones autocontenidas y reutilizables<br>🔹 Fácil debug | 🔸 Requiere definir clases para cada operación<br>🔸 Menos intuitivo funcional<br> |
| **Funciones Puras** | 🔹 Funciones son mas ligeras que clases<br>🔹 Inmutable<br>🔹 Fácil de testear<br> | 🔸 Poca estructura: Difícil manejar configuraciones complejas<br>🔸 Funciones pueden necesitar muchos parámetros<br> |
| **`eval()`**     | 🔹 Flexibilidad: Permite reglas dinámicas, se cargan desde JSON<br>🔹 Código mínimo<br> | 🔸 Riesgo de seguridad: eval() puede ejecutar código arbitrario<br>🔸 Difícil debuggear y mantener<br> |

El tipo de enfoque dependera del caso
1. **Patrón Estrategia:**
   - Sistemas con muchas operaciones complejas  
   - Equipos grandes que necesitan mantenibilidad a largo plazo

2. **Funciones Puras:**
   - Procesamiento simple de datos  
   - Equipos con preferencia por programación funcional

3. **`eval()`:**
   - **Evitar completamente en producción**
   - Solo para herramientas internas, en entornos controlados  
   - Prototipos que luego se reescriben

## Para la NormalizeAmountOperation

### Como se aseguraria de que esta operacion sea verdaderamente flexible para cualquier campo numerico y no solo para amount o price?
La operación no debe estar acoplada a campos específicos (amount, price), sino servir para cualquier campo numérico (ej: price, total).
Recibir el nombre del campo como parámetro al crear la operacion
```python
class NormalizeAmountOperation(Operation):
    def __init__(self, field_name: str):
        self.field_name = field_name
```
```
ops = [
    NormalizeAmountOperation("amount"),
    NormalizeAmountOperation("price"),
    NormalizeAmountOperation("total")
]
```

### Como manejaria el caso donde el campo a normalizar no existe en el registro? Piense en el estado de la operacion versus el estado del registro

Se decide entre error o valor por defecto según el contexto.

| Enfoque                | Implementación                              | Casos de Uso                          |
|------------------------|---------------------------------------------|---------------------------------------|
| **Error**  | Reportar error si el campo es requerido     | Campos críticos        |
| **Valor por defecto**  | Asignar `0.0` o `None` si el campo falta    | Campos opcionales    |

Tambien teniendo en cuenta que se tiene un estado de registro, se puede implementar añadir el estado de la operacion, esto para auditar que operaciones fallaron y por que; y depurar flujos complejos.

Se puede extender apply (Registro + Errores + Estado de Operación). Tambien process_stream se debera cambiar para manejar el retorno de 2 o 3 elementos segun corresponda.

```
class NormalizeAmountOperation(Operation):

   def apply(self, record: Dict) -> Tuple[Dict, List[str], str]:
      ...
      ...
       # retorna: (registro, errores, estado_operación)
       estado_op = "éxito"  # o "fallo", "omitido"
       return record, errors, estado_op
```



