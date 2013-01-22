import os

from mwr.common import cli
from mwr.droidhg.ssl.provider import Provider

class SSLManager(cli.Base):
    """
    mercury ssl {ca,keypair,truststore} [OPTIONS]
    
    Run the Mercury SSL Manager.

    The SSL Manager allows you to generate key material to enable TLS for your Mercury connections.
    """

    def __init__(self):
        cli.Base.__init__(self)
        
        self._parser.add_argument("type", choices=["ca", "keypair", "truststore"], help="the type of key material to create", nargs='?')
        self._parser.add_argument("subject", help="the subject CN, when generating a keypair", nargs='?')
        self._parser.add_argument("--bks", help="also build a BouncyCastle store (for Android), using the store and key password (keypair only)", metavar=("STORE_PW", "KEY_PW"), nargs=2)
    
    def do_create(self, arguments):
        """create some new key material"""
        
        provider = Provider()
        
        if arguments.type == "ca":
            self.__create_ca(provider, arguments)
        elif arguments.type == "keypair":
            self.__create_keypair(provider, arguments)
        elif arguments.type == "truststore":
            provider.make_bks_trust_store()
        else:
            print "Unexpected type:", arguments.type
    
    def do_show(self, arguments):
        """show SSL configuration information"""
        
        provider = Provider()
        
        if provider.key_material_exists():
            print "SSL has been provisioned:"
            print "          SSL Key:", provider.key_exists() and "EXISTS" or "MISSING"
            print "  SSL Certificate:", provider.certificate_exists() and "EXISTS" or "MISSING"
            print "         Key Pair:", provider.key_material_valid() and "VALID" or "INVALID"
        else:
            print "SSL has not been provisioned."
        
    def __create_ca(self, provider, arguments):
        """
        Creates a new SSL CA.
        """
        
        path = provider.ca_path(skip_default=True)

        if path == None or not os.path.exists(path):
            path = os.path.abspath(os.curdir)
        
        if provider.keypair_exists("mercury-ca", skip_default=True):
            print "A Mercury CA already exists at", path
            
            if self.confirm("Do you want to overwrite the existing CA?") == "n":
                print "Aborted."
                
                return
            
        if provider.provision(path):
            print "Created Authority."
        else:
            print "There was a problem whilst creating the authority."
            
    def __create_keypair(self, provider, arguments):
        """
        Creates an SSL Keypair, signing it with the built-in CA.
        """
        
        if arguments.subject == None or arguments.subject == "":
            print "Please specify the subject CN."
        else:
            if provider.keypair_exists(arguments.subject):
                print "A key pair with CN=%s already exists." % (arguments.subject)
            
                if self.confirm("Do you want to overwrite the existing key pair?") == "n":
                    print "Aborted."
                    
                    return
                
            key, certificate = provider.create_keypair(arguments.subject)
            
            if arguments.bks:
                p12_path, export_password = provider.make_pcks12(arguments.subject, key, certificate)
                bks_path = provider.make_bks_key_store(arguments.subject, p12_path, export_password, arguments.bks[0], arguments.bks[1])
                
                if bks_path != None:
                    print "Created SSL keypair, %s: %s" % (arguments.subject, bks_path)
                else:
                    print "There was a problem creating the BKS KeyStore."
            else:
                print "Created keypair."
                