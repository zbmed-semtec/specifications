from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, DCTERMS
import sys

class ProcPofiles:
    def __init__(self, name):
        self.name = name

    # Function to generate RDF for a specified profile using triples according to the Profile Ontology.
    def generate_rdf_for_profile(self, profile_name, label, comment, publisher, is_profile_of, webpage_url, f, outputfilename, filetype):
        # Defining namespaces
        bioschemas = Namespace("https://bioschemas.org/profiles/")
        prof = Namespace("http://www.w3.org/ns/dx/prof/")
        role = Namespace("http://www.w3.org/ns/dx/prof/role/")
        schema = Namespace("http://schema.org/")

        # Loading JSON-LD from repository as graph using rdflib
        g = Graph()
        g.parse(file=f, format="application/ld+json")

        # Creating profile URI
        profile_uri = URIRef(str(bioschemas) + profile_name.capitalize() + "/")
        
        # Adding triples for profile information
        g.add((profile_uri, RDF.type, prof.Profile))
        g.add((profile_uri, RDFS.label, Literal(label)))
        g.add((profile_uri, RDFS.comment, Literal(comment)))
        g.add((profile_uri, DCTERMS.publisher, URIRef(publisher)))
        g.add((profile_uri, prof.isProfileOf, getattr(schema, is_profile_of)))

        # Adding triples for webpage
        if webpage_url:
            webpage_descriptor = BNode()
            g.add((profile_uri, prof.hasResource, webpage_descriptor))
            g.add((webpage_descriptor, RDF.type, prof.ResourceDescriptor))
            g.add((webpage_descriptor, DCTERMS.format, URIRef("https://www.iana.org/assignments/media-types/text/html")))
            g.add((webpage_descriptor, prof.role, role.example))
            g.add((webpage_descriptor, prof.role, role.guidance))
            g.add((webpage_descriptor, prof.hasArtifact, URIRef(webpage_url)))

        # Adding triples for JSON-LD
        json_ld_descriptor = BNode()
        g.add((profile_uri, prof.hasResource, json_ld_descriptor))
        g.add((json_ld_descriptor, RDF.type, prof.ResourceDescriptor))
        g.add((json_ld_descriptor, DCTERMS.format, URIRef("https://www.iana.org/assignments/media-types/application/ld+json")))
        g.add((json_ld_descriptor, prof.role, role.schema))
        g.add((json_ld_descriptor, prof.role, role.specification))
        g.add((json_ld_descriptor, prof.hasArtifact, URIRef(jsonld_urls)))
        g.add((json_ld_descriptor, prof.hasArtifact, URIRef("https://raw.githubusercontent.com/BioSchemas/bioschemas-dde/main/bioschemas.json")))
        
        # save the graph with additional profile triples
        outfile = outputfilename+"."+filetype
        g.serialize(destination=outfile, format=filetype)
        print("Writing result to", outfile)

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
                outputfilename=profilename,
                filetype="ttl")
                                        

# ## Main Script

args = sys.argv
proc = ProcPofiles("proc")

# For each new uploaded JSON-LD file
for arg in args:
    print("Checking current script argument: ", arg)
    if "jsonld" in arg.split("/"):
        print("Found JSON-LD file.")
        if "json" in arg.split("."):
            print("Found json file.")
            arglist = arg.split("/")

            profile_name = arg.split("/")[-1].split(".json")[0].split("_")[0]
            print("Running processProfiles() for : ", profile_name)
            proc.processProfiles(arg, profile_name)
