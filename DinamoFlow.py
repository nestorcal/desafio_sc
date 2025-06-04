from abc import ABC,abstractmethod
from typing import Dict,List,Tuple,Iterable,Optional
import re


class Operation(ABC):
    @abstractmethod
    def apply(self, record:Dict) -> Tuple[Dict,List[str]]:
        pass

class NormalizeAmountOperation(Operation):
    def __init__(self, field_name:str):
        self.field_name = field_name

    def apply(self, record:Dict) -> Tuple[Dict,List[str]]:
        errors=[]
        if self.field_name not in record:
            errors.append(f"Campo ' {self.field_name}' no encontrado")
            record[self.field_name] = None
            return record,errors
        value = record[self.field_name]
        if value is None:
            return record,errors

        try:
            cleaned_value = re.sub(r"[^\d.,-]", "", str(value))
            cleaned_value=cleaned_value.replace(",",".")
            normalized = float(cleaned_value)
            record[self.field_name] = normalized
        except ValueError:
            errors.append(f"Valor ' {value}' no se puede convertirse a float")
            record[self.field_name] = None
        return record,errors


class ContextualFieldValidation(Operation):
    def __init__(self, field_name:str, required: bool=True, regex: Optional[str]=None):
        self.field_name = field_name
        self.required = required
        self.regex = regex

    def apply(self, record:Dict) -> Tuple[Dict,List[str]]:
        errors=[]
        if self.required and self.field_name not in record:
            errors.append(f"Campo obligatorio ' {self.field_name}' no encontrado")
        elif self.field_name in record and self.regex and not re.match(self.regex, str(record[self.field_name])):
            errors.append(f"Campo ' {self.field_name}' no cumple formato esperado")
        return record, errors

class RecordContextManager:
    def __init__(self):
        self._context_operations = {
            "order_event": [
                NormalizeAmountOperation("amount"),
                ContextualFieldValidation("order_id", required=True, regex=r"^ORD\d+$"),
                ContextualFieldValidation("customer_name", required=True),
                ContextualFieldValidation("timestamp", regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            ],
            "product_update": [
                NormalizeAmountOperation("price"),
                ContextualFieldValidation("product_sku", required=True, regex=r"^SKU_\w+$"),
                ContextualFieldValidation("is_active", required=False)
            ]
        }

    def register_context(self, context_type:str, operations:List[Operation]) -> None:
        pass

    def process_stream(self, record_iterator: Iterable[Dict])->Iterable[Tuple[Dict,List[str]]]:
        for record in record_iterator:
            errors = []
            record.setdefault("__estado__", "válido")
            record.setdefault("__errors__", [])

            context_type = record.get("__type__")
            if not context_type or context_type not in self._context_operations:
                errors.append(f"Tipo de registro '{context_type}' no reconocido")
                record["__estado__"] = "inválido"
                yield record, errors
                continue

            for operation in self._context_operations[context_type]:
                record, op_errors = operation.apply(record)
                errors.extend(op_errors)

            if errors:
                record["__estado__"] = "inválido"
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
    for processed_record, errors in manager.process_stream(records):
        print("\nRegistro procesado:")
        print(processed_record)
        print("\nErrors:", errors)
