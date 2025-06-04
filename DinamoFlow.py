from abc import ABC,abstractmethod
from typing import Dict,List,Tuple,Iterable,Optional
import re


class Operation(ABC):
    """
    Clase base abstracta
    """
    @abstractmethod
    def apply(self, record:Dict) -> Tuple[Dict,List[str]]:
        """
        :param record(Dict) Registro a procesar
        :return: Tuple[Dict,List[str] Tupla conteniendo el registro(modificado) y lista de mensajes de error
        """
        pass

class NormalizeAmountOperation(Operation):
    """
    Operation para normalizar campo numerico a float.
    Limpia el valor de caracteres no numericos, menos el separador de decimales
    """
    def __init__(self, field_name:str):
        """
        Inicializa la operacion de normalizacion
        :param field_name: Nombre del campo en el registro que contiene el monto
        """
        self.field_name = field_name

    def apply(self, record:Dict) -> Tuple[Dict,List[str]]:
        errors=[]
        if self.field_name not in record:
            # Si el campo no existe añade un error establece el campo a None.
            errors.append(f"Campo ' {self.field_name}' no encontrado")
            record[self.field_name] = None
            return record,errors

        value = record[self.field_name]

        if value is None:
            # Si value es None, no se normaliza.
            return record,errors

        try:
            # Convertir a string para asegurar que re.sub funcione
            cleaned_value = re.sub(r"[^\d.,-]", "", str(value))
            # Estandariza el separador decimal a '.'
            cleaned_value=cleaned_value.replace(",",".")
            normalized = float(cleaned_value)
            record[self.field_name] = normalized
        except ValueError:
            # Si la conversión falla registrar el error y establecer el campo a None.
            errors.append(f"Valor ' {value}' no se puede convertirse a float")
            record[self.field_name] = None
        return record,errors


class ContextualFieldValidation(Operation):
    """
    Operation para validar un campo.
    """
    def __init__(self, field_name:str, regex: Optional[str]=None):
        """
        Inicializa la operacion de validacion
        :param field_name: Nombre del campo a validar
        :param regex: Expresión regular opcional que el valor del campo debe cumplir.
        """
        self.field_name = field_name
        self.regex = regex

    def apply(self, record:Dict) -> Tuple[Dict,List[str]]:
        errors=[]
        if self.field_name not in record:
            errors.append(f"Campo obligatorio ' {self.field_name}' no encontrado")
        elif self.field_name in record and self.regex and not re.match(self.regex, str(record[self.field_name])):
            errors.append(f"Campo ' {self.field_name}' no cumple formato esperado")
        elif not record[self.field_name]:
            errors.append(f"Campo obligatorio '{self.field_name}' está vacío")
        return record, errors

class RecordContextManager:
    """
    GEstiona y aplica los contextos(Operaciones) a un flujo de registros
    Cada registro tendra un __type__ que determinara q operaciones aplicar
    """
    def __init__(self):
        self.context_operations: Dict[str, List[Operation]] = {}

    def register_context(self, context_type:str, operations:List[Operation]) -> None:
        """
        Registra un nuevo tipo de contexto con su lista de operaciones
        :param context_type: Identifica el tipo de contexto
        :param operations: Lista de operaciones que contiene el tipo de contexto

        """
        if context_type in self.context_operations:
            raise ValueError(f"El contexto '{context_type}' ya está registrado")
        self.context_operations[context_type] = operations

    def process_stream(self, record_iterator: Iterable[Dict])->Iterable[Tuple[Dict,List[str]]]:
        """
        Procesa un registro aplicando las operaciones que contiene el tipo de contexto segun __type__
        :param record_iterator: Iterable que produce diccionario(registro)
        :return: Tupla con registro procesado y lista de errores.
                El registro procesado incluye campos: __estado__ y __errors__
        """
        for record in record_iterator:
            errors = []
            # Establecer valores por defecto para metadatos de procesamiento en el registro.
            record.setdefault("__estado__", "válido")
            record.setdefault("__errors__", [])

            context_type = record.get("__type__")
            if not context_type or context_type not in self.context_operations:
                error_msg=f"Tipo de registro '{context_type}' no reconocido"
                errors.append(error_msg)
                record["__estado__"] = "inválido"
                record["__errors__"].append(error_msg)
                yield record, errors
                continue

            for operation in self.context_operations[context_type]:
                record, op_errors = operation.apply(record)
                errors.extend(op_errors)

            if errors:
                record["__estado__"] = "inválido"
                # Añadir todos los errores acumulados al campo __errors__ del registro.
                # Usar extend para no crear listas anidadas si __errors__ ya tenía algo
                record["__errors__"].extend(errors)

            yield record, errors


if __name__ == '__main__':
    records = [
        {
            "__type__": "order_event",
            "order_id": "ORD789",
            "customer_name": "Luis Vargas",
            "amount": "123,45 EUR",
            "timestamp": "2024-10-26T14:00:00Z"
        },
        {
            "__type__": "order_event",
            "order_id": "ORD100",
            "customer_name": "Bob el Constructor",
            "amount": "no_es_un_numero",
            "timestamp": "2024-13-01T25:61:00Z"
        },
        {
            "__type__": "product_update",
            "product_sku": "SKU_P002",
            "price": None,
            "is_active": "False"
        },
        {
            "__type__": "product_update",
            "product_sku": "SKU_P003",
            "price": "25.00"
        },
        {}
    ]
    manager = RecordContextManager()

    manager.register_context(
        "order_event",
        [
            NormalizeAmountOperation("amount"),
            ContextualFieldValidation("order_id", regex=r"^ORD\d+$"),
            ContextualFieldValidation("customer_name"),
            ContextualFieldValidation("timestamp", regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        ]
    )
    manager.register_context(
        "product_update",
        [
            NormalizeAmountOperation("price"),
            ContextualFieldValidation("product_sku", regex=r"^SKU_\w+$"),
            ContextualFieldValidation("is_active")
        ]
    )

    for i, (processed_record, errors) in enumerate(manager.process_stream(records)):
        print(f"\nRegistro {i}")
        print("\nRegistro procesado:")
        print(processed_record)
        print("\nErrors:", errors)
