import ssl

# Function to create a context for TLS
def create_tls_context():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='path/to/certfile', keyfile='path/to/keyfile')
    return context