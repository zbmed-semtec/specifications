from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.graph import ConjunctiveGraph, Dataset
from rdflib.namespace import RDF, RDFS, DCTERMS, NamespaceManager
import sys
import rdflib
import json
from collections import ChainMap


class ProcPofiles:
    validation = ""
    name = ""
    context = ""

    def __init__(self, name):
        self.name = name

    # saves @context attribute from JSON-LD graph in self.context
    def getContextFromJSON(self, file):
        jay = ""
        with open(file) as f:
            try:
                jay = json.load(f)
            except Exception as error:
                print("### ERROR in parsing file", file, "with error", error)

        for i in jay:
            if i == "@context":
                self.context = jay[i]
        return self.context

    # saves @graph attribute from JSON-LD graph in self.graph
    def getGraphFromJSON(self, file):
        jay = ""
        with open(file) as f:
            try:
                jay = json.load(f)
            except Exception as error:
                print("### ERROR in parsing file", file, "with error", error)
        f.close()
        for i in jay:
            if i == "@graph":
                self.graph = jay[i]
        return self.graph

    # saves $validation from inside the @graph attribute of the JSON-LD graph in self.validation
    def getValidationFromJSON(self, file):
        jay = ""
        with open(file) as f:
            try:
                jay = json.load(f)
            except Exception as error:
                print("### ERROR in parsing file", file, "with error", error)

        for i in jay:
            if i == "@graph":
                for j in jay[i]:
                    for k in j:
                        if k == "$validation":
                            self.validation = j[k]

        return self.validation

    # Function to generate RDF for a specified profile using triples according to the Profile Ontology.

    def generate_rdf_for_profile(self, profile_name, label, comment, publisher, is_profile_of, webpage_url, f, outputfilename, filetype):
        print ("Saving current @context attribute from", f)
        self.getContextFromJSON(f)
        print("Saving current $validation triples in @graph attribute from", f)
        self.getValidationFromJSON(f)

        # Defining namespaces
        bioschemas = Namespace(
            "https://bioschemas.org/profiles/")
        prof = Namespace("http://www.w3.org/ns/dx/prof/")
        role = Namespace("http://www.w3.org/ns/dx/prof/role/")
        schema = Namespace("http://schema.org/")

        contextDict = {}
        contextDict = self.context

        contextDict.update(
            {"bioschemas": "https://bioschemas.org/profiles/"})
        contextDict.update({"prof": "http://www.w3.org/ns/dx/prof/"})
        contextDict.update({"role": "http://www.w3.org/ns/dx/prof/role/"})
        contextDict.update({"schema": "http://schema.org/"})

        self.context = contextDict

        rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        owl = Namespace("http://www.w3.org/2002/07/owl/")
        dcterms = Namespace("http://purl.org/dc/terms/")

        print("Parsing", f, "as RDF graph with version", rdflib.__version__)
        # Loading JSON-LD from repository as graph using rdflib
        g = Graph()

        g.parse(source=f, format="application/ld+json")

        print("Parsing completed with size", len(g), "")

        print("Constructing enrichment profiles to be added to the graph.")

        # Creating profile URI
        profile_uri = URIRef(str(bioschemas) + profile_name.capitalize() + "/")

        # Adding triples for webpage
        if webpage_url:
            webpage_descriptor = BNode()
            g.add((profile_uri, prof.hasResource, webpage_descriptor))
            g.add((webpage_descriptor, RDF.type, prof.ResourceDescriptor))
            g.add((webpage_descriptor, DCTERMS.format, URIRef(
                "https://www.iana.org/assignments/media-types/text/html")))
            g.add((webpage_descriptor, prof.role, role.example))
            g.add((webpage_descriptor, prof.role, role.guidance))
            g.add((webpage_descriptor, prof.hasArtifact, URIRef(webpage_url)))

        # Adding triples for profile information
        g.add((profile_uri, RDF.type, prof.Profile))
        g.add((profile_uri, RDFS.label, Literal(label)))
        g.add((profile_uri, RDFS.comment, Literal(comment)))
        g.add((profile_uri, DCTERMS.publisher, URIRef(publisher)))
        g.add((profile_uri, prof.isProfileOf, getattr(schema, is_profile_of)))

        # Adding triples for JSON-LD
        json_ld_descriptor = BNode()
        g.add((profile_uri, prof.hasResource, json_ld_descriptor))
        g.add((json_ld_descriptor, RDF.type, prof.ResourceDescriptor))
        g.add((json_ld_descriptor, DCTERMS.format, URIRef(
            "https://www.iana.org/assignments/media-types/application/ld+json")))
        g.add((json_ld_descriptor, prof.role, role.schema))
        g.add((json_ld_descriptor, prof.role, role.specification))
        g.add((json_ld_descriptor, prof.hasArtifact, URIRef(f)))
        g.add((json_ld_descriptor, prof.hasArtifact, URIRef(
            "https://raw.githubusercontent.com/BioSchemas/bioschemas-dde/main/bioschemas.json")))

        # save the graph with additional profile triples
        # outfile = outputfilename+"."+filetype


        outfile = outputfilename
        print("Writing intermediate results to", outfile)
        g.serialize(destination=outfile, format="json-ld", auto_compact=True)
        print("Writing result to", outfile)

        # Writing graph serialization in turtle format as additional files with same
        # name but with different file ending for filetype ttl.
        turtlefile = outfile[:-5] + ".ttl"
        print("Writing turtle file to", turtlefile)
        g.serialize(destination=turtlefile, format="turtle")
        g.close()


        print("Loading intermediate results again from", outfile)
        jay = self.getGraphFromJSON(outfile)

        # print(type(jay))
        jaydict = {}
        jaydict = dict(ChainMap(*jay))
        print("Adding $validation triples to @graph attribute.")
        jaydict.update({"$validation": self.validation})

        print("Adding @context attribute to @graph")
        resDict = {"@context": self.context, "@graph": [jaydict]}

        print("Dumping result json to", outfile)
        jdump = json.dumps(resDict, indent=4)

        with open(outfile, "w") as f:
            f.write(jdump)

    # Process profile information from the GitHub repository of BioSchemas. All profiles in JSON-LD format
    # which have a release and version tag, are read. Then, only the latest version of the available profiles
    # is taken to generate enriched turtle files.

    def processProfiles(self, filename, profilename):
        # browsable url of the repository
        weburl = "https://github.com/BioSchemas/specifications/blob/master/"

        print("Processing " + profilename)
        webpage_url = weburl+profilename

        # generating additional profile triples to store with retrieved JSON-LD
        self.generate_rdf_for_profile(
            profile_name=profilename,
            label=f"{profilename.capitalize()} Profile",
            comment="",
            publisher=webpage_url,
            is_profile_of=profilename.capitalize(),
            webpage_url=webpage_url,
            f=filename,
            outputfilename=filename,
            filetype="")


# ## Main Script

args = sys.argv
proc = ProcPofiles("proc")

# For each new uploaded JSON-LD file
for arg in args:
    print("Checking current script argument: ", arg)
    if "jsonld" in arg.split("/"):
        print("Found JSON-LD file.")
        arglist = arg.split("/")

        profile_name = arg.split("/")[-1].split(".json")[0].split("_")[0]

        if not "type" in arg:
            # abspath = "https://raw.githubusercontent.com/zbmed-semtec/specifications/master/" + arg
            print("Running processProfiles() for : ",
                profile_name, "with file", arg)
            proc.processProfiles(arg, profile_name)
        else:
            print("Not processing", arg, "because 'type' in path name!")
    else:
        print("No JSON-LD file identified. Skipping process...")