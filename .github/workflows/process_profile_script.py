from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.graph import ConjunctiveGraph, Dataset
from rdflib.namespace import RDF, RDFS, DCTERMS, NamespaceManager
import sys
import rdflib
import json
from collections import ChainMap

class ProcPofiles:
    def __init__(self, name):
        self.name = name

    def getContextFromJSON(self, file):
        jay = ""
        with open(file) as f:
            jay = json.load(f)
        
        for i in jay:
            if i == "@context":
                self.context = jay[i]
        return self.context
    
    def getValidationFromJSON (self, file):
        jay = ""
        with open(file) as f:
            jay = json.load(f)
        
        for i in jay:
            if i == "@graph":
                for j in jay[i]:
                    for k in j:
                        if k == "$validation":
                            self.validation = j[k]
            
        return self.validation


    # Function to generate RDF for a specified profile using triples according to the Profile Ontology.
    def generate_rdf_for_profile(self, profile_name, label, comment, publisher, is_profile_of, webpage_url, f, outputfilename, filetype):
        self.getContextFromJSON(f)
        self.getValidationFromJSON(f)


        # Defining namespaces
        bioschemas = Namespace("https://discovery.biothings.io/view/bioschemas/")
        prof = Namespace("http://www.w3.org/ns/dx/prof/")
        role = Namespace("http://www.w3.org/ns/dx/prof/role/")
        schema = Namespace("http://schema.org/")

        contextDict = {}
        contextDict = self.context

        contextDict.update({"bioschemas" : "https://discovery.biothings.io/view/bioschemas/"})
        contextDict.update({"prof" : "http://www.w3.org/ns/dx/prof/"})
        contextDict.update({"role" : "http://www.w3.org/ns/dx/prof/role/"})
        contextDict.update({"schema" : "http://schema.org/"})

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

        print(g.subject_objects(), "\n\n#\n")

        # Creating profile URI
        profile_uri = URIRef(str(bioschemas) + profile_name.capitalize() + "/")

        # Adding triples for webpage
        if webpage_url:
            webpage_descriptor = BNode()
            g.add((profile_uri, prof.hasResource, webpage_descriptor))
            g.add((webpage_descriptor, RDF.type, prof.ResourceDescriptor))
            g.add((webpage_descriptor, DCTERMS.format, URIRef("https://www.iana.org/assignments/media-types/text/html")))
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
        g.add((json_ld_descriptor, DCTERMS.format, URIRef("https://www.iana.org/assignments/media-types/application/ld+json")))
        g.add((json_ld_descriptor, prof.role, role.schema))
        g.add((json_ld_descriptor, prof.role, role.specification))
        g.add((json_ld_descriptor, prof.hasArtifact, URIRef(f)))
        g.add((json_ld_descriptor, prof.hasArtifact, URIRef("https://raw.githubusercontent.com/BioSchemas/bioschemas-dde/main/bioschemas.json")))
        
        # save the graph with additional profile triples
        # outfile = outputfilename+"."+filetype

        outfile = outputfilename
        g.serialize(destination=outfile, format="json-ld")
        print("Writing result to", outfile)
        g.close()

        jay = ""
        with open(outfile) as of:
            jay = json.load(of)
        
        # print(type(jay))
        jaydict = {}
        jaydict = dict(ChainMap(*jay))

        jaydict.update({"$validation" : self.validation})
        
        resDict = {"@context" : self.context, "@graph" : [jaydict]}

        jdump = json.dumps(resDict, indent=4)

        with open(outfile, "w") as f:
            f.write(jdump)



    # Process profile information from the GitHub repository of BioSchemas. All profiles in JSON-LD format
    # which have a release and version tag, are read. Then, only the latest version of the available profiles
    # is taken to generate enriched turtle files.
    def processProfiles (self, filename, profilename):        
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
            
        # abspath = "https://raw.githubusercontent.com/zbmed-semtec/specifications/master/" + arg
        print("Running processProfiles() for : ", profile_name, "with file", arg)
        
        
        proc.processProfiles(arg, profile_name)

        # proc.preserveJSON(arg)
