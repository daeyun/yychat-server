from OpenSSL import crypto, SSL
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join, expanduser
from os import makedirs
from time import time


def prepare_ssl_cert():
    """ Generates a private key and a self-signed certificate. """

    config_folder = get_config_folder()

    if not exists(config_folder):
        makedirs(config_folder)

    pem_file = get_cert_path()

    if not exists(pem_file):
        # generate a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        # generate a self-signed cert
        cert = crypto.X509()
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(60*60*24*365*20)
        cert.set_serial_number(int(time()*10000))
        cert.get_subject().O = "CatChat IRC"
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')

        pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, k) +\
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert)

        open(pem_file, "wt").write(pem)


def get_config_folder():
    return expanduser("~/.catchat")


def get_cert_path():
    return join(get_config_folder(), "catchat.pem")
