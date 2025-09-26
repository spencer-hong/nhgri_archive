from string import punctuation
import re
import json
from unidecode import unidecode
from pathlib import Path

whitespace_regex = re.compile(r"\s+", re.MULTILINE)
email_regex = re.compile(r'[%\w.+-—:]+@[\w-]+\.[\w.-]+')
parentheses_regex = re.compile(r'\[(?:[^\]]*)\]|\((?:[^)]*)\)')

prefixes_suffixes = ["mr.", "mr", "mrs", "mrs.", "dr", "dr.", "phd", "ph.d", "ph.d.", "ms", "ms.", "m.p.h.", "mph", "m.p.h", "mister", "miss", "doctor","frs", "professor", "prof", "prof."]

prefix_suffix_pattern = r'\b(?:' + "|".join(map(re.escape, prefixes_suffixes)) + r')\b'


class KnowledgeBase:
    """
    A class representing a knowledge base.

    Attributes:
    - knowledge_dict (dict): A dictionary to store knowledge entries.
    """

    def __init__(self, knowledge_base):
        """
        Initialize a new KnowledgeBase object.

        Args:
        - knowledge_base: directory containing necessary knowledge base files
        """
        self.knowledge_dict = {}
        with open(Path(knowledge_base) / "starting_individuals.txt", "r",  encoding="utf-8") as f:
            for i, line in enumerate(f):
                self.knowledge_dict[normalize_name(line.strip().split(';')[0].strip())]= i + 1
        total = i 

        with open(Path(knowledge_base) / "new_individuals.txt", "r",  encoding="utf-8") as f:
            for i, line in enumerate(f):
                if line.strip() not in self.knowledge_dict:
                    self.knowledge_dict[normalize_name(line.strip())] = i+1+total
                else:
                    raise Exception(f"There is a name in new individual list that already exists in the starting list.\nThe name is {line.strip()}")

        with open(Path(knowledge_base) / "starting_individuals_aliases.json", "r") as f:
            self.aliases_starting = json.load(f)
        with open(Path(knowledge_base) / "new_individuals_aliases.json", "r") as f:
            self.aliases_new = json.load(f)
        with open(Path(knowledge_base) / "manual.json", "r") as f:
            self.IDs_manual = json.load(f)

    def get_entry(self, name):
        """
        Retrieve an entry from the knowledge base.

        Args:
        - name: potential name to find in the knowledge base
        Returns:
        - The name and the value associated with the key, or None if the key does not exist.
        """

        cleaned_name = normalize_name(name)

        # if manually checked, return ID
        if cleaned_name in self.IDs_manual:
            return cleaned_name, self.IDs_manual[cleaned_name]
        elif cleaned_name in self.aliases_starting:

            # if the alias only has one individual
            if len(self.aliases_starting[cleaned_name]) == 1:
                return self.aliases_starting[cleaned_name][0], self.knowledge_dict[normalize_name(self.aliases_starting[cleaned_name][0])]
            # if not, there's enough ambiguity for us to not know exactly which individual
            else:
                return cleaned_name, None

        # note that we check the alises of new individuals after the starting individuals
        elif cleaned_name in self.aliases_new:
            if len(self.aliases_new[cleaned_name]) == 1:
                return self.aliases_new[cleaned_name][0], self.knowledge_dict[normalize_name(self.aliases_new[cleaned_name][0])]
            else:
                return cleaned_name, None
        else:
            return cleaned_name, None
        

def normalize_name(name):
    
    if len(name) > 40:
        return name
        
    cleaned_name = name.replace("\n", " ")
    # remove all prefix and suffix
    cleaned_name = re.sub(prefix_suffix_pattern, '', unidecode(cleaned_name.lower()))
    
    
    # remove every leading and trailing commas
    cleaned_name = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', cleaned_name)
    
    # remove everything that is not a alphabetic character and a comma
    
    cleaned_name = re.sub(r"[^a-zA-Z\s,]" ,'', cleaned_name)
    if "," in cleaned_name:
        
        # if there is a comma, there should only be one as its usually lastname, first name
        if len(cleaned_name.split(",")) > 2:
            return name
        else:
            first = cleaned_name.split(",")[0]
            last = cleaned_name.split(",")[-1]

            if len(first) == 1 or len(last) == 1:
                return name
            else:
                return last + " " + first
    
    return cleaned_name
