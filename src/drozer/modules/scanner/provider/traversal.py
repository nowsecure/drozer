from pydiesel.reflection import ReflectionException

from drozer.modules import common, Module

class Traversal(Module, common.FileSystem, common.PackageManager, common.Provider, common.Strings, common.ZipFile):

    name = "Test content providers for basic directory traversal vulnerabilities."
    description = "Finds content providers with basic directory traversal vulnerabilities."
    examples = ""
    author = "Nils (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["scanner", "provider"]
    permissions = ["com.mwr.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-a", "--package", "--uri", dest="package_or_uri", help="specify a package, or content uri to search", metavar="<package or uri>")
        parser.add_argument("-s", "--silent", action="store_true", dest="silent", default=False, help="silenty runs module with no stdout noise")

    def execute(self, arguments):
        vulnerable = set([])
        uris = set([])

        flag_path = "/data/data/com.mwr.dz/files/public/"
        flag_name = "traversal_flag"
        self.__traversal_flag = flag_path + flag_name

        self.ensureDirectory(flag_path)
        self.setFileWorldReadableWritableExecutable(flag_path)
        self.writeFile(self.__traversal_flag, "Hello")
        self.setFileWorldReadableWritableExecutable(self.__traversal_flag)

        if arguments.package_or_uri != None and arguments.package_or_uri.startswith("content://"):
            uris.add(arguments.package_or_uri)

            self.__test_uri(arguments.package_or_uri, vulnerable)
        else:
            for uri in self.findAllContentUris(arguments.package_or_uri):
                uris.add(uri)

                self.__test_uri(uri, vulnerable)

        # remove the collection of vulnerable URIs from the set of all URIs
        uris = uris - vulnerable


        if not arguments.silent:
            # print out a report
            self.stdout.write("Not Vulnerable:\n")
            if len(uris) > 0:
                for uri in uris:
                    self.stdout.write("  %s\n" % uri)
            else:
                self.stdout.write("  No non-vulnerable URIs found.\n")

            self.stdout.write("\nVulnerable Providers:\n")
            if len(vulnerable) > 0:
                for uri in vulnerable:
                    self.stdout.write("  %s\n" % uri)
            else:
                self.stdout.write("  No vulnerable providers found.\n")

        return vulnerable

    def __test_uri(self, uri, vulnerable):
        try:
            data = self.contentResolver().read(uri + "/../../../../../../../../../../../../../../../.." + self.__traversal_flag)
        except ReflectionException as e:
            if e.message.find("java.io.FileNotFoundException") >= 0 or \
                e.message.find("java.lang.IllegalArgumentException") >= 0 or \
                e.message.find("java.lang.SecurityException") >= 0 or \
                e.message.find("No content provider") >= 0 or \
                e.message.find("RuntimeException"):
                data = ""
            else:
                raise

        if data != None and len(data) > 0:
            vulnerable.add(uri)

