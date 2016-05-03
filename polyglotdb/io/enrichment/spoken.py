
import csv
from collections import defaultdict

from .helper import parse_file

def enrich_speakers_from_csv(corpus_context, path):
    data, type_data = parse_file(path)
    corpus_context.enrich_speakers(data, type_data)

def enrich_discourses_from_csv(corpus_context, path):
    data, type_data = parse_file(path)
    corpus_context.enrich_discourses(data, type_data)
