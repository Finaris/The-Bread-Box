import json
import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool


class BreadBoxNameGenerator:

    def __init__(self, insertion_cost=1, deletion_cost=1, substitution_cost=1):
        """ Creates a new BreadBoxNameGenerator with the provided costs for distance calculation. Costs are
            multiplied with a default cost of 1 (i.e., by default all operations have a cost of 1, but if we wish
            to state that deletions are twice as expensive as the other two then the deletion cost will be 2).

        :param insertion_cost: (float) weight of insertions in a provided name
        :param deletion_cost: (float) weight of deletions in a provided name
        :param substitution_cost: (float) weight of substitutions in a provided name
        """
        self._insertion_cost = insertion_cost
        self._deletion_cost = deletion_cost
        self._substitution_cost = substitution_cost

    def _weighted_levenshtein_distance(self, a, b, i=None, j=None, memo={}):
        """Calculates a weighted Levenshtein distance between two strings A and B. All weights are multiplied to 1 for
            determining an overall cost.

        :param a: (str) source word
        :param b: (str) destination word
        :param i: (int) first i characters of a
        :param j: (int) first j characters of b
        :param memo: (dict) A memo containing a mapping for the levenshtein distance between two words.
        :return: (tuple) the number of operations and the score of these operations
        """
        if (a, b, i, j) in memo:
            return memo[a, b, i, j]

        # Initialize i and j to the lengths of their respective words.
        if i is None:
            i = len(a)
        if j is None:
            j = len(b)

        # Base cases (empty strings).
        if i == 0:
            return j
        if j == 0:
            return i

        # Check if the last characters of the strings match.
        sub_cost = 0 if a[i-1] == b[j-1] else 1

        # Return the minimum of deleting from s, deleting from t (insertion for s), and delete from both (substitution).
        memo[a, b, i, j] = min(self._weighted_levenshtein_distance(a, b, i-1, j) + self._insertion_cost * 1,
                               self._weighted_levenshtein_distance(a, b, i, j-1) + self._deletion_cost * 1,
                               self._weighted_levenshtein_distance(a, b, i-1, j-1) + self._substitution_cost * sub_cost)
        return memo[a, b, i, j]

    def best_breads_for_name(self, name, use_all_breads=False, threading=None):
        """ Provides a sorted list of matching bread names given an individual's name.

        :param name: (str) an individual's name
        :param use_all_breads: (bool) determines whether or not we scrape wikipedia for breads
        :param threading: (int) number of threads to use if multithreading is desired (must be greater than 0)
        :return: (list) sorted list of bread names based off of weighted levenshtein distance to name
        """
        every_bread = self._all_breads() | self._bread_terms() if use_all_breads else self._bread_terms()

        if threading:
            pool = ThreadPool(threading)
            bread_weights = pool.map(lambda bread: (bread,
                                                    self._weighted_levenshtein_distance(name.lower(), bread.lower())),
                                     every_bread)
            return list(map(lambda bread_weight: bread_weight[0],
                            sorted(bread_weights, key=lambda bread_weight: bread_weight[1])))
        return sorted(every_bread,
                      key=lambda bread: self._weighted_levenshtein_distance(name.lower(), bread.lower()))

    @staticmethod
    def _json_to_python_list(filename):
        """ Reads a JSON file and converts it into a Python list.

        :param filename: (str) path to a JSON file to open
        :return: (list) iterable of elements stored in JSON file
        """
        with open(filename) as file:
            return json.load(file)

    @staticmethod
    def _bread_terms():
        """ Loads an additional JSON of bread-related terms for name generation.

        :return: (set) set of fun bread-related terms
        """
        bread_terms_path = 'additional_bread_terms.json'
        return set(BreadBoxNameGenerator._json_to_python_list(bread_terms_path))

    @staticmethod
    def _all_breads():
        """ Queries Wikipedia for a list of all bread names (https://en.wikipedia.org/wiki/List_of_breads).

        :return: (set) all bread names
        """
        session = requests.session()

        # Relatively static information used to fetch information from Wikipedia. This information may change
        # in the future.
        base_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page": "List_of_breads",
            "format": "json",
            "section": 1
        }

        # Get the raw (no pun intended, this bread is very cooked) name for each bread, then handle special names.
        bread_types_raw = session.get(url=base_url, params=params)
        bread_types = BeautifulSoup(json.loads(bread_types_raw.content.decode('utf-8'))
                                    ['parse']['text']['*'], "html.parser")
        raw_bread_names = [tr.contents[1].get_text().strip() for tr in bread_types.findAll("tr")[1:]]

        # Process the raw bread names by normalizing them and flattening them into a single list.
        bread_names = set()
        for bread_name in raw_bread_names:
            bread_names |= BreadBoxNameGenerator._normalize_bread_name(bread_name)

        return bread_names

    @staticmethod
    def _normalize_bread_name(bread_name):
        """ Normalizes the bread's name for usage in edit distance calculation.
            TODO: Capitalization check does not work completely for non-Latin alphabet capitals.

        :param bread_name: (str) Raw name of a bread parsed from Wikipedia
        :return: (set) set containing the normalized bread name along with any others in the same field
        """
        # Defines a list of exceptions during normalization when considering capital words, as well as characters
        # to remove.
        normalization_capitalization_exceptions = {" ", "'"}
        illegal_characters = {"\"", "’"}

        # Strip away any unnecessary characters (special characters are okay).
        for illegal_character in illegal_characters:
            bread_name = bread_name.replace(illegal_character, "")

        # Some words have new words begin in the middle - this happens when a word is capitalized in the center.
        # Also break into components based on certain tokens like "or" or a comma.
        components, last_i = set(), 0
        chunks = [comma_split.strip() for or_split in bread_name.split("or") for comma_split in or_split.split(',')]
        for chunk in chunks:
            # First, process each chunk into its own set of words.
            for i, char in enumerate(chunk):
                # Ignore the first component of the word.
                if i == 0:
                    continue

                # If there is a capital letter, add the previous word in (unless it is preceded by a space).
                if 65 <= ord(char) <= 90 and chunk[i-1] not in normalization_capitalization_exceptions:
                    components.add(chunk[last_i:i])
                    last_i = i
            # Add the last word we were counting
            else:
                components.add(chunk[last_i:len(chunk)])

            last_i = 0

        return components

# Custom weights used in our name generator. Give less cost to insertions.
INSERTION_COST = 1
DELETION_COST = 2
SUBSTITUTION_COST = 2

if __name__ == "__main__":
    generator = BreadBoxNameGenerator(insertion_cost=INSERTION_COST,
                                      deletion_cost=DELETION_COST,
                                      substitution_cost=SUBSTITUTION_COST)

    name = ""
    first_last = name.split()
    thread_count = 16

    # Check first, last, and first+last name combinations.
    print(generator.best_breads_for_name(first_last[0], threading=thread_count))
    print(generator.best_breads_for_name(first_last[1], threading=thread_count))
    print(generator.best_breads_for_name(name, threading=thread_count))
