class Characteristic:
    BROADCAST = 0
    READ = 0
    WRITE = 0
    NOTIFY = 0
    INDICATE = 0
    WRITE_NO_RESPONSE = 0
    def __init__(self, properties, read_perm, write_perm, fixed_length):
        pass

class ComplexCharacteristic:
    def __init__(self, properties, read_perm, write_perm, max_length, fixed_length):
        pass
