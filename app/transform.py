from dataclasses import asdict

def class_to_dict(obj):
    if isinstance(obj, dict):
        return {k: class_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [class_to_dict(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        return {k: class_to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    else:
        return obj
    
# Dict to class, class must be a dataclass
def dict_to_class(cls, data):
    if hasattr(cls, "__dataclass_fields__"):
        fieldtypes = {f.name: f.type for f in cls.__dataclass_fields__.values()}
        return cls(**{
            f: dict_to_class(fieldtypes[f], data[f]) if isinstance(data[f], dict) or isinstance(data[f], list) else data[f]
            for f in data
        })
    elif isinstance(data, list):
        return [dict_to_class(cls.__args__[0], item) for item in data]
    else:
        return data