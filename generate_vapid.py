from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def generate_vapid_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")
    private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode("utf-8").rstrip("=")
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    x_bytes = public_numbers.x.to_bytes(32, "big")
    y_bytes = public_numbers.y.to_bytes(32, "big")
    public_key_b64 = base64.urlsafe_b64encode(b"\x04" + x_bytes + y_bytes).decode("utf-8").rstrip("=")
    return {"publicKey": public_key_b64, "privateKey": private_key_b64}

vapid_keys = generate_vapid_keys()
print(vapid_keys)
